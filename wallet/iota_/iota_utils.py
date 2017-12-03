import functools
import logging
import time
from datetime import datetime

from django.utils.timezone import make_aware

from wallet import user_utils
from wallet.iota_ import InsufficientBalanceException, trytes2string
from wallet.iota_.iota_api import IotaApi
from wallet.models import IotaAddress, IotaTransaction, IotaBalance
from wallet.user_utils import get_user_safe

logger = logging.getLogger(__name__)


def api_resolver(func):
    @functools.wraps(func)
    def wrapper(user, **kwargs):
        api = IotaApi(seed=user.iotaseed.seed)
        return func(user=user, api=api, **kwargs)

    return wrapper


@api_resolver
def get_new_address(user, with_checksum=False, api=None):
    """
    Creates a new IOTA address, which is not attached to the tangle.
    :param user: user object containing seed
    :param with_checksum: append checksum to returned address
    :param api: IOTA api object (should be resolved by decorator)
    :return: new address in the IOTA network (not attached to the Tangle)
    """
    # create and store new address
    new_address, new_address_witch_checksum = api.get_new_address()
    IotaAddress.objects.update_or_create(user=user, address=new_address)

    logger.info('Generated address %s (cs:{}) for user %s', new_address, with_checksum, user)

    return new_address_witch_checksum if with_checksum else new_address


@api_resolver
def get_balance(user, api=None):
    balance = api.get_account_balance()
    stored_balance, _ = IotaBalance.objects.get_or_create(user=user)
    stored_balance.balance = balance
    stored_balance.save()
    logger.info('Fetched balance for user %s (balance: %i)', user, balance)
    return balance


@api_resolver
def get_account_data(user, api=None):
    num_addresses = IotaAddress.objects.filter(user=user).count()
    # start_index = max(0, num_addresses - 4)  # decrease by number, which might be used in bundle
    start_index = 0
    account_data = api.get_account_data(inclusion_states=True, start=start_index)

    logger.debug('Requesting user data for user %s', user)

    # convert account data
    balance = account_data['balance']
    addresses = account_data['addresses']
    bundles = account_data['bundles']
    updated_transactions = update_bundles(bundles=bundles, user_addresses=addresses, owner=user)

    # update addresses of user
    fetched_addresses = {IotaAddress(user=user, address=trytes2string(a)) for a in addresses}
    stored_addresses = set(IotaAddress.objects.filter(user=user))
    for new_address in fetched_addresses - stored_addresses:
        new_address.save()

    logger.info('Fetched data for user %s (#updated transactions: %i, balance: %i)',
                user, len(updated_transactions), balance)

    # ToDo: update unconfirmed transactions

    # get update transactions from database
    transactions = get_cached_transactions(user=user)
    return balance, transactions


def get_cached_transactions(user):
    return list(IotaTransaction.objects.filter(owner=user).order_by('-execution_time'))[:4]


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
        bundle = api.transfer(receiver_address=receiving_address,
                              change_address=change_address,
                              value=value,
                              message=message)

        pow_execution_time = time.time() - pow_start_time
        logger.info('Performed PoW in %i secs', pow_execution_time, extra={'pow_time': pow_execution_time})

        # check for consistency
        transaction = bundle.transactions[0]
        assert trytes2string(transaction.address) == receiving_address

        # save successfully executed transaction twice (for sender and receiver)
        sender_transaction = extract_transaction(transaction=transaction, bundle=bundle, owner=sender)
        sender_transaction.direction = IotaTransaction.OUT_GOING if value else IotaTransaction.NEUTRAL
        sender_transaction.is_confirmed = False
        sender_transaction.sender = sender
        sender_transaction.receiver = receiver
        sender_transaction.save()
        receiver_transaction = extract_transaction(transaction=transaction, bundle=bundle, owner=receiver)
        receiver_transaction.direction = IotaTransaction.IN_GOING if value else IotaTransaction.NEUTRAL
        receiver_transaction.is_confirmed = False
        receiver_transaction.sender = sender
        receiver_transaction.receiver = receiver
        receiver_transaction.save()

        # ToDo: Check receiver in the case of zero value

        # inform receiver via mail
        user_utils.send_token_received_email(request=request,
                                             sender=sender,
                                             receiver=receiver,
                                             is_new=is_new,
                                             amount=value,
                                             message=message)
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


def extract_transaction(transaction, bundle, owner, user_addresses=None):
    if not user_addresses:
        user_addresses = []

    receiver_address = trytes2string(bundle.transactions[0].address)
    receiver = user_for_address(receiver_address)

    # try to find sender (e.g. if value no zero)
    sender, sender_address = (None, None)
    if len(bundle.transactions) >= 4:
        # assumption: change address is known address of sender
        sender_address = trytes2string(bundle.transactions[3].address)
        sender = user_for_address(sender_address)

    # determine direction of transaction
    direction = IotaTransaction.OUT_GOING
    if transaction.value == 0:
        direction = IotaTransaction.NEUTRAL
    elif receiver_address in [trytes2string(a) for a in user_addresses]:
        direction = IotaTransaction.IN_GOING

    return IotaTransaction(owner=owner,
                           sender=sender,
                           receiver=receiver,
                           sender_address=sender_address,
                           receiver_address=receiver_address,
                           bundle_hash=trytes2string(transaction.bundle_hash),
                           transaction_hash=trytes2string(transaction.hash),
                           value=transaction.value,
                           execution_time=make_aware(datetime.fromtimestamp(transaction.timestamp)),
                           is_confirmed=transaction.is_confirmed,
                           direction=direction)


def update_bundles(bundles, user_addresses, owner):
    fetched_transactions = {}
    for bundle in bundles:
        # on transfer results in four transactions within a bundle (https://iota.readme.io/docs/bundles)
        # actual movement of IOTA is stored in first transaction
        if len(bundle.transactions) >= 3:
            extracted_transaction = extract_transaction(transaction=bundle.transactions[0],
                                                        user_addresses=user_addresses,
                                                        bundle=bundle,
                                                        owner=owner)
            fetched_transactions[extracted_transaction.transaction_hash] = extracted_transaction
        else:
            for t in bundle.transactions:
                extracted_transaction = extract_transaction(transaction=t,
                                                            user_addresses=user_addresses,
                                                            bundle=bundle,
                                                            owner=owner)
                fetched_transactions[extracted_transaction.transaction_hash] = extracted_transaction

    # determine and store new/changed transactions
    new_or_changed_transactions = []
    already_stored = {t.transaction_hash: t for t in IotaTransaction.objects.filter(owner=owner)}
    for transaction_hash, extracted_transaction in fetched_transactions.items():

        # check if new
        if transaction_hash not in already_stored:
            extracted_transaction.save()
            new_or_changed_transactions.append(extracted_transaction)

        # check if state has changed and update in database
        elif already_stored[transaction_hash].is_confirmed != extracted_transaction.is_confirmed:
            old_transaction = already_stored[transaction_hash]
            old_transaction.is_confirmed = extracted_transaction.is_confirmed
            old_transaction.save()
            new_or_changed_transactions.append(old_transaction)

    return new_or_changed_transactions
