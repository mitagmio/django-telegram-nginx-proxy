# Generated by Django 3.2.12 on 2022-04-10 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0027_alter_order_merchant_executor_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status_fee',
            field=models.CharField(default='not_paid', max_length=32),
        ),
    ]
