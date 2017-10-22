import logging

from iota import Iota, ProposedTransaction, Address, TryteString
from iota.adapter.wrappers import RoutingWrapper
from iota.crypto.types import Seed

AUTH_TOKEN = '03f7571a-bb6c-4a5d-86eb-0fd73f02da78'
SANDBOX_URI = 'https://sandbox.iota.org/api/v1/'
DEFAULT_DEPTH = 3

logger = logging.getLogger(__name__)

# create default adapter
DEFAULT_ADAPTER = RoutingWrapper('http://localhost:14265/api/v1/commands')
DEFAULT_ADAPTER.set_logger(logger)
for a in DEFAULT_ADAPTER.routes.values():
    a.set_logger(logger)


# for cmd in ['attachToTangle', 'storeTransactions', 'broadcastTransactions']:
#     adapter.add_route(cmd, 'http://localhost:14265/api/v1/commands'),

# noinspection PyProtectedMember
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

        # convert seed
        seed = Seed(string2trytes(seed))

        self.api = Iota(adapter=adapter, seed=seed)
        self.api.adapter.set_logger(logger)

    def get_new_address(self):
        """
        Fetch new address from IRI (deterministically)
        :return: String representation of new address
        """
        response = self.api.get_new_addresses(count=None)
        return trytes2string(response['addresses'][0])

    def get_address_balance(self, address):
        address = Address(string2trytes(address))
        return self.api.get_balances([address])[address]

    def get_account_balance(self):
        return self.api.get_inputs()['totalBalance']

    def transfer(self, receiver_address, change_address, value, tag=None, message=None):
        if message:
            message = TryteString.from_string(message)

        # convert addresses
        receiver_address = Address(string2trytes(receiver_address))
        change_address = Address(string2trytes(change_address))

        # construct transaction
        transaction = ProposedTransaction(address=receiver_address, value=value, tag=tag, message=message)

        # trigger transfer
        self.api.send_transfer(depth=DEFAULT_DEPTH, transfers=[transaction], change_address=change_address)


def trytes2string(trytes):
    return str(trytes)


def string2trytes(string):
    return string.encode()


# if __name__ == '__main__':
#     iota_api = IotaApi(seed=SEED)
#
#     print(iota_api.api.get_node_info())
#
#     inputs = iota_api.api.get_inputs()
#
#     print(inputs)
#
#     send_to = Address(
#         b'FWAWQKLNAVEPOCDNKJUERBD9YKNWLZWQLVDOI99MDGCJOLYBFMSLVAUGFQVECFIULMFGCRURRMEWVFQDWKZAXZELOW')
#     # transaction = ProposedTransaction(address=send_to,
#     #                                   value=10,
#     #                                   tag=Tag(b'ADAPT'),
#     #                                   message=TryteString.from_string('Hello!'))
#     # bundle = iota_api.api.send_transfer(depth=100, transfers=[transaction], inputs=inputs['inputs'])
#     # print(bundle)
#     print(iota_api.api.get_inputs())
#
#     print(iota_api.api.get_balances([send_to]))
