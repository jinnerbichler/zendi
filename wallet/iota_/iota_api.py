import logging

import requests
from iota import Iota, ProposedTransaction, Address, TryteString, Tag
from iota.adapter.sandbox import SandboxAdapter
from iota.adapter.wrappers import RoutingWrapper
from iota.crypto.types import Seed

AUTH_TOKEN = '03f7571a-bb6c-4a5d-86eb-0fd73f02da78'
SANDBOX_URI = 'https://sandbox.iota.org/api/v1/'
SEED = b'MHPMRXKXECRNBLGZAUVHFFWLWMWBLOYKSICDAFOOHNHIQYZPILWXFSRUQCTSPKVXMGYWMLVLNFI9ISNKQ'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

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
    return Seed.random()._trytes.decode('ascii')  # ToDo: Test this! ...as_string is not working


class IotaApi:
    def __init__(self, seed, adapter=None):
        if adapter is None:
            adapter = DEFAULT_ADAPTER

        # convert seed
        seed = Seed.from_bytes(seed.encode('ascii'))
        self.api = Iota(adapter=adapter, seed=seed)
        self.api.adapter.set_logger(logger)

    def get_new_address(self):
        return self.api.get_new_addresses()[0]

    def get_address_balance(self, address):
        return self.api.get_balances([address])[address]

    def get_account_balance(self):
        return self.api.get_inputs()['totalBalance']


if __name__ == '__main__':
    iota_api = IotaApi(seed=SEED)

    print(iota_api.api.get_node_info())

    inputs = iota_api.api.get_inputs()

    print(inputs)

    send_to = Address(
        b'FWAWQKLNAVEPOCDNKJUERBD9YKNWLZWQLVDOI99MDGCJOLYBFMSLVAUGFQVECFIULMFGCRURRMEWVFQDWKZAXZELOW')
    # transaction = ProposedTransaction(address=send_to,
    #                                   value=10,
    #                                   tag=Tag(b'ADAPT'),
    #                                   message=TryteString.from_string('Hello!'))
    # bundle = iota_api.api.send_transfer(depth=100, transfers=[transaction], inputs=inputs['inputs'])
    # print(bundle)
    print(iota_api.api.get_inputs())

    print(iota_api.api.get_balances([send_to]))
