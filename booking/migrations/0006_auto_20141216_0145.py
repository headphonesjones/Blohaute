# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_remove_treatment_full_description'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='treatment',
            options={'ordering': ['order']},
        ),
        migrations.AddField(
            model_name='treatment',
            name='order',
            field=models.PositiveIntegerField(default=1, editable=False, db_index=True),
            preserve_default=True,
        ),
    ]
