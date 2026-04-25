"""
Add transaction_hash field to LedgerEntry for blockchain transaction tracking.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ledger', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ledgerentry',
            name='transaction_hash',
            field=models.CharField(blank=True, db_index=True, max_length=128, null=True),
        ),
        migrations.AddIndex(
            model_name='ledgerentry',
            index=models.Index(fields=['transaction_hash'], name='ledger_entr_transac_hash_idx'),
        ),
    ]
