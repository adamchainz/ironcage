# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-07-06 16:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20170702_1250'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='ukpa_membership',
            field=models.NullBooleanField(),
        ),
    ]
