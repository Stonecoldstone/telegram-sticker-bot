# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-09 15:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stickerbot', '0005_auto_20160908_1818'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chat',
            name='probability',
            field=models.FloatField(default=0.04),
        ),
    ]