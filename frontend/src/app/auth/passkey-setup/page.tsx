"use client";

/**
 * Passkey setup page.
 *
 * Handles two entry points:
 *
 * 1. Bridge Token deep link (from Telegram bot):
 *    URL: /auth/passkey-setup?bridge_token=<token>
 *    - Redeems the bridge token → receives a temporary session token
 *    - Proceeds with registration using that token
 *
 * 2. Post-Telegram-login redirect (from web login page):
 *    - Reads temporary token from sessionStorage
 *    - Proceeds with registration using that token
 *
 * On success: calls setAuth(), clears sessionStorage, redirects to /dashboard.
 * On WebAuthn error (user cancel / no authenticator): shows toast + "Skip for now" link.
 * On bridge token error: redirects to /login?error=bridge_token_invalid.
 *
 * Requirements: 7.3, 7.4, 7.5, 7.6, 9.4, 9.5
 */

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useAuthStore } from '@/store/auth';
import { KeyRound, Loader2, ShieldCheck, Smartphone } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { startPasskeyRegistration } from '@/lib/webauthn';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function PasskeySetupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { setAuth } = useAuthStore();
  const { toast } = useToast();

  const [isLoading, setIsLoading] = useState(false);
  const [deviceName, setDeviceName] = useState('');
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [setupUser, setSetupUser] = useState<any>(null);
  const [bridgeError, setBridgeError] = useState(false);
  const [registrationError, setRegistrationError] = useState<string | null>(null);

  // ── On mount: resolve the session token ──────────────────────────────────
  useEffect(() => {
    const bridgeToken = searchParams.get('bridge_token');

    console.log('[PasskeySetup] Mount - bridgeToken:', bridgeToken);

    if (bridgeToken) {
      // Entry point 1: Bridge Token from Telegram bot deep link
      console.log('[PasskeySetup] Redeeming bridge token...');
      redeemBridgeToken(bridgeToken);
    } else {
      // Entry point 2: Post-Telegram-login redirect
      const token = sessionStorage.getItem('passkey_setup_token');
      const userJson = sessionStorage.getItem('passkey_setup_user');
      console.log('[PasskeySetup] SessionStorage - token:', !!token, 'user:', !!userJson);
      
      if (token && userJson) {
        try {
          console.log('[PasskeySetup] Setting session token from sessionStorage');
          setSessionToken(token);
          setSetupUser(JSON.parse(userJson));
        } catch (err) {
          console.error('[PasskeySetup] Error parsing sessionStorage:', err);
          router.push('/login?error=bridge_token_invalid');
        }
      } else {
        // No token available — redirect to login
        console.log('[PasskeySetup] No token found, redirecting to login');
        router.push('/login');
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const redeemBridgeToken = async (bridgeToken: string) => {
    setIsLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/bridge/redeem/`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bridge_token: bridgeToken }),
        },
      );

      if (!res.ok) {
        setBridgeError(true);
        router.push('/login?error=bridge_token_invalid');
        return;
      }

      const data = await res.json();
      if (data.flow !== 'register') {
        // Wrong flow — this page only handles registration
        router.push('/login?error=bridge_token_invalid');
        return;
      }

      setSessionToken(data.token);
      setSetupUser(data.user);
    } catch {
      setBridgeError(true);
      router.push('/login?error=bridge_token_invalid');
    } finally {
      setIsLoading(false);
    }
  };

  // ── Registration ceremony ─────────────────────────────────────────────────
  const handleRegister = async () => {
    if (!sessionToken) return;
    setIsLoading(true);
    setRegistrationError(null);

    try {
      // 1. Get registration options from server
      const beginRes = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/register/begin/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Token ${sessionToken}`,
          },
        },
      );

      if (!beginRes.ok) {
        throw new Error('Failed to start Passkey registration');
      }
      const options = await beginRes.json();

      // 2. Prompt the authenticator
      const credential = await startPasskeyRegistration(options);

      // 3. Complete registration
      const completeRes = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/register/complete/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Token ${sessionToken}`,
          },
          body: JSON.stringify({
            credential,
            device_name: deviceName.trim() || undefined,
          }),
        },
      );

      if (!completeRes.ok) {
        const err = await completeRes.json().catch(() => ({}));
        throw new Error(err.error || 'Passkey registration failed');
      }

      const data = await completeRes.json();

      // 4. Persist auth state and clean up
      setAuth(data.user, data.token);
      sessionStorage.removeItem('passkey_setup_token');
      sessionStorage.removeItem('passkey_setup_user');

      toast({
        title: 'Passkey created!',
        description: 'You can now sign in with your Passkey on this device.',
      });
      router.push('/dashboard');
    } catch (err: any) {
      const isCancelled =
        err?.name === 'NotAllowedError' ||
        err?.message?.toLowerCase().includes('cancel') ||
        err?.message?.toLowerCase().includes('abort');

      if (isCancelled) {
        setRegistrationError(
          'Passkey setup was cancelled. You can try again or skip for now.',
        );
      } else {
        setRegistrationError(err?.message || 'Passkey setup failed. Please try again.');
        toast({
          title: 'Passkey setup failed',
          description: err?.message || 'Please try again.',
          variant: 'destructive',
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    // If we have a session token from Telegram login, use it to log in without a passkey
    if (sessionToken && setupUser) {
      setAuth(setupUser, sessionToken);
      sessionStorage.removeItem('passkey_setup_token');
      sessionStorage.removeItem('passkey_setup_user');
    }
    router.push('/dashboard');
  };

  // ── Render ────────────────────────────────────────────────────────────────

  if (bridgeError) return null; // redirecting

  return (
    <div className="min-h-screen flex items-center justify-center bg-layered p-4">
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/6 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-blue-500/5 blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
        <Card className="border-border/60 shadow-[0_24px_64px_rgba(0,0,0,0.12),0_8px_24px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.7)] dark:shadow-[0_24px_64px_rgba(0,0,0,0.5),0_8px_24px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.07)]">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-5">
              <div className="relative p-4 rounded-2xl bg-primary/10 icon-3d">
                <ShieldCheck className="h-12 w-12 text-primary" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold gradient-text tracking-tight">
              Set Up Your Passkey
            </CardTitle>
            <CardDescription className="text-base mt-1">
              Create a Passkey so you can sign in instantly next time — no Telegram needed.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            {/* Loading state while resolving bridge token */}
            {isLoading && !sessionToken && (
              <div className="flex items-center justify-center py-8 space-x-3 text-muted-foreground">
                <Loader2 className="h-6 w-6 animate-spin" />
                <span>Preparing setup…</span>
              </div>
            )}

            {/* Main content once token is resolved */}
            {sessionToken && (
              <>
                {/* What is a Passkey */}
                <div className="rounded-xl border border-border/60 bg-muted/30 p-4 space-y-3">
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-primary/10 rounded-lg mt-0.5">
                      <Smartphone className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">Stored on this device</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Your Passkey is saved securely in your device's biometric system (Face ID, Touch ID, Windows Hello, etc.)
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="p-2 bg-green-500/10 rounded-lg mt-0.5">
                      <KeyRound className="h-4 w-4 text-green-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium">One-tap sign-in</p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        Next time you visit, just tap "Sign in with Passkey" — no Telegram prompt needed.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Optional device name */}
                <div className="space-y-1.5">
                  <label htmlFor="device-name" className="text-sm font-medium">
                    Device name{' '}
                    <span className="text-muted-foreground font-normal">(optional)</span>
                  </label>
                  <input
                    id="device-name"
                    type="text"
                    value={deviceName}
                    onChange={(e) => setDeviceName(e.target.value.slice(0, 100))}
                    placeholder="e.g. MacBook Pro, iPhone 15"
                    className="w-full rounded-lg border border-border/60 bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>

                {/* Error message */}
                {registrationError && (
                  <p className="text-sm text-destructive text-center">{registrationError}</p>
                )}

                {/* Create Passkey button */}
                <button
                  onClick={handleRegister}
                  disabled={isLoading}
                  className={[
                    'w-full font-semibold py-3 px-6 rounded-xl',
                    'flex items-center justify-center space-x-2.5',
                    'bg-primary text-primary-foreground',
                    'shadow-[0_4px_0_rgba(0,0,0,0.2),0_6px_16px_rgba(0,0,0,0.15),inset_0_1px_0_rgba(255,255,255,0.2)]',
                    'hover:shadow-[0_6px_0_rgba(0,0,0,0.18),0_10px_24px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.25)]',
                    'hover:-translate-y-0.5',
                    'active:shadow-[0_1px_0_rgba(0,0,0,0.15),inset_0_2px_4px_rgba(0,0,0,0.15)]',
                    'active:translate-y-0.5',
                    'transition-[box-shadow,transform] duration-200',
                    'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
                  ].join(' ')}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span>Setting up…</span>
                    </>
                  ) : (
                    <>
                      <KeyRound className="h-5 w-5" />
                      <span>Create Passkey</span>
                    </>
                  )}
                </button>

                {/* Skip link */}
                <button
                  onClick={handleSkip}
                  disabled={isLoading}
                  className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors text-center disabled:opacity-50"
                >
                  Skip for now →
                </button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
