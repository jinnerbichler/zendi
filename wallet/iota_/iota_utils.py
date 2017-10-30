import collections
import logging
import functools
import time
from datetime import datetime

from django.utils.timezone import make_aware
from pytz import UTC

from wallet import user_utils
from wallet.iota_ import InsufficientBalanceException, trytes2string, convert_bundles
from wallet.iota_.iota_api import IotaApi
from wallet.models import IotaAddress, IotaExecutedTransaction
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
    logger.info('Fetched balance for user %s (balance: %i)', user, balance)
    return balance


@api_resolver
def get_account_data(user, api=None):
    account_data = api.get_account_data(inclusion_states=True)

    logger.debug('Requesting user data for user %s', user)

    # convert account data
    balance = account_data['balance']
    transactions = convert_bundles(bundles=account_data['bundles'], user_addresses=account_data['addresses'])

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

        # save successfully executed transaction
        execution_time = make_aware(datetime.fromtimestamp(transaction.timestamp), timezone=UTC)
        IotaExecutedTransaction.objects.get_or_create(sender=sending_user,
                                                      receiver=receiving_user,
                                                      receiver_address=receiving_address,
                                                      bundle_hash=trytes2string(bundle.hash),
                                                      transaction_hash=trytes2string(transaction.hash),
                                                      value=value,
                                                      execution_time=execution_time,
                                                      message=message)
        # inform receiver via mail
        user_utils.send_token_received_email(request=request,
                                             sender=sending_user,
                                             receiver=receiving_user,
                                             is_new=is_new,
                                             amount=value)
        return bundle
    except Exception as e:
        logger.exception('Error while transferring %i IOTA from %s to %s (address %s, new:%s)',
                         value, sending_user, receiving_user, receiving_address, is_new)
        raise e
