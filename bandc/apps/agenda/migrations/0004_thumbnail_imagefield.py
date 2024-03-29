# Generated by Django 3.0.2 on 2020-01-19 03:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0003_auto_20160124_1941"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="thumbnail",
            field=models.ImageField(
                blank=True,
                help_text="A jpeg of the first page",
                null=True,
                upload_to="thumbs/%Y/%m",
            ),
        ),
    ]
