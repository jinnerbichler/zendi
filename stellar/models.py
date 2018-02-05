from django.contrib.auth.models import User
from django.db import models


class StellarAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    seed = models.TextField(unique=True)
    address = models.TextField(unique=True)
    balance = models.FloatField(default=0.0)

    class Meta:
        unique_together = (('user', 'seed'))


class StellarTransaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stellar_sent',
                               blank=True, null=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stellar_received',
                                 blank=True, null=True)
    identifier = models.TextField(unique=True)
    sender_address = models.TextField()
    receiver_address = models.TextField()
    amount = models.FloatField()
    source_account = models.TextField()
    type = models.TextField()
    type_i = models.IntegerField()
    asset_type = models.TextField()
    transaction_hash = models.TextField()
    created_at = models.DateTimeField()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.identifier == other.identifier

    def __hash__(self):
        return hash((self.identifier))

    def __repr__(self):
        return '<StellarTransaction\n\t' \
               'from_address={from_address}\n\tto_address={to_address}\n\tamount={amount}\n\t' \
               'type={type}>' \
            .format(**self.__dict__)

    def __str__(self):
        return self.__repr__()

    class Meta:
        unique_together = (('identifier', 'sender', 'receiver'))
