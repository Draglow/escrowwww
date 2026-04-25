"use client";

import { formatDate } from '@/lib/utils';
import { Check, X, Clock } from 'lucide-react';

interface Deal {
  status: string;
  created_at: string;
  funded_at?: string;
  started_at?: string;
  completed_at?: string;
  disputed_at?: string;
  cancelled_at?: string;
}

interface DealTimelineProps {
  deal: Deal;
}

export function DealTimeline({ deal }: DealTimelineProps) {
  const steps = [
    { label: 'Created', date: deal.created_at, completed: true },
    { label: 'Funded', date: deal.funded_at, completed: !!deal.funded_at },
    { label: 'Started', date: deal.started_at, completed: !!deal.started_at },
    {
      label: deal.disputed_at ? 'Disputed' : deal.cancelled_at ? 'Cancelled' : 'Completed',
      date: deal.completed_at || deal.disputed_at || deal.cancelled_at,
      completed: !!(deal.completed_at || deal.disputed_at || deal.cancelled_at),
      isDisputed: !!deal.disputed_at,
      isCancelled: !!deal.cancelled_at,
    },
  ];

  return (
    <div className="space-y-0">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        const isNegative = step.isDisputed || step.isCancelled;

        return (
          <div key={index} className="flex items-start space-x-4">
            {/* Icon + connector */}
            <div className="flex flex-col items-center">
              <div className={[
                "flex items-center justify-center w-9 h-9 rounded-xl border-2 transition-all",
                step.completed
                  ? isNegative
                    ? "bg-red-500 border-red-500 shadow-[0_2px_8px_rgba(239,68,68,0.4),inset_0_1px_0_rgba(255,255,255,0.2)]"
                    : "bg-primary border-primary shadow-[0_2px_8px_hsl(var(--primary)/0.4),inset_0_1px_0_rgba(255,255,255,0.2)]"
                  : "bg-background border-border shadow-[inset_0_1px_3px_rgba(0,0,0,0.06)]",
              ].join(" ")}>
                {step.completed ? (
                  isNegative ? (
                    <X className="h-4 w-4 text-white" />
                  ) : (
                    <Check className="h-4 w-4 text-white" />
                  )
                ) : (
                  <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </div>
              {!isLast && (
                <div className={`w-0.5 h-10 mt-1 rounded-full ${
                  step.completed ? 'timeline-line' : 'bg-border'
                }`} />
              )}
            </div>

            {/* Content */}
            <div className={`flex-1 ${isLast ? 'pb-0' : 'pb-2'} pt-1.5`}>
              <div className={`font-semibold text-sm ${
                step.completed
                  ? isNegative ? 'text-red-500' : 'text-foreground'
                  : 'text-muted-foreground'
              }`}>
                {step.label}
              </div>
              {step.date ? (
                <div className="text-xs text-muted-foreground mt-0.5">{formatDate(step.date)}</div>
              ) : (
                <div className="text-xs text-muted-foreground/50 mt-0.5">Pending</div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
