# Generated by Django 4.2.13 on 2024-10-08 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_alter_affiliatelink_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitor',
            name='ip_address',
            field=models.GenericIPAddressField(unique=True),
        ),
    ]
