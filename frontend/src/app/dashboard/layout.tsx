"use client";

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Shield, Wallet, FileText, User, LogOut, Menu, X, Home } from 'lucide-react';
import { useLogout } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, user, clearAuth } = useAuthStore();
  const logout = useLogout();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    const token = localStorage.getItem('auth_token');
    if (!token) {
      clearAuth();
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  if (!isAuthenticated) {
    return null;
  }

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: '/dashboard/wallet', label: 'Wallet', icon: Wallet },
    { href: '/dashboard/deals', label: 'Deals', icon: FileText },
    { href: '/dashboard/profile', label: 'Profile', icon: User },
  ];

  const isActive = (href: string) => {
    if (href === '/dashboard') return pathname === href;
    return pathname.startsWith(href);
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 header-glass">
        <div className="container mx-auto px-4 py-3.5">
          <div className="flex items-center justify-between">
            <Link href="/dashboard" className="flex items-center space-x-2.5 group">
              <div className="relative p-1.5 rounded-xl bg-primary/10 icon-3d">
                <Shield className="h-6 w-6 text-primary transition-transform duration-300 group-hover:scale-110" />
              </div>
              <span className="text-xl font-bold gradient-text tracking-tight">CryptoEscrow</span>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-1 p-1 rounded-xl bg-muted/50 shadow-[inset_0_1px_3px_rgba(0,0,0,0.06)]">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium",
                      "transition-[box-shadow,transform,background-color] duration-200",
                      active
                        ? [
                            "bg-background text-foreground",
                            "shadow-[0_2px_6px_rgba(0,0,0,0.1),0_1px_2px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.8)]",
                            "dark:shadow-[0_2px_8px_rgba(0,0,0,0.35),inset_0_1px_0_rgba(255,255,255,0.07)]",
                            "-translate-y-px",
                          ].join(" ")
                        : "text-muted-foreground hover:text-foreground hover:bg-background/60"
                    )}
                  >
                    <Icon className={cn("h-4 w-4", active && "text-primary")} />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center space-x-3">
              {/* User pill */}
              <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-primary/8 border border-primary/15 shadow-[0_1px_3px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.6)] dark:shadow-[0_1px_3px_rgba(0,0,0,0.2)]">
                <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]" />
                <span className="text-sm font-semibold">{user?.username || user?.first_name}</span>
              </div>

              <Button
                variant="ghost"
                size="icon"
                onClick={() => logout.mutate()}
                className="hidden md:flex rounded-xl hover:bg-destructive/10 hover:text-destructive"
                title="Logout"
              >
                <LogOut className="h-4 w-4" />
              </Button>

              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden rounded-xl"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-border/40 bg-background/98 backdrop-blur-xl">
            <div className="container mx-auto px-4 py-4 space-y-1.5">
              {navItems.map((item) => {
                const Icon = item.icon;
                const active = isActive(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      "flex items-center space-x-3 px-4 py-3 rounded-xl transition-all",
                      active
                        ? "bg-primary text-primary-foreground shadow-[0_4px_12px_hsl(var(--primary)/0.3),inset_0_1px_0_rgba(255,255,255,0.2)]"
                        : "text-foreground hover:bg-accent"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                );
              })}

              <div className="pt-3 border-t border-border/40">
                <div className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.6)]" />
                    <span className="text-sm font-semibold">{user?.username || user?.first_name}</span>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="rounded-lg hover:bg-destructive/10 hover:text-destructive"
                    onClick={() => {
                      logout.mutate();
                      setMobileMenuOpen(false);
                    }}
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </header>

      {/* Bottom Navigation for Mobile */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur-xl border-t border-border/40 shadow-[0_-4px_16px_rgba(0,0,0,0.08)]">
        <div className="grid grid-cols-4 gap-1 p-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center py-2 px-1 rounded-xl transition-all",
                  active
                    ? "bg-primary/10 text-primary shadow-[inset_0_1px_3px_rgba(0,0,0,0.06)]"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                <Icon className="h-5 w-5 mb-1" />
                <span className="text-xs font-medium">{item.label}</span>
              </Link>
            );
          })}
        </div>
      </nav>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 pb-24 md:pb-8">
        {children}
      </main>
    </div>
  );
}
