'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
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
  Sparkles,
  ChevronLeft,
  ChevronRight
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
    group: 'Primary Workflow',
    items: [
      { href: '/', label: 'System Studio', icon: Sliders, badge: 'Start Here' },
    ],
  },
  {
    group: 'Subsystem Deep-Dives',
    items: [
      { href: '/fuzzy', label: '5 Fuzzy Engines', icon: Sliders, badge: '5 FIS' },
      { href: '/simulation', label: 'Simulation Studio', icon: Cpu, badge: '1440m' },
      { href: '/dashboard', label: 'Dashboard & 3D Twin', icon: Activity, badge: 'WebGL' },
      { href: '/allocation', label: 'Supervisory Allocation', icon: Layers },
      { href: '/optimization', label: 'PSO Parameter Tuning', icon: TrendingUp },
      { href: '/scenarios', label: '6 Climate Scenarios', icon: GitFork },
      { href: '/zones', label: 'Zone Agronomy', icon: MapPin },
    ],
  },
  {
    group: 'Outputs & Advisory',
    items: [
      { href: '/ai', label: 'AI Advisory Copilot', icon: Bot, badge: 'Groq' },
      { href: '/reports', label: 'PDF Reports & CSV', icon: FileText },
      { href: '/architecture', label: 'System Architecture', icon: ShieldCheck },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { isOpen, setIsOpen, isCollapsed, toggleCollapse } = useSidebar();

  const closeSidebar = () => setIsOpen(false);

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={closeSidebar}
          className="fixed inset-0 z-40 bg-slate-900/30 backdrop-blur-xs lg:hidden transition-opacity"
        />
      )}

      {/* Left Sidebar Shell */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 flex flex-col border-r border-slate-200/90 bg-white shadow-xs transition-all duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } ${isCollapsed ? 'lg:w-20' : 'lg:w-64'} w-64`}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between px-4 border-b border-slate-100">
          <Link
            href="/"
            onClick={closeSidebar}
            className={`flex items-center gap-3 group overflow-hidden ${isCollapsed ? 'lg:justify-center lg:w-full' : ''}`}
            title="Smart Multizone Fuzzy Irrigation"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-600/20 group-hover:scale-105 transition-transform">
              <Sprout className="h-5 w-5" />
            </div>

            {!isCollapsed && (
              <div className="lg:block overflow-hidden whitespace-nowrap">
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
            )}
          </Link>

          {/* Desktop collapse toggle button */}
          <button
            onClick={toggleCollapse}
            className={`hidden lg:flex items-center justify-center h-8 w-8 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors ${
              isCollapsed ? 'hidden' : ''
            }`}
            title="Collapse sidebar"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>

          {/* Close button on mobile inside drawer */}
          <button
            onClick={closeSidebar}
            className="lg:hidden rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
            aria-label="Close navigation"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation Links Scroll Area */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {NAV_GROUPS.map((group) => (
            <div key={group.group} className="space-y-1">
              {!isCollapsed && (
                <div className="px-2.5 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                  {group.group}
                </div>
              )}
              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={closeSidebar}
                      title={isCollapsed ? item.label : undefined}
                      className={`group flex items-center ${
                        isCollapsed ? 'lg:justify-center lg:px-2' : 'justify-between px-3'
                      } py-2.5 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-emerald-50 text-emerald-900 font-bold border border-emerald-200/90 shadow-2xs'
                          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon
                          className={`h-4 w-4 shrink-0 transition-colors ${
                            isActive
                              ? 'text-emerald-700'
                              : 'text-slate-400 group-hover:text-emerald-600'
                          }`}
                        />
                        {!isCollapsed && <span>{item.label}</span>}
                      </div>

                      {!isCollapsed && item.badge && (
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
        <div className="p-3 border-t border-slate-100 bg-slate-50/60">
          {!isCollapsed ? (
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
          ) : (
            <div className="flex flex-col items-center gap-2">
              <button
                onClick={toggleCollapse}
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 hover:bg-emerald-50 hover:text-emerald-700 transition-colors"
                title="Expand sidebar"
                aria-label="Expand sidebar"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}
