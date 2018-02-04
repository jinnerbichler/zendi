from django.contrib.auth.models import User
from django.db import models


class IotaSeed(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    seed = models.TextField(unique=True)

    class Meta:
        unique_together = (('user', 'seed'))


class IotaAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField(unique=True)

    class Meta:
        unique_together = (('user', 'address'))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.address == other.address and self.user == other.user

    def __hash__(self):
        return hash((self.address, self.user))

    def __str__(self):
        return self.address


class IotaBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0)


class IotaTransaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions',
                               blank=True, null=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions',
                                 blank=True, null=True)
    sender_address = models.TextField()
    receiver_address = models.TextField()
    bundle_hash = models.TextField()
    value = models.BigIntegerField()
    attachment_time = models.DateTimeField()
    is_confirmed = models.BooleanField(default=False)
    replay_count = models.BigIntegerField(default=0)
    tail_transaction_hash = models.TextField(default='')

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.tail_transaction_hash == other.tail_transaction_hash

    def __hash__(self):
        return hash((self.tail_transaction_hash))

    def __repr__(self):
        return '<IotaExecutedTransaction\n\t' \
               'receiver_addr={receiver_address}\n\tvalue={value}\n\treplay_count={replay_count}\n\t' \
               'bundle_hash={bundle_hash}\n\t' \
               'sender={sender}\n\treceiver={receiver}\n\ttail_transaction_hash={tail_transaction_hash}\n\t' \
               'attachment_time={attachment_time}>' \
            .format(**self.__dict__)

    class Meta:
        unique_together = (('bundle_hash', 'tail_transaction_hash'))
