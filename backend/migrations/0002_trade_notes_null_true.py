# Generated by Django 3.1.4 on 2021-02-18 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='trade',
            name='notes',
            field=models.TextField(blank=True, default='', max_length=255, null=True),
        ),
    ]
