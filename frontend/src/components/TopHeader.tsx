'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useSidebar } from '@/context/SidebarContext';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { soundEngine } from '@/lib/audioHaptics';
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
  LogIn, 
  Globe,
  Sun,
  Moon,
  Volume2,
  VolumeX,
  Search
} from 'lucide-react';

const ROUTE_LABELS: Record<string, { label: string; icon: React.ComponentType<{ className?: string }> }> = {
  '/': { label: 'End-to-End Fuzzy Architecture Studio', icon: Sliders },
  '/dashboard': { label: 'National GIS Map & FIS Command Center', icon: Globe },
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
  const { theme, toggleTheme, audioFeedback, toggleAudioFeedback } = useTheme();

  const currentRoute = ROUTE_LABELS[pathname] || { label: 'Irrigation Platform', icon: Sprout };
  const RouteIcon = currentRoute.icon;

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  const handleOpenCommand = () => {
    soundEngine.playPing('mode');
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
  };

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200/90 dark:border-emerald-950/80 bg-white/90 dark:bg-[#070d0a]/90 px-3 sm:px-6 backdrop-blur-md shadow-2xs transition-colors">
      <div className="flex items-center gap-2.5 sm:gap-3.5 min-w-0">
        {/* Mobile Sidebar Toggle Button (< lg) */}
        <button
          onClick={toggleSidebar}
          className="flex lg:hidden items-center justify-center h-9 w-9 shrink-0 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
          aria-label="Toggle Navigation Sidebar"
          title="Toggle Navigation Menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        {/* Current Active Page Breadcrumb & Vector Icon */}
        <div className="flex items-center gap-2 text-xs min-w-0">
          <div className="flex items-center gap-1.5 font-semibold text-slate-900 dark:text-slate-100 min-w-0">
            <RouteIcon className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span className="truncate max-w-[130px] sm:max-w-[240px] md:max-w-none">{currentRoute.label}</span>
          </div>
        </div>
      </div>

      {/* Top Right Live Telemetry Badge, Command Palette, Theme & Audio Controls */}
      <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
        {/* Cmd+K Quick Search Pill */}
        <button
          onClick={handleOpenCommand}
          className="hidden md:flex items-center gap-2 px-2.5 py-1.5 rounded-xl border border-slate-200 dark:border-emerald-950/80 bg-slate-50/80 dark:bg-[#0c1511] text-slate-500 dark:text-slate-400 hover:border-emerald-500/50 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors text-xs cursor-pointer"
          title="Open Quick Command Palette"
        >
          <Search className="h-3.5 w-3.5 text-emerald-500" />
          <span className="text-[11px]">Search...</span>
          <kbd className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-400">
            ⌘K
          </kbd>
        </button>

        {/* Audio Haptics Toggle Button */}
        <button
          onClick={() => {
            toggleAudioFeedback();
            soundEngine.playPing('alert');
          }}
          className={`flex items-center justify-center h-8.5 w-8.5 rounded-xl border transition-colors cursor-pointer ${
            audioFeedback
              ? 'border-emerald-200 dark:border-emerald-900/60 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400'
              : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'
          }`}
          title={`Audio Haptics: ${audioFeedback ? 'Enabled (Click to mute)' : 'Muted (Click to enable)'}`}
          aria-label="Toggle Audio Feedback"
        >
          {audioFeedback ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
        </button>

        {/* Theme Mode Toggle Button */}
        <button
          onClick={() => {
            toggleTheme();
            soundEngine.playPing('mode');
          }}
          className="flex items-center justify-center h-8.5 w-8.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
          title={`Switch to ${theme === 'dark' ? 'Daylight Light Mode' : 'Cyber-Agri Dark Cockpit'}`}
          aria-label="Toggle Theme Mode"
        >
          {theme === 'dark' ? (
            <Sun className="h-4 w-4 text-amber-400 animate-spin-slow" />
          ) : (
            <Moon className="h-4 w-4 text-slate-700" />
          )}
        </button>

        {/* 3-Zone HAFC Status Badge */}
        <div className="hidden xl:flex items-center gap-2 px-2.5 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 border border-emerald-200/80 dark:border-emerald-800/60 text-xs font-semibold shadow-2xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-600"></span>
          </span>
          <span className="font-mono text-[11px]">3-Zone HAFC Active</span>
        </div>

        {/* Operator Account Status */}
        {isAuthenticated && user ? (
          <div className="flex items-center gap-1.5 sm:gap-2 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/80 dark:bg-[#0c1511] px-2 sm:px-2.5 py-1.5 text-xs shadow-2xs">
            <div className="flex items-center gap-1.5 min-w-0">
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-[10px] font-bold text-white uppercase">
                {user.email.charAt(0)}
              </div>
              <span className="hidden md:inline font-medium text-slate-800 dark:text-slate-200 max-w-[110px] truncate" title={user.email}>
                {user.name || user.email.split('@')[0]}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-200/60 dark:hover:bg-slate-800 hover:text-rose-600 transition-colors cursor-pointer"
              title="Sign Out Operator"
              aria-label="Sign Out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        ) : (
          <button
            onClick={openAuthModal}
            className="inline-flex items-center gap-1 sm:gap-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#0c1511] px-2.5 sm:px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:border-emerald-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors shadow-2xs cursor-pointer"
          >
            <LogIn className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span className="hidden sm:inline">Sign In</span>
          </button>
        )}

        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 rounded-xl border border-emerald-300 dark:border-emerald-800 bg-emerald-50 dark:bg-emerald-950/60 px-2.5 sm:px-3.5 py-2 text-xs font-bold text-emerald-800 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition-all shadow-2xs cursor-pointer shrink-0"
        >
          <Globe className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 animate-pulse" />
          <span className="hidden sm:inline">India GIS</span>
          <span className="sm:hidden">GIS</span>
        </Link>

        <Link
          href="/simulation"
          className="inline-flex items-center gap-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-3 sm:px-3.5 py-2 text-xs font-bold text-white hover:from-emerald-500 hover:to-teal-500 transition-all shadow-sm shadow-emerald-600/25 cursor-pointer shrink-0"
        >
          <Play className="h-3.5 w-3.5 fill-current" />
          <span className="hidden sm:inline">Launch Sim</span>
          <span className="sm:hidden">Sim</span>
        </Link>
      </div>
    </header>
  );
}
