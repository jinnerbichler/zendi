# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2018-02-04 20:04
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='StellarAccount',
            fields=[
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('seed', models.TextField(unique=True)),
                ('address', models.TextField(unique=True)),
                ('balance', models.FloatField(default=0.0)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='stellaraccount',
            unique_together=set([('user', 'seed')]),
        ),
    ]
