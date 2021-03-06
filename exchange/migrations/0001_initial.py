# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-24 15:47
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=63, unique=True, verbose_name='identifier')),
                ('name', models.CharField(max_length=63, verbose_name='name')),
            ],
        ),
        migrations.CreateModel(
            name='DynamicSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=31)),
                ('value', models.CharField(max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExchangeOffice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=63, unique=True, verbose_name='identifier')),
                ('address', models.CharField(max_length=127, verbose_name='address')),
                ('bank', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exchange.Bank')),
            ],
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('currency', models.PositiveSmallIntegerField(choices=[(0, 'usd'), (1, 'eur'), (2, 'rub')], verbose_name='currency')),
                ('buy', models.BooleanField(verbose_name='buy')),
                ('rate', models.DecimalField(decimal_places=4, max_digits=11, verbose_name='rate')),
                ('exchange_office', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exchange.ExchangeOffice')),
            ],
        ),
        migrations.CreateModel(
            name='UserInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(verbose_name='registration IP address')),
                ('exchange_offices', models.ManyToManyField(to='exchange.ExchangeOffice')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
        ),
    ]
