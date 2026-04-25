"use client";

/**
 * Login page — passkey-first flow.
 *
 * Priority order:
 *  1. If a valid session token already exists → redirect to /dashboard (Req 10.1)
 *  2. "Sign in with Passkey" button (primary, hidden when WebAuthn unsupported) (Req 10.2)
 *  3. Telegram Login Widget (secondary / fallback) (Req 10.5)
 *  4. Dev-login button (development only)
 *
 * After Telegram login:
 *  - If response contains passkey_setup_required: true → redirect to /auth/passkey-setup (Req 9.4)
 *  - Otherwise → redirect to /dashboard
 *
 * After Passkey authentication failure → show error toast and reveal Telegram widget (Req 10.4)
 */

import React, { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { useAuthStore } from '@/store/auth';
import {
  CheckCircle2,
  Globe,
  KeyRound,
  Loader2,
  Lock,
  Shield,
  Zap,
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import {
  isWebAuthnSupported,
  startPasskeyAuthentication,
} from '@/lib/webauthn';

declare global {
  interface Window {
    onTelegramAuth?: (user: any) => void;
  }
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, setAuth, setPasskeySetupRequired } = useAuthStore();
  const { toast } = useToast();
  const scriptLoaded = useRef(false);

  const [isLoading, setIsLoading] = useState(false);
  const [passkeyLoading, setPasskeyLoading] = useState(false);
  const [showTelegramFallback, setShowTelegramFallback] = useState(false);
  const [webAuthnAvailable, setWebAuthnAvailable] = useState(false);

  // Detect WebAuthn support on mount (client-side only)
  useEffect(() => {
    setWebAuthnAvailable(isWebAuthnSupported());
  }, []);

  // Redirect if already authenticated (Req 10.1)
  useEffect(() => {
    if (isAuthenticated) {
      const token = localStorage.getItem('auth_token');
      if (token) router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  // ── Passkey authentication flow ──────────────────────────────────────────

  const handlePasskeyLogin = async () => {
    setPasskeyLoading(true);
    try {
      // 1. Get challenge from server
      const beginRes = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/authenticate/begin/`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' } },
      );
      if (!beginRes.ok) throw new Error('Failed to get authentication challenge');
      const options = await beginRes.json();

      // 2. Prompt the authenticator
      const credential = await startPasskeyAuthentication(options);

      // 3. Verify with server
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
        throw new Error(err.error || 'Passkey authentication failed');
      }

      const data = await completeRes.json();
      setAuth(data.user, data.token);
      toast({ title: 'Welcome back!', description: `Signed in as ${data.user.first_name || data.user.username}` });
      router.push('/dashboard');
    } catch (err: any) {
      // User cancelled → don't show error toast, just reveal Telegram fallback
      const isCancelled =
        err?.name === 'NotAllowedError' ||
        err?.message?.toLowerCase().includes('cancel') ||
        err?.message?.toLowerCase().includes('abort');

      if (!isCancelled) {
        toast({
          title: 'Passkey sign-in failed',
          description: err?.message || 'Please try again or use Telegram to sign in.',
          variant: 'destructive',
        });
      }
      // Reveal Telegram widget as fallback (Req 10.4)
      setShowTelegramFallback(true);
    } finally {
      setPasskeyLoading(false);
    }
  };

  // ── Telegram authentication flow ─────────────────────────────────────────

  useEffect(() => {
    window.onTelegramAuth = async (user: any) => {
      setIsLoading(true);
      try {
        const authString = Object.entries(user)
          .map(([key, value]) => `${key}=${value}`)
          .join('&');

        const response = await fetch(
          `${API_URL}/api/v1/users/auth/login/`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Telegram ${authString}`,
            },
          },
        );

        if (response.ok) {
          const data = await response.json();
          console.log('[Login] Telegram auth response:', { passkey_setup_required: data.passkey_setup_required, hasToken: !!data.token, hasUser: !!data.user });

          if (data.passkey_setup_required) {
            // Store temporary token in sessionStorage (not localStorage) (Req 9.4)
            console.log('[Login] Storing passkey setup token in sessionStorage');
            sessionStorage.setItem('passkey_setup_token', data.token);
            sessionStorage.setItem('passkey_setup_user', JSON.stringify(data.user));
            setPasskeySetupRequired(true);
            console.log('[Login] Redirecting to /auth/passkey-setup');
            router.push('/auth/passkey-setup');
          } else {
            setAuth(data.user, data.token);
            toast({
              title: 'Login Successful!',
              description: `Welcome back, ${data.user.first_name || data.user.username}!`,
            });
            router.push('/dashboard');
          }
        } else {
          toast({
            title: 'Login Failed',
            description: 'Please try again or contact support.',
            variant: 'destructive',
          });
        }
      } catch {
        toast({
          title: 'Connection Error',
          description: `Could not reach the server. Make sure the backend is running.`,
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (!scriptLoaded.current) {
      const script = document.createElement('script');
      script.src = 'https://telegram.org/js/telegram-widget.js?22';
      script.async = true;
      script.setAttribute(
        'data-telegram-login',
        process.env.NEXT_PUBLIC_TELEGRAM_BOT_USERNAME || 'your_bot',
      );
      script.setAttribute('data-size', 'large');
      script.setAttribute('data-onauth', 'onTelegramAuth(user)');
      script.setAttribute('data-request-access', 'write');
      const container = document.getElementById('telegram-login-container');
      if (container) {
        container.appendChild(script);
        scriptLoaded.current = true;
      }
    }

    return () => {
      delete window.onTelegramAuth;
    };
  }, [setAuth, setPasskeySetupRequired, router, toast]);

  const handleDevLogin = async () => {
    setIsLoading(true);
    const mockUser = {
      id: 123456789,
      first_name: 'Test',
      username: 'testuser',
      auth_date: Math.floor(Date.now() / 1000),
      hash: 'mock_hash',
    };
    if (window.onTelegramAuth) await window.onTelegramAuth(mockUser);
  };

  // ── UI ────────────────────────────────────────────────────────────────────

  const features = [
    { icon: Lock, label: 'Secure authentication', color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { icon: Zap, label: 'No password required', color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    { icon: CheckCircle2, label: 'Instant verification', color: 'text-green-500', bg: 'bg-green-500/10' },
    { icon: Globe, label: 'Privacy protected', color: 'text-purple-500', bg: 'bg-purple-500/10' },
  ];

  // Show Telegram widget when: no WebAuthn, user clicked fallback, or explicitly shown
  const showTelegram = !webAuthnAvailable || showTelegramFallback;

  return (
    <div className="min-h-screen flex items-center justify-center bg-layered p-4">
      {/* Background orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 rounded-full bg-primary/6 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-96 h-96 rounded-full bg-blue-500/5 blur-3xl" />
      </div>

      <div className="w-full max-w-md relative z-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
        <Card className="border-border/60 shadow-[0_24px_64px_rgba(0,0,0,0.12),0_8px_24px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.7)] dark:shadow-[0_24px_64px_rgba(0,0,0,0.5),0_8px_24px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.07)]">
          <CardHeader className="text-center pb-4">
            <div className="flex justify-center mb-5">
              <div className="relative p-4 rounded-2xl bg-primary/10 icon-3d">
                <Shield className="h-12 w-12 text-primary" />
                <div className="absolute inset-0 rounded-2xl bg-primary/5 animate-ping" />
              </div>
            </div>
            <CardTitle className="text-3xl font-bold gradient-text tracking-tight">
              Welcome Back
            </CardTitle>
            <CardDescription className="text-base mt-1">
              Sign in securely with your Passkey or Telegram account
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-5">
            {/* Why secure */}
            <div className="rounded-xl border border-border/60 bg-muted/30 p-4 shadow-[inset_0_1px_3px_rgba(0,0,0,0.04)]">
              <h3 className="font-semibold mb-3 flex items-center text-sm">
                <div className="p-1 bg-primary/10 rounded-md mr-2 icon-3d">
                  <Shield className="h-3.5 w-3.5 text-primary" />
                </div>
                Why Passkeys?
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {features.map(({ icon: Icon, label, color, bg }) => (
                  <div
                    key={label}
                    className="flex items-center space-x-2 p-2 rounded-lg bg-background/60 border border-border/40 shadow-[0_1px_3px_rgba(0,0,0,0.04)]"
                  >
                    <div className={`p-1 ${bg} rounded-md`}>
                      <Icon className={`h-3 w-3 ${color}`} />
                    </div>
                    <span className="text-xs font-medium text-foreground/80">{label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Primary: Sign in with Passkey (hidden when unsupported) ── */}
            {webAuthnAvailable && (
              <button
                onClick={handlePasskeyLogin}
                disabled={passkeyLoading || isLoading}
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
                {passkeyLoading ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Authenticating…</span>
                  </>
                ) : (
                  <>
                    <KeyRound className="h-5 w-5" />
                    <span>Sign in with Passkey</span>
                  </>
                )}
              </button>
            )}

            {/* ── Show Telegram option link when WebAuthn is available ── */}
            {webAuthnAvailable && !showTelegramFallback && (
              <button
                onClick={() => setShowTelegramFallback(true)}
                className="w-full text-sm text-muted-foreground hover:text-foreground transition-colors text-center"
              >
                Use Telegram instead →
              </button>
            )}

            {/* ── Secondary: Telegram Login Widget ── */}
            {showTelegram && (
              <div className="space-y-3">
                {showTelegramFallback && webAuthnAvailable && (
                  <p className="text-sm text-muted-foreground text-center">
                    Sign in with Telegram to continue
                  </p>
                )}
                {!webAuthnAvailable && (
                  <p className="text-sm text-muted-foreground text-center">
                    Click the button below to login with Telegram
                  </p>
                )}
                <div id="telegram-login-container" className="flex justify-center min-h-[46px]">
                  {isLoading && (
                    <div className="flex items-center space-x-2 text-muted-foreground">
                      <Loader2 className="h-5 w-5 animate-spin" />
                      <span className="text-sm">Logging in…</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* ── Divider ── */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-border/60" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-3 text-muted-foreground font-medium tracking-wider">
                  Or for development
                </span>
              </div>
            </div>

            {/* ── Dev Login ── */}
            <button
              onClick={handleDevLogin}
              disabled={isLoading || passkeyLoading}
              className={[
                'w-full text-white font-semibold py-3 px-6 rounded-xl',
                'flex items-center justify-center space-x-2.5',
                'bg-[#0088cc] hover:bg-[#0077b3]',
                'shadow-[0_4px_0_rgba(0,100,180,0.5),0_6px_16px_rgba(0,136,204,0.3),inset_0_1px_0_rgba(255,255,255,0.2)]',
                'hover:shadow-[0_6px_0_rgba(0,100,180,0.45),0_10px_24px_rgba(0,136,204,0.35),inset_0_1px_0_rgba(255,255,255,0.25)]',
                'hover:-translate-y-0.5',
                'active:shadow-[0_1px_0_rgba(0,100,180,0.4),inset_0_2px_4px_rgba(0,0,0,0.15)]',
                'active:translate-y-0.5',
                'transition-[box-shadow,transform] duration-200',
                'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
              ].join(' ')}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Logging in…</span>
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.832.941z" />
                  </svg>
                  <span>Login with Telegram (Dev)</span>
                </>
              )}
            </button>

            {/* Note */}
            <div className="rounded-xl bg-yellow-500/8 border border-yellow-500/20 p-3.5 shadow-[inset_0_1px_3px_rgba(0,0,0,0.04)]">
              <p className="text-xs text-center text-yellow-700 dark:text-yellow-400">
                <strong>Note:</strong> Set your bot username in{' '}
                <code className="bg-yellow-500/20 px-1.5 py-0.5 rounded-md font-mono">.env.local</code>
              </p>
            </div>

            <p className="text-xs text-center text-muted-foreground">
              By signing in, you agree to our Terms of Service and Privacy Policy
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
