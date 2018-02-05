from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

import stellar.api


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Created init fields for user.
    """
    if created:
        # create new Stellar account
        stellar.api.create_account(user=instance)