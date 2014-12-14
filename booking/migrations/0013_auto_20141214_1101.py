# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_bleach.models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0012_auto_20141214_0518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='treatment',
            name='full_description',
            field=django_bleach.models.BleachField(blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='treatmentimage',
            name='image',
            field=models.ImageField(null=True, upload_to=b'treatment_images', blank=True),
            preserve_default=True,
        ),
    ]
