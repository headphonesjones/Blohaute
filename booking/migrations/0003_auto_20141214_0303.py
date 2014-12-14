# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_auto_20141214_0301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='treatment',
            name='deposit_required',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
