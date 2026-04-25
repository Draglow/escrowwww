"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/store/auth';
import { useBalance } from '@/hooks/useWallet';
import { formatCurrency } from '@/lib/utils';
import {
  Wallet, TrendingUp, FileText, Shield,
  ArrowUpRight, ArrowDownRight, Plus, Activity, Zap,
  CheckCircle2,
} from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: balanceData, isLoading } = useBalance();

  const quickActions = [
    {
      href: '/dashboard/wallet?action=deposit',
      icon: ArrowDownRight,
      iconBg: 'bg-emerald-500/15',
      iconColor: 'text-emerald-500',
      ringColor: 'hover:border-emerald-500/40 hover:shadow-[0_8px_24px_rgba(16,185,129,0.15)]',
      label: 'Deposit',
      sub: 'Add funds',
      accent: 'from-emerald-500/8',
    },
    {
      href: '/dashboard/wallet?action=withdraw',
      icon: ArrowUpRight,
      iconBg: 'bg-blue-500/15',
      iconColor: 'text-blue-500',
      ringColor: 'hover:border-blue-500/40 hover:shadow-[0_8px_24px_rgba(59,130,246,0.15)]',
      label: 'Withdraw',
      sub: 'Send funds',
      accent: 'from-blue-500/8',
    },
    {
      href: '/dashboard/deals/new',
      icon: FileText,
      iconBg: 'bg-primary/15',
      iconColor: 'text-primary',
      ringColor: 'hover:border-primary/40 hover:shadow-[0_8px_24px_hsl(var(--primary)/0.15)]',
      label: 'New Deal',
      sub: 'Create escrow',
      accent: 'from-primary/8',
    },
    {
      href: '/dashboard/profile?tab=security',
      icon: Shield,
      iconBg: 'bg-amber-500/15',
      iconColor: 'text-amber-500',
      ringColor: 'hover:border-amber-500/40 hover:shadow-[0_8px_24px_rgba(245,158,11,0.15)]',
      label: 'Security',
      sub: 'Manage 2FA',
      accent: 'from-amber-500/8',
    },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-500">

      {/* ── Welcome ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
            Welcome back,{' '}
            <span className="gradient-text">{user?.first_name || user?.username}</span>{' '}
            <span className="not-italic">👋</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Here's an overview of your account activity
          </p>
        </div>
        <Link href="/dashboard/deals/new">
          <Button size="lg" className="group w-full sm:w-auto gap-2 pulse-glow">
            <Plus className="h-4 w-4" />
            Create Deal
            <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Button>
        </Link>
      </div>

      {/* ── Stats Cards ──────────────────────────────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">

        {/* Balance */}
        <Card className="relative overflow-hidden border-primary/20 hover:border-primary/40 hover:shadow-[0_12px_32px_hsl(var(--primary)/0.14)] transition-all duration-300 hover:-translate-y-1 group">
          {/* top accent stripe */}
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-primary/60 via-primary to-primary/60 rounded-t-xl" />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Balance
            </CardTitle>
            <div className="p-1.5 bg-primary/12 rounded-lg shadow-[0_2px_6px_hsl(var(--primary)/0.2),inset_0_1px_0_rgba(255,255,255,0.15)] group-hover:scale-110 transition-transform duration-200">
              <Wallet className="h-3.5 w-3.5 text-primary" />
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-xl sm:text-2xl font-bold gradient-text leading-tight">
              {isLoading ? (
                <div className="h-7 w-20 bg-muted animate-pulse rounded-lg" />
              ) : (
                `$${formatCurrency(balanceData?.balance || '0')}`
              )}
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5 font-medium">USDT · TRC20</p>
            <div className="mt-2.5 flex items-center gap-1 text-[10px] text-emerald-500 font-semibold">
              <TrendingUp className="h-2.5 w-2.5 shrink-0" />
              <span className="truncate">
                ${formatCurrency(balanceData?.available_balance || '0')} avail.
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Active Deals */}
        <Card className="relative overflow-hidden border-blue-500/15 hover:border-blue-500/40 hover:shadow-[0_12px_32px_rgba(59,130,246,0.12)] transition-all duration-300 hover:-translate-y-1 group">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500/60 via-blue-500 to-blue-500/60 rounded-t-xl" />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Active
            </CardTitle>
            <div className="p-1.5 bg-blue-500/12 rounded-lg shadow-[0_2px_6px_rgba(59,130,246,0.2),inset_0_1px_0_rgba(255,255,255,0.15)] group-hover:scale-110 transition-transform duration-200">
              <Activity className="h-3.5 w-3.5 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-xl sm:text-2xl font-bold leading-tight">0</div>
            <p className="text-[10px] text-muted-foreground mt-0.5 font-medium">In progress</p>
            <div className="mt-2.5">
              <Link href="/dashboard/deals">
                <span className="text-[10px] font-semibold text-blue-500 hover:text-blue-400 transition-colors">
                  View deals →
                </span>
              </Link>
            </div>
          </CardContent>
        </Card>

        {/* Completed Deals */}
        <Card className="relative overflow-hidden border-emerald-500/15 hover:border-emerald-500/40 hover:shadow-[0_12px_32px_rgba(16,185,129,0.1)] transition-all duration-300 hover:-translate-y-1 group">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500/60 via-emerald-500 to-emerald-500/60 rounded-t-xl" />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Completed
            </CardTitle>
            <div className="p-1.5 bg-emerald-500/12 rounded-lg shadow-[0_2px_6px_rgba(16,185,129,0.2),inset_0_1px_0_rgba(255,255,255,0.15)] group-hover:scale-110 transition-transform duration-200">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="text-xl sm:text-2xl font-bold leading-tight">0</div>
            <p className="text-[10px] text-muted-foreground mt-0.5 font-medium">All time</p>
            <div className="mt-2.5 flex items-center gap-1 text-[10px] text-emerald-500 font-semibold">
              <TrendingUp className="h-2.5 w-2.5" />
              <span>100% success</span>
            </div>
          </CardContent>
        </Card>

        {/* Security */}
        <Card className={`relative overflow-hidden transition-all duration-300 hover:-translate-y-1 group ${
          user?.is_2fa_enabled
            ? 'border-emerald-500/20 hover:border-emerald-500/40 hover:shadow-[0_12px_32px_rgba(16,185,129,0.12)]'
            : 'border-amber-500/20 hover:border-amber-500/40 hover:shadow-[0_12px_32px_rgba(245,158,11,0.12)]'
        }`}>
          <div className={`absolute top-0 left-0 right-0 h-0.5 rounded-t-xl bg-gradient-to-r ${
            user?.is_2fa_enabled
              ? 'from-emerald-500/60 via-emerald-500 to-emerald-500/60'
              : 'from-amber-500/60 via-amber-500 to-amber-500/60'
          }`} />
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-1 pt-4 px-4">
            <CardTitle className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Security
            </CardTitle>
            <div className={`p-1.5 rounded-lg group-hover:scale-110 transition-transform duration-200 ${
              user?.is_2fa_enabled
                ? 'bg-emerald-500/12 shadow-[0_2px_6px_rgba(16,185,129,0.2),inset_0_1px_0_rgba(255,255,255,0.15)]'
                : 'bg-amber-500/12 shadow-[0_2px_6px_rgba(245,158,11,0.2),inset_0_1px_0_rgba(255,255,255,0.15)]'
            }`}>
              <Shield className={`h-3.5 w-3.5 ${user?.is_2fa_enabled ? 'text-emerald-500' : 'text-amber-500'}`} />
            </div>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className={`text-xl sm:text-2xl font-bold leading-tight ${
              user?.is_2fa_enabled ? 'text-emerald-500' : 'text-amber-500'
            }`}>
              {user?.is_2fa_enabled ? '✓' : '!'}
            </div>
            <p className="text-[10px] text-muted-foreground mt-0.5 font-medium">
              {user?.is_2fa_enabled ? '2FA enabled' : '2FA disabled'}
            </p>
            {!user?.is_2fa_enabled && (
              <div className="mt-2.5">
                <Link href="/dashboard/profile?tab=security">
                  <span className="text-[10px] font-semibold text-amber-500 hover:text-amber-400 transition-colors">
                    Enable now →
                  </span>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Quick Actions ────────────────────────────────────── */}
      <Card className="border-border/60">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <div className="p-1.5 bg-primary/10 rounded-lg shadow-[0_2px_6px_hsl(var(--primary)/0.2),inset_0_1px_0_rgba(255,255,255,0.15)]">
              <Zap className="h-3.5 w-3.5 text-primary" />
            </div>
            Quick Actions
          </CardTitle>
          <CardDescription className="text-xs">Common tasks at your fingertips</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {quickActions.map(({ href, icon: Icon, iconBg, iconColor, ringColor, label, sub, accent }) => (
            <Link key={href} href={href} className="group">
              <div className={`
                relative overflow-hidden flex flex-col items-center justify-center
                gap-2 p-4 sm:p-5 rounded-2xl border border-border/60 bg-card
                cursor-pointer transition-all duration-250
                hover:-translate-y-1 ${ringColor}
                shadow-[0_2px_6px_rgba(0,0,0,0.04),inset_0_1px_0_rgba(255,255,255,0.5)]
                dark:shadow-[0_2px_6px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.04)]
                active:translate-y-0 active:shadow-none
              `}>
                {/* subtle gradient wash on hover */}
                <div className={`absolute inset-0 bg-gradient-to-br ${accent} to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-250 rounded-2xl`} />

                {/* icon */}
                <div className={`
                  relative z-10 p-2.5 sm:p-3 ${iconBg} rounded-xl
                  shadow-[0_2px_8px_rgba(0,0,0,0.1),inset_0_1px_0_rgba(255,255,255,0.2)]
                  group-hover:scale-110 group-hover:shadow-[0_4px_12px_rgba(0,0,0,0.15),inset_0_1px_0_rgba(255,255,255,0.25)]
                  transition-all duration-200
                `}>
                  <Icon className={`h-5 w-5 sm:h-6 sm:w-6 ${iconColor}`} />
                </div>

                {/* text */}
                <div className="relative z-10 text-center">
                  <p className="font-bold text-xs sm:text-sm leading-tight">{label}</p>
                  <p className="text-[10px] sm:text-xs text-muted-foreground mt-0.5">{sub}</p>
                </div>
              </div>
            </Link>
          ))}
        </CardContent>
      </Card>

      {/* ── Recent Activity ──────────────────────────────────── */}
      <Card className="border-border/60">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <div className="p-1.5 bg-primary/10 rounded-lg shadow-[0_2px_6px_hsl(var(--primary)/0.2),inset_0_1px_0_rgba(255,255,255,0.15)]">
              <Activity className="h-3.5 w-3.5 text-primary" />
            </div>
            Recent Activity
          </CardTitle>
          <CardDescription className="text-xs">Your latest transactions and deals</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <div className="flex items-center justify-center w-14 h-14 rounded-2xl bg-muted/50 shadow-[inset_0_2px_8px_rgba(0,0,0,0.07)]">
              <FileText className="h-6 w-6 text-muted-foreground/60" />
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-muted-foreground">No recent activity</p>
              <p className="text-xs text-muted-foreground/60 mt-0.5">Your transactions will appear here</p>
            </div>
            <Link href="/dashboard/deals/new">
              <Button variant="outline" size="sm" className="mt-1 gap-1.5 rounded-xl">
                <Plus className="h-3.5 w-3.5" />
                Create your first deal
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* ── Security Alert ───────────────────────────────────── */}
      {!user?.is_2fa_enabled && (
        <Card className="relative overflow-hidden border-amber-500/30 animate-in slide-in-from-bottom-4 duration-700">
          {/* gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-amber-500/8 via-amber-500/4 to-transparent pointer-events-none" />
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-amber-500/60 via-amber-500 to-amber-500/60 rounded-t-xl" />

          <CardHeader className="relative pb-2">
            <CardTitle className="flex items-center gap-2.5 text-base">
              <div className="p-2 bg-amber-500/15 rounded-xl shadow-[0_2px_8px_rgba(245,158,11,0.2),inset_0_1px_0_rgba(255,255,255,0.15)]">
                <Shield className="h-4 w-4 text-amber-500" />
              </div>
              Security Recommendation
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              Enable two-factor authentication to secure your account and protect your funds
            </CardDescription>
          </CardHeader>
          <CardContent className="relative">
            <div className="flex flex-col sm:flex-row gap-2.5">
              <Link href="/dashboard/profile?tab=security" className="flex-1">
                <Button className="w-full gap-2 rounded-xl" size="sm">
                  <Shield className="h-3.5 w-3.5" />
                  Enable 2FA Now
                </Button>
              </Link>
              <Button variant="outline" size="sm" className="flex-1 rounded-xl">
                Learn More
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
