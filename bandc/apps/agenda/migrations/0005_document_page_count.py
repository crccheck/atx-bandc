# Generated by Django 3.0.2 on 2020-01-20 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0004_thumbnail_imagefield'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='page_count',
            field=models.PositiveSmallIntegerField(blank=True, help_text="Number of pages in a document if it's a PDF", null=True),
        ),
    ]