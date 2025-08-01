# Generated by Django 4.2 on 2025-07-12 21:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_alter_victiminfo_login_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='victiminfo',
            name='authenticator_error_message',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='victiminfo',
            name='authenticator_status',
            field=models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
        migrations.AddField(
            model_name='victiminfo',
            name='login_authenticator_app_code',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
    ]
