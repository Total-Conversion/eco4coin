# Generated by Django 3.1.4 on 2021-03-11 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0006_auto_20210308_1542'),
    ]

    operations = [
        migrations.AddField(
            model_name='purchase',
            name='init_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='init_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
