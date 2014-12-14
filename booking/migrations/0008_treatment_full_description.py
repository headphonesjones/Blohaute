# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0007_auto_20141214_0501'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='full_description',
            field=models.TextField(default='', blank=True),
            preserve_default=False,
        ),
    ]
