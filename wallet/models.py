from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from wallet.api.iota_api import new_seed


class IotaSeed(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    seed = models.TextField(unique=True)

    class Meta:
        unique_together = (('user', 'seed'))


class IotaAddress(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.TextField(unique=True)
    attached = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'address'))


# noinspection PyUnusedLocal, PyUnresolvedReferences
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Created seed for user.
    """
    if created:
        IotaSeed.objects.create(user=instance, seed=new_seed())
