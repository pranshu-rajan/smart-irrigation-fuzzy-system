'use client';

import React, { useState } from 'react';
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
  Sprout,
  Menu,
  X,
  ShieldCheck,
  Compass,
  MapPin,
  Sparkles
} from 'lucide-react';

interface NavGroup {
  group: string;
  items: {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
  }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    group: 'Supervisory Control',
    items: [
      { href: '/dashboard', label: 'Dashboard', icon: Activity },
      { href: '/', label: '3D Digital Twin', icon: Compass, badge: 'WebGL' },
      { href: '/simulation', label: 'Simulation Studio', icon: Cpu, badge: '1440m' },
      { href: '/allocation', label: 'Water Allocation', icon: Layers },
    ],
  },
  {
    group: 'Fuzzy & Optimization',
    items: [
      { href: '/fuzzy', label: 'Fuzzy Subsystems', icon: Sliders, badge: '5 FIS' },
      { href: '/optimization', label: 'PSO Parameter Tuning', icon: TrendingUp },
      { href: '/scenarios', label: '6 Climate Scenarios', icon: GitFork },
      { href: '/zones', label: 'Zone Agronomy', icon: MapPin },
    ],
  },
  {
    group: 'Intelligence & Audit',
    items: [
      { href: '/ai', label: 'AI Advisory Copilot', icon: Bot, badge: 'Groq' },
      { href: '/reports', label: 'PDF Reports & CSV', icon: FileText },
      { href: '/architecture', label: 'System Architecture', icon: ShieldCheck },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  const closeSidebar = () => setIsOpen(false);

  return (
    <>
      {/* Mobile Top Header */}
      <div className="sticky top-0 z-40 flex h-16 w-full items-center justify-between border-b border-slate-200/90 bg-white/95 px-4 backdrop-blur-md lg:hidden shadow-xs">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-xs">
            <Sprout className="h-5 w-5" />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-slate-900 flex items-center gap-1.5">
              <span>AGRI-FUZZY</span>
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
                v2.4
              </span>
            </div>
            <div className="text-[9px] text-slate-500 font-mono uppercase tracking-wider">
              Smart Irrigation
            </div>
          </div>
        </Link>

        <button
          onClick={() => setIsOpen(!isOpen)}
          className="rounded-xl border border-slate-200 bg-slate-50 p-2 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors"
          aria-label="Toggle Navigation Menu"
        >
          {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={closeSidebar}
          className="fixed inset-0 z-40 bg-slate-900/30 backdrop-blur-xs lg:hidden transition-opacity"
        />
      )}

      {/* Left Sidebar Shell */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200/90 bg-white shadow-xs transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="flex h-18 items-center justify-between px-5 border-b border-slate-100">
          <Link href="/" onClick={closeSidebar} className="flex items-center gap-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-600/20 group-hover:scale-105 transition-transform">
              <Sprout className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-slate-900 flex items-center gap-1.5">
                <span>AGRI-FUZZY</span>
                <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200/80">
                  HAFC
                </span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono tracking-wider uppercase font-medium">
                Smart Multizone
              </div>
            </div>
          </Link>

          {/* Close button on mobile inside drawer */}
          <button
            onClick={closeSidebar}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Navigation Links Scroll Area */}
        <div className="flex-1 overflow-y-auto px-3.5 py-4 space-y-6">
          {NAV_GROUPS.map((group) => (
            <div key={group.group} className="space-y-1">
              <div className="px-2.5 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                {group.group}
              </div>
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={closeSidebar}
                      className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-900 font-bold border border-emerald-200/90 shadow-2xs'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon
                          className={`h-4 w-4 transition-colors ${
                            isActive
                              ? 'text-emerald-700'
                              : 'text-slate-400 group-hover:text-emerald-600'
                          }`}
                        />
                        <span>{item.label}</span>
                      </div>

                      {item.badge && (
                        <span
                          className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-semibold ${
                            isActive
                              ? 'bg-emerald-600 text-white'
                              : 'bg-slate-100 text-slate-500 group-hover:bg-emerald-50 group-hover:text-emerald-700'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Bottom System Status Panel */}
        <div className="p-3.5 border-t border-slate-100 bg-slate-50/60">
          <div className="rounded-xl border border-emerald-200/80 bg-emerald-50/70 p-3 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
                </span>
                <span className="text-xs font-bold text-emerald-950">HAFC Online</span>
              </div>
              <span className="text-[10px] font-mono text-emerald-700 font-bold bg-white px-1.5 py-0.5 rounded border border-emerald-200">
                0.00 mm
              </span>
            </div>

            <p className="text-[10px] text-slate-600 leading-tight">
              3 zones in active closed-loop mass balance with supervisory priority dispatch.
            </p>

            <Link
              href="/simulation"
              onClick={closeSidebar}
              className="flex items-center justify-center gap-1.5 w-full rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white py-1.5 text-xs font-bold shadow-xs shadow-emerald-600/20 transition-all cursor-pointer"
            >
              <Sparkles className="h-3 w-3" />
              <span>Launch Sim Lab</span>
            </Link>
          </div>
        </div>
      </aside>
    </>
  );
}
