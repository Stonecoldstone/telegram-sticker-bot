# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-09 16:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stickerbot', '0006_auto_20160909_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='lang',
            field=models.CharField(default='russian', max_length=100),
        ),
    ]
