"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDate } from '@/lib/utils';
import { Shield, Loader2, AlertCircle, Info } from 'lucide-react';
import api from '@/lib/api';

interface AuditLog {
  id: string;
  action: string;
  ip_address: string;
  success: boolean;
  created_at: string;
  details: Record<string, any>;
}

const ACTION_LABELS: Record<string, string> = {
  LOGIN: 'Login',
  LOGOUT: 'Logout',
  WITHDRAWAL: 'Withdrawal',
  WITHDRAWAL_APPROVED: 'Withdrawal Approved',
  WITHDRAWAL_REJECTED: 'Withdrawal Rejected',
  DEAL_CREATED: 'Deal Created',
  DEAL_FUNDED: 'Deal Funded',
  DEAL_COMPLETED: 'Deal Completed',
  DEAL_DISPUTED: 'Deal Disputed',
  DEAL_CANCELLED: 'Deal Cancelled',
  PROFILE_UPDATED: 'Profile Updated',
  '2FA_ENABLED': '2FA Enabled',
  '2FA_DISABLED': '2FA Disabled',
};

const ACTION_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'success' | 'warning'> = {
  LOGIN: 'default',
  LOGOUT: 'secondary',
  WITHDRAWAL: 'warning',
  DEAL_CREATED: 'success',
  DEAL_COMPLETED: 'success',
  DEAL_DISPUTED: 'destructive',
  '2FA_ENABLED': 'success',
  '2FA_DISABLED': 'destructive',
};

export function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { fetchLogs(); }, []);

  const fetchLogs = async () => {
    try {
      const response = await api.get('/users/audit_logs/');
      setLogs(response.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-red-500/10 mb-4">
              <AlertCircle className="h-7 w-7 text-red-500" />
            </div>
            <p className="text-muted-foreground">{error}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <div className="p-1.5 bg-primary/10 rounded-lg icon-3d">
              <Shield className="h-4 w-4 text-primary" />
            </div>
            <span>Audit Logs</span>
          </CardTitle>
          <CardDescription>View your account activity and security events</CardDescription>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-muted/50 mb-3 shadow-[inset_0_2px_6px_rgba(0,0,0,0.06)]">
                <Shield className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground font-medium">No audit logs yet</p>
            </div>
          ) : (
            <div className="space-y-2.5">
              {logs.map((log, i) => (
                <div
                  key={log.id}
                  className="flex items-start justify-between p-4 rounded-xl border border-border/60 bg-muted/20 hover:bg-muted/40 transition-colors shadow-[0_1px_3px_rgba(0,0,0,0.04)] stagger-item"
                  style={{ animationDelay: `${i * 40}ms` }}
                >
                  <div className="flex items-start space-x-3.5 flex-1 min-w-0">
                    {/* Status dot */}
                    <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${log.success ? 'bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.5)]' : 'bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.5)]'}`} />

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <Badge variant={ACTION_VARIANT[log.action] || 'secondary'} className="text-xs">
                          {ACTION_LABELS[log.action] || log.action}
                        </Badge>
                        {!log.success && (
                          <Badge variant="destructive" className="text-xs">Failed</Badge>
                        )}
                      </div>
                      <div className="text-xs text-muted-foreground space-y-0.5">
                        <div>IP: <span className="font-mono">{log.ip_address || 'Unknown'}</span></div>
                        <div>{formatDate(log.created_at)}</div>
                        {log.details && Object.keys(log.details).length > 0 && (
                          <div className="mt-2 p-2.5 bg-muted/60 rounded-lg text-xs font-mono border border-border/40 overflow-x-auto">
                            {JSON.stringify(log.details, null, 2)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-base">
            <div className="p-1.5 bg-blue-500/10 rounded-lg">
              <Info className="h-4 w-4 text-blue-500" />
            </div>
            <span>About Audit Logs</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {[
            'Audit logs track all security-sensitive operations on your account',
            'Logs are immutable and cannot be deleted or modified',
            'Review your logs regularly to detect suspicious activity',
            'Contact support immediately if you notice unauthorized access',
          ].map((tip) => (
            <div key={tip} className="flex items-start space-x-2.5 p-2.5 rounded-lg bg-muted/30 border border-border/40">
              <div className="w-1.5 h-1.5 rounded-full bg-primary mt-1.5 shrink-0" />
              <p className="text-sm text-muted-foreground">{tip}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
