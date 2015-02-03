# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20141214_1542'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='booker_id',
            field=models.IntegerField(default=0),
            preserve_default=True,
        ),
    ]
