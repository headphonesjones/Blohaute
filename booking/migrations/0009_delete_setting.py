# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0008_auto_20141220_0627'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Setting',
        ),
    ]
