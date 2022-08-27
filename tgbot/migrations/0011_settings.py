# Generated by Django 3.2.13 on 2022-08-13 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0010_user_first_month'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('last_time_payment', models.PositiveBigIntegerField(default=1651688047000)),
                ('key1', models.CharField(blank=True, max_length=256, null=True)),
                ('key2', models.CharField(blank=True, max_length=256, null=True)),
                ('key3', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
    ]