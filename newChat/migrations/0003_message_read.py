# Generated by Django 4.2.13 on 2024-09-20 15:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('newChat', '0002_message_receiver_alter_message_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='read',
            field=models.BooleanField(default=False),
            preserve_default=False,
        ),
    ]