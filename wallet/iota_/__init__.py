import collections
import logging
import operator
from datetime import datetime

from django.utils.timezone import make_aware
from iota import STANDARD_UNITS

logger = logging.getLogger(__name__)

Transaction = collections.namedtuple('Transaction', 'bundle_hash is_confirmed address '
                                                    'email time hash value in_going')


class InsufficientBalanceException(Exception):
    def __init__(self, *args, user, proposed_amount, balance):
        self.user = user
        self.proposed_amount = proposed_amount
        self.balance = balance
        message = '{} has not enough balance ({}) for sending {} IOTA'.format(user, balance, proposed_amount)
        super().__init__(message, *args)


def trytes2string(trytes):
    return str(trytes)


def string2trytes_bytes(string):
    return string.encode('utf-8')


def convert_transaction(transaction, user_addresses):
    from wallet.models import IotaAddress
    address = trytes2string(transaction.address)
    try:
        # check if email is attached to address
        attached_email = IotaAddress.objects.get(address=address).user.email
        logger.debug('Found attached email %s for address %s', attached_email, address)
    except IotaAddress.DoesNotExist:
        attached_email = None

    return Transaction(bundle_hash=trytes2string(transaction.bundle_hash),
                       is_confirmed=transaction.is_confirmed,
                       address=address,
                       time=make_aware(datetime.fromtimestamp(transaction.timestamp)),
                       hash=trytes2string(transaction.hash),
                       value=transaction.value,
                       email=attached_email,
                       in_going=address in user_addresses)


def convert_bundles(bundles, user_addresses):
    transactions = []
    for bundle in bundles:
        # on transfer results in four transactions within a bundle (https://iota.readme.io/docs/bundles)
        # actual movement of IOTA is stored in fourth transaction
        if len(bundle.transactions) == 4:
            transactions.append(convert_transaction(transaction=bundle.transactions[0],
                                                    user_addresses=user_addresses))
        else:
            transactions += [convert_transaction(transaction=t, user_addresses=user_addresses)
                             for t in bundle.transactions]

    # sort by date (recent transactions first)
    return sorted(transactions, key=lambda t: t.time, reverse=True)


def iota_display_format(amount):
    previous_unit = 'i'
    for unit, decimal in sorted(STANDARD_UNITS.items(), key=operator.itemgetter(1)):
        if decimal >= amount / 10:
            break
        previous_unit = unit
    return amount / STANDARD_UNITS[previous_unit], previous_unit
