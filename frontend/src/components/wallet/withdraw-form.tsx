"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useWithdraw } from '@/hooks/useWallet';
import { useAuthStore } from '@/store/auth';
import { useToast } from '@/hooks/use-toast';
import { formatCurrency } from '@/lib/utils';
import { AlertCircle, Loader2, ArrowUpRight, Shield } from 'lucide-react';

interface WithdrawFormProps {
  balance: string;
}

export function WithdrawForm({ balance }: WithdrawFormProps) {
  const { user } = useAuthStore();
  const { toast } = useToast();
  const withdraw = useWithdraw();

  const [formData, setFormData] = useState({ to_address: '', amount: '', totp_token: '' });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    if (!formData.to_address) {
      newErrors.to_address = 'Address is required';
    } else if (!formData.to_address.startsWith('T') || formData.to_address.length !== 34) {
      newErrors.to_address = 'Invalid Tron address';
    }
    if (!formData.amount) {
      newErrors.amount = 'Amount is required';
    } else {
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) newErrors.amount = 'Amount must be greater than 0';
      else if (amount < 10) newErrors.amount = 'Minimum withdrawal is $10.00';
      else if (amount > parseFloat(balance)) newErrors.amount = 'Insufficient balance';
    }
    if (user?.is_2fa_enabled && !formData.totp_token) {
      newErrors.totp_token = '2FA token is required';
    } else if (formData.totp_token && formData.totp_token.length !== 6) {
      newErrors.totp_token = '2FA token must be 6 digits';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    withdraw.mutate(formData, {
      onSuccess: () => {
        toast({
          title: 'Withdrawal submitted',
          description: `Your withdrawal of $${formatCurrency(formData.amount)} has been submitted for processing.`,
        });
        setFormData({ to_address: '', amount: '', totp_token: '' });
      },
      onError: (error: any) => {
        toast({
          title: 'Withdrawal failed',
          description: error.response?.data?.error || 'Failed to process withdrawal',
          variant: 'destructive',
        });
      },
    });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <div className="p-1.5 bg-blue-500/10 rounded-lg icon-3d">
              <ArrowUpRight className="h-4 w-4 text-blue-500" />
            </div>
            <span>Withdraw USDT</span>
          </CardTitle>
          <CardDescription>Send USDT from your wallet to an external address</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Destination Address */}
            <div className="space-y-1.5">
              <Label htmlFor="to_address">Destination Address</Label>
              <Input
                id="to_address"
                placeholder="TRC20 address (starts with T)"
                value={formData.to_address}
                onChange={(e) => setFormData({ ...formData, to_address: e.target.value })}
                className={errors.to_address ? 'border-red-500 focus-visible:border-red-500' : ''}
              />
              {errors.to_address && (
                <p className="text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />{errors.to_address}
                </p>
              )}
            </div>

            {/* Amount */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="amount">Amount (USDT)</Label>
                <span className="text-xs text-muted-foreground">
                  Available: <strong className="text-foreground">${formatCurrency(balance)}</strong>
                </span>
              </div>
              <div className="flex space-x-2">
                <Input
                  id="amount"
                  type="number"
                  step="0.000001"
                  placeholder="0.00"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  className={errors.amount ? 'border-red-500 focus-visible:border-red-500' : ''}
                />
                <Button type="button" variant="outline" onClick={() => setFormData({ ...formData, amount: balance })} className="shrink-0 rounded-xl">
                  Max
                </Button>
              </div>
              {errors.amount && (
                <p className="text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle className="h-3 w-3" />{errors.amount}
                </p>
              )}
            </div>

            {/* 2FA Token */}
            {user?.is_2fa_enabled && (
              <div className="space-y-1.5">
                <Label htmlFor="totp_token">2FA Code</Label>
                <Input
                  id="totp_token"
                  type="text"
                  maxLength={6}
                  placeholder="000000"
                  value={formData.totp_token}
                  onChange={(e) => setFormData({ ...formData, totp_token: e.target.value.replace(/\D/g, '') })}
                  className={`text-center text-xl tracking-[0.5em] font-mono ${errors.totp_token ? 'border-red-500' : ''}`}
                />
                {errors.totp_token && (
                  <p className="text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />{errors.totp_token}
                  </p>
                )}
                <p className="text-xs text-muted-foreground">Enter the 6-digit code from your authenticator app</p>
              </div>
            )}

            {/* Fee Info */}
            <div className="p-4 rounded-xl bg-muted/30 border border-border/40 shadow-[inset_0_1px_3px_rgba(0,0,0,0.04)] space-y-2">
              {[
                { label: 'Network Fee', value: '~1 TRX' },
                { label: 'Processing Time', value: '1-5 minutes' },
                { label: 'Min Withdrawal', value: '$10.00' },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-muted-foreground">{label}</span>
                  <span className="font-semibold">{value}</span>
                </div>
              ))}
            </div>

            <Button type="submit" className="w-full" size="lg" disabled={withdraw.isPending}>
              {withdraw.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <ArrowUpRight className="mr-2 h-4 w-4" />
                  Withdraw USDT
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Security Notice */}
      <Card className="border-yellow-500/30 bg-yellow-500/5">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center space-x-2 text-base">
            <div className="p-1.5 bg-yellow-500/15 rounded-lg icon-3d">
              <AlertCircle className="h-4 w-4 text-yellow-500" />
            </div>
            <span className="text-yellow-600 dark:text-yellow-400">Security Notice</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1.5">
          {[
            'Double-check the destination address before confirming',
            'Withdrawals cannot be reversed once processed',
            'Only send to TRC20 compatible wallets',
            ...(user?.is_2fa_enabled ? ['2FA code is required for all withdrawals'] : []),
            ...(!user?.is_2fa_enabled ? ['Consider enabling 2FA for additional security'] : []),
          ].map((note) => (
            <div key={note} className="flex items-start space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 mt-1.5 shrink-0" />
              <p className="text-sm text-muted-foreground">{note}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
