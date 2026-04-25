"""
Ledger API views.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import LedgerEntry
from .serializers import LedgerEntrySerializer


class LedgerEntryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing ledger entries.
    Read-only to maintain immutability.
    """
    queryset = LedgerEntry.objects.all()
    serializer_class = LedgerEntrySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter to only show current user's entries."""
        return LedgerEntry.objects.filter(
            user=self.request.user
        ).select_related('deal')
