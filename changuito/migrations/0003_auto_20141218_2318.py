# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changuito', '0002_cart_mode'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cart',
            name='mode',
        ),
        migrations.AddField(
            model_name='cart',
            name='series_id',
            field=models.CharField(default=None, max_length=20, null=True, blank=True),
            preserve_default=True,
        ),
    ]
