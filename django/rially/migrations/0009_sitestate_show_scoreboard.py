# Generated by Django 2.0.2 on 2019-01-21 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rially', '0008_stateentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitestate',
            name='show_scoreboard',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
    ]
