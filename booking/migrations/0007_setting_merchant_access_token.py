# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_auto_20141216_0145'),
    ]

    operations = [
        migrations.AddField(
            model_name='setting',
            name='merchant_access_token',
            field=models.CharField(default=1, max_length=255),
            preserve_default=False,
        ),
    ]
