# Generated by Django 3.2.15 on 2022-11-13 08:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0019_auto_20221018_1545'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='animoca_2_4_balance',
            field=models.FloatField(default=0),
        ),
    ]
