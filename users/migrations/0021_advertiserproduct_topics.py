# Generated by Django 4.2.1 on 2024-11-08 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0020_alter_advertiserproduct_producttype'),
    ]

    operations = [
        migrations.AddField(
            model_name='advertiserproduct',
            name='topics',
            field=models.TextField(blank=True, null=True),
        ),
    ]
