from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from iotaclient.iota_.iota_api import new_seed


# noinspection PyUnusedLocal, PyUnresolvedReferences
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Created init fields for user.
    """
    if created:
        IotaSeed.objects.create(user=instance, seed=new_seed())
        IotaBalance.objects.create(user=instance, balance=0)
