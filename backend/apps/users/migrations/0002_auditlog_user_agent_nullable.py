"""
Make AuditLog.user_agent nullable to allow None values from log_audit().
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='user_agent',
            field=models.TextField(blank=True, null=True),
        ),
    ]
