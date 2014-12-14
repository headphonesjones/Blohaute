# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='creation date')),
                ('checked_out', models.BooleanField(default=False, verbose_name='checked out')),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-creation_date',),
                'verbose_name': 'cart',
                'verbose_name_plural': 'carts',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.DecimalField(verbose_name='quantity', max_digits=18, decimal_places=3)),
                ('unit_price', models.DecimalField(verbose_name='unit price', max_digits=18, decimal_places=2)),
                ('object_id', models.PositiveIntegerField()),
                ('cart', models.ForeignKey(verbose_name='cart', to='changuito.Cart')),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('cart',),
                'verbose_name': 'item',
                'verbose_name_plural': 'items',
            },
            bases=(models.Model,),
        ),
    ]
