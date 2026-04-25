import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Shield, Lock, Zap, Users, ArrowRight, CheckCircle2, TrendingUp, Globe } from "lucide-react";

export default function Home() {
  const features = [
    {
      icon: Shield,
      title: "Secure Escrow",
      desc: "Funds are locked in smart contracts until both parties confirm completion.",
      color: "text-primary",
      bg: "bg-primary/10",
    },
    {
      icon: Lock,
      title: "2FA Protection",
      desc: "Two-factor authentication for withdrawals and sensitive operations.",
      color: "text-blue-500",
      bg: "bg-blue-500/10",
    },
    {
      icon: Zap,
      title: "Instant Deposits",
      desc: "Automatic USDT (TRC20) deposit detection and balance updates.",
      color: "text-yellow-500",
      bg: "bg-yellow-500/10",
    },
    {
      icon: Users,
      title: "Real-time Chat",
      desc: "Communicate with your trading partner directly in the platform.",
      color: "text-green-500",
      bg: "bg-green-500/10",
    },
  ];

  const stats = [
    { value: "$2M+", label: "Total Volume" },
    { value: "10K+", label: "Active Users" },
    { value: "50K+", label: "Deals Completed" },
    { value: "99.9%", label: "Success Rate" },
  ];

  const steps = [
    { n: 1, title: "Create Deal", desc: "Buyer and seller agree on terms and create an escrow deal with clear conditions." },
    { n: 2, title: "Fund Escrow", desc: "Seller deposits USDT into the secure escrow contract for protection." },
    { n: 3, title: "Complete Trade", desc: "After delivery, buyer confirms and funds are released automatically." },
  ];

  const benefits = [
    { title: "Zero Trust Required", desc: "Trade with anyone, anywhere. Our escrow system eliminates the need for trust." },
    { title: "Low Fees", desc: "Only 2.5% platform fee. No hidden charges or surprise costs." },
    { title: "24/7 Support", desc: "Our support team is always available to help resolve any issues." },
    { title: "Telegram Integration", desc: "Manage deals directly from Telegram with our powerful bot." },
  ];

  const liveStats = [
    { icon: TrendingUp, label: "Total Volume", value: "$2,145,890" },
    { icon: Globe, label: "Countries", value: "120+" },
    { icon: Users, label: "Active Users", value: "10,234" },
  ];

  const footerLinks = {
    Product: ["Features", "Pricing", "Security", "API"],
    Company: ["About", "Blog", "Careers", "Contact"],
    Legal: ["Terms", "Privacy", "Cookies", "Licenses"],
  };

  return (
    <div className="min-h-screen bg-background smooth-scroll">
      {/* Ambient background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-60 left-1/2 -translate-x-1/2 w-[800px] h-[600px] rounded-full bg-primary/6 blur-3xl" />
        <div className="absolute top-1/2 -right-60 w-96 h-96 rounded-full bg-blue-500/4 blur-3xl" />
        <div className="absolute bottom-0 -left-40 w-80 h-80 rounded-full bg-cyan-500/4 blur-3xl" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 header-glass">
        <div className="container mx-auto px-4 py-3.5">
          <nav className="flex items-center justify-between">
            <div className="flex items-center space-x-2.5">
              <div className="relative p-1.5 rounded-xl bg-primary/10 icon-3d">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <span className="text-xl font-bold gradient-text tracking-tight">CryptoEscrow</span>
            </div>
            <div className="flex items-center space-x-3">
              <Link href="/login">
                <Button variant="ghost" className="hidden sm:inline-flex rounded-xl">Login</Button>
              </Link>
              <Link href="/login">
                <Button className="group rounded-xl">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
            </div>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 relative z-10">
        {/* Hero */}
        <section className="py-16 sm:py-24 text-center max-w-5xl mx-auto">
          <div className="inline-flex items-center space-x-2 bg-primary/10 border border-primary/20 rounded-full px-4 py-2 mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700 shadow-[0_2px_8px_hsl(var(--primary)/0.15),inset_0_1px_0_rgba(255,255,255,0.4)]">
            <CheckCircle2 className="h-4 w-4 text-primary" />
            <span className="text-sm font-semibold">Trusted by 10,000+ users worldwide</span>
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold mb-6 leading-tight tracking-tight animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
            <span className="gradient-text">Secure USDT Escrow</span>
            <br />
            <span className="text-foreground">Transactions Made Simple</span>
          </h1>

          <p className="text-lg sm:text-xl text-muted-foreground mb-10 max-w-3xl mx-auto leading-relaxed animate-in fade-in slide-in-from-bottom-8 duration-700 delay-200">
            Trade with confidence using our trustless escrow platform.
            Protected by blockchain technology and Telegram authentication.
            Fast, secure, and transparent.
          </p>

          <div className="flex flex-col sm:flex-row justify-center gap-4 animate-in fade-in slide-in-from-bottom-10 duration-700 delay-300">
            <Link href="/login">
              <Button size="lg" className="text-base px-8 w-full sm:w-auto group pulse-glow rounded-xl">
                Start Trading Now
                <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="#features">
              <Button size="lg" variant="outline" className="text-base px-8 w-full sm:w-auto rounded-xl">
                Learn More
              </Button>
            </Link>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16 animate-in fade-in slide-in-from-bottom-12 duration-700 delay-500">
            {stats.map(({ value, label }) => (
              <div key={label} className="glass-card rounded-2xl p-5 hover:-translate-y-1 hover:shadow-[0_12px_28px_rgba(0,0,0,0.15)] transition-all duration-300">
                <div className="text-2xl sm:text-3xl font-bold gradient-text mb-1">{value}</div>
                <div className="text-xs text-muted-foreground font-medium">{label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Features */}
        <section id="features" className="py-16 sm:py-24">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 tracking-tight">Everything You Need</h2>
            <p className="text-muted-foreground text-lg max-w-xl mx-auto">Built for security, speed, and simplicity</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {features.map(({ icon: Icon, title, desc, color, bg }) => (
              <div
                key={title}
                className="group card-3d bg-card p-6 rounded-2xl border border-border/60 cursor-default"
              >
                <div className={`${bg} w-14 h-14 rounded-2xl flex items-center justify-center mb-4 icon-3d group-hover:scale-110 transition-transform duration-200`}>
                  <Icon className={`h-7 w-7 ${color}`} />
                </div>
                <h3 className="text-lg font-bold mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How It Works */}
        <section className="py-16 sm:py-24">
          <div className="text-center mb-14">
            <h2 className="text-3xl sm:text-4xl font-bold mb-3 tracking-tight">How It Works</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Simple, secure, and transparent process from start to finish
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 relative">
            {/* Connector line */}
            <div className="hidden md:block absolute top-8 left-[calc(16.67%+2rem)] right-[calc(16.67%+2rem)] h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

            {steps.map(({ n, title, desc }) => (
              <div key={n} className="text-center relative group">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-blue-500 text-white flex items-center justify-center text-2xl font-bold mx-auto mb-5 shadow-[0_4px_0_hsl(var(--primary)/0.4),0_8px_24px_hsl(var(--primary)/0.3),inset_0_1px_0_rgba(255,255,255,0.25)] group-hover:-translate-y-1 transition-transform duration-200">
                  {n}
                </div>
                <div className="card-3d bg-card p-6 rounded-2xl border border-border/60">
                  <h3 className="text-lg font-bold mb-2">{title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Benefits */}
        <section className="py-16 sm:py-24">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold mb-8 tracking-tight">
                Why Choose <span className="gradient-text">CryptoEscrow</span>?
              </h2>
              <div className="space-y-4">
                {benefits.map(({ title, desc }) => (
                  <div key={title} className="flex items-start space-x-3.5 p-4 rounded-2xl bg-card border border-border/60 shadow-[0_2px_6px_rgba(0,0,0,0.04)] hover:border-primary/30 hover:shadow-[0_4px_12px_rgba(0,0,0,0.06)] transition-all duration-200">
                    <div className="p-1 bg-primary/10 rounded-lg mt-0.5 shrink-0 icon-3d">
                      <CheckCircle2 className="h-4 w-4 text-primary" />
                    </div>
                    <div>
                      <h4 className="font-bold text-sm mb-0.5">{title}</h4>
                      <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="glass-card rounded-2xl p-6 space-y-3">
                {liveStats.map(({ icon: Icon, label, value }) => (
                  <div key={label} className="flex items-center space-x-4 p-4 rounded-xl bg-primary/8 border border-primary/15 shadow-[0_2px_6px_rgba(0,0,0,0.04),inset_0_1px_0_rgba(255,255,255,0.4)] dark:shadow-[0_2px_6px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.05)] hover:-translate-y-0.5 transition-transform duration-200">
                    <div className="p-2.5 bg-primary/15 rounded-xl icon-3d">
                      <Icon className="h-6 w-6 text-primary" />
                    </div>
                    <div>
                      <div className="text-xs text-muted-foreground">{label}</div>
                      <div className="text-2xl font-bold gradient-text">{value}</div>
                    </div>
                  </div>
                ))}
              </div>
              {/* Decorative glow */}
              <div className="absolute -inset-4 rounded-3xl bg-primary/4 blur-2xl -z-10" />
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 sm:py-24">
          <div className="gradient-bg rounded-3xl p-12 sm:p-16 relative overflow-hidden shadow-[0_16px_48px_rgba(30,64,175,0.4),inset_0_1px_0_rgba(255,255,255,0.15)]">
            <div className="absolute inset-0 bg-black/20 rounded-3xl" />
            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
            <div className="relative z-10 text-center">
              <h2 className="text-3xl sm:text-4xl font-bold mb-4 text-white tracking-tight">Ready to Start Trading?</h2>
              <p className="text-lg text-white/85 mb-8 max-w-2xl mx-auto leading-relaxed">
                Join thousands of users trading securely with our escrow platform. Get started in minutes.
              </p>
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Link href="/login">
                  <Button size="lg" className="text-base px-8 bg-white text-primary hover:bg-white/95 w-full sm:w-auto group rounded-xl shadow-[0_4px_0_rgba(0,0,0,0.15),0_8px_24px_rgba(0,0,0,0.2),inset_0_1px_0_rgba(255,255,255,0.8)] hover:-translate-y-0.5 hover:shadow-[0_6px_0_rgba(0,0,0,0.12),0_12px_32px_rgba(0,0,0,0.25)] active:translate-y-0.5 transition-all duration-200">
                    Get Started Now
                    <ArrowRight className="ml-2 h-5 w-5 transition-transform group-hover:translate-x-1" />
                  </Button>
                </Link>
                <Button size="lg" variant="outline" className="text-base px-8 border-white/40 text-white hover:bg-white/10 hover:border-white/60 w-full sm:w-auto rounded-xl">
                  View Documentation
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-12 border-t border-border/40 relative z-10">
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          <div>
            <div className="flex items-center space-x-2.5 mb-4">
              <div className="p-1.5 bg-primary/10 rounded-xl icon-3d">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <span className="text-lg font-bold gradient-text">CryptoEscrow</span>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Secure, trustless, and decentralized escrow platform for USDT transactions.
            </p>
          </div>

          {Object.entries(footerLinks).map(([section, links]) => (
            <div key={section}>
              <h4 className="font-bold mb-4 text-sm tracking-wide">{section}</h4>
              <ul className="space-y-2.5">
                {links.map((link) => (
                  <li key={link}>
                    <Link href="#" className="text-sm text-muted-foreground hover:text-primary transition-colors duration-200">
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="text-center pt-8 border-t border-border/40">
          <p className="text-sm text-muted-foreground">&copy; 2026 CryptoEscrow. All rights reserved.</p>
          <p className="mt-1.5 text-xs text-muted-foreground/60 tracking-widest uppercase">Secure · Trustless · Decentralized</p>
        </div>
      </footer>
    </div>
  );
}
