'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Search, 
  Sliders, 
  Cpu, 
  Globe, 
  Layers, 
  TrendingUp, 
  GitFork, 
  MapPin, 
  Bot, 
  FileText, 
  ShieldCheck, 
  X,
  ArrowRight,
  Sun,
  Moon,
  Volume2,
  VolumeX,
  Play
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { soundEngine } from '@/lib/audioHaptics';

interface ActionItem {
  id: string;
  title: string;
  category: 'Navigation' | 'Actions' | 'Presets' | 'System';
  icon: React.ComponentType<{ className?: string }>;
  shortcut?: string;
  action: () => void;
}

export default function CommandPalette() {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const { theme, toggleTheme, audioFeedback, toggleAudioFeedback } = useTheme();

  // Listen for Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen((prev) => {
          if (!prev) {
            soundEngine.playPing('mode');
          }
          return !prev;
        });
      }
      if (e.key === 'Escape' && isOpen) {
        e.preventDefault();
        setIsOpen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery('');
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const actions: ActionItem[] = [
    {
      id: 'nav-studio',
      title: 'Go to System Studio (End-to-End Workflow)',
      category: 'Navigation',
      icon: Sliders,
      action: () => { router.push('/'); setIsOpen(false); },
    },
    {
      id: 'nav-dashboard',
      title: 'Go to National GIS Map & FIS Command Center',
      category: 'Navigation',
      icon: Globe,
      action: () => { router.push('/dashboard'); setIsOpen(false); },
    },
    {
      id: 'nav-sim',
      title: 'Go to Simulation Studio (1440m Telemetry)',
      category: 'Navigation',
      icon: Cpu,
      action: () => { router.push('/simulation'); setIsOpen(false); },
    },
    {
      id: 'nav-fuzzy',
      title: 'Go to 5 Fuzzy Logic Subsystems',
      category: 'Navigation',
      icon: Sliders,
      action: () => { router.push('/fuzzy'); setIsOpen(false); },
    },
    {
      id: 'nav-allocation',
      title: 'Go to Supervisory Water Allocation',
      category: 'Navigation',
      icon: Layers,
      action: () => { router.push('/allocation'); setIsOpen(false); },
    },
    {
      id: 'nav-optimization',
      title: 'Go to PSO Parameter Tuning',
      category: 'Navigation',
      icon: TrendingUp,
      action: () => { router.push('/optimization'); setIsOpen(false); },
    },
    {
      id: 'nav-scenarios',
      title: 'Go to 6 Environmental Benchmark Scenarios',
      category: 'Navigation',
      icon: GitFork,
      action: () => { router.push('/scenarios'); setIsOpen(false); },
    },
    {
      id: 'nav-zones',
      title: 'Go to Zone Agronomy & Soil Hydraulics',
      category: 'Navigation',
      icon: MapPin,
      action: () => { router.push('/zones'); setIsOpen(false); },
    },
    {
      id: 'nav-ai',
      title: 'Ask AI Agronomic Copilot (Groq + Tavily)',
      category: 'Navigation',
      icon: Bot,
      action: () => { router.push('/ai'); setIsOpen(false); },
    },
    {
      id: 'nav-reports',
      title: 'Go to PDF Engineering Reports & Export',
      category: 'Navigation',
      icon: FileText,
      action: () => { router.push('/reports'); setIsOpen(false); },
    },
    {
      id: 'act-theme',
      title: `Switch Theme to ${theme === 'dark' ? 'Daylight Field (Light)' : 'Cyber-Agri Cockpit (Dark)'}`,
      category: 'System',
      icon: theme === 'dark' ? Sun : Moon,
      shortcut: 'T',
      action: () => {
        toggleTheme();
        soundEngine.playPing('mode');
        setIsOpen(false);
      },
    },
    {
      id: 'act-audio',
      title: `Toggle Audio Haptics (${audioFeedback ? 'Enabled' : 'Muted'})`,
      category: 'System',
      icon: audioFeedback ? Volume2 : VolumeX,
      action: () => {
        toggleAudioFeedback();
        soundEngine.playPing('alert');
        setIsOpen(false);
      },
    },
  ];

  const filtered = actions.filter((item) =>
    item.title.toLowerCase().includes(query.toLowerCase()) ||
    item.category.toLowerCase().includes(query.toLowerCase())
  );

  const handleKeyDownList = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % (filtered.length || 1));
      soundEngine.playSliderTick();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filtered.length) % (filtered.length || 1));
      soundEngine.playSliderTick();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        filtered[selectedIndex].action();
      }
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/60 backdrop-blur-md transition-opacity">
      <div 
        className="w-full max-w-xl rounded-2xl border border-emerald-500/30 bg-white dark:bg-[#0c1411] text-slate-900 dark:text-slate-100 shadow-2xl shadow-emerald-950/50 overflow-hidden transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-slate-200 dark:border-emerald-950/80 gap-3">
          <Search className="h-5 w-5 text-emerald-500 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDownList}
            placeholder="Type a command, district, or page... (e.g. 'simulation', 'theme', 'fuzzy')"
            className="w-full bg-transparent text-sm placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none"
          />
          <button
            onClick={() => setIsOpen(false)}
            className="rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Action List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-xs text-slate-400 dark:text-slate-500">
              No matching commands or destinations found.
            </div>
          ) : (
            filtered.map((item, idx) => {
              const Icon = item.icon;
              const isSelected = idx === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    item.action();
                    soundEngine.playPing('success');
                  }}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-left text-xs transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-semibold border border-emerald-200 dark:border-emerald-800/60'
                      : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-900/40 border border-transparent'
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${
                      isSelected ? 'bg-emerald-600 text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                    }`}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="truncate">{item.title}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                      {item.category}
                    </span>
                    {isSelected && <ArrowRight className="h-3.5 w-3.5 text-emerald-500 animate-pulse" />}
                  </div>
                </button>
              );
            })
          )}
        </div>

        {/* Footer shortcuts */}
        <div className="px-4 py-2.5 bg-slate-50 dark:bg-[#080d0a] border-t border-slate-200 dark:border-emerald-950/60 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <div className="flex items-center gap-2">
            <span>Navigate:</span>
            <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-[10px]">↑</kbd>
            <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-[10px]">↓</kbd>
            <span>Select:</span>
            <kbd className="px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-mono text-[10px]">↵</kbd>
          </div>
          <div className="font-mono text-[10px] text-emerald-600 dark:text-emerald-400">
            Smart Irrigation HAFC Cockpit
          </div>
        </div>
      </div>
    </div>
  );
}
