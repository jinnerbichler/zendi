from django.apps import AppConfig


class WalletConfig(AppConfig):
    name = 'wallet'
    verbose_name = 'IOTA Wallet'

    def ready(self):
        pass
