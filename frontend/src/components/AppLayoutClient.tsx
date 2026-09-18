'use client';

import React from 'react';
import { useSidebar } from '@/context/SidebarContext';
import Sidebar from '@/components/Sidebar';
import TopHeader from '@/components/TopHeader';

export default function AppLayoutClient({ children }: { children: React.ReactNode }) {
  const { isCollapsed } = useSidebar();

  return (
    <div className="min-h-screen bg-[#f8faf9] text-slate-900 font-sans selection:bg-emerald-500 selection:text-white antialiased">
      <Sidebar />

      {/* Dynamic left margin based on desktop collapse state */}
      <div
        className={`flex flex-col min-h-screen transition-all duration-300 ease-in-out ${
          isCollapsed ? 'lg:pl-20' : 'lg:pl-64'
        }`}
      >
        <TopHeader />

        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        <footer className="border-t border-slate-200/90 bg-white py-6 text-center text-xs text-slate-500 shadow-xs mt-auto">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span className="font-semibold text-slate-800">Smart Multizone Irrigation Platform</span>
              <span className="text-slate-300">&bull;</span>
              <span className="text-slate-600">Hierarchical Adaptive Fuzzy Control</span>
            </div>
            <div className="font-mono text-[11px] text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
              FAO-56 Penman-Monteith &bull; Bounded Water-Filling &bull; 3D Digital Twin
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
