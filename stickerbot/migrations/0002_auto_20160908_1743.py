# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-08 17:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stickerbot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='intermediate',
            name='word',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
