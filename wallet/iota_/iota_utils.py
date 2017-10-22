# noinspection PyUnresolvedReferences
import logging
from datetime import datetime

from django.utils.timezone import make_aware
from pytz import UTC

from wallet.iota_ import NotEnoughBalanceException
from wallet.iota_.iota_api import IotaApi
from wallet.models import IotaAddress, IotaExecutedTransaction
from wallet.user_utils import get_user_safe
from wallet.iota_ import trytes2string

logger = logging.getLogger(__name__)


# noinspection PyUnresolvedReferences
def get_new_address(user):
    """
    Creates a new IOTA address, which is not attached to the tangle.
    :param user: user object containing seed
    :return: new address in the IOTA network (not attached to the Tangle)
    """
    api = IotaApi(seed=user.iotaseed.seed)

    # create and store new address
    new_address = api.get_new_address()
    IotaAddress.objects.get_or_create(user=user, address=new_address)

    logger.info('Generated address %s for user %s', new_address, user)

    return new_address


# noinspection PyUnresolvedReferences,PyBroadException
def send_tokens(sender, receiver, amount, msg=None):
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

    logger.info('Sending %i IOTA from %s to %s (address: %s, new:%s)',
                amount, sending_user, receiving_user, receiving_address, is_new)

    try:
        # send transaction
        pow_start_time = time.time()
        bundle = api.transfer(receiver_address=receiving_address,
                              change_address=change_address,
                              value=amount,
                              message=msg)

        pow_execution_time = time.time() - pow_start_time
        logger.info('Performed PoW in %i secs', pow_execution_time, extras={'pow_time': pow_execution_time})

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
                                                      message=msg)

        return bundle
    except:
        logger.exception('Error while transferring %i IOTA from %s to %s (address %s, new:%s)',
                         amount, sending_user, receiving_user, receiving_address, is_new)

    return
