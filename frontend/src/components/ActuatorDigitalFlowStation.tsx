'use client';

import React, { useState } from 'react';
import { 
  Cpu, 
  Activity, 
  Droplets, 
  Zap, 
  Gauge, 
  ShieldCheck, 
  Sliders, 
  RotateCw, 
  AlertCircle, 
  CheckCircle2, 
  Play, 
  Pause,
  Layers,
  ArrowRight
} from 'lucide-react';

interface ZoneData {
  zone_id: number;
  name: string;
  crop: string;
  main_command_pct: number;
  allocated_liters: number;
  current_moisture_pct: number;
  target_moisture_pct: number;
  soil_stress_pct: number;
}

interface ActuatorDigitalFlowStationProps {
  zones: ZoneData[];
  isSupplyConstrained?: boolean;
  totalAllocatedLiters?: number;
  onOverrideModeChange?: (mode: string) => void;
}

export default function ActuatorDigitalFlowStation({
  zones,
  isSupplyConstrained = false,
  totalAllocatedLiters = 0,
  onOverrideModeChange,
}: ActuatorDigitalFlowStationProps) {
  const [controlMode, setControlMode] = useState<'fuzzy' | 'manual' | 'pulse' | 'cutoff'>('fuzzy');
  const [manualApertures, setManualApertures] = useState<Record<number, number>>({ 1: 50, 2: 50, 3: 40 });
  const [emergencyCutoff, setEmergencyCutoff] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const handleModeSwitch = (mode: 'fuzzy' | 'manual' | 'pulse' | 'cutoff') => {
    setControlMode(mode);
    if (mode === 'cutoff') {
      setEmergencyCutoff(true);
      setToastMessage('Safety Interlock: All solenoids forcibly closed.');
    } else {
      setEmergencyCutoff(false);
      setToastMessage(`Supervisory mode switched to ${mode.toUpperCase()} control.`);
    }
    if (onOverrideModeChange) {
      onOverrideModeChange(mode);
    }
    setTimeout(() => setToastMessage(null), 3000);
  };

  const calculateFlowRate = (cmdPct: number) => {
    if (emergencyCutoff) return 0.0;
    // 35 L/min nominal pump delivery at 2.4 bar pressure
    const baseLpm = 35.0;
    return Number(((cmdPct / 100.0) * baseLpm).toFixed(1));
  };

  return (
    <div className="rounded-3xl border border-slate-700/70 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 sm:p-7 shadow-2xl text-white space-y-6">
      {/* 1. Header & Supervisory Mode Control Ribbon */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Gauge className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                <span>Real-Time Actuator & Solenoid Telemetry Station</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2.5 py-0.5 text-[10px] font-semibold text-cyan-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
                  Live Hydraulic Manifold
                </span>
              </h2>
            </div>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl">
            Multi-channel PWM pulse-width modulated solenoids driven by Stage 4 & 5 Mamdani fuzzy inference with hydraulic mass balance.
          </p>
        </div>

        {/* Global Control Mode Selector */}
        <div className="flex items-center gap-1.5 rounded-2xl border border-slate-800 bg-slate-900/90 p-1 text-xs">
          <button
            onClick={() => handleModeSwitch('fuzzy')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              controlMode === 'fuzzy'
                ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>Auto Fuzzy HAFC</span>
          </button>

          <button
            onClick={() => handleModeSwitch('manual')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              controlMode === 'manual'
                ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>Manual Trim</span>
          </button>

          <button
            onClick={() => handleModeSwitch('pulse')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              controlMode === 'pulse'
                ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <RotateCw className="h-3.5 w-3.5" />
            <span>Pulsed Flush</span>
          </button>

          <button
            onClick={() => handleModeSwitch('cutoff')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              emergencyCutoff
                ? 'bg-rose-600 text-white shadow-md shadow-rose-600/30'
                : 'text-rose-400 hover:bg-rose-950/40'
            }`}
            title="Emergency Solenoid Shutoff"
          >
            <AlertCircle className="h-3.5 w-3.5" />
            <span>Emergency Cutoff</span>
          </button>
        </div>
      </div>

      {/* Toast Feedback */}
      {toastMessage && (
        <div className="rounded-xl border border-cyan-500/40 bg-cyan-500/10 px-4 py-2 text-xs font-semibold text-cyan-300 flex items-center gap-2 animate-in fade-in">
          <Activity className="h-3.5 w-3.5 animate-spin text-cyan-400" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* 2. Three Hydraulic Actuator Channels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {zones.map((zone) => {
          const rawCmd = controlMode === 'manual' 
            ? (manualApertures[zone.zone_id] || 50) 
            : controlMode === 'pulse'
            ? 75
            : zone.main_command_pct;
          const cmdPct = emergencyCutoff ? 0 : rawCmd;
          const flowRate = calculateFlowRate(cmdPct);
          const isActuatorActive = cmdPct > 15 && !emergencyCutoff;

          return (
            <div
              key={zone.zone_id}
              className={`rounded-2xl border p-5 transition-all duration-300 relative overflow-hidden ${
                isActuatorActive
                  ? 'border-cyan-500/40 bg-slate-900/90 shadow-lg shadow-cyan-950/40'
                  : 'border-slate-800 bg-slate-950/60'
              }`}
            >
              {/* Ambient Glowing Water Pipeline Bar at Top */}
              <div 
                className={`absolute top-0 left-0 right-0 h-1 transition-all duration-500 ${
                  isActuatorActive ? 'bg-gradient-to-r from-cyan-500 via-emerald-400 to-cyan-500 animate-pulse' : 'bg-slate-800'
                }`} 
              />

              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 font-bold block">
                    CHANNEL 0{zone.zone_id} &bull; SOLENOID
                  </span>
                  <div className="font-bold text-sm text-white flex items-center gap-1.5 mt-0.5">
                    <span>{zone.crop}</span>
                    <span className="text-[11px] text-slate-400 font-normal">({zone.name.split(':')[0]})</span>
                  </div>
                </div>

                {/* Valve Pulse Status Badge */}
                <div
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${
                    isActuatorActive
                      ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      isActuatorActive ? 'bg-cyan-400 animate-ping' : 'bg-slate-500'
                    }`}
                  />
                  <span>{isActuatorActive ? 'MODULATING' : 'CLOSED'}</span>
                </div>
              </div>

              {/* Dynamic Flow Rate Metric & Aperture Gauge */}
              <div className="mt-4 grid grid-cols-2 gap-3 bg-slate-950/70 rounded-xl p-3 border border-slate-800/80">
                <div>
                  <span className="text-[10px] text-slate-400 block font-mono">Discharge Velocity</span>
                  <div className="text-base font-bold text-cyan-300 font-mono mt-0.5">
                    {flowRate} <span className="text-[11px] font-normal text-slate-400">L/min</span>
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-mono">Line Pressure</span>
                  <div className="text-base font-bold text-slate-200 font-mono mt-0.5">
                    2.4 <span className="text-[11px] font-normal text-slate-400">bar</span>
                  </div>
                </div>
              </div>

              {/* PWM Aperture Bar */}
              <div className="mt-4 space-y-1.5">
                <div className="flex justify-between text-[11px] font-mono">
                  <span className="text-slate-400">Fuzzy Valve Aperture:</span>
                  <span className="font-bold text-cyan-300">{cmdPct.toFixed(0)}% (PWM)</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-cyan-400 transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(0, cmdPct))}%` }}
                  />
                </div>
              </div>

              {/* Manual Trim Slider (When in manual mode) */}
              {controlMode === 'manual' && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-400 shrink-0">Trim:</span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={manualApertures[zone.zone_id] || 50}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setManualApertures((prev) => ({ ...prev, [zone.zone_id]: v }));
                    }}
                    className="w-full h-1.5 accent-cyan-400 bg-slate-800 rounded-lg cursor-pointer"
                  />
                  <span className="text-[10px] font-mono text-cyan-400 font-bold w-7 text-right">
                    {manualApertures[zone.zone_id] || 50}%
                  </span>
                </div>
              )}

              {/* Bottom Channel Diagnostics */}
              <div className="mt-4 border-t border-slate-800/80 pt-3 flex items-center justify-between text-[11px] text-slate-400 font-mono">
                <span>Soil Stress: {zone.soil_stress_pct?.toFixed(0)}%</span>
                <span className="text-emerald-400 font-semibold">
                  Today: {zone.allocated_liters?.toFixed(1)} L
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Manifold Pressure & Hydraulic Diagnostics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/60 rounded-2xl p-4 border border-slate-800 text-xs">
        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold block">Hydraulic Source</span>
          <span className="text-slate-200 font-semibold flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Solar Drip Irrigation Main
          </span>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold block">Supervisory Law</span>
          <span className="text-cyan-300 font-semibold font-mono">
            Mamdani Max-Min + Water-Filling
          </span>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold block">Manifold Delivery</span>
          <span className="text-emerald-400 font-mono font-bold">
            {totalAllocatedLiters.toFixed(1)} Liters
          </span>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-400 font-semibold block">Safety Interlock</span>
          <span className={`font-semibold font-mono ${emergencyCutoff ? 'text-rose-400' : 'text-emerald-400'}`}>
            {emergencyCutoff ? 'CUTOFF ACTIVE' : 'NOMINAL 100%'}
          </span>
        </div>
      </div>
    </div>
  );
}
