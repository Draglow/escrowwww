"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Copy, AlertCircle, ArrowDownRight } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { QRCodeSVG } from 'qrcode.react';

interface DepositInstructionsProps {
  address?: string;
}

export function DepositInstructions({ address }: DepositInstructionsProps) {
  const { toast } = useToast();

  const handleCopy = () => {
    if (address) {
      navigator.clipboard.writeText(address);
      toast({ title: 'Address copied', description: 'Deposit address copied to clipboard' });
    }
  };

  if (!address) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <div className="h-10 w-10 rounded-full bg-muted/60 animate-pulse mx-auto mb-3" />
              <p className="text-muted-foreground text-sm">Loading deposit address...</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const steps = [
    { n: 1, title: 'Copy the address', desc: 'Click the copy button or scan the QR code' },
    { n: 2, title: 'Send USDT (TRC20)', desc: 'Open your wallet and send USDT on the TRC20 network' },
    { n: 3, title: 'Wait for confirmation', desc: 'Your balance will update automatically after 19 confirmations' },
  ];

  const networkInfo = [
    { label: 'Network', value: 'TRC20 (Tron)' },
    { label: 'Currency', value: 'USDT' },
    { label: 'Min Deposit', value: '$1.00' },
    { label: 'Confirmations', value: '19 blocks' },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <div className="p-1.5 bg-green-500/10 rounded-lg icon-3d">
              <ArrowDownRight className="h-4 w-4 text-green-500" />
            </div>
            <span>Deposit USDT (TRC20)</span>
          </CardTitle>
          <CardDescription>Send USDT to this address to add funds to your wallet</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          {/* QR Code */}
          <div className="flex justify-center">
            <div className="p-5 bg-white rounded-2xl shadow-[0_4px_16px_rgba(0,0,0,0.1),inset_0_1px_0_rgba(255,255,255,0.8)]">
              <QRCodeSVG value={address} size={180} />
            </div>
          </div>

          {/* Address */}
          <div className="space-y-1.5">
            <label className="text-sm font-semibold text-foreground/80">Your Deposit Address</label>
            <div className="flex space-x-2">
              <div className="flex-1 p-3.5 bg-muted/40 rounded-xl border border-border/60 font-mono text-xs break-all shadow-[inset_0_1px_3px_rgba(0,0,0,0.06)]">
                {address}
              </div>
              <Button variant="outline" size="icon" onClick={handleCopy} className="rounded-xl shrink-0">
                <Copy className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Network Info */}
          <div className="grid grid-cols-2 gap-2.5">
            {networkInfo.map(({ label, value }) => (
              <div key={label} className="p-3 rounded-xl bg-muted/30 border border-border/40 shadow-[inset_0_1px_2px_rgba(0,0,0,0.04)]">
                <div className="text-xs text-muted-foreground mb-0.5">{label}</div>
                <div className="text-sm font-semibold">{value}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Important Notes */}
      <Card className="border-yellow-500/30 bg-yellow-500/5">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center space-x-2 text-base">
            <div className="p-1.5 bg-yellow-500/15 rounded-lg icon-3d">
              <AlertCircle className="h-4 w-4 text-yellow-500" />
            </div>
            <span className="text-yellow-600 dark:text-yellow-400">Important Notes</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-1.5">
          {[
            'Only send USDT (TRC20) to this address',
            'Sending other tokens may result in permanent loss',
            'Minimum deposit amount is $1.00',
            'Deposits are credited after 19 network confirmations',
            'This usually takes 1-3 minutes',
            'Your balance will update automatically',
          ].map((note) => (
            <div key={note} className="flex items-start space-x-2">
              <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 mt-1.5 shrink-0" />
              <p className="text-sm text-muted-foreground">{note}</p>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* How to Deposit */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">How to Deposit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {steps.map(({ n, title, desc }) => (
            <div key={n} className="flex space-x-4 items-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm shadow-[0_2px_6px_hsl(var(--primary)/0.35),inset_0_1px_0_rgba(255,255,255,0.2)]">
                {n}
              </div>
              <div className="pt-0.5">
                <div className="font-semibold text-sm mb-0.5">{title}</div>
                <div className="text-xs text-muted-foreground">{desc}</div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
