# Generated by Django 4.2.13 on 2024-09-23 17:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0019_advertiserproduct_producttype'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advertiserproduct',
            name='productType',
            field=models.CharField(default='public', max_length=255),
        ),
    ]
