import logging

from django.conf import settings
from iota import Iota, ProposedTransaction, Address, TryteString, Tag
from iota.adapter.wrappers import RoutingWrapper
from iota.crypto.types import Seed

from iotaclient.iota_ import string2trytes_bytes, trytes2string

logger = logging.getLogger(__name__)

# create default adapter
DEFAULT_ADAPTER = RoutingWrapper(settings.IOTA_NODE_URL)
for command, url in settings.IOTA_ROUTES.items():
    DEFAULT_ADAPTER.add_route(command=command, adapter=url)

# set proper loggers
for a in list(DEFAULT_ADAPTER.routes.values()) + [DEFAULT_ADAPTER]:
    a.set_logger(logger)


def new_seed():
    """
    Creates a new seed and returns the string representation.
    :return: String (ascii) representation of new seed.
    """
    return trytes2string(Seed.random())


class IotaApi:
    def __init__(self, seed, adapter=None):
        if adapter is None:
            adapter = DEFAULT_ADAPTER

        adapter._logger.setLevel(logging.DEBUG)

        # convert seed
        seed = Seed(string2trytes_bytes(seed))

        self.api = Iota(adapter=adapter, seed=seed)
        self.api.adapter.set_logger(logger)

    def get_node_info(self):
        return self.api.get_node_info()

    def get_new_address(self, start=0):
        """
        Fetch new address from IRI (deterministically)
        :return: tuple: address -> str, address_with_check_sum --> str
        """
        response = self.api.get_new_addresses(index=start, count=None)
        return (trytes2string(response['addresses'][0]),
                trytes2string(response['addresses'][0].with_valid_checksum()))

    def get_address_balance(self, address):
        address = Address(string2trytes_bytes(address))
        return self.api.get_balances([address])[address]

    def get_account_balance(self):
        return self.api.get_inputs()['totalBalance']

    def get_bundles(self, transaction):
        return self.api.get_bundles(transaction=transaction)

    def replay_bundle(self, transaction):
        return self.api.replay_bundle(transaction=transaction, depth=settings.IOTA_DEFAULT_DEPTH)

    def get_inclusion_states(self, transactions, milestone):
        return self.api.get_inclusion_states(transactions=transactions, tips=[milestone])['states']

    def get_transfers(self, inclusion_states=False):
        return self.api.get_transfers(inclusion_states=inclusion_states)['bundles']

    def get_account_data(self, inclusion_states=False, start=0):
        return self.api.get_account_data(start=start, inclusion_states=inclusion_states)

    def get_transactions_for_addresses(self, addresses):
        return self.api.find_transactions(addresses=addresses)

    def transfer(self, receiver_address, change_address, value, tag=None, message=None):
        if message:
            message = TryteString.from_string(message)

        # convert addresses
        receiver_address = Address(string2trytes_bytes(receiver_address))
        change_address = Address(string2trytes_bytes(change_address))

        tag = Tag(b'ZENDI') if not tag else tag

        # construct transaction
        transaction = ProposedTransaction(address=receiver_address, value=value, tag=tag, message=message)

        # trigger transfer
        logger.info('########################## STARTING PoW ###########################################')
        bundle = self.api.send_transfer(depth=settings.IOTA_DEFAULT_DEPTH,
                                        transfers=[transaction],
                                        change_address=change_address)
        logger.info('########################## FINISHED PoW ###########################################')

        return bundle['bundle']
