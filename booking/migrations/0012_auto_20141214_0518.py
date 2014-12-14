# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0011_treatment_plural_name'),
    ]

    operations = [
        migrations.RenameField(
            model_name='treatment',
            old_name='treatment_id',
            new_name='booker_id',
        ),
        migrations.AddField(
            model_name='membership',
            name='booker_id',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='package',
            name='booker_id',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
