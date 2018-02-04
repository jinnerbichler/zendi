import functools
import logging
import time
from datetime import datetime
from typing import List, Optional

import pytz
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q
from django.utils.timezone import make_aware
from iota import TransactionHash, Transaction, Bundle

from web import user_utils
from iotaclient.iota_ import InsufficientBalanceException, trytes2string, string2trytes_bytes
from iotaclient.iota_.iota_api import IotaApi
from iotaclient.models import IotaAddress, IotaTransaction, IotaBalance
from web.user_utils import get_user_safe

logger = logging.getLogger(__name__)


def api_resolver(func):
    @functools.wraps(func)
    def wrapper(user, **kwargs):
        if 'api' not in kwargs:
            api = IotaApi(seed=user.iotaseed.seed)
        else:
            api = kwargs['api']
        return func(user=user, api=api, **kwargs)

    return wrapper


@api_resolver
def get_new_address(user, with_checksum=False, api=None):
    """
    Creates a new IOTA address, which is not attached to the tangle. Note that the generated address is
    not attached to the Tangle.
    :param user: user object containing seed
    :param with_checksum: append checksum to returned address
    :param api: IOTA api object (should be resolved by decorator)
    :return: new address in the IOTA network (not attached to the Tangle)
    """
    # create and store new address
    num_addresses = IotaAddress.objects.filter(user=user).count()
    new_address, new_address_witch_checksum = api.get_new_address(start=num_addresses)

    # store newly generated address
    IotaAddress.objects.update_or_create(user=user, address=new_address)

    logger.info('Generated address %s for user %s', new_address, user)

    return new_address_witch_checksum if with_checksum else new_address


@api_resolver
def get_balance(user, api=None):
    balance = api.get_account_balance()
    stored_balance, _ = IotaBalance.objects.get_or_create(user=user)
    stored_balance.balance = balance
    stored_balance.save()
    logger.info('Fetched balance for user %s (balance: %i)', user, balance)
    return balance


# noinspection PyBroadException
@api_resolver
def get_account_data(user, api=None):
    # replay_bundles()

    # check unconfirmed transactions  # ToDo: find unconfirmed transaction by database queries (faster)
    query = (Q(sender=user) | Q(receiver=user)) & Q(is_confirmed=False)
    unconfirmed_transactions = list(IotaTransaction.objects.filter(query))
    updated_transactions = update_confirmation_states(transactions=unconfirmed_transactions, api=api)

    logger.debug('Updated {} inclusion states of user {}'.format(len(updated_transactions), user))

    try:
        # fetch general account data
        num_addresses = IotaAddress.objects.filter(user=user).count()
        start_index = max(0, num_addresses - 1)  # decrease by number, which might be used in bundle
        logger.debug('Requesting user data for user %s', user)
        account_data = api.get_account_data(inclusion_states=True, start=start_index)

        # convert account data (only difference because start address was not 0)
        balance_diff = account_data['balance']
        new_addresses = account_data['addresses']
        new_bundles = account_data['bundles']

        # update addresses of user
        fetched_addresses = {IotaAddress(user=user, address=trytes2string(a)) for a in new_addresses}
        stored_addresses = set(IotaAddress.objects.filter(user=user))
        for new_address in fetched_addresses - stored_addresses:
            new_address.save()

        # update stored transactions
        user_addresses = [str(a) for a in IotaAddress.objects.filter(user=user)]
        updated_transactions += update_bundles(bundles=new_bundles, user_addresses=user_addresses, user=user)

        logger.info('Fetched data for user %s (#updated transactions: %i, balance_diff: %i)',
                    user, len(updated_transactions), balance_diff)
    except:
        logger.exception('Error while fetching new bundles.')

    # get update transactions from database
    return get_cached_transactions(user=user)


def get_cached_transactions(user):
    return list(IotaTransaction.objects
                .filter(Q(sender=user) | Q(receiver=user))
                .order_by('-attachment_time'))


# noinspection PyBroadException
def send_tokens(request, sender_mail, receiver_mail, value, message=None):
    # get proper users
    _, sender = get_user_safe(email=sender_mail)
    is_new, receiver = get_user_safe(email=receiver_mail)

    # check balance
    api = IotaApi(seed=sender.iotaseed.seed)
    balance = api.get_account_balance()
    if balance < value:
        raise InsufficientBalanceException(user=str(sender), proposed_amount=value, balance=balance)

    change_address = get_new_address(sender)
    receiving_address = get_new_address(receiver)

    logger.info('Sending %i IOTA from %s to %s (address: %s, new: %s)',
                value, sender, receiver, receiving_address, is_new)

    try:
        # send transaction
        pow_start_time = time.time()
        bundle = api.transfer(receiver_address=receiving_address, change_address=change_address,
                              value=value, message=message)

        pow_execution_time = time.time() - pow_start_time
        logger.info('Performed PoW in %i secs', pow_execution_time, extra={'pow_time': pow_execution_time})

        # check for consistency
        transaction = bundle.tail_transaction
        assert trytes2string(transaction.address) == receiving_address

        # save successfully executed transaction (for sender and receiver)
        iota_transaction = extract_transaction(transaction=transaction, bundle=bundle)
        iota_transaction.is_confirmed = False
        iota_transaction.sender = sender
        iota_transaction.receiver = receiver
        iota_transaction.save()

        # ToDo: Check receiver in the case of zero value

        # inform receiver via mail
        user_utils.send_token_received_email(request=request, sender=sender, receiver=receiver,
                                             is_new=is_new, amount=value, message=message)
        return bundle
    except Exception as e:
        logger.exception('Error while transferring %i IOTA from %s to %s (address %s, new:%s)',
                         value, sender, receiver, receiving_address, is_new)
        raise e


def user_for_address(address):
    try:
        # check if email is attached to address
        user = IotaAddress.objects.get(address=address).user
        logger.debug('Found attached user %s for address %s', user, address)
    except IotaAddress.DoesNotExist:
        user = None
    return user


def extract_transaction(transaction, bundle, owner_addresses=None):
    # type: (Transaction, Bundle, User, Optional(List[str])) -> IotaTransaction
    """
    Extract user and iota transaction for a raw transaction object. Note that object are just created, but
    not saved in database. They must be saved explicitly.
    :param transaction: Raw TTransaction object
    :param bundle:  Raw Bundle object
    :param owner_addresses: Optional list of owning user addresses
    :return: Extracted address
    """
    if not owner_addresses:
        # noinspection PyUnusedLocal
        owner_addresses = []

    receiver_address = trytes2string(bundle.transactions[0].address)
    receiver = user_for_address(receiver_address)  # might be None

    # try to find sender (e.g. if value no zero)
    sender, sender_address = (None, None)
    if len(bundle.transactions) >= 4:
        # assumption: change address is known address of sender
        sender_address = trytes2string(bundle.transactions[3].address)
        sender = user_for_address(sender_address)

    # create iota transaction
    tail_transaction = bundle.tail_transaction
    tail_transaction_hash = trytes2string(tail_transaction.hash)  # tail transaction
    attachment_time = make_aware(datetime.fromtimestamp(tail_transaction.attachment_timestamp / 1000),
                                 timezone=pytz.UTC)
    iota_transaction = IotaTransaction(sender=sender,
                                       receiver=receiver,
                                       sender_address=sender_address,
                                       receiver_address=receiver_address,
                                       bundle_hash=trytes2string(transaction.bundle_hash),
                                       value=transaction.value,
                                       attachment_time=attachment_time,
                                       is_confirmed=transaction.is_confirmed,
                                       tail_transaction_hash=tail_transaction_hash)
    return iota_transaction


def update_bundles(bundles, user_addresses, user):
    fetched_transactions = {}

    # filter duplicates by extracting one with newer attachment timestamp of tail transaction
    # This might happen when bundle are reattached --> on bundle for each reattachment
    unique_bundles = {}
    for bundle in bundles:
        bundle_hash = bundle.hash

        # check if newer tail transaction
        if bundle_hash in unique_bundles:
            existing_bundle = unique_bundles[bundle_hash]
            existing_timestamp = existing_bundle.tail_transaction.attachment_timestamp
            new_timestamp = bundle.tail_transaction.attachment_timestamp
            if new_timestamp > existing_timestamp:
                unique_bundles[bundle_hash] = bundle
        else:
            unique_bundles[bundle_hash] = bundle
    bundles = list(unique_bundles.values())

    for bundle in bundles:
        # on transfer results in four transactions within a bundle (https://iota.readme.io/docs/bundles)
        # actual movement of IOTA is stored in first transaction

        if len(bundle.transactions) >= 3:
            extracted_transaction = extract_transaction(transaction=bundle.transactions[0],
                                                        owner_addresses=user_addresses,
                                                        bundle=bundle)
            fetched_transactions[extracted_transaction.bundle_hash] = extracted_transaction
        else:
            for t in bundle.transactions:

                # ignore zero value transactions
                if t.value == 0:
                    continue

                extracted_transaction = extract_transaction(transaction=t,
                                                            owner_addresses=user_addresses,
                                                            bundle=bundle)
                fetched_transactions[extracted_transaction.bundle_hash] = extracted_transaction

    # ToDo: Filter duplicate bundle hashes --> TEST
    # fetched_transactions = list({t.bundle.hash: t for t in fetched_transactions}.values())

    # determine and store new/changed transactions
    new_or_changed_transactions = []
    already_stored = {t.bundle_hash: t for t in get_cached_transactions(user=user)}
    for bundle_hash, extracted_transaction in fetched_transactions.items():

        # check if new
        if bundle_hash not in already_stored:
            extracted_transaction.save()
            new_or_changed_transactions.append(extracted_transaction)

        # check if state has changed and update in database
        else:
            old_transaction = already_stored[bundle_hash]
            old_transaction.is_confirmed = extracted_transaction.is_confirmed
            old_transaction.tail_transaction_hash = extracted_transaction.tail_transaction_hash
            old_transaction.attachment_time = extracted_transaction.attachment_time
            old_transaction.save()
            new_or_changed_transactions.append(old_transaction)

    return new_or_changed_transactions


def update_confirmation_states(transactions, api):
    updated_transactions = []

    # check if empty
    if not transactions:
        return []

    # a set because transaction hashes may appear twice
    transaction_hashes = list({t.tail_transaction_hash for t in transactions})

    # fetch new states
    current_milestone = api.get_node_info()['latestSolidSubtangleMilestone']
    inclusion_states = api.get_inclusion_states(transactions=transaction_hashes, milestone=current_milestone)

    # update states
    for i in range(len(transaction_hashes)):
        for transaction in [t for t in transactions if t.tail_transaction_hash == transaction_hashes[i]]:
            # check if status has changed
            if transaction.is_confirmed != inclusion_states[i]:
                transaction.is_confirmed = inclusion_states[i]
                transaction.save()
                updated_transactions.append(transaction)

    return updated_transactions


# noinspection PyBroadException
def replay_bundles():
    logger.info('############### Starting REPLAY of transactions...')
    start_time = time.time()

    replayed_transactions = []
    unconfirmed_transactions = IotaTransaction.objects.filter(is_confirmed=False)
    for transaction in unconfirmed_transactions:

        # check if old version of transaction (hash of tail transaction is not set)
        if not transaction.tail_transaction_hash:
            continue

        # only replay "sending transactions"initiated on the platform
        if transaction.sender:
            try:

                if transaction.replay_count > settings.IOTA_REPLAY_MAX_COUNT:
                    logger.warning('Skipping replay of transaction {}. Max number of {} replays reached'
                                   .format(transaction.tail_transaction_hash, transaction.replay_count))
                    continue

                api = IotaApi(seed=transaction.sender.iotaseed.seed)
                tail_hash = TransactionHash(string2trytes_bytes(transaction.tail_transaction_hash))

                # update confirmation state
                if not update_confirmation_states(transactions=[tail_hash], api=api):
                    # replay transaction
                    replayed_trytes = api.replay_bundle(transaction=tail_hash)['trytes']
                    replayed = [Transaction.from_tryte_string(t) for t in replayed_trytes]

                    replayed_transactions.append(transaction)

                    logger.info('Replayed transaction {} (bundle:{}) for user {}'.format(
                        tail_hash, transaction.bundle_hash, transaction.sender))

                    # update transaction --> hashes of transactions have changed.
                    # Hash of bundle itself stayed the same
                    new_transaction_hash = next((t.hash for t in replayed if t.value == transaction.value))
                    transaction.transaction_hash = trytes2string(new_transaction_hash)
                    transaction.tail_transaction_hash = trytes2string(replayed[0].hash)  # tail transaction
                    # ToDO: update attachment timestamp as well
                    transaction.replay_count += 1
                    transaction.save()
            except:
                logger.exception('Error while replaying transaction {}'.format(transaction))

    execution_time = time.time() - start_time
    logger.info('############### Finished REPLAY of {} transactions in {} seconds.'.format(
        len(replayed_transactions), execution_time))
