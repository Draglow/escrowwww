"""
Add WebAuthnCredential model for storing passkey credentials.

The existing webauthn_credentials JSONField on User is kept in place
(deprecated, not removed) for migration compatibility.
"""
import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auditlog_user_agent_nullable'),
    ]

    operations = [
        migrations.CreateModel(
            name='WebAuthnCredential',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='webauthn_credentials_set',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('credential_id', models.BinaryField(db_index=True, unique=True)),
                ('public_key', models.BinaryField()),
                ('sign_count', models.PositiveIntegerField(default=0)),
                ('device_name', models.CharField(blank=True, max_length=100, null=True)),
                ('aaguid', models.UUIDField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'WebAuthn Credential',
                'verbose_name_plural': 'WebAuthn Credentials',
                'db_table': 'webauthn_credentials',
            },
        ),
        migrations.AddIndex(
            model_name='webauthnCredential',
            index=models.Index(
                fields=['user', '-created_at'],
                name='webauthn_cred_user_created_idx',
            ),
        ),
    ]
