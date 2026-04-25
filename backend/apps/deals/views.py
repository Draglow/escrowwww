"""
Deal API views.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Deal
from .chat_models import Message
from .serializers import DealSerializer, DealCreateSerializer
from .serializers_chat import MessageSerializer, MessageCreateSerializer
from .services import DealService


class DealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for deal operations.
    """
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter deals for current user. Staff can see all deals."""
        user = self.request.user
        if user.is_staff:
            return Deal.objects.all().select_related('buyer', 'seller').order_by('-created_at')
        return Deal.objects.filter(
            Q(buyer=user) | Q(seller=user)
        ).select_related('buyer', 'seller').order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DealCreateSerializer
        return DealSerializer
    
    def create(self, request, *args, **kwargs):
        """Create a new deal."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        deal = DealService.create_deal(
            buyer=request.user,
            **serializer.validated_data
        )
        
        response_serializer = DealSerializer(deal)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def fund(self, request, pk=None):
        """
        Fund a deal (seller action).
        Locks seller's balance and transitions DRAFT -> FUNDED.
        """
        deal = self.get_object()
        
        # Verify user is the seller
        if deal.seller != request.user:
            return Response(
                {'error': 'Only the seller can fund this deal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            deal = DealService.fund_deal(deal)
            serializer = self.get_serializer(deal)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """
        Start a deal (buyer action).
        Transitions FUNDED -> IN_PROGRESS.
        """
        deal = self.get_object()
        
        # Verify user is the buyer
        if deal.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can start this deal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            deal = DealService.start_deal(deal)
            serializer = self.get_serializer(deal)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """
        Complete a deal (buyer action).
        Releases funds to buyer and transitions IN_PROGRESS -> COMPLETED.
        """
        deal = self.get_object()
        
        # Verify user is the buyer
        if deal.buyer != request.user:
            return Response(
                {'error': 'Only the buyer can complete this deal'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            deal = DealService.complete_deal(deal)
            serializer = self.get_serializer(deal)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def dispute(self, request, pk=None):
        """
        Dispute a deal (buyer or seller action).
        Freezes funds and transitions IN_PROGRESS -> DISPUTED.
        """
        deal = self.get_object()
        
        # Verify user is buyer or seller
        if deal.buyer != request.user and deal.seller != request.user:
            return Response(
                {'error': 'Only deal participants can dispute'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get('reason', '')
        
        try:
            deal = DealService.dispute_deal(deal, reason)
            serializer = self.get_serializer(deal)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel a deal (buyer or seller action).
        Refunds locked funds if applicable.
        """
        deal = self.get_object()
        
        # Verify user is buyer or seller
        if deal.buyer != request.user and deal.seller != request.user:
            return Response(
                {'error': 'Only deal participants can cancel'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow cancellation in certain states
        if deal.status not in ['DRAFT', 'FUNDED']:
            return Response(
                {'error': f'Cannot cancel deal in {deal.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            deal = DealService.cancel_deal(deal, refund=True)
            serializer = self.get_serializer(deal)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Resolve a disputed deal (admin action only).
        
        Body:
            - resolution: Resolution description
            - refund_to_seller: Boolean, if true refunds to seller, else releases to buyer
        """
        deal = self.get_object()
        
        # Verify user is admin/staff
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can resolve disputes'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resolution = request.data.get('resolution', '')
        refund_to_seller = request.data.get('refund_to_seller', False)
        
        try:
            deal = DealService.resolve_dispute(deal, resolution, refund_to_seller)
            serializer = self.get_serializer(deal)
            return Response(serializer.data)
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get chat messages for a deal.
        """
        deal = self.get_object()
        
        # Verify user is buyer or seller
        if deal.buyer != request.user and deal.seller != request.user:
            return Response(
                {'error': 'Only deal participants can view messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        messages = Message.objects.filter(deal=deal).select_related('sender').order_by('created_at')
        
        # Paginate messages
        paginator = PageNumberPagination()
        paginator.page_size = 50
        paginated_messages = paginator.paginate_queryset(messages, request)
        
        serializer = MessageSerializer(paginated_messages, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """
        Send a chat message in a deal (REST fallback for WebSocket).
        """
        deal = self.get_object()
        
        # Verify user is buyer or seller
        if deal.buyer != request.user and deal.seller != request.user:
            return Response(
                {'error': 'Only deal participants can send messages'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            deal=deal,
            sender=request.user,
            content=serializer.validated_data['content']
        )
        
        response_serializer = MessageSerializer(message)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def mark_messages_read(self, request, pk=None):
        """
        Mark messages as read.
        
        Body:
            - message_ids: List of message UUIDs to mark as read
        """
        deal = self.get_object()
        
        # Verify user is buyer or seller
        if deal.buyer != request.user and deal.seller != request.user:
            return Response(
                {'error': 'Only deal participants can mark messages as read'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        message_ids = request.data.get('message_ids', [])
        
        # Mark messages as read (exclude own messages)
        updated_count = Message.objects.filter(
            id__in=message_ids,
            deal=deal
        ).exclude(
            sender=request.user
        ).update(is_read=True)
        
        return Response({
            'updated_count': updated_count
        })
