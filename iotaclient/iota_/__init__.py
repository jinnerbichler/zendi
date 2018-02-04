import logging
import operator

from iota import STANDARD_UNITS

logger = logging.getLogger(__name__)


# Transaction = collections.namedtuple('Transaction', 'bundle_hash is_confirmed sender_address '
#                                                     'sender_mail receiver_address receiver_mail '
#                                                     'time hash value direction')


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


def normalize_value(value, unit):
    return int(value * STANDARD_UNITS[unit])


def iota_display_format(amount):
    previous_unit = 'i'
    for unit, decimal in sorted(STANDARD_UNITS.items(), key=operator.itemgetter(1)):
        if decimal >= amount / 10:
            break
        previous_unit = unit
    return amount / STANDARD_UNITS[previous_unit], previous_unit
