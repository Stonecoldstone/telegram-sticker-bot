# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-10 16:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stickerbot', '0007_chat_lang'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chat',
            name='burst',
        ),
    ]