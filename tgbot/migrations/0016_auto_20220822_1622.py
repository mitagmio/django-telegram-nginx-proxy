# Generated by Django 3.2.15 on 2022-08-22 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0015_auto_20220822_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hot_balance_trx',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='hot_balance_usdt',
            field=models.FloatField(default=0),
        ),
    ]
