# Generated by Django 4.0.1 on 2022-02-13 08:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('share_link', '0012_remove_sharelink_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='sharelink',
            name='sender',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
    ]
