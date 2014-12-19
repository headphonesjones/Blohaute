# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changuito', '0004_auto_20141218_2319'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='series_id',
        ),
        migrations.AddField(
            model_name='item',
            name='series_id',
            field=models.IntegerField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
