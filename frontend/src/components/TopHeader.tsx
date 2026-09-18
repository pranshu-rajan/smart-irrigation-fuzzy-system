'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
import { 
  Menu, 
  PanelLeftClose, 
  PanelLeft, 
  Activity, 
  Cpu, 
  Sliders, 
  Layers, 
  TrendingUp, 
  GitFork, 
  Bot, 
  FileText, 
  ShieldCheck, 
  MapPin, 
  Compass,
  Play,
  Sprout
} from 'lucide-react';

const ROUTE_LABELS: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  '/': { label: '3D Digital Twin Overview', icon: Compass },
  '/dashboard': { label: 'Telemetry & Supervisory Dashboard', icon: Activity },
  '/simulation': { label: 'Closed-Loop Simulation Studio', icon: Cpu },
  '/fuzzy': { label: 'Fuzzy Logic Diagnostics', icon: Sliders },
  '/allocation': { label: 'Hierarchical Water Allocation', icon: Layers },
  '/optimization': { label: 'Offline PSO Parameter Tuning', icon: TrendingUp },
  '/scenarios': { label: 'Environmental Benchmark Matrix', icon: GitFork },
  '/zones': { label: 'Zone Agronomy & Soil Hydraulics', icon: MapPin },
  '/ai': { label: 'Grounded AI Advisory Assistant', icon: Bot },
  '/reports': { label: 'PDF Reports & Telemetry Export', icon: FileText },
  '/architecture': { label: 'System Architecture & Proofs', icon: ShieldCheck },
  '/login': { label: 'Operator Authentication', icon: ShieldCheck },
};

export default function TopHeader() {
  const pathname = usePathname();
  const { isOpen, toggleSidebar, isCollapsed, toggleCollapse } = useSidebar();

  const currentRoute = ROUTE_LABELS[pathname] || { label: 'Irrigation Platform', icon: Sprout };
  const RouteIcon = currentRoute.icon;

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/90 bg-white/95 px-4 sm:px-6 backdrop-blur-md shadow-2xs">
      <div className="flex items-center gap-3.5">
        {/* 3-Line Bar (Hamburger) Toggle Button for Mobile (< lg) */}
        <button
          onClick={toggleSidebar}
          className="flex lg:hidden items-center justify-center h-9 w-9 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors cursor-pointer"
          aria-label="Toggle Navigation Sidebar"
          title="Toggle Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* 3-Line Bar (Hamburger) Toggle Button for Desktop (lg+) */}
        <button
          onClick={toggleCollapse}
          className="hidden lg:flex items-center justify-center h-9 w-9 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 hover:bg-emerald-50 hover:text-emerald-800 hover:border-emerald-300 transition-colors cursor-pointer"
          aria-label={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
          title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
        >
          <Menu className="h-4 w-4" />
        </button>

        {/* Current Active Page Breadcrumb & Vector Icon */}
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 font-semibold text-slate-900">
            <RouteIcon className="h-4 w-4 text-emerald-600" />
            <span className="hidden sm:inline">{currentRoute.label}</span>
          </div>
        </div>
      </div>

      {/* Top Right Live Telemetry Badge & Sim Quick Action */}
      <div className="flex items-center gap-3">
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200/80 text-xs font-semibold shadow-2xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
          </span>
          <span className="font-mono text-[11px]">3-Zone HAFC Active</span>
        </div>

        <Link
          href="/simulation"
          className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-3.5 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-all shadow-sm shadow-emerald-600/15 cursor-pointer"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span className="hidden sm:inline">Launch Simulation</span>
        </Link>
      </div>
    </header>
  );
}
