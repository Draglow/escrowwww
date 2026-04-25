"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useBalance, useDepositAddress, useTransactions } from '@/hooks/useWallet';
import { formatCurrency, formatDate, truncateAddress } from '@/lib/utils';
import { Wallet, ArrowDownRight, ArrowUpRight, Copy, RefreshCw, TrendingUp, Lock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { WithdrawForm } from '@/components/wallet/withdraw-form';
import { DepositInstructions } from '@/components/wallet/deposit-instructions';

export default function WalletPage() {
  const { data: balanceData, isLoading: balanceLoading, refetch: refetchBalance } = useBalance();
  const { data: depositData } = useDepositAddress();
  const { data: transactionsData, isLoading: transactionsLoading } = useTransactions();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('overview');

  const handleCopyAddress = () => {
    if (depositData?.address) {
      navigator.clipboard.writeText(depositData.address);
      toast({ title: 'Address copied', description: 'Deposit address copied to clipboard' });
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Wallet</h1>
          <p className="text-muted-foreground mt-0.5">Manage your USDT balance</p>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={() => refetchBalance()}
          disabled={balanceLoading}
          className="rounded-xl"
        >
          <RefreshCw className={`h-4 w-4 ${balanceLoading ? 'animate-spin' : ''}`} />
        </Button>
      </div>

      {/* Balance Hero Card */}
      <Card className="relative overflow-hidden border-primary/20 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent shadow-[0_8px_32px_hsl(var(--primary)/0.12),inset_0_1px_0_rgba(255,255,255,0.6)] dark:shadow-[0_8px_32px_hsl(var(--primary)/0.2),inset_0_1px_0_rgba(255,255,255,0.07)]">
        {/* Decorative orb */}
        <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full bg-primary/8 blur-2xl pointer-events-none" />
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-base font-medium text-muted-foreground">
            <div className="p-1.5 bg-primary/15 rounded-lg icon-3d">
              <Wallet className="h-4 w-4 text-primary" />
            </div>
            <span>Total Balance</span>
          </CardTitle>
          <CardDescription>USDT (TRC20)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-4xl sm:text-5xl font-bold gradient-text mb-3">
            {balanceLoading ? (
              <div className="h-12 w-48 bg-muted/60 animate-pulse rounded-xl" />
            ) : (
              `$${formatCurrency(balanceData?.balance || '0')}`
            )}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center space-x-1.5 text-sm text-muted-foreground">
              <TrendingUp className="h-3.5 w-3.5 text-green-500" />
              <span>Available: <strong className="text-foreground">${formatCurrency(balanceData?.available_balance || '0')}</strong></span>
            </div>
            {depositData?.address && (
              <div className="flex items-center space-x-1.5">
                <span className="text-xs text-muted-foreground font-mono bg-muted/60 px-2 py-1 rounded-lg border border-border/40">
                  {truncateAddress(depositData.address)}
                </span>
                <Button variant="ghost" size="sm" className="h-7 w-7 p-0 rounded-lg" onClick={handleCopyAddress}>
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="deposit">Deposit</TabsTrigger>
          <TabsTrigger value="withdraw">Withdraw</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4 mt-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                <Button
                  className="w-full justify-start rounded-xl group"
                  variant="outline"
                  onClick={() => setActiveTab('deposit')}
                >
                  <div className="p-1 bg-green-500/10 rounded-lg mr-2.5 icon-3d group-hover:scale-110 transition-transform">
                    <ArrowDownRight className="h-3.5 w-3.5 text-green-500" />
                  </div>
                  Deposit USDT
                </Button>
                <Button
                  className="w-full justify-start rounded-xl group"
                  variant="outline"
                  onClick={() => setActiveTab('withdraw')}
                >
                  <div className="p-1 bg-blue-500/10 rounded-lg mr-2.5 icon-3d group-hover:scale-110 transition-transform">
                    <ArrowUpRight className="h-3.5 w-3.5 text-blue-500" />
                  </div>
                  Withdraw USDT
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Wallet Info</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2.5">
                {[
                  { label: 'Network', value: 'TRC20' },
                  { label: 'Currency', value: 'USDT' },
                  { label: 'Min Deposit', value: '$1.00' },
                  { label: 'Min Withdraw', value: '$10.00' },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between items-center py-1.5 border-b border-border/40 last:border-0">
                    <span className="text-sm text-muted-foreground">{label}</span>
                    <span className="text-sm font-semibold">{value}</span>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Recent Transactions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <div className="p-1.5 bg-primary/10 rounded-lg icon-3d">
                  <TrendingUp className="h-4 w-4 text-primary" />
                </div>
                <span>Recent Transactions</span>
              </CardTitle>
              <CardDescription>Your latest wallet activity</CardDescription>
            </CardHeader>
            <CardContent>
              {transactionsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 bg-muted/40 animate-pulse rounded-xl" />
                  ))}
                </div>
              ) : transactionsData?.transactions?.length > 0 ? (
                <div className="space-y-3">
                  {transactionsData.transactions.slice(0, 5).map((tx: any) => (
                    <div
                      key={tx.id}
                      className="flex items-center justify-between p-4 rounded-xl border border-border/60 bg-muted/20 hover:bg-muted/40 transition-colors shadow-[0_1px_3px_rgba(0,0,0,0.04)] stagger-item"
                    >
                      <div className="flex items-center space-x-3.5">
                        <div className={`p-2.5 rounded-xl icon-3d ${
                          tx.transaction_type === 'DEPOSIT'
                            ? 'bg-green-500/10 text-green-500'
                            : 'bg-red-500/10 text-red-500'
                        }`}>
                          {tx.transaction_type === 'DEPOSIT' ? (
                            <ArrowDownRight className="h-4 w-4" />
                          ) : (
                            <ArrowUpRight className="h-4 w-4" />
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-sm">{tx.transaction_type}</div>
                          <div className="text-xs text-muted-foreground">{formatDate(tx.created_at)}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-bold text-sm ${
                          tx.transaction_type === 'DEPOSIT' ? 'text-green-500' : 'text-red-500'
                        }`}>
                          {tx.transaction_type === 'DEPOSIT' ? '+' : '-'}${formatCurrency(tx.amount)}
                        </div>
                        {tx.transaction_hash && (
                          <div className="text-xs text-muted-foreground font-mono">
                            {truncateAddress(tx.transaction_hash)}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-muted/50 mb-3 shadow-[inset_0_2px_6px_rgba(0,0,0,0.06)]">
                    <Lock className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <p className="text-muted-foreground font-medium">No transactions yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="deposit" className="mt-4">
          <DepositInstructions address={depositData?.address} />
        </TabsContent>

        <TabsContent value="withdraw" className="mt-4">
          <WithdrawForm balance={balanceData?.balance || '0'} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
