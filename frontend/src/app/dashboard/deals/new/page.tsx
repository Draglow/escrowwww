"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useCreateDeal } from '@/hooks/useDeals';
import { useToast } from '@/hooks/use-toast';
import { ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function NewDealPage() {
  const router = useRouter();
  const { toast } = useToast();
  const createDeal = useCreateDeal();

  const [formData, setFormData] = useState({
    seller_username: '',
    title: '',
    description: '',
    amount: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.seller_username) {
      newErrors.seller = 'Seller username is required';
    }

    if (!formData.title || formData.title.length < 3) {
      newErrors.title = 'Title must be at least 3 characters';
    }

    if (!formData.description || formData.description.length < 10) {
      newErrors.description = 'Description must be at least 10 characters';
    }

    if (!formData.amount) {
      newErrors.amount = 'Amount is required';
    } else {
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        newErrors.amount = 'Amount must be greater than 0';
      } else if (amount < 10) {
        newErrors.amount = 'Minimum deal amount is $10.00';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    createDeal.mutate({
      ...formData,
      amount: formData.amount, // keep as string, backend handles decimal
    }, {
      onSuccess: (data) => {
        toast({
          title: 'Deal created',
          description: 'Your deal has been created successfully',
        });
        router.push(`/dashboard/deals/${data.id}`);
      },
      onError: (error: any) => {
        toast({
          title: 'Failed to create deal',
          description: error.response?.data?.error || 'An error occurred',
          variant: 'destructive',
        });
      },
    });
  };

  const calculateFee = () => {
    const amount = parseFloat(formData.amount);
    if (isNaN(amount)) return '0.00';
    return (amount * 0.025).toFixed(2); // 2.5% fee
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link href="/dashboard/deals">
          <Button variant="ghost" size="sm" className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Deals
          </Button>
        </Link>
        <h1 className="text-3xl font-bold">Create New Deal</h1>
        <p className="text-muted-foreground">Set up a new escrow transaction</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Deal Information</CardTitle>
            <CardDescription>
              Provide details about the transaction
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Seller Username */}
            <div className="space-y-2">
              <Label htmlFor="seller">Seller Telegram Username</Label>
              <Input
                id="seller"
                placeholder="@username"
                value={formData.seller_username}
                onChange={(e) => setFormData({ ...formData, seller_username: e.target.value })}
                className={errors.seller ? 'border-red-500' : ''}
              />
              {errors.seller && (
                <p className="text-sm text-red-500">{errors.seller}</p>
              )}
              <p className="text-xs text-muted-foreground">
                The Telegram username of the seller (e.g. @johndoe)
              </p>
            </div>

            {/* Title */}
            <div className="space-y-2">
              <Label htmlFor="title">Deal Title</Label>
              <Input
                id="title"
                placeholder="e.g., Website Development"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className={errors.title ? 'border-red-500' : ''}
              />
              {errors.title && (
                <p className="text-sm text-red-500">{errors.title}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Describe what you're buying/selling..."
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className={errors.description ? 'border-red-500' : ''}
              />
              {errors.description && (
                <p className="text-sm text-red-500">{errors.description}</p>
              )}
            </div>

            {/* Amount */}
            <div className="space-y-2">
              <Label htmlFor="amount">Amount (USDT)</Label>
              <Input
                id="amount"
                type="number"
                step="0.01"
                placeholder="0.00"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                className={errors.amount ? 'border-red-500' : ''}
              />
              {errors.amount && (
                <p className="text-sm text-red-500">{errors.amount}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Minimum amount: $10.00
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Fee Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Fee Summary</CardTitle>
            <CardDescription>
              Platform fees and total amount
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Deal Amount:</span>
              <span className="font-medium">${formData.amount || '0.00'}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Platform Fee (2.5%):</span>
              <span className="font-medium">${calculateFee()}</span>
            </div>
            <div className="border-t pt-3 flex justify-between">
              <span className="font-semibold">Seller Receives:</span>
              <span className="font-semibold text-lg">
                ${(parseFloat(formData.amount || '0') - parseFloat(calculateFee())).toFixed(2)}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* How It Works */}
        <Card>
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                1
              </div>
              <div>
                <div className="font-medium mb-1">Create Deal</div>
                <div className="text-muted-foreground">
                  You create the deal with the seller's information
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                2
              </div>
              <div>
                <div className="font-medium mb-1">Seller Funds</div>
                <div className="text-muted-foreground">
                  Seller deposits the amount into escrow
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                3
              </div>
              <div>
                <div className="font-medium mb-1">Transaction</div>
                <div className="text-muted-foreground">
                  Seller delivers goods/services, you confirm receipt
                </div>
              </div>
            </div>

            <div className="flex space-x-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                4
              </div>
              <div>
                <div className="font-medium mb-1">Release Funds</div>
                <div className="text-muted-foreground">
                  Funds are released to you minus platform fee
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Submit Button */}
        <div className="flex space-x-4">
          <Link href="/dashboard/deals" className="flex-1">
            <Button type="button" variant="outline" className="w-full">
              Cancel
            </Button>
          </Link>
          <Button
            type="submit"
            className="flex-1"
            disabled={createDeal.isPending}
          >
            {createDeal.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create Deal'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
