# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0010_treatment_list_tagline'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='plural_name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
