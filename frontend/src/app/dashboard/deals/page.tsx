"use client";

import { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useDeals } from '@/hooks/useDeals';
import { useAuthStore } from '@/store/auth';
import { formatCurrency, formatDate } from '@/lib/utils';
import { FileText, Plus, Search, Filter, ArrowUpRight } from 'lucide-react';

const STATUS_BADGE: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning'; label: string }> = {
  DRAFT:       { variant: 'secondary', label: 'Draft' },
  FUNDED:      { variant: 'default',   label: 'Funded' },
  IN_PROGRESS: { variant: 'warning',   label: 'In Progress' },
  COMPLETED:   { variant: 'success',   label: 'Completed' },
  DISPUTED:    { variant: 'destructive', label: 'Disputed' },
  CANCELLED:   { variant: 'secondary', label: 'Cancelled' },
};

export default function DealsPage() {
  const { user } = useAuthStore();
  const { data: deals, isLoading } = useDeals();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  // API may return a paginated object { results: [...] } or a plain array
  const dealsArray: any[] = Array.isArray(deals)
    ? deals
    : Array.isArray((deals as any)?.results)
    ? (deals as any).results
    : [];

  const filterDeals = (list: any[]) => {
    let filtered = list;
    if (activeTab === 'buying') filtered = filtered.filter(d => d.buyer?.id === user?.id);
    else if (activeTab === 'selling') filtered = filtered.filter(d => d.seller?.id === user?.id);
    if (searchQuery) {
      filtered = filtered.filter(d =>
        d.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.description?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    return filtered;
  };

  const filteredDeals = filterDeals(dealsArray);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Deals</h1>
          <p className="text-muted-foreground mt-0.5">Manage your escrow transactions</p>
        </div>
        <Link href="/dashboard/deals/new">
          <Button className="rounded-xl">
            <Plus className="mr-2 h-4 w-4" />
            Create Deal
          </Button>
        </Link>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-5 pb-5">
          <div className="flex space-x-2.5">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search deals..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button variant="outline" size="icon" className="rounded-xl shrink-0">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="all">All Deals</TabsTrigger>
          <TabsTrigger value="buying">Buying</TabsTrigger>
          <TabsTrigger value="selling">Selling</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="space-y-3 mt-5">
          {isLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-32 bg-muted/40 animate-pulse rounded-2xl" />
              ))}
            </div>
          ) : filteredDeals.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-14">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-muted/50 mb-4 shadow-[inset_0_2px_6px_rgba(0,0,0,0.06)]">
                    <FileText className="h-7 w-7 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">No deals found</h3>
                  <p className="text-muted-foreground mb-5 text-sm">
                    {searchQuery ? 'Try adjusting your search query' : 'Create your first deal to get started'}
                  </p>
                  {!searchQuery && (
                    <Link href="/dashboard/deals/new">
                      <Button>
                        <Plus className="mr-2 h-4 w-4" />
                        Create Deal
                      </Button>
                    </Link>
                  )}
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-3">
              {filteredDeals.map((deal: any, i: number) => {
                const statusInfo = STATUS_BADGE[deal.status as keyof typeof STATUS_BADGE] || { variant: 'secondary' as const, label: deal.status };
                return (
                  <Link key={deal.id} href={`/dashboard/deals/${deal.id}`}>
                    <Card className={`cursor-pointer hover:border-primary/40 hover:-translate-y-0.5 hover:shadow-[0_8px_24px_rgba(0,0,0,0.1)] transition-all duration-200 stagger-item`} style={{ animationDelay: `${i * 60}ms` }}>
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <CardTitle className="text-lg mb-1 truncate">{deal.title}</CardTitle>
                            <CardDescription className="line-clamp-1 text-sm">
                              {deal.description}
                            </CardDescription>
                          </div>
                          <div className="flex items-center gap-2 shrink-0">
                            <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>
                            <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="pt-0">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                          {[
                            { label: 'Amount', value: `$${formatCurrency(deal.amount)}`, highlight: true },
                            { label: 'Fee', value: `$${formatCurrency(deal.fee)}` },
                            {
                              label: deal.buyer.id === user?.id ? 'Seller' : 'Buyer',
                              value: deal.buyer.id === user?.id
                                ? deal.seller.telegram_username || deal.seller.username
                                : deal.buyer.telegram_username || deal.buyer.username,
                            },
                            { label: 'Created', value: formatDate(deal.created_at) },
                          ].map(({ label, value, highlight }) => (
                            <div key={label} className="p-2.5 rounded-lg bg-muted/30 border border-border/40">
                              <div className="text-xs text-muted-foreground mb-0.5">{label}</div>
                              <div className={`text-sm font-semibold truncate ${highlight ? 'gradient-text' : ''}`}>{value}</div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
