# Generated by Django 3.2.12 on 2022-04-07 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0005_p2p_usd_tinkoff_usdt'),
    ]

    operations = [
        migrations.AlterField(
            model_name='p2p',
            name='eur_revolut_usdt',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='p2p',
            name='rub_tinkoff_usdt',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='p2p',
            name='uah_usdt',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='p2p',
            name='usd_tinkoff_usdt',
            field=models.FloatField(default=0),
        ),
        migrations.AlterField(
            model_name='p2p',
            name='usdt_lkr',
            field=models.FloatField(default=0),
        ),
    ]
