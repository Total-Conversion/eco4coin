# Generated by Django 3.1.4 on 2021-03-01 09:29

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='cash_balance',
            field=models.FloatField(default=10, help_text='how much cash_balance a user has', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100000000)]),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='coin_balance',
            field=models.IntegerField(default=10),
        ),
    ]