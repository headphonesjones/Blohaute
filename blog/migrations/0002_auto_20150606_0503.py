# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostImage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=b'blog/images/', blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ('-publication_date',)},
        ),
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(upload_to=b'blog/images/', blank=True),
        ),
        migrations.AddField(
            model_name='postimage',
            name='post',
            field=models.ForeignKey(blank=True, to='blog.Post', null=True),
        ),
    ]
