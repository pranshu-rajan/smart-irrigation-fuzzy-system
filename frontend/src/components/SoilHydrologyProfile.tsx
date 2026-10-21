'use client';

import React from 'react';
import { Layers, Droplets, AlertTriangle, ShieldCheck, ArrowDown, Activity, Info } from 'lucide-react';

interface SoilHydrologyProfileProps {
  soilType: string;
  currentMoisture: number;
  fieldCapacity: number;
  wiltingPoint: number;
  saturation?: number;
  className?: string;
}

export default function SoilHydrologyProfile({
  soilType,
  currentMoisture,
  fieldCapacity,
  wiltingPoint,
  saturation = 45.0,
  className = '',
}: SoilHydrologyProfileProps) {
  const fc = fieldCapacity || 28.0;
  const wp = wiltingPoint || 12.0;
  const sat = Math.max(saturation, fc + 8.0);
  const sm = currentMoisture || 24.0;

  // Plant Available Water Capacity (AWC = FC - WP)
  const awc = Math.max(0.1, fc - wp);
  // Readily Available Water (RAW ~ 50% of AWC for field crops)
  const rawThreshold = fc - 0.5 * awc;
  // Current Relative Soil Moisture (RSM)
  const rsm = Math.max(0, Math.min(1, (sm - wp) / awc));

  // Determine Hydrological Status
  let statusText = 'Optimal Transpiration Zone';
  let statusColor = 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30';
  let statusIcon = ShieldCheck;

  if (sm < wp) {
    statusText = 'Severe Root Desiccation / Wilting';
    statusColor = 'text-rose-400 bg-rose-500/10 border-rose-500/30';
    statusIcon = AlertTriangle;
  } else if (sm < rawThreshold) {
    statusText = 'Moderate Moisture Stress (Deficit)';
    statusColor = 'text-amber-400 bg-amber-500/10 border-amber-500/30';
    statusIcon = AlertTriangle;
  } else if (sm > fc) {
    statusText = 'Gravitational Saturated Drainage';
    statusColor = 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30';
    statusIcon = Droplets;
  }

  const StatusIcon = statusIcon;

  // Height percentages for visual column (0 to sat)
  const satHeightPct = 100;
  const fcHeightPct = Math.min(100, (fc / sat) * 100);
  const rawHeightPct = Math.min(100, (rawThreshold / sat) * 100);
  const wpHeightPct = Math.min(100, (wp / sat) * 100);
  const currentHeightPct = Math.min(100, Math.max(4, (sm / sat) * 100));

  return (
    <div className={`rounded-2xl border border-slate-700/60 bg-slate-900/90 backdrop-blur-md p-5 text-white shadow-xl ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <Layers className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>Root-Zone Soil Hydrology & Porosity Profile</span>
            </h3>
            <span className="text-[11px] text-slate-400 font-mono">
              ICAR Soil Order: <strong className="text-emerald-400 font-semibold">{soilType || 'Alluvial (Inceptisol)'}</strong>
            </span>
          </div>
        </div>

        <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${statusColor}`}>
          <StatusIcon className="h-3.5 w-3.5 shrink-0" />
          <span>{statusText}</span>
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-center">
        {/* Left Column: Visual Soil Column Cross-Section */}
        <div className="md:col-span-5 flex items-center justify-center">
          <div className="relative w-full max-w-[240px] h-64 rounded-2xl border border-slate-700 bg-slate-950 p-3 shadow-inner flex flex-col justify-between">
            {/* Background Layer Indicators */}
            <div className="absolute inset-x-3 inset-y-3 rounded-xl overflow-hidden pointer-events-none flex flex-col justify-end">
              {/* Saturated Zone Top */}
              <div
                className="w-full bg-cyan-950/30 border-b border-dashed border-cyan-500/40 relative"
                style={{ height: `${100 - fcHeightPct}%` }}
              >
                <span className="absolute top-1 right-2 text-[9px] font-mono text-cyan-400 font-semibold">
                  Sat ({sat.toFixed(0)}%)
                </span>
              </div>

              {/* Readily Available Water (Optimal Band) */}
              <div
                className="w-full bg-emerald-950/40 border-b border-dashed border-emerald-500/40 relative"
                style={{ height: `${fcHeightPct - wpHeightPct}%` }}
              >
                <span className="absolute top-1 right-2 text-[9px] font-mono text-emerald-400 font-semibold">
                  FC ({fc.toFixed(1)}%)
                </span>
                <span className="absolute bottom-1 right-2 text-[9px] font-mono text-amber-400 font-semibold">
                  WP ({wp.toFixed(1)}%)
                </span>
              </div>

              {/* Hygroscopic / Wilting Bottom */}
              <div
                className="w-full bg-rose-950/30 relative"
                style={{ height: `${wpHeightPct}%` }}
              >
                <span className="absolute bottom-1 right-2 text-[9px] font-mono text-rose-400 font-semibold">
                  Hygroscopic (0%)
                </span>
              </div>
            </div>

            {/* Active Soil Moisture Column Fill */}
            <div
              className="absolute left-6 right-20 bottom-3 rounded-xl transition-all duration-700 shadow-lg overflow-hidden border border-emerald-400/60"
              style={{
                height: `${currentHeightPct}%`,
                background: 'linear-gradient(180deg, rgba(16, 185, 129, 0.8) 0%, rgba(6, 95, 70, 0.9) 100%)',
              }}
            >
              {/* Animated Rippling Surface */}
              <div className="h-1.5 w-full bg-emerald-300/80 animate-pulse" />
            </div>

            {/* Pointer / Callout Marker */}
            <div
              className="absolute left-2 transition-all duration-700 -translate-y-1/2 flex items-center gap-1"
              style={{ bottom: `${currentHeightPct}%` }}
            >
              <div className="flex items-center gap-1 rounded-md bg-emerald-500 px-1.5 py-0.5 text-[10px] font-bold text-slate-950 shadow-md">
                <Droplets className="h-2.5 w-2.5" />
                <span>{sm.toFixed(1)}%</span>
              </div>
              <div className="h-px w-3 bg-emerald-400" />
            </div>
          </div>
        </div>

        {/* Right Column: Physical Hydraulic Parameters */}
        <div className="md:col-span-7 space-y-3">
          <div className="grid grid-cols-2 gap-2.5 text-xs font-mono">
            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Field Capacity (θ_fc)</span>
              <span className="text-base font-bold text-emerald-400 block mt-0.5">{fc.toFixed(1)}% vol</span>
              <span className="text-[10px] text-slate-500 block">Upper drainage limit</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Permanent Wilting (θ_wp)</span>
              <span className="text-base font-bold text-rose-400 block mt-0.5">{wp.toFixed(1)}% vol</span>
              <span className="text-[10px] text-slate-500 block">Suction: 1500 kPa</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Plant Available (AWC)</span>
              <span className="text-base font-bold text-cyan-400 block mt-0.5">{awc.toFixed(1)}% vol</span>
              <span className="text-[10px] text-slate-500 block">Total retention pool</span>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-950/70 p-3">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Relative Moisture (RSM)</span>
              <span className="text-base font-bold text-indigo-400 block mt-0.5">{(rsm * 100).toFixed(0)}%</span>
              <span className="text-[10px] text-slate-500 block">Mamdani input 0–1.0</span>
            </div>
          </div>

          {/* Infiltration & Drainage Note */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-[11px] text-slate-300 leading-relaxed flex items-start gap-2">
            <Info className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            <p>
              In <strong className="text-white">{soilType}</strong>, the hydraulic conductivity operates at high drainage efficiency when moisture exceeds {fc.toFixed(1)}%. The 5-stage FIS applies closed-loop dampening to ensure zero gravitational deep percolation losses ($D = 0$).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
