# noinspection PyUnresolvedReferences
import collections
import logging
import functools
import operator
import time
from datetime import datetime

from django.utils.timezone import make_aware
from iota import STANDARD_UNITS
from pytz import UTC

from wallet.iota_ import NotEnoughBalanceException, trytes2string
from wallet.iota_.iota_api import IotaApi
from wallet.models import IotaAddress, IotaExecutedTransaction
from wallet.user_utils import get_user_safe

logger = logging.getLogger(__name__)

Transaction = collections.namedtuple('Transaction', 'bundle_hash is_confirmed address time hash value')


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


# noinspection PyUnusedLocal
@api_resolver
def get_balance(user, api=None):
    return api.get_account_balance()


# noinspection PyUnusedLocal
@api_resolver
def get_transactions(user, api=None):
    bundles = api.get_transfers(inclusion_states=True)
    return convert_bundles(bundles)


# noinspection PyUnusedLocal
@api_resolver
def get_account_data(user, api=None):
    account_data = api.get_account_data(inclusion_states=True)

    # convert account data (get account data retrieves only outgoing transactions)
    balance = account_data['balance']
    outgoing_transactions = convert_bundles(account_data['bundles'])

    return balance, outgoing_transactions


# noinspection PyBroadException
def send_tokens(sender, receiver, amount, message=None):
    # get proper users
    _, sending_user = get_user_safe(email=sender)
    is_new, receiving_user = get_user_safe(email=receiver)

    # ToDo: inform user about new wallet

    # check balance
    api = IotaApi(seed=sending_user.iotaseed.seed)
    balance = api.get_account_balance()
    if balance < amount:
        raise NotEnoughBalanceException(user=str(sending_user), proposed_amount=amount, balance=balance)

    change_address = get_new_address(sending_user)
    receiving_address = get_new_address(receiving_user)

    logger.info('Sending %i IOTA from %s to %s (address: %s, new: %s)',
                amount, sending_user, receiving_user, receiving_address, is_new)

    try:
        # send transaction
        pow_start_time = time.time()
        bundle = api.transfer(receiver_address=receiving_address,
                              change_address=change_address,
                              value=amount,
                              message=message)

        pow_execution_time = time.time() - pow_start_time
        logger.info('Performed PoW in %i secs', pow_execution_time, extra={'pow_time': pow_execution_time})

        # ToDo: inform users via mail

        # check for consistency
        transaction = bundle.transactions[0]
        assert trytes2string(transaction.address) == receiving_address

        # save successfully executed transaction
        execution_time = make_aware(datetime.fromtimestamp(transaction.timestamp), timezone=UTC)
        IotaExecutedTransaction.objects.get_or_create(sender=sending_user,
                                                      receiver=receiving_user,
                                                      receiver_address=receiving_address,
                                                      bundle_hash=trytes2string(bundle.hash),
                                                      transaction_hash=trytes2string(transaction.hash),
                                                      amount=amount,
                                                      execution_time=execution_time,
                                                      message=message)

        return bundle
    except Exception as e:
        logger.exception('Error while transferring %i IOTA from %s to %s (address %s, new:%s)',
                         amount, sending_user, receiving_user, receiving_address, is_new)
        raise e


def convert_bundles(bundles):
    transactions = []
    for bundle in bundles:
        for transaction in bundle.transactions:
            transactions.append(Transaction(bundle_hash=trytes2string(transaction.bundle_hash),
                                            is_confirmed=transaction.is_confirmed,
                                            address=trytes2string(transaction.address),
                                            time=make_aware(datetime.fromtimestamp(transaction.timestamp)),
                                            hash=trytes2string(transaction.hash),
                                            value=transaction.value))
    return transactions


def iota_display_format(amount):
    previous_unit = 'i'
    for unit, decimal in sorted(STANDARD_UNITS.items(), key=operator.itemgetter(1)):
        if decimal >= amount / 10:
            break
        previous_unit = unit
    return amount / STANDARD_UNITS[previous_unit], previous_unit
