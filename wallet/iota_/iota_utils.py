import collections
import logging
import functools
import time
from datetime import datetime

from django.utils.timezone import make_aware
from pytz import UTC

from wallet import user_utils
from wallet.iota_ import InsufficientBalanceException, trytes2string
from wallet.iota_.iota_api import IotaApi
from wallet.models import IotaAddress, IotaTransaction, IotaBalance
from wallet.user_utils import get_user_safe

logger = logging.getLogger(__name__)

Transaction = collections.namedtuple('Transaction', 'bundle_hash is_confirmed address email time hash value')


def api_resolver(func):
    @functools.wraps(func)
    def wrapper(user, **kwargs):
        api = IotaApi(seed=user.iotaseed.seed)
        return func(user=user, api=api, **kwargs)

    return wrapper


@api_resolver
def get_new_address(user, api=None):
    """
    Creates a new IOTA address, which is not attached to the tangle.
    :param user: user object containing seed
    :param api: IOTA api object (should be resolved by decorator)
    :return: new address in the IOTA network (not attached to the Tangle)
    """
    # create and store new address
    new_address = api.get_new_address()
    IotaAddress.objects.update_or_create(user=user, address=new_address)

    logger.info('Generated address %s for user %s', new_address, user)

    return new_address


@api_resolver
def get_balance(user, api=None):
    balance = api.get_account_balance()
    IotaBalance.objects.update_or_create(user=user, balance=balance)
    logger.info('Fetched balance for user %s (balance: %i)', user, balance)
    return balance


@api_resolver
def get_account_data(user, api=None):
    account_data = api.get_account_data(inclusion_states=True)

    logger.debug('Requesting user data for user %s', user)

    # convert account data
    balance = account_data['balance']
    addresses = account_data['addresses']
    bundles = account_data['bundles']
    store_bundles(bundles=bundles, user_addresses=addresses, owner=user)

    # ToDo: get all transaction from database with filter and sorting.
    transactions = []

    # update user addresses
    fetched_addresses = {trytes2string(a) for a in addresses}
    stored_addresses = set(IotaAddress.objects.filter(user=user))
    new_addresses = fetched_addresses - stored_addresses
    for new_address in new_addresses:
        IotaAddress.objects.create(user=user, address=new_address)

    logger.info('Fetched data for user %s (#transactions: %i, balance: %i)', user, len(transactions), balance)

    return balance, transactions


# noinspection PyBroadException
def send_tokens(request, sender, receiver, value, message=None):
    # get proper users
    _, sending_user = get_user_safe(email=sender)
    is_new, receiving_user = get_user_safe(email=receiver)

    # check balance
    api = IotaApi(seed=sending_user.iotaseed.seed)
    balance = api.get_account_balance()
    if balance < value:
        raise InsufficientBalanceException(user=str(sending_user), proposed_amount=value, balance=balance)

    change_address = get_new_address(sending_user)
    receiving_address = get_new_address(receiving_user)

    logger.info('Sending %i IOTA from %s to %s (address: %s, new: %s)',
                value, sending_user, receiving_user, receiving_address, is_new)

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
        sender_transaction = extract_transaction(transaction=transaction, bundle=bundle, owner=receiver)
        sender_transaction.direction = IotaTransaction.OUT_GOING if value else IotaTransaction.NEUTRAL
        sender_transaction.save()
        receiver_transaction = extract_transaction(transaction=transaction, bundle=bundle, owner=receiver)
        receiver_transaction.direction = IotaTransaction.IN_GOING if value else IotaTransaction.NEUTRAL
        receiver_transaction.save()

        # ToDo: Check receiver in the case of zero value

        # inform receiver via mail
        user_utils.send_token_received_email(request=request,
                                             sender=sending_user,
                                             receiver=receiving_user,
                                             is_new=is_new,
                                             amount=value,
                                             message=message)
        return bundle
    except Exception as e:
        logger.exception('Error while transferring %i IOTA from %s to %s (address %s, new:%s)',
                         value, sending_user, receiving_user, receiving_address, is_new)
        raise e


def user_for_address(address):
    from wallet.models import IotaAddress
    try:
        # check if email is attached to address
        email = IotaAddress.objects.get(address=address).user.email
        logger.debug('Found attached email %s for address %s', email, address)
    except IotaAddress.DoesNotExist:
        email = None
    return email


def extract_transaction(transaction, bundle, owner, user_addresses=None):
    if not user_addresses:
        user_addresses = []

    receiver_address = trytes2string(bundle.transactions[0].address)
    receiver_mail = user_for_address(receiver_address)

    # try to find sender (e.g. if value no zero)
    sender_mail, sender_address = (receiver_mail, receiver_address)
    if len(bundle.transactions) >= 4:
        # assumption: change address is known address of sender
        sender_address = trytes2string(bundle.transactions[3].address)
        sender_mail = user_for_address(sender_address)

    # determine direction of transaction
    direction = IotaTransaction.OUT_GOING
    if transaction.value == 0:
        direction = IotaTransaction.NEUTRAL
    elif receiver_address in [trytes2string(a) for a in user_addresses]:
        direction = IotaTransaction.IN_GOING

    return IotaTransaction(bundle_hash=trytes2string(transaction.bundle_hash),
                           is_confirmed=transaction.is_confirmed,
                           receiver_address=receiver_address,
                           receiver_mail=receiver_mail,
                           time=make_aware(datetime.fromtimestamp(transaction.timestamp)),
                           hash=trytes2string(transaction.hash),
                           value=transaction.value,
                           sender_address=sender_address,
                           sender_mail=sender_mail,
                           direction=direction)


def store_bundles(bundles, user_addresses, owner):
    transactions = set()
    for bundle in bundles:
        # on transfer results in four transactions within a bundle (https://iota.readme.io/docs/bundles)
        # actual movement of IOTA is stored in first transaction
        if len(bundle.transactions) >= 4:
            transactions.add(extract_transaction(transaction=bundle.transactions[0],
                                                 user_addresses=user_addresses,
                                                 bundle=bundle,
                                                 owner=owner))
        else:
            for t in bundle.transactions:
                transactions.add(extract_transaction(transaction=t,
                                                     user_addresses=user_addresses,
                                                     bundle=bundle,
                                                     owner=owner))

                # # filter ones with zero values
                # if not include_zero:
                #     transactions = list(filter(lambda t: t.value != 0, transactions))
                #
                # # sort by date (recent transactions first)
                # return sorted(transactions, key=lambda t: t.time, reverse=True)
