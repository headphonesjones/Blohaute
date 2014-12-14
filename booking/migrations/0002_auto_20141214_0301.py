# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShoppingCart',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShoppingCartItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField(default=1)),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Treatment',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('available_in_advance_days', models.IntegerField(default=365)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deposit_required', models.BooleanField()),
                ('depoist_percentage', models.IntegerField(default=0)),
                ('description', models.TextField(blank=True)),
                ('duration_type', models.IntegerField(default=1)),
                ('image_url', models.URLField(blank=True)),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
                ('total_duration', models.IntegerField(default=0)),
                ('treatment_duration', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='shoppingcartitem',
            name='treatment',
            field=models.ForeignKey(to='booking.Treatment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='shoppingcart',
            name='items',
            field=models.ManyToManyField(to='booking.ShoppingCartItem'),
            preserve_default=True,
        ),
    ]
