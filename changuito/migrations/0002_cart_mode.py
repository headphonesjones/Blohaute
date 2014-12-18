# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('changuito', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='mode',
            field=models.IntegerField(default=2, choices=[(1, b'Normal'), (2, b'Schedule')]),
            preserve_default=True,
        ),
    ]
