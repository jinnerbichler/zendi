import logging
from typing import List, Optional
from urllib.parse import urlparse, parse_qs

import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from stellar_base.address import Address
from stellar_base.builder import Builder
from stellar_base.keypair import Keypair

from stellar.models import StellarAccount, StellarTransaction

logger = logging.getLogger(__name__)

network = 'TESTNET' if settings.STELLAR_TESTNET else 'PUBLIC'


def create_account(user):
    # type: (User) -> None

    # create keypair
    keypair = Keypair.random()
    public_key = keypair.address().decode()
    seed = keypair.seed().decode()

    # store account
    StellarAccount.objects.create(seed=seed, address=public_key, user=user, balance=0.0)

    # fund account
    if settings.STELLAR_TESTNET:
        response = requests.get('https://horizon-testnet.stellar.org/friendbot?addr=' + public_key)
        response.raise_for_status()
        if response.status_code == 200:
            logger.info('[TESTNET] Successfully funded address {} ()'.format(
                public_key, response.json()['_links']['transaction']['href']))

    logger.info('Created Stellar Lumen account {} for {}'.format(public_key, user))


def get_balance(user, cached=False):
    # type: (User, bool) -> float

    if cached:
        return user.stellaraccount.balance

    # fetch balance
    address = _get_address(user.stellaraccount.address)
    balances = {a['asset_type']: float(a['balance']) for a in address.balances}
    balance = balances['native']

    # update balance
    user.stellaraccount.balance = balance
    user.stellaraccount.save()

    return balance


def get_deposit_address(user):
    # type: (User) -> str
    return user.stellaraccount.address


def get_transactions(user, cached=False):
    # type: (User, bool) -> List[dict]

    if cached:
        return _get_cached_transactions(user=user)

    address = _get_address(user.stellaraccount.address)

    # fetch payments
    _update_payments(address=address)

    return _get_cached_transactions(user=user)


def transfer_lumen(from_user, to_user, amount, memo=None):
    # type: (User, User, float, Optional[str]) -> None

    # ToDo: check remaining lumen of seeding account (fee + base reserve)
    # (take base reserve https://www.stellar.org/developers/guides/concepts/fees.html)

    logger.info('Transferring XLM from {} to {}'.format(from_user, to_user))

    builder = Builder(secret=from_user.stellaraccount.seed, network=network)
    builder.append_payment_op(to_user.stellaraccount.address, str(amount), 'XLM')
    if memo:
        builder.add_text_memo(memo)  # string length <= 28 bytes

    builder.sign()
    builder.submit()


class InsufficientBalanceException(Exception):
    def __init__(self, *args, user, proposed_amount, balance):
        self.user = user
        self.proposed_amount = proposed_amount
        self.balance = balance
        message = '{} has not enough balance ({}) for sending {} XLM'.format(user, balance, proposed_amount)
        super().__init__(message, *args)


def _get_address(public_key):
    # type: (str) -> Address
    address = Address(address=public_key, network=network)
    address.get()
    return address


def _update_payments(address):
    # type: (Address) -> None

    cursor = None
    while True:
        payments = address.payments(cursor=cursor, order='desc', limit='10')
        records = payments['_embedded']['records']

        # determine cursor of next page
        next_link = payments['_links']['next']['href']
        new_cursor = parse_qs(urlparse(next_link).query)['cursor'][0]

        # check if last page was fetched
        if new_cursor == cursor:
            break
        cursor = new_cursor

        # store new records
        for payment in records:

            # only check relevant payments
            if payment['type'] in ['create_account', 'payment']:

                # set common attributes
                transaction = StellarTransaction()
                transaction.identifier = payment['id']
                transaction.type = payment['type']
                transaction.transaction_hash = payment['transaction_hash']
                transaction.created_at = parse_datetime(payment['created_at'])
                transaction.type_i = payment['type_i']
                transaction.source_account = payment['source_account']

                # handle payment for creating the account
                if payment['type'] == 'create_account':
                    transaction.sender = _user_for_address(address=payment['funder'])
                    transaction.receiver = _user_for_address(address=payment['account'])
                    transaction.sender_address = payment['funder']
                    transaction.receiver_address = payment['account']
                    transaction.amount = payment['starting_balance']
                    transaction.asset_type = 'native'

                # handle payment for sending / receiving tokens
                elif payment['type'] == 'payment':

                    # ToDo: handle only native tokens

                    transaction.sender = _user_for_address(address=payment['from'])
                    transaction.receiver = _user_for_address(address=payment['to'])
                    transaction.sender_address = payment['from']
                    transaction.receiver_address = payment['to']
                    transaction.amount = payment['amount']
                    transaction.asset_type = payment['asset_type']

                try:
                    # saving transaction
                    transaction.save()
                    logger.info('Saved new transaction {}'.format(transaction))
                except IntegrityError:
                    pass


def _user_for_address(address):
    try:
        # check if email is attached to address
        user = StellarAccount.objects.get(address=address).user
        logger.debug('Found attached user %s for address %s', user, address)
    except StellarAccount.DoesNotExist:
        user = None
    return user


def _get_cached_transactions(user):
    return list(StellarTransaction.objects
                .filter(Q(sender=user) | Q(receiver=user))
                .order_by('-created_at'))
