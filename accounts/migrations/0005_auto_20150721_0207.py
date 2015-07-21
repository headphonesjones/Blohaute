# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import accounts.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20150606_0503'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=accounts.fields.CaseInsensitiveEmailField(unique=True, max_length=254, verbose_name='email address'),
        ),
    ]
