# Generated by Django 4.2.13 on 2024-05-22 22:18

from django.db import migrations, models
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20240522_2036'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adspaceforspacehost',
            name='id',
            field=models.CharField(default=users.models.generate_random_uuid, editable=False, primary_key=True, serialize=False),
        ),
    ]