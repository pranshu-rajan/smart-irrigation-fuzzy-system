'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Activity, 
  Cpu, 
  Sliders, 
  Layers, 
  TrendingUp, 
  Bot, 
  FileText, 
  GitFork,
  CheckCircle2
} from 'lucide-react';

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: Activity },
  { href: '/simulation', label: 'Simulation Lab', icon: Cpu },
  { href: '/fuzzy', label: 'Fuzzy Logic', icon: Sliders },
  { href: '/allocation', label: 'Water Allocation', icon: Layers },
  { href: '/optimization', label: 'PSO Optimizer', icon: TrendingUp },
  { href: '/scenarios', label: 'Scenarios', icon: GitFork },
  { href: '/ai', label: 'AI Advisor', icon: Bot },
  { href: '/reports', label: 'Reports', icon: FileText },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500 to-teal-700 text-white shadow-md shadow-emerald-500/20 group-hover:scale-105 transition-transform">
              <Cpu className="h-5 w-5" />
            </div>
            <div>
              <div className="font-bold tracking-tight text-white flex items-center gap-2">
                <span>AGRI-FUZZY</span>
                <span className="text-xs font-mono font-normal px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  HAFC v2.4
                </span>
              </div>
              <div className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">
                Hierarchical Adaptive Control
              </div>
            </div>
          </Link>
        </div>

        {/* Navigation links */}
        <nav className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-400' : 'text-slate-400'}`} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* System Online Status Pill */}
        <div className="flex items-center gap-3">
          <Link 
            href="/architecture"
            className="hidden sm:flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 border border-slate-800 rounded-md px-2.5 py-1 transition-colors"
          >
            <span>Architecture</span>
          </Link>
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/40 text-emerald-400 text-xs">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-[11px] font-medium tracking-wide">3 ZONES ONLINE</span>
          </div>
        </div>
      </div>
      
      {/* Mobile navigation bar */}
      <div className="lg:hidden flex items-center gap-1 overflow-x-auto px-4 py-2 border-t border-slate-900 bg-slate-950 scrollbar-none">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-1 whitespace-nowrap px-2.5 py-1 rounded-md text-xs font-medium ${
                isActive
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              {item.label}
            </Link>
          );
        })}
      </div>
    </header>
  );
}
