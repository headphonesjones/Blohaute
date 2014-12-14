# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_bleach.models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('booker_id', models.IntegerField(null=True, blank=True)),
                ('quantity', models.IntegerField()),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('booker_id', models.IntegerField(null=True, blank=True)),
                ('quantity', models.IntegerField()),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Treatment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('plural_name', models.CharField(max_length=255)),
                ('slug', models.SlugField(unique=True)),
                ('booker_id', models.IntegerField(null=True, blank=True)),
                ('list_tagline', models.CharField(max_length=255, blank=True)),
                ('description', models.TextField(blank=True)),
                ('full_description', django_bleach.models.BleachField(blank=True)),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
                ('original_price', models.DecimalField(default=0.0, null=True, max_digits=10, decimal_places=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TreatmentImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(null=True, upload_to=b'treatment_images', blank=True)),
                ('primary_image', models.BooleanField(default=False)),
                ('treatment', models.ForeignKey(related_name='images', to='booking.Treatment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='package',
            name='treatment',
            field=models.ForeignKey(related_name='packages', to='booking.Treatment'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='membership',
            name='treatment',
            field=models.ForeignKey(related_name='memberships', to='booking.Treatment'),
            preserve_default=True,
        ),
    ]
