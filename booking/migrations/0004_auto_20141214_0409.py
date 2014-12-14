# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0003_auto_20141214_0303'),
    ]

    operations = [
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField()),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
                ('treatment', models.ForeignKey(related_name='memberships', to='booking.Treatment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Package',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('quantity', models.IntegerField()),
                ('price', models.DecimalField(default=0.0, max_digits=10, decimal_places=2)),
                ('treatment', models.ForeignKey(related_name='packages', to='booking.Treatment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='available_in_advance_days',
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='image_url',
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='total_duration',
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='treatment_duration',
        ),
        migrations.AddField(
            model_name='treatment',
            name='image',
            field=models.ImageField(null=True, upload_to=b'', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='treatment',
            name='original_price',
            field=models.DecimalField(default=0.0, null=True, max_digits=10, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='treatment',
            name='treatment_id',
            field=models.IntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='treatment',
            name='id',
            field=models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True),
            preserve_default=True,
        ),
    ]
