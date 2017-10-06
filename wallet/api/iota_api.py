import logging

import requests
from iota import Iota, ProposedTransaction, Address, TryteString, Tag
from iota.adapter.sandbox import SandboxAdapter

AUTH_TOKEN = '03f7571a-bb6c-4a5d-86eb-0fd73f02da78'
SANDBOX_URI = 'https://sandbox.iota.org/api/v1/'
SEED = b'RPAHPPZ9GZUQQ'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class IotaApi:
    def __init__(self):
        adapter = SandboxAdapter(uri=SANDBOX_URI, auth_token=AUTH_TOKEN)
        adapter.set_logger(logger)

        self.api = Iota(adapter=adapter, seed=SEED)

    def get_account_balance(self, index):
        """
        Returns the total balance of the iota account
        Parameters:
            index: the current address index(i.e. the count of all the used addresses)
        """

        while True:
            try:
                # Index must be at least 1
                if index == 0:
                    index = 1
                addresses = self.api.get_new_addresses(index=index, count=1)['addresses']
                balances = self.api.get_balances(addresses)['Balances']
                total = 0
                for balance in balances:
                    total = total + balance
                return total
            except requests.exceptions.RequestException:
                pass


if __name__ == '__main__':
    iota_api = IotaApi()

    print(iota_api.get_account_balance(index=1))
