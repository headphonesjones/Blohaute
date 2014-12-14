# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_auto_20141214_0439'),
    ]

    operations = [
        migrations.CreateModel(
            name='TreatmentImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(null=True, upload_to=b'', blank=True)),
                ('primary_image', models.BooleanField(default=False)),
                ('treatment', models.ForeignKey(related_name='images', to='booking.Treatment')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='treatment',
            name='image',
        ),
    ]
