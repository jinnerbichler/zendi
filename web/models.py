from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models

import stellar.api


class UserFeedback(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback', blank=True, null=True)
    email = models.TextField()
    message = models.TextField()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Created init fields for user.
    """
    if created:
        # create new Stellar account
        stellar.api.create_account(user=instance)
