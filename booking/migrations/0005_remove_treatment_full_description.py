# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0004_treatment_thumb_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='treatment',
            name='full_description',
        ),
    ]
