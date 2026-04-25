"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/store/auth';
import { formatDate } from '@/lib/utils';
import { User, Calendar, Shield, CheckCircle, XCircle, Hash } from 'lucide-react';
import { CredentialManager } from '@/components/auth/CredentialManager';

export function ProfileSettings() {
  const { user } = useAuthStore();

  if (!user) return null;

  const infoRows = [
    { icon: Hash, label: 'User ID', value: user.id, mono: true },
    { icon: User, label: 'Telegram ID', value: String(user.telegram_id), mono: true },
    { icon: Calendar, label: 'Member Since', value: formatDate(user.created_at), mono: false },
  ];

  const stats = [
    { label: 'Total Deals', value: '0' },
    { label: 'Completed', value: '0' },
    { label: 'As Buyer', value: '0' },
    { label: 'As Seller', value: '0' },
  ];

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>Your account details from Telegram</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* Avatar row */}
          <div className="flex items-center space-x-4 p-4 rounded-2xl bg-muted/30 border border-border/40 shadow-[inset_0_1px_3px_rgba(0,0,0,0.04)]">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center icon-3d shrink-0">
              <User className="h-8 w-8 text-primary" />
            </div>
            <div>
              <div className="font-bold text-lg">
                {user.first_name} {user.last_name}
              </div>
              <div className="text-sm text-muted-foreground">
                @{user.username || user.telegram_id}
              </div>
              <div className="flex items-center gap-2 mt-1.5">
                <Badge variant={user.is_verified ? 'success' : 'warning'} className="text-xs">
                  {user.is_verified ? '✓ Verified' : 'Not Verified'}
                </Badge>
                <Badge variant={user.is_2fa_enabled ? 'success' : 'secondary'} className="text-xs">
                  {user.is_2fa_enabled ? '🔒 2FA On' : '2FA Off'}
                </Badge>
              </div>
            </div>
          </div>

          {/* Info rows */}
          <div className="space-y-1">
            {infoRows.map(({ icon: Icon, label, value, mono }) => (
              <div key={label} className="flex items-center justify-between py-3 px-1 border-b border-border/40 last:border-0">
                <div className="flex items-center space-x-2.5">
                  <div className="p-1.5 bg-muted/60 rounded-lg">
                    <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <span className="text-sm text-muted-foreground">{label}</span>
                </div>
                <span className={`text-sm font-semibold ${mono ? 'font-mono' : ''}`}>{value}</span>
              </div>
            ))}

            {/* 2FA row */}
            <div className="flex items-center justify-between py-3 px-1 border-b border-border/40">
              <div className="flex items-center space-x-2.5">
                <div className="p-1.5 bg-muted/60 rounded-lg">
                  <Shield className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <span className="text-sm text-muted-foreground">2FA Status</span>
              </div>
              <div className="flex items-center space-x-1.5">
                {user.is_2fa_enabled ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-semibold text-green-500">Enabled</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-red-500" />
                    <span className="text-sm font-semibold text-red-500">Disabled</span>
                  </>
                )}
              </div>
            </div>

            {/* Verification row */}
            <div className="flex items-center justify-between py-3 px-1">
              <div className="flex items-center space-x-2.5">
                <div className="p-1.5 bg-muted/60 rounded-lg">
                  <CheckCircle className="h-3.5 w-3.5 text-muted-foreground" />
                </div>
                <span className="text-sm text-muted-foreground">Verification Status</span>
              </div>
              <div className="flex items-center space-x-1.5">
                {user.is_verified ? (
                  <>
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <span className="text-sm font-semibold text-green-500">Verified</span>
                  </>
                ) : (
                  <>
                    <XCircle className="h-4 w-4 text-yellow-500" />
                    <span className="text-sm font-semibold text-yellow-500">Not Verified</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Account Statistics</CardTitle>
          <CardDescription>Your activity on the platform</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {stats.map(({ label, value }) => (
              <div
                key={label}
                className="text-center p-4 rounded-2xl bg-muted/30 border border-border/40 shadow-[inset_0_1px_3px_rgba(0,0,0,0.04)] hover:bg-muted/50 transition-colors"
              >
                <div className="text-2xl font-bold gradient-text">{value}</div>
                <div className="text-xs text-muted-foreground mt-1 font-medium">{label}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Passkeys */}
      <Card>
        <CardHeader>
          <CardTitle>Passkeys</CardTitle>
          <CardDescription>
            Manage the Passkeys registered to your account. You can rename or remove individual devices.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <CredentialManager />
        </CardContent>
      </Card>
    </div>
  );
}
