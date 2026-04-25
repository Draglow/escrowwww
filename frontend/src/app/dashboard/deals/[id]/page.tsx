"use client";

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useDeal,
  useFundDeal,
  useStartDeal,
  useCompleteDeal,
  useDisputeDeal,
  useCancelDeal,
} from '@/hooks/useDeals';
import { useAuthStore } from '@/store/auth';
import { useToast } from '@/hooks/use-toast';
import { formatCurrency, formatDate } from '@/lib/utils';
import { ArrowLeft, Loader2, AlertCircle, MessageSquare, Info } from 'lucide-react';
import { DealChat } from '@/components/deals/deal-chat';
import { DealTimeline } from '@/components/deals/deal-timeline';
import { ConfirmDialog } from '@/components/ui/confirm-dialog';

const STATUS_COLORS = {
  DRAFT: 'bg-gray-500',
  FUNDED: 'bg-blue-500',
  IN_PROGRESS: 'bg-yellow-500',
  COMPLETED: 'bg-green-500',
  DISPUTED: 'bg-red-500',
  CANCELLED: 'bg-gray-500',
};

export default function DealDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuthStore();
  const { toast } = useToast();
  const dealId = params.id as string;

  const { data: deal, isLoading } = useDeal(dealId);
  const fundDeal = useFundDeal();
  const startDeal = useStartDeal();
  const completeDeal = useCompleteDeal();
  const disputeDeal = useDisputeDeal();
  const cancelDeal = useCancelDeal();

  const [showDisputeDialog, setShowDisputeDialog] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showCompleteDialog, setShowCompleteDialog] = useState(false);
  const [disputeReason, setDisputeReason] = useState('');

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!deal) {
    return (
      <div className="text-center py-12">
        <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Deal not found</h3>
        <p className="text-muted-foreground mb-4">
          This deal doesn't exist or you don't have access to it
        </p>
        <Link href="/dashboard/deals">
          <Button>Back to Deals</Button>
        </Link>
      </div>
    );
  }

  const isBuyer = deal.buyer.id === user?.id;
  const isSeller = deal.seller.id === user?.id;
  const otherParty = isBuyer ? deal.seller : deal.buyer;

  const handleFund = () => {
    fundDeal.mutate(dealId, {
      onSuccess: () => {
        toast({
          title: 'Deal funded',
          description: 'The deal has been funded successfully',
        });
      },
      onError: (error: any) => {
        toast({
          title: 'Failed to fund deal',
          description: error.response?.data?.error || 'An error occurred',
          variant: 'destructive',
        });
      },
    });
  };

  const handleStart = () => {
    startDeal.mutate(dealId, {
      onSuccess: () => {
        toast({
          title: 'Deal started',
          description: 'The deal is now in progress',
        });
      },
      onError: (error: any) => {
        toast({
          title: 'Failed to start deal',
          description: error.response?.data?.error || 'An error occurred',
          variant: 'destructive',
        });
      },
    });
  };

  const handleComplete = () => {
    completeDeal.mutate(dealId, {
      onSuccess: () => {
        toast({
          title: 'Deal completed',
          description: 'The deal has been completed and funds released',
        });
        setShowCompleteDialog(false);
      },
      onError: (error: any) => {
        toast({
          title: 'Failed to complete deal',
          description: error.response?.data?.error || 'An error occurred',
          variant: 'destructive',
        });
      },
    });
  };

  const handleDispute = () => {
    if (!disputeReason.trim()) {
      toast({
        title: 'Reason required',
        description: 'Please provide a reason for the dispute',
        variant: 'destructive',
      });
      return;
    }

    disputeDeal.mutate(
      { dealId, reason: disputeReason },
      {
        onSuccess: () => {
          toast({
            title: 'Dispute opened',
            description: 'An admin will review your dispute',
          });
          setShowDisputeDialog(false);
          setDisputeReason('');
        },
        onError: (error: any) => {
          toast({
            title: 'Failed to open dispute',
            description: error.response?.data?.error || 'An error occurred',
            variant: 'destructive',
          });
        },
      }
    );
  };

  const handleCancel = () => {
    cancelDeal.mutate(dealId, {
      onSuccess: () => {
        toast({
          title: 'Deal cancelled',
          description: 'The deal has been cancelled',
        });
        setShowCancelDialog(false);
      },
      onError: (error: any) => {
        toast({
          title: 'Failed to cancel deal',
          description: error.response?.data?.error || 'An error occurred',
          variant: 'destructive',
        });
      },
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <Link href="/dashboard/deals">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Deals
          </Button>
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">{deal.title}</h1>
            <p className="text-muted-foreground">{deal.description}</p>
          </div>
          <Badge className={STATUS_COLORS[deal.status]}>
            {deal.status}
          </Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Deal Info */}
          <Card>
            <CardHeader>
              <CardTitle>Deal Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Amount</div>
                  <div className="text-2xl font-bold">${formatCurrency(deal.amount)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Platform Fee</div>
                  <div className="text-2xl font-bold">${formatCurrency(deal.fee)}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Buyer</div>
                  <div className="font-medium">
                    {deal.buyer.telegram_username || deal.buyer.username}
                    {isBuyer && <span className="text-primary ml-2">(You)</span>}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Seller</div>
                  <div className="font-medium">
                    {deal.seller.telegram_username || deal.seller.username}
                    {isSeller && <span className="text-primary ml-2">(You)</span>}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <DealTimeline deal={deal} />
            </CardContent>
          </Card>

          {/* Chat */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <MessageSquare className="h-5 w-5" />
                <span>Chat</span>
              </CardTitle>
              <CardDescription>
                Communicate with {otherParty.telegram_username || otherParty.username}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DealChat dealId={dealId} />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {/* Seller: Fund Deal */}
              {isSeller && deal.status === 'DRAFT' && (
                <Button
                  className="w-full"
                  onClick={handleFund}
                  disabled={fundDeal.isPending}
                >
                  {fundDeal.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Funding...
                    </>
                  ) : (
                    'Fund Deal'
                  )}
                </Button>
              )}

              {/* Buyer: Start Deal */}
              {isBuyer && deal.status === 'FUNDED' && (
                <Button
                  className="w-full"
                  onClick={handleStart}
                  disabled={startDeal.isPending}
                >
                  {startDeal.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    'Start Deal'
                  )}
                </Button>
              )}

              {/* Buyer: Complete Deal */}
              {isBuyer && deal.status === 'IN_PROGRESS' && (
                <Button
                  className="w-full"
                  onClick={() => setShowCompleteDialog(true)}
                >
                  Complete Deal
                </Button>
              )}

              {/* Both: Dispute */}
              {deal.status === 'IN_PROGRESS' && (
                <Button
                  className="w-full"
                  variant="destructive"
                  onClick={() => setShowDisputeDialog(true)}
                >
                  Open Dispute
                </Button>
              )}

              {/* Both: Cancel */}
              {(deal.status === 'DRAFT' || deal.status === 'FUNDED') && (
                <Button
                  className="w-full"
                  variant="outline"
                  onClick={() => setShowCancelDialog(true)}
                >
                  Cancel Deal
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Status Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Info className="h-5 w-5" />
                <span>Status Info</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm space-y-2">
              {deal.status === 'DRAFT' && (
                <p>Waiting for seller to fund the deal</p>
              )}
              {deal.status === 'FUNDED' && (
                <p>Waiting for buyer to start the deal</p>
              )}
              {deal.status === 'IN_PROGRESS' && (
                <p>Deal is in progress. Buyer can complete when satisfied.</p>
              )}
              {deal.status === 'COMPLETED' && (
                <p>Deal completed successfully on {formatDate(deal.completed_at!)}</p>
              )}
              {deal.status === 'DISPUTED' && (
                <p className="text-red-500">
                  Deal is under dispute. An admin will review.
                </p>
              )}
              {deal.status === 'CANCELLED' && (
                <p>Deal was cancelled on {formatDate(deal.cancelled_at!)}</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dialogs */}
      <ConfirmDialog
        open={showCompleteDialog}
        onOpenChange={setShowCompleteDialog}
        onConfirm={handleComplete}
        title="Complete Deal"
        description="Are you sure you want to complete this deal? Funds will be released to you."
        confirmText="Complete"
        loading={completeDeal.isPending}
      />

      <ConfirmDialog
        open={showCancelDialog}
        onOpenChange={setShowCancelDialog}
        onConfirm={handleCancel}
        title="Cancel Deal"
        description="Are you sure you want to cancel this deal? This action cannot be undone."
        confirmText="Cancel Deal"
        variant="destructive"
        loading={cancelDeal.isPending}
      />

      <ConfirmDialog
        open={showDisputeDialog}
        onOpenChange={setShowDisputeDialog}
        onConfirm={handleDispute}
        title="Open Dispute"
        description="Please provide a reason for opening this dispute:"
        confirmText="Open Dispute"
        variant="destructive"
        loading={disputeDeal.isPending}
        showInput
        inputValue={disputeReason}
        onInputChange={setDisputeReason}
        inputPlaceholder="Describe the issue..."
      />
    </div>
  );
}
