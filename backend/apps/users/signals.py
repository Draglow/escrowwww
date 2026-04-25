"""
User model signals.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Automatically create a wallet for new users.
    """
    if created:
        from apps.wallets.services import WalletService
        WalletService.create_wallet(instance)
