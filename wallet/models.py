from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from wallet.iota_.iota_api import new_seed


class IotaSeed(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    seed = models.TextField(unique=True)

    class Meta:
        unique_together = (('user', 'seed'))


class IotaAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.TextField(unique=True)
    attached = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'address'))


class IotaBalance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    balance = models.PositiveIntegerField(default=0)


class IotaExecutedTransaction(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_transactions')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_transactions')
    receiver_address = models.TextField()
    bundle_hash = models.TextField()
    transaction_hash = models.TextField()
    value = models.BigIntegerField()
    execution_time = models.DateTimeField()
    message = models.TextField(default='')

    def __repr__(self):
        return '<IotaExecutedTransaction \n\tsender={sender}\n\treceiver={receiver}\n\t' \
               'receiver_addr={receiver_address}\n\tamount={amount}\n\tmessage={message}\n\t' \
               'bundle_hash={bundle_hash}\n\ttransaction_hash={transaction_hash}\n\t' \
               'execution_time={execution_time}>'.format(sender=self.sender,
                                                         receiver=self.receiver,
                                                         **self.__dict__)


# noinspection PyUnusedLocal, PyUnresolvedReferences
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Created init fields for user.
    """
    if created:
        IotaSeed.objects.create(user=instance, seed=new_seed())
        IotaBalance.objects.create(user=instance, balance=0)
