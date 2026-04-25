"use client";

/**
 * CredentialManager — list, rename, and revoke WebAuthn credentials.
 *
 * Fetches GET /api/v1/users/credentials/ on mount.
 * Supports inline rename (pencil icon → editable input → PATCH).
 * Supports revocation (DELETE); the button is disabled for the last active credential.
 *
 * Requirements: 11.1, 11.2, 11.4, 11.5
 */

import React, { useCallback, useEffect, useState } from 'react';
import { useAuthStore } from '@/store/auth';
import { useToast } from '@/hooks/use-toast';
import {
  Check,
  KeyRound,
  Loader2,
  Pencil,
  Trash2,
  X,
} from 'lucide-react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface Credential {
  id: string;
  device_name: string | null;
  aaguid: string | null;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

function formatRelativeDate(iso: string | null): string {
  if (!iso) return 'Never';
  const date = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 30) return `${diffDays} days ago`;
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
  return `${Math.floor(diffDays / 365)} years ago`;
}

export function CredentialManager() {
  const { token } = useAuthStore();
  const { toast } = useToast();

  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');
  const [savingId, setSavingId] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const authHeaders = {
    'Content-Type': 'application/json',
    Authorization: `Token ${token}`,
  };

  // ── Fetch credentials ─────────────────────────────────────────────────────
  const fetchCredentials = useCallback(async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const res = await fetch(`${API_URL}/api/v1/users/credentials/`, {
        headers: authHeaders,
      });
      if (!res.ok) throw new Error('Failed to load credentials');
      const data: Credential[] = await res.json();
      setCredentials(data);
    } catch {
      toast({
        title: 'Could not load Passkeys',
        description: 'Please refresh the page.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  // ── Rename ────────────────────────────────────────────────────────────────
  const startEdit = (cred: Credential) => {
    setEditingId(cred.id);
    setEditValue(cred.device_name || '');
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue('');
  };

  const saveEdit = async (id: string) => {
    setSavingId(id);
    try {
      const res = await fetch(`${API_URL}/api/v1/users/credentials/${id}/`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify({ device_name: editValue.trim() || null }),
      });
      if (!res.ok) throw new Error('Rename failed');
      const updated: Credential = await res.json();
      setCredentials((prev) =>
        prev.map((c) => (c.id === id ? updated : c)),
      );
      toast({ title: 'Passkey renamed' });
      setEditingId(null);
    } catch {
      toast({ title: 'Rename failed', description: 'Please try again.', variant: 'destructive' });
    } finally {
      setSavingId(null);
    }
  };

  // ── Revoke ────────────────────────────────────────────────────────────────
  const revokeCredential = async (id: string) => {
    setRevokingId(id);
    try {
      const res = await fetch(`${API_URL}/api/v1/users/credentials/${id}/`, {
        method: 'DELETE',
        headers: authHeaders,
      });
      if (res.status === 400) {
        const err = await res.json().catch(() => ({}));
        toast({
          title: 'Cannot remove Passkey',
          description: err.error || 'This is your last active Passkey.',
          variant: 'destructive',
        });
        return;
      }
      if (!res.ok) throw new Error('Revoke failed');
      setCredentials((prev) =>
        prev.map((c) => (c.id === id ? { ...c, is_active: false } : c)),
      );
      toast({ title: 'Passkey removed' });
    } catch {
      toast({ title: 'Remove failed', description: 'Please try again.', variant: 'destructive' });
    } finally {
      setRevokingId(null);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────────
  const activeCount = credentials.filter((c) => c.is_active).length;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 space-x-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span className="text-sm">Loading Passkeys…</span>
      </div>
    );
  }

  if (credentials.length === 0) {
    return (
      <div className="text-center py-8 space-y-2">
        <KeyRound className="h-10 w-10 text-muted-foreground/40 mx-auto" />
        <p className="text-sm text-muted-foreground">No Passkeys registered yet.</p>
        <p className="text-xs text-muted-foreground">
          Sign in via the Telegram bot or use the login page to set one up.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {credentials.map((cred) => {
        const isEditing = editingId === cred.id;
        const isSaving = savingId === cred.id;
        const isRevoking = revokingId === cred.id;
        const isLastActive = cred.is_active && activeCount === 1;

        return (
          <div
            key={cred.id}
            className={[
              'flex items-center justify-between p-3 rounded-xl border',
              'bg-background/60 shadow-[0_1px_3px_rgba(0,0,0,0.04)]',
              cred.is_active
                ? 'border-border/60'
                : 'border-border/30 opacity-50',
            ].join(' ')}
          >
            {/* Left: icon + name + meta */}
            <div className="flex items-center space-x-3 min-w-0">
              <div className={`p-2 rounded-lg shrink-0 ${cred.is_active ? 'bg-primary/10' : 'bg-muted/40'}`}>
                <KeyRound className={`h-4 w-4 ${cred.is_active ? 'text-primary' : 'text-muted-foreground'}`} />
              </div>
              <div className="min-w-0">
                {isEditing ? (
                  <input
                    autoFocus
                    type="text"
                    value={editValue}
                    onChange={(e) => setEditValue(e.target.value.slice(0, 100))}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveEdit(cred.id);
                      if (e.key === 'Escape') cancelEdit();
                    }}
                    placeholder="Device name"
                    className="text-sm font-medium bg-transparent border-b border-primary outline-none w-full max-w-[180px]"
                  />
                ) : (
                  <p className="text-sm font-medium truncate">
                    {cred.device_name || 'Unnamed device'}
                    {!cred.is_active && (
                      <span className="ml-2 text-xs text-muted-foreground">(revoked)</span>
                    )}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-0.5">
                  Added {formatRelativeDate(cred.created_at)}
                  {cred.last_used_at && ` · Last used ${formatRelativeDate(cred.last_used_at)}`}
                </p>
              </div>
            </div>

            {/* Right: action buttons */}
            {cred.is_active && (
              <div className="flex items-center space-x-1 shrink-0 ml-2">
                {isEditing ? (
                  <>
                    <button
                      onClick={() => saveEdit(cred.id)}
                      disabled={isSaving}
                      aria-label="Save name"
                      className="p-1.5 rounded-lg hover:bg-green-500/10 text-green-500 transition-colors disabled:opacity-50"
                    >
                      {isSaving ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Check className="h-4 w-4" />
                      )}
                    </button>
                    <button
                      onClick={cancelEdit}
                      aria-label="Cancel"
                      className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => startEdit(cred)}
                      aria-label="Rename Passkey"
                      className="p-1.5 rounded-lg hover:bg-muted/60 text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => revokeCredential(cred.id)}
                      disabled={isRevoking || isLastActive}
                      aria-label={
                        isLastActive
                          ? 'Cannot remove last Passkey'
                          : 'Remove Passkey'
                      }
                      title={isLastActive ? 'Cannot remove your last active Passkey' : undefined}
                      className="p-1.5 rounded-lg hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      {isRevoking ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Trash2 className="h-4 w-4" />
                      )}
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default CredentialManager;
