# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0003_treatment_list_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='treatment',
            name='thumb_image',
            field=models.ImageField(default='', upload_to=b'thumbnail_images'),
            preserve_default=False,
        ),
    ]
