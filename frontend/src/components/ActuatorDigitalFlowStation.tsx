'use client';

import React, { useState } from 'react';
import { soundEngine } from '@/lib/audioHaptics';
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
      soundEngine.playRelayClick(false);
    } else {
      setEmergencyCutoff(false);
      setToastMessage(`Supervisory mode switched to ${mode.toUpperCase()} control.`);
      soundEngine.playRelayClick(true);
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
    <div className="rounded-3xl border border-emerald-200/90 bg-white p-6 sm:p-7 shadow-xl text-slate-800 space-y-6">
      {/* 1. Header & Supervisory Mode Control Ribbon */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-emerald-100 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-600">
              <Gauge className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
                <span>Real-Time Actuator & Solenoid Telemetry Station</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-[10px] font-semibold text-emerald-700">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                  Live Hydraulic Manifold
                </span>
              </h2>
            </div>
          </div>
          <p className="text-xs text-slate-500 max-w-2xl">
            Multi-channel PWM pulse-width modulated solenoids driven by Stage 4 & 5 Mamdani fuzzy inference with hydraulic mass balance.
          </p>
        </div>

        {/* Global Control Mode Selector */}
        <div className="flex items-center gap-1.5 rounded-2xl border border-emerald-200 bg-emerald-50/50 p-1 text-xs">
          <button
            onClick={() => handleModeSwitch('fuzzy')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              controlMode === 'fuzzy'
                ? 'bg-emerald-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-emerald-700'
            }`}
          >
            <Cpu className="h-3.5 w-3.5" />
            <span>Auto Fuzzy HAFC</span>
          </button>

          <button
            onClick={() => handleModeSwitch('manual')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              controlMode === 'manual'
                ? 'bg-emerald-700 text-white shadow-xs'
                : 'text-slate-600 hover:text-emerald-700'
            }`}
          >
            <Sliders className="h-3.5 w-3.5" />
            <span>Manual Trim</span>
          </button>

          <button
            onClick={() => handleModeSwitch('pulse')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              controlMode === 'pulse'
                ? 'bg-amber-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-amber-700'
            }`}
          >
            <RotateCw className="h-3.5 w-3.5" />
            <span>Pulsed Flush</span>
          </button>

          <button
            onClick={() => handleModeSwitch('cutoff')}
            className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              emergencyCutoff
                ? 'bg-rose-600 text-white shadow-xs'
                : 'text-rose-600 hover:bg-rose-50'
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
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-800 flex items-center gap-2 animate-in fade-in">
          <Activity className="h-3.5 w-3.5 animate-spin text-emerald-600" />
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
                  ? 'border-emerald-300 bg-emerald-50/40 shadow-md'
                  : 'border-slate-200 bg-white'
              }`}
            >
              {/* Ambient Glowing Water Pipeline Bar at Top */}
              <div 
                className={`absolute top-0 left-0 right-0 h-1 transition-all duration-500 ${
                  isActuatorActive ? 'bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-500 animate-pulse' : 'bg-slate-200'
                }`} 
              />

              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
                    CHANNEL 0{zone.zone_id} &bull; SOLENOID
                  </span>
                  <div className="font-bold text-sm text-slate-900 flex items-center gap-1.5 mt-0.5">
                    <span>{zone.crop}</span>
                    <span className="text-[11px] text-slate-500 font-normal">({zone.name.split(':')[0]})</span>
                  </div>
                </div>

                {/* Valve Pulse Status Badge */}
                <div
                  className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold border ${
                    isActuatorActive
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : 'bg-slate-100 text-slate-500 border-slate-200'
                  }`}
                >
                  <span
                    className={`h-2 w-2 rounded-full ${
                      isActuatorActive ? 'bg-emerald-500 animate-ping' : 'bg-slate-400'
                    }`}
                  />
                  <span>{isActuatorActive ? 'MODULATING' : 'CLOSED'}</span>
                </div>
              </div>

              {/* Dynamic Flow Rate Metric & Aperture Gauge */}
              <div className="mt-4 grid grid-cols-2 gap-3 bg-white rounded-xl p-3 border border-emerald-100 shadow-2xs">
                <div>
                  <span className="text-[10px] text-slate-500 block font-mono">Discharge Velocity</span>
                  <div className="text-base font-bold text-emerald-700 font-mono mt-0.5">
                    {flowRate} <span className="text-[11px] font-normal text-slate-500">L/min</span>
                  </div>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block font-mono">Line Pressure</span>
                  <div className="text-base font-bold text-slate-800 font-mono mt-0.5">
                    2.4 <span className="text-[11px] font-normal text-slate-500">bar</span>
                  </div>
                </div>
              </div>

              {/* PWM Aperture Bar */}
              <div className="mt-4 space-y-1.5">
                <div className="flex justify-between text-[11px] font-mono">
                  <span className="text-slate-500">Fuzzy Valve Aperture:</span>
                  <span className="font-bold text-emerald-700">{cmdPct.toFixed(0)}% (PWM)</span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-400 transition-all duration-300"
                    style={{ width: `${Math.min(100, Math.max(0, cmdPct))}%` }}
                  />
                </div>
              </div>

              {/* Manual Trim Slider (When in manual mode) */}
              {controlMode === 'manual' && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-500 shrink-0">Trim:</span>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={manualApertures[zone.zone_id] || 50}
                    onChange={(e) => {
                      const v = Number(e.target.value);
                      setManualApertures((prev) => ({ ...prev, [zone.zone_id]: v }));
                    }}
                    className="w-full h-1.5 accent-emerald-600 bg-slate-200 rounded-lg cursor-pointer"
                  />
                  <span className="text-[10px] font-mono text-emerald-700 font-bold w-7 text-right">
                    {manualApertures[zone.zone_id] || 50}%
                  </span>
                </div>
              )}

              {/* Bottom Channel Diagnostics */}
              <div className="mt-4 border-t border-slate-100 pt-3 flex items-center justify-between text-[11px] text-slate-500 font-mono">
                <span>Soil Stress: {zone.soil_stress_pct?.toFixed(0)}%</span>
                <span className="text-emerald-700 font-semibold">
                  Today: {zone.allocated_liters?.toFixed(1)} L
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 3. Manifold Pressure & Hydraulic Diagnostics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-emerald-50/40 rounded-2xl p-4 border border-emerald-100 text-xs">
        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">Hydraulic Source</span>
          <span className="text-slate-800 font-semibold flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Solar Drip Irrigation Main
          </span>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">Supervisory Law</span>
          <span className="text-emerald-800 font-semibold font-mono">
            Mamdani Max-Min + Water-Filling
          </span>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">Manifold Delivery</span>
          <span className="text-emerald-700 font-mono font-bold">
            {totalAllocatedLiters.toFixed(1)} Liters
          </span>
        </div>

        <div className="space-y-0.5">
          <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold block">Safety Interlock</span>
          <span className={`font-semibold font-mono ${emergencyCutoff ? 'text-rose-600' : 'text-emerald-700'}`}>
            {emergencyCutoff ? 'CUTOFF ACTIVE' : 'NOMINAL 100%'}
          </span>
        </div>
      </div>
    </div>
  );
}
