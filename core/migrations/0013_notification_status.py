# Generated by Django 4.2.1 on 2024-11-24 06:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_notification'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='status',
            field=models.CharField(default='sent', max_length=255),
            preserve_default=False,
        ),
    ]
