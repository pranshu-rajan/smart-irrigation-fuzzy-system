'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
import { useAuth } from '@/context/AuthContext';
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
  Sprout,
  LogOut,
  User,
  LogIn
} from 'lucide-react';

const ROUTE_LABELS: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  '/': { label: 'End-to-End Fuzzy Architecture Studio', icon: Sliders },
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
  const router = useRouter();
  const { isOpen, toggleSidebar, isCollapsed, toggleCollapse } = useSidebar();
  const { user, isAuthenticated, logout, openAuthModal } = useAuth();

  const currentRoute = ROUTE_LABELS[pathname] || { label: 'Irrigation Platform', icon: Sprout };
  const RouteIcon = currentRoute.icon;

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/90 bg-white/95 px-3 sm:px-6 backdrop-blur-md shadow-2xs">
      <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0">
        {/* Mobile Sidebar Toggle Button (< lg) */}
        <button
          onClick={toggleSidebar}
          className="flex lg:hidden items-center justify-center h-9 w-9 shrink-0 rounded-xl border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100 hover:text-slate-900 transition-colors cursor-pointer"
          aria-label="Toggle Navigation Sidebar"
          title="Toggle Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Current Active Page Breadcrumb & Vector Icon */}
        <div className="flex items-center gap-2 text-xs min-w-0">
          <div className="flex items-center gap-1.5 font-semibold text-slate-900 min-w-0">
            <RouteIcon className="h-4 w-4 text-emerald-600 shrink-0" />
            <span className="truncate max-w-[140px] sm:max-w-[260px] md:max-w-none">{currentRoute.label}</span>
          </div>
        </div>
      </div>

      {/* Top Right Live Telemetry Badge & Operator Session */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        <div className="hidden xl:flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200/80 text-xs font-semibold shadow-2xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
          </span>
          <span className="font-mono text-[11px]">3-Zone HAFC Active</span>
        </div>

        {/* Operator Account Status */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-1.5 sm:gap-2 rounded-xl border border-slate-200/80 bg-slate-50/80 px-2 sm:px-2.5 py-1.5 text-xs shadow-2xs">
            <div className="flex items-center gap-1.5 min-w-0">
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-white uppercase">
                {user.email.charAt(0)}
              </div>
              <span className="hidden md:inline font-medium text-slate-800 max-w-[120px] truncate" title={user.email}>
                {user.name || user.email.split('@')[0]}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-200/60 hover:text-rose-600 transition-colors cursor-pointer"
              title="Sign Out Operator"
              aria-label="Sign Out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={openAuthModal}
            className="inline-flex items-center gap-1 sm:gap-1.5 rounded-xl border border-slate-200 bg-white px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-emerald-300 hover:text-emerald-700 transition-colors shadow-2xs cursor-pointer"
          >
            <LogIn className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
            <span className="hidden sm:inline">Sign In</span>
          </button>
        )}

        <Link
          href="/simulation"
          className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-3 sm:px-3.5 py-2 text-xs font-bold text-white hover:bg-emerald-700 transition-all shadow-sm shadow-emerald-600/15 cursor-pointer shrink-0"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span className="hidden sm:inline">Launch Simulation</span>
          <span className="sm:hidden">Sim</span>
        </Link>
      </div>
    </header>
  );
}
