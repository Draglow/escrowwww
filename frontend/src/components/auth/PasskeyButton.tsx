"use client";

/**
 * PasskeyButton — reusable Passkey authentication trigger.
 *
 * Runs the full authenticate begin → startPasskeyAuthentication → authenticate
 * complete flow internally. Calls onSuccess with the DRF token on success, or
 * onError with the error on failure.
 *
 * Returns null when the browser does not support WebAuthn so callers don't
 * need to check support themselves.
 *
 * Requirements: 10.2, 10.3
 */

import React, { useState } from 'react';
import { KeyRound, Loader2 } from 'lucide-react';
import { isWebAuthnSupported, startPasskeyAuthentication } from '@/lib/webauthn';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PasskeyButtonProps {
  /** Called with the DRF token string on successful authentication. */
  onSuccess: (token: string) => void;
  /** Called with the error on failure (not called for user-cancelled events). */
  onError?: (err: Error) => void;
  /** Optional label override. Defaults to "Sign in with Passkey". */
  label?: string;
  /** Additional CSS class names. */
  className?: string;
  disabled?: boolean;
}

export function PasskeyButton({
  onSuccess,
  onError,
  label = 'Sign in with Passkey',
  className = '',
  disabled = false,
}: PasskeyButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  // Hide entirely when WebAuthn is not supported (Req 10.2)
  if (!isWebAuthnSupported()) return null;

  const handleClick = async () => {
    if (isLoading || disabled) return;
    setIsLoading(true);

    try {
      // 1. Get challenge
      const beginRes = await fetch(
        `${API_URL}/api/v1/users/auth/webauthn/authenticate/begin/`,
        { method: 'POST', headers: { 'Content-Type': 'application/json' } },
      );
      if (!beginRes.ok) throw new Error('Failed to get authentication challenge');
      const options = await beginRes.json();

      // 2. Prompt authenticator
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
      onSuccess(data.token);
    } catch (err: any) {
      // Don't surface user-cancelled events as errors
      const isCancelled =
        err?.name === 'NotAllowedError' ||
        err?.message?.toLowerCase().includes('cancel') ||
        err?.message?.toLowerCase().includes('abort');

      if (!isCancelled && onError) {
        onError(err instanceof Error ? err : new Error(String(err)));
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isLoading || disabled}
      aria-label={label}
      className={[
        'font-semibold py-3 px-6 rounded-xl',
        'flex items-center justify-center space-x-2.5',
        'bg-primary text-primary-foreground',
        'shadow-[0_4px_0_rgba(0,0,0,0.2),0_6px_16px_rgba(0,0,0,0.15),inset_0_1px_0_rgba(255,255,255,0.2)]',
        'hover:shadow-[0_6px_0_rgba(0,0,0,0.18),0_10px_24px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.25)]',
        'hover:-translate-y-0.5',
        'active:shadow-[0_1px_0_rgba(0,0,0,0.15),inset_0_2px_4px_rgba(0,0,0,0.15)]',
        'active:translate-y-0.5',
        'transition-[box-shadow,transform] duration-200',
        'disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none',
        className,
      ].join(' ')}
    >
      {isLoading ? (
        <>
          <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
          <span>Authenticating…</span>
        </>
      ) : (
        <>
          <KeyRound className="h-5 w-5" aria-hidden="true" />
          <span>{label}</span>
        </>
      )}
    </button>
  );
}

export default PasskeyButton;
