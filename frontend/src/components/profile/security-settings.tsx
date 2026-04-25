"use client";

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useAuthStore } from '@/store/auth';
import { useToast } from '@/hooks/use-toast';
import { Shield, Lock, Key, AlertCircle, CheckCircle, Copy } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import api from '@/lib/api';

export function SecuritySettings() {
  const { user, updateUser } = useAuthStore();
  const { toast } = useToast();

  const [show2FASetup, setShow2FASetup] = useState(false);
  const [setupStep, setSetupStep] = useState<'qr' | 'verify'>('qr');
  const [qrData, setQrData] = useState<any>(null);
  const [verifyToken, setVerifyToken] = useState('');
  const [disableToken, setDisableToken] = useState('');
  const [showDisable2FA, setShowDisable2FA] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleEnable2FA = async () => {
    setLoading(true);
    try {
      const response = await api.post('/users/enable_2fa/');
      setQrData(response.data);
      setShow2FASetup(true);
      setSetupStep('qr');
    } catch (error: any) {
      toast({ title: 'Failed to enable 2FA', description: error.response?.data?.error || 'An error occurred', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleVerify2FA = async () => {
    if (!verifyToken || verifyToken.length !== 6) {
      toast({ title: 'Invalid code', description: 'Please enter a 6-digit code', variant: 'destructive' });
      return;
    }
    setLoading(true);
    try {
      await api.post('/users/verify_2fa_setup/', { token: verifyToken });
      updateUser({ is_2fa_enabled: true });
      toast({ title: '2FA enabled', description: 'Two-factor authentication has been enabled successfully' });
      setShow2FASetup(false);
      setVerifyToken('');
      setQrData(null);
    } catch (error: any) {
      toast({ title: 'Verification failed', description: error.response?.data?.error || 'Invalid code', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    if (!disableToken || disableToken.length !== 6) {
      toast({ title: 'Invalid code', description: 'Please enter a 6-digit code', variant: 'destructive' });
      return;
    }
    setLoading(true);
    try {
      await api.post('/users/disable_2fa/', { token: disableToken });
      updateUser({ is_2fa_enabled: false });
      toast({ title: '2FA disabled', description: 'Two-factor authentication has been disabled' });
      setShowDisable2FA(false);
      setDisableToken('');
    } catch (error: any) {
      toast({ title: 'Failed to disable 2FA', description: error.response?.data?.error || 'Invalid code', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const copyBackupCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast({ title: 'Copied', description: 'Backup code copied to clipboard' });
  };

  const securityTips = [
    { title: 'Enable 2FA', desc: 'Protect your account with two-factor authentication' },
    { title: 'Keep backup codes safe', desc: 'Store your backup codes in a secure location' },
    { title: 'Verify addresses', desc: 'Always double-check withdrawal addresses' },
    { title: 'Monitor activity', desc: 'Regularly check your audit logs for suspicious activity' },
  ];

  return (
    <div className="space-y-5">
      {/* 2FA Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <div className="p-1.5 bg-primary/10 rounded-lg icon-3d">
              <Shield className="h-4 w-4 text-primary" />
            </div>
            <span>Two-Factor Authentication</span>
          </CardTitle>
          <CardDescription>Add an extra layer of security to your account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className={`flex items-center justify-between p-4 rounded-2xl border transition-colors ${
            user?.is_2fa_enabled
              ? 'bg-green-500/5 border-green-500/20'
              : 'bg-yellow-500/5 border-yellow-500/20'
          }`}>
            <div className="flex items-center space-x-3.5">
              <div className={`p-2.5 rounded-xl icon-3d ${
                user?.is_2fa_enabled ? 'bg-green-500/15' : 'bg-yellow-500/15'
              }`}>
                {user?.is_2fa_enabled ? (
                  <CheckCircle className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                )}
              </div>
              <div>
                <div className="font-semibold">
                  {user?.is_2fa_enabled ? '2FA is enabled' : '2FA is disabled'}
                </div>
                <div className="text-sm text-muted-foreground">
                  {user?.is_2fa_enabled
                    ? 'Your account is protected with 2FA'
                    : 'Enable 2FA to secure your account'}
                </div>
              </div>
            </div>
            {user?.is_2fa_enabled ? (
              <Button variant="destructive" size="sm" onClick={() => setShowDisable2FA(true)}>
                Disable 2FA
              </Button>
            ) : (
              <Button size="sm" onClick={handleEnable2FA} disabled={loading}>
                Enable 2FA
              </Button>
            )}
          </div>

          {user?.is_2fa_enabled && (
            <div className="p-4 rounded-xl bg-green-500/8 border border-green-500/20 shadow-[inset_0_1px_3px_rgba(0,0,0,0.04)]">
              <div className="flex items-start space-x-3">
                <div className="p-1.5 bg-green-500/15 rounded-lg icon-3d mt-0.5">
                  <Lock className="h-4 w-4 text-green-500" />
                </div>
                <div className="text-sm">
                  <div className="font-semibold text-green-600 dark:text-green-400 mb-0.5">Enhanced Security Active</div>
                  <div className="text-muted-foreground">All withdrawals require a 2FA code from your authenticator app</div>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Security Tips */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <div className="p-1.5 bg-primary/10 rounded-lg icon-3d">
              <Key className="h-4 w-4 text-primary" />
            </div>
            <span>Security Tips</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2.5">
          {securityTips.map(({ title, desc }) => (
            <div key={title} className="flex items-start space-x-3 p-3 rounded-xl bg-muted/30 border border-border/40">
              <div className="p-1 bg-primary/10 rounded-md mt-0.5 shrink-0">
                <CheckCircle className="h-3.5 w-3.5 text-primary" />
              </div>
              <div>
                <div className="text-sm font-semibold">{title}</div>
                <div className="text-xs text-muted-foreground mt-0.5">{desc}</div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* 2FA Setup Dialog */}
      <Dialog open={show2FASetup} onOpenChange={setShow2FASetup}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Enable Two-Factor Authentication</DialogTitle>
            <DialogDescription>
              {setupStep === 'qr'
                ? 'Scan the QR code with your authenticator app'
                : 'Enter the 6-digit code from your authenticator app'}
            </DialogDescription>
          </DialogHeader>

          {setupStep === 'qr' && qrData && (
            <div className="space-y-4">
              <div className="flex justify-center p-5 bg-white rounded-2xl shadow-[inset_0_2px_6px_rgba(0,0,0,0.06)]">
                <QRCodeSVG
                  value={`otpauth://totp/CryptoEscrow:${user?.username}?secret=${qrData.secret}&issuer=CryptoEscrow`}
                  size={200}
                />
              </div>

              <div className="space-y-1.5">
                <Label>Secret Key (manual entry)</Label>
                <div className="flex space-x-2">
                  <Input value={qrData.secret} readOnly className="font-mono text-xs" />
                  <Button
                    variant="outline"
                    size="icon"
                    className="shrink-0 rounded-xl"
                    onClick={() => {
                      navigator.clipboard.writeText(qrData.secret);
                      toast({ title: 'Copied', description: 'Secret key copied' });
                    }}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="space-y-1.5">
                <Label>Backup Codes <span className="text-yellow-500 font-normal">(save these!)</span></Label>
                <div className="grid grid-cols-2 gap-2">
                  {qrData.backup_codes?.map((code: string, i: number) => (
                    <div
                      key={i}
                      className="flex items-center justify-between p-2.5 bg-muted/50 rounded-xl border border-border/40 font-mono text-xs"
                    >
                      <span>{code}</span>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0 rounded-lg" onClick={() => copyBackupCode(code)}>
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              <Button className="w-full" onClick={() => setSetupStep('verify')}>
                Continue to Verification
              </Button>
            </div>
          )}

          {setupStep === 'verify' && (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label htmlFor="verify-token">Verification Code</Label>
                <Input
                  id="verify-token"
                  type="text"
                  maxLength={6}
                  placeholder="000000"
                  value={verifyToken}
                  onChange={(e) => setVerifyToken(e.target.value.replace(/\D/g, ''))}
                  className="text-center text-2xl tracking-[0.5em] font-mono"
                />
              </div>
              <div className="flex space-x-2.5">
                <Button variant="outline" className="flex-1" onClick={() => setSetupStep('qr')}>Back</Button>
                <Button className="flex-1" onClick={handleVerify2FA} disabled={loading || verifyToken.length !== 6}>
                  Verify & Enable
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Disable 2FA Dialog */}
      <Dialog open={showDisable2FA} onOpenChange={setShowDisable2FA}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disable Two-Factor Authentication</DialogTitle>
            <DialogDescription>Enter your 2FA code to disable two-factor authentication</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="disable-token">2FA Code</Label>
              <Input
                id="disable-token"
                type="text"
                maxLength={6}
                placeholder="000000"
                value={disableToken}
                onChange={(e) => setDisableToken(e.target.value.replace(/\D/g, ''))}
                className="text-center text-2xl tracking-[0.5em] font-mono"
              />
            </div>
            <div className="flex space-x-2.5">
              <Button variant="outline" className="flex-1" onClick={() => setShowDisable2FA(false)}>Cancel</Button>
              <Button variant="destructive" className="flex-1" onClick={handleDisable2FA} disabled={loading || disableToken.length !== 6}>
                Disable 2FA
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
