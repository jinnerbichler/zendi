# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-10-24 17:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wallet', '0006_auto_20171023_2026'),
    ]

    operations = [
        migrations.RenameField(
            model_name='iotaexecutedtransaction',
            old_name='amount',
            new_name='value',
        ),
    ]