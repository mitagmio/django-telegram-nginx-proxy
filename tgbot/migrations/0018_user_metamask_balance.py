# Generated by Django 3.2.15 on 2022-08-24 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0017_user_marker'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='metamask_balance',
            field=models.FloatField(default=0),
        ),
    ]
