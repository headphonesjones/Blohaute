# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0002_auto_20141214_1409'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='list_image',
            field=models.ImageField(default='', upload_to=b'treatment_images'),
            preserve_default=False,
        ),
    ]
