# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-05 01:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stellar', '0002_auto_20180205_0034'),
    ]

    operations = [
        migrations.RenameField(
            model_name='stellartransaction',
            old_name='from_address',
            new_name='receiver_address',
        ),
        migrations.RenameField(
            model_name='stellartransaction',
            old_name='to_address',
            new_name='sender_address',
        ),
    ]
