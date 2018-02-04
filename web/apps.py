from django.apps import AppConfig


class WalletConfig(AppConfig):
    name = 'web'
    verbose_name = 'Web'

    def ready(self):
        pass
