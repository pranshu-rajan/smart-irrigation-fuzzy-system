'use client';

import React from 'react';
import { useSidebar } from '@/context/SidebarContext';
import Sidebar from '@/components/Sidebar';
import TopHeader from '@/components/TopHeader';
import LoginModal from '@/components/LoginModal';

export default function AppLayoutClient({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();

  return (
    <div className="min-h-screen bg-[#f8faf9] text-slate-900 font-sans selection:bg-emerald-500 selection:text-white antialiased max-w-full overflow-x-hidden">
      <LoginModal />
      <Sidebar />

      {/* Dynamic left margin based on desktop collapse state */}
      <div
        className={`flex flex-col min-h-screen transition-all duration-300 ease-in-out ${
          isCollapsed ? 'lg:pl-20' : 'lg:pl-64'
        } w-full max-w-full overflow-x-hidden`}
      >
        <TopHeader />

        <main className="flex-1 w-full max-w-7xl mx-auto px-3 sm:px-6 lg:px-8 py-4 sm:py-6 lg:py-8">
          {children}
        </main>

        <footer className="border-t border-slate-200/90 bg-white py-5 sm:py-6 text-center text-xs text-slate-500 shadow-xs mt-auto">
          <div className="max-w-7xl mx-auto px-3 sm:px-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
            <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="font-semibold text-slate-800">Smart Multizone Irrigation Platform</span>
              <span className="text-slate-300 hidden sm:inline">&bull;</span>
              <span className="text-slate-600 block sm:inline">Hierarchical Adaptive Fuzzy Control</span>
            </div>
            <div className="font-mono text-[10px] sm:text-[11px] text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200 text-center">
              FAO-56 Penman-Monteith &bull; Bounded Water-Filling &bull; 3D Digital Twin
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
