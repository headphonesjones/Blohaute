# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0009_treatment_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='list_tagline',
            field=models.CharField(default='', max_length=255, blank=True),
            preserve_default=False,
        ),
    ]
