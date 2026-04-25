"""
Factory Boy factories for test data generation.
"""
import os
import factory
from decimal import Decimal
from django.contrib.auth import get_user_model
from apps.deals.models import Deal
from apps.ledger.models import LedgerEntry
from apps.wallets.models import Wallet
from apps.users.models import WebAuthnCredential

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    telegram_id = factory.Sequence(lambda n: 100000000 + n)
    username = factory.Sequence(lambda n: f'testuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    balance = Decimal('0.000000')
    is_active = True
    is_staff = False


class AdminUserFactory(UserFactory):
    """Factory for admin users."""
    is_staff = True
    is_superuser = True


class WebAuthnCredentialFactory(factory.django.DjangoModelFactory):
    """Factory for creating test WebAuthn credentials."""

    class Meta:
        model = WebAuthnCredential

    user = factory.SubFactory(UserFactory)
    credential_id = factory.LazyFunction(lambda: os.urandom(32))
    public_key = factory.LazyFunction(lambda: os.urandom(77))
    sign_count = 0
    device_name = factory.Sequence(lambda n: f'Test Device {n}')
    aaguid = None
    is_active = True


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    telegram_id = factory.Sequence(lambda n: 100000000 + n)
    username = factory.Sequence(lambda n: f'testuser{n}')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    balance = Decimal('0.000000')
    is_active = True
    is_staff = False


class AdminUserFactory(UserFactory):
    """Factory for admin users."""
    is_staff = True
    is_superuser = True


class WalletFactory(factory.django.DjangoModelFactory):
    """Factory for creating test wallets."""

    class Meta:
        model = Wallet
        django_get_or_create = ('user',)

    user = factory.SubFactory(UserFactory)
    # Unique TRC20-style address using UUID
    address = factory.LazyAttribute(
        lambda o: 'T' + str(o.user.id).replace('-', '')[:33]
    )
    encrypted_private_key = b'fake_encrypted_key_for_testing_only'


class DealFactory(factory.django.DjangoModelFactory):
    """Factory for creating test deals."""

    class Meta:
        model = Deal

    buyer = factory.SubFactory(UserFactory)
    seller = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'Test Deal {n}')
    description = factory.Faker('paragraph')
    amount = Decimal('100.000000')
    fee = Decimal('2.500000')
    status = 'DRAFT'


class FundedDealFactory(DealFactory):
    """Factory for funded deals."""
    status = 'FUNDED'


class InProgressDealFactory(DealFactory):
    """Factory for in-progress deals."""
    status = 'IN_PROGRESS'


class LedgerEntryFactory(factory.django.DjangoModelFactory):
    """Factory for creating test ledger entries."""

    class Meta:
        model = LedgerEntry

    user = factory.SubFactory(UserFactory)
    transaction_type = 'DEPOSIT'
    amount = Decimal('100.000000')
    balance_before = Decimal('0.000000')
    balance_after = Decimal('100.000000')
    description = 'Test transaction'
    transaction_hash = factory.Sequence(lambda n: f'0x{"a" * 62}{n:02d}')
