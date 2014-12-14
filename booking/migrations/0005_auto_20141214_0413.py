# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_auto_20141214_0409'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='treatment',
            name='depoist_percentage',
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='deposit_required',
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='duration_type',
        ),
    ]
