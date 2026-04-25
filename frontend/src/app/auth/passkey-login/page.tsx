"use client";

/**
 * Passkey login page — handles Bridge Token deep links for returning users.
 *
 * URL: /auth/passkey-login?bridge_token=<token>
 *
 * Flow:
 *  1. Redeem the bridge token → receive authentication options (flow = "authenticate")
 *  2. Pass options to startPasskeyAuthentication()
 *  3. POST assertion to authenticate/complete → receive DRF token
 *  4. setAuth() → redirect to /dashboard
 *
 * On any error: redirect to /login?error=bridge_token_invalid
 *
 * Requirements: 8.3
 */

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { Loader2, ShieldCheck } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { startPasskeyAuthentication } from '@/lib/webauthn';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PasskeyLoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();
  const { toast } = useToast();

  const [statusMessage, setStatusMessage] = useState('Verifying your link…');

  useEffect(() => {
    const bridgeToken = searchParams.get('bridge_token');
    if (!bridgeToken) {
      router.push('/login?error=bridge_token_invalid');
      return;
    }
    runAuthFlow(bridgeToken);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runAuthFlow = async (bridgeToken: string) => {
    try {
      // 1. Redeem bridge token → get authentication options
      setStatusMessage('Verifying your link…');
      const redeemRes = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/bridge/redeem/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bridge_token: bridgeToken }),
        },
      );

      if (!redeemRes.ok) {
        router.push('/login?error=bridge_token_invalid');
        return;
      }

      const redeemData = await redeemRes.json();

      if (redeemData.flow !== 'authenticate') {
        // Wrong flow — redirect to setup page instead
        router.push('/login?error=bridge_token_invalid');
        return;
      }

      const options = redeemData.options;

      // 2. Prompt the authenticator
      setStatusMessage('Waiting for your Passkey…');
      const credential = await startPasskeyAuthentication(options);

      // 3. Complete authentication
      setStatusMessage('Signing you in…');
      const completeRes = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/authenticate/complete/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ credential }),
        },
      );

      if (!completeRes.ok) {
        const err = await completeRes.json().catch(() => ({}));
        throw new Error(err.error || 'Authentication failed');
      }

      const data = await completeRes.json();
      setAuth(data.user, data.token);
      toast({
        title: 'Welcome back!',
        description: `Signed in as ${data.user.first_name || data.user.username}`,
      });
      router.push('/dashboard');
    } catch (err: any) {
      // User cancelled or authenticator error
      const isCancelled =
        err?.name === 'NotAllowedError' ||
        err?.message?.toLowerCase().includes('cancel') ||
        err?.message?.toLowerCase().includes('abort');

      if (!isCancelled) {
        toast({
          title: 'Sign-in failed',
          description: err?.message || 'Please try again from the Telegram bot.',
          variant: 'destructive',
        });
      }
      router.push('/login?error=bridge_token_invalid');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-layered p-4">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/6 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-blue-500/5 blur-3xl" />
      </div>

      <div className="flex flex-col items-center space-y-6 relative z-10 animate-in fade-in duration-500">
        <div className="p-5 rounded-2xl bg-primary/10 icon-3d">
          <ShieldCheck className="h-14 w-14 text-primary" />
        </div>
        <div className="flex items-center space-x-3 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span className="text-sm font-medium">{statusMessage}</span>
        </div>
      </div>
    </div>
  );
}
