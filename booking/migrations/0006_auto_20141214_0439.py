# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0005_auto_20141214_0413'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shoppingcart',
            name='items',
        ),
        migrations.DeleteModel(
            name='ShoppingCart',
        ),
        migrations.RemoveField(
            model_name='shoppingcartitem',
            name='treatment',
        ),
        migrations.DeleteModel(
            name='ShoppingCartItem',
        ),
    ]
