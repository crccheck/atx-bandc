# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-01-18 23:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BandC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('identifier', models.CharField(help_text='The id, probaly an auto-inc integer.', max_length=50, unique=True)),
                ('slug', models.SlugField(max_length=255, unique=True)),
                ('homepage', models.URLField()),
                ('description', models.TextField(blank=True, null=True)),
                ('scrapable', models.BooleanField(default=True)),
                ('scraped_at', models.DateTimeField(blank=True, help_text='The last time documents were scraped.', null=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Board or Commission',
                'verbose_name_plural': 'Boards and Commissions',
            },
        ),
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('type', models.CharField(help_text='Document/video, etc. scraped from the css class', max_length=50)),
                ('url', models.URLField(unique=True, verbose_name='URL')),
                ('active', models.BooleanField(default=True)),
                ('scraped_at', models.DateTimeField(auto_now_add=True)),
                ('scrape_status', models.CharField(choices=[('toscrape', 'To Scrape'), ('scraped', 'Scraped'), ('error', 'Error Scraping')], default='toscrape', max_length=20)),
                ('thumbnail', models.URLField(blank=True, null=True)),
                ('text', models.TextField(blank=True, help_text='The text extracted from the pdf', null=True)),
            ],
            options={
                'ordering': ('-meeting__date',),
            },
        ),
        migrations.CreateModel(
            name='Meeting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=512, null=True)),
                ('date', models.DateField()),
                ('scraped_at', models.DateTimeField(auto_now_add=True)),
                ('bandc', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='meetings', to='agenda.BandC')),
            ],
            options={
                'ordering': ('-date',),
                'get_latest_by': 'date',
            },
        ),
        migrations.AddField(
            model_name='document',
            name='meeting',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='agenda.Meeting'),
        ),
        migrations.AlterUniqueTogether(
            name='meeting',
            unique_together=set([('date', 'bandc')]),
        ),
    ]