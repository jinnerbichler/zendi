import collections
import logging
import operator
from datetime import datetime

from django.utils.timezone import make_aware
from iota import STANDARD_UNITS

logger = logging.getLogger(__name__)

Transaction = collections.namedtuple('Transaction', 'bundle_hash is_confirmed sender_address '
                                                    'sender_mail receiver_address receiver_mail '
                                                    'time hash value direction')


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


def bundle_to_transaction(transaction, user_addresses, bundle):
    receiver_address = trytes2string(bundle.transactions[0].address)
    receiver_mail = mail_for_address(receiver_address)

    # try to find sender (e.g. if value no zero)
    sender_mail, sender_address = (receiver_mail, receiver_address)
    if len(bundle.transactions) >= 4:
        # change address is known address of sender
        sender_address = trytes2string(bundle.transactions[3].address)
        sender_mail = mail_for_address(sender_address)

    # determine direction of transaction
    direction = 'out_going'
    if transaction.value == 0:
        direction = 'neutral'
    elif receiver_address in [trytes2string(a) for a in user_addresses]:
        direction = 'in_going'

    return Transaction(bundle_hash=trytes2string(transaction.bundle_hash),
                       is_confirmed=transaction.is_confirmed,
                       receiver_address=receiver_address,
                       receiver_mail=receiver_mail,
                       time=make_aware(datetime.fromtimestamp(transaction.timestamp)),
                       hash=trytes2string(transaction.hash),
                       value=transaction.value,
                       sender_address=sender_address,
                       sender_mail=sender_mail,
                       direction=direction)


def convert_bundles(bundles, user_addresses, include_zero=True):
    transactions = []
    for bundle in bundles:
        # on transfer results in four transactions within a bundle (https://iota.readme.io/docs/bundles)
        # actual movement of IOTA is stored in first transaction
        if len(bundle.transactions) >= 4:
            transactions.append(bundle_to_transaction(transaction=bundle.transactions[0],
                                                      user_addresses=user_addresses,
                                                      bundle=bundle))
        else:
            transactions += [
                bundle_to_transaction(transaction=t, user_addresses=user_addresses, bundle=bundle)
                for t in bundle.transactions]

    # filter ones with zero values
    if not include_zero:
        transactions = list(filter(lambda t: t.value != 0, transactions))

    # sort by date (recent transactions first)
    return sorted(transactions, key=lambda t: t.time, reverse=True)


def mail_for_address(address):
    from wallet.models import IotaAddress
    try:
        # check if email is attached to address
        email = IotaAddress.objects.get(address=address).user.email
        logger.debug('Found attached email %s for address %s', email, address)
    except IotaAddress.DoesNotExist:
        email = None
    return email


def iota_display_format(amount):
    previous_unit = 'i'
    for unit, decimal in sorted(STANDARD_UNITS.items(), key=operator.itemgetter(1)):
        if decimal >= amount / 10:
            break
        previous_unit = unit
    return amount / STANDARD_UNITS[previous_unit], previous_unit
