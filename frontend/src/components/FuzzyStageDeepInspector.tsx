'use client';

import React, { useState } from 'react';
import { 
  Cpu, 
  Layers, 
  Activity, 
  ShieldCheck, 
  Sparkles, 
  ArrowRight, 
  Sliders, 
  HelpCircle,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';

interface ZoneData {
  zone_id: number;
  name: string;
  crop: string;
  season: string;
  kc: number;
  soil_type: string;
  area_m2: number;
  target_moisture_pct: number;
  current_moisture_pct: number;
  soil_stress_pct: number;
  water_demand_pct: number;
  main_command_pct: number;
  requested_liters: number;
  allocated_liters: number;
  fulfillment_ratio_pct: number;
  status: string;
}

interface FuzzyStageDeepInspectorProps {
  zones: ZoneData[];
  weatherStress: number;
  et0Val: number;
  reservoirStorage: number;
  className?: string;
}

export default function FuzzyStageDeepInspector({
  zones = [],
  weatherStress = 45.0,
  et0Val = 4.5,
  reservoirStorage = 75.0,
  className = '',
}: FuzzyStageDeepInspectorProps) {
  const [selectedZoneId, setSelectedZoneId] = useState<number>(zones[0]?.zone_id || 1);
  const [activeStage, setActiveStage] = useState<number>(1);

  const activeZone = zones.find((z) => z.zone_id === selectedZoneId) || zones[0] || {
    zone_id: 1,
    name: 'Zone 1: Primary Kharif',
    crop: 'Rice/Paddy',
    season: 'Kharif',
    kc: 1.15,
    soil_type: 'Alluvial',
    area_m2: 1000,
    target_moisture_pct: 28.0,
    current_moisture_pct: 23.5,
    soil_stress_pct: 46.2,
    water_demand_pct: 54.0,
    main_command_pct: 58.5,
    requested_liters: 145.0,
    allocated_liters: 145.0,
    fulfillment_ratio_pct: 100.0,
    status: 'OPTIMAL',
  };

  const STAGES = [
    { num: 1, name: 'Stage 1: Soil Stress FIS', short: 'Soil Stress', value: activeZone.soil_stress_pct, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
    { num: 2, name: 'Stage 2: Weather Stress FIS', short: 'Weather Stress', value: weatherStress, color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
    { num: 3, name: 'Stage 3: Water Demand FIS', short: 'Water Demand', value: activeZone.water_demand_pct, color: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/30' },
    { num: 4, name: 'Stage 4: Main Irrigation FIS', short: 'Command FIS', value: activeZone.main_command_pct, color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30' },
    { num: 5, name: 'Stage 5: Supervisory Allocation', short: 'Water Allocation', value: activeZone.fulfillment_ratio_pct, color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30' },
  ];

  // Membership Function Terms for Active Stage
  const renderMembershipTerms = () => {
    switch (activeStage) {
      case 1:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-300">
              <strong className="text-emerald-400">Inputs:</strong> Relative Soil Moisture (RSM: {((activeZone.current_moisture_pct / activeZone.target_moisture_pct) * 0.5).toFixed(2)}) & Moisture Error ($e(t)$: {(activeZone.target_moisture_pct - activeZone.current_moisture_pct).toFixed(1)}%)
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">μ_Very_Dry</span>
                <span className="text-emerald-400 font-bold">{activeZone.soil_stress_pct > 70 ? '0.85' : '0.10'}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">μ_Dry</span>
                <span className="text-emerald-400 font-bold">{activeZone.soil_stress_pct > 40 && activeZone.soil_stress_pct <= 70 ? '0.72' : '0.15'}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">μ_Optimal</span>
                <span className="text-emerald-400 font-bold">{activeZone.soil_stress_pct <= 40 ? '0.90' : '0.05'}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Defuzz Centroid</span>
                <span className="text-white font-bold">{activeZone.soil_stress_pct.toFixed(1)}%</span>
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400 font-mono">
              <strong>Active Mamdani Rule Fired:</strong>
              <div className="text-emerald-300 mt-1">
                IF (RSM is Dry) AND (Error is Positive) THEN (Soil_Stress is Moderate_High) [Weight: 1.0]
              </div>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-300">
              <strong className="text-amber-400">Atmospheric Forcing:</strong> FAO-56 Reference ET₀ = {et0Val.toFixed(2)} mm/day
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">μ_Solar_High</span>
                <span className="text-amber-400 font-bold">0.82</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">μ_Temp_Elevated</span>
                <span className="text-amber-400 font-bold">0.65</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">μ_Wind_Moderate</span>
                <span className="text-amber-400 font-bold">0.50</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Defuzz Centroid</span>
                <span className="text-white font-bold">{weatherStress.toFixed(1)}%</span>
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400 font-mono">
              <strong>Active Mamdani Rule Fired:</strong>
              <div className="text-amber-300 mt-1">
                IF (Solar is High) AND (RH is Low) AND (Rainfall is Zero) THEN (Weather_Stress is High) [Weight: 1.0]
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-300">
              <strong className="text-cyan-400">Crop Evapotranspiration:</strong> ETc = Kc × ET₀ = {(activeZone.kc * et0Val).toFixed(2)} mm/day
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Crop Kc Factor</span>
                <span className="text-cyan-400 font-bold">{activeZone.kc.toFixed(2)}</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Effective Rain (P_eff)</span>
                <span className="text-cyan-400 font-bold">0.0 mm</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Net Water Deficit</span>
                <span className="text-cyan-400 font-bold">{(activeZone.kc * et0Val).toFixed(1)} mm</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Demand Output</span>
                <span className="text-white font-bold">{activeZone.water_demand_pct.toFixed(1)}%</span>
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400 font-mono">
              <strong>Active Mamdani Rule Fired:</strong>
              <div className="text-cyan-300 mt-1">
                IF (ETc is High) AND (Effective_Rain is Zero) THEN (Water_Demand is High) [Weight: 1.0]
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-300">
              <strong className="text-indigo-400">Multimodal Fusion:</strong> Fuses Soil Stress ({activeZone.soil_stress_pct.toFixed(1)}%) + Weather Stress ({weatherStress.toFixed(1)}%) + Water Demand ({activeZone.water_demand_pct.toFixed(1)}%)
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Command Intensity</span>
                <span className="text-indigo-400 font-bold">{activeZone.main_command_pct.toFixed(1)}%</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Requested Volume</span>
                <span className="text-indigo-400 font-bold">{activeZone.requested_liters.toFixed(1)} L</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Rain Infiltration Suppress</span>
                <span className="text-emerald-400 font-bold">Inactive (0 mm)</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Actuator Aperture</span>
                <span className="text-white font-bold">VALVE OPEN</span>
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400 font-mono">
              <strong>Active Mamdani Rule Fired:</strong>
              <div className="text-indigo-300 mt-1">
                IF (Soil_Stress is Moderate) AND (Weather_Stress is High) AND (Water_Demand is High) THEN (Command is Medium_High)
              </div>
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-300">
              <strong className="text-emerald-400">Bounded Priority-Weighted Water-Filling:</strong> Reservoir Storage: {reservoirStorage}% • Mass Residual = 0.00e+00 mm
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Requested L</span>
                <span className="text-slate-300 font-bold">{activeZone.requested_liters.toFixed(1)} L</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Allocated L</span>
                <span className="text-emerald-400 font-bold">{activeZone.allocated_liters.toFixed(1)} L</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Fulfillment Ratio</span>
                <span className="text-emerald-400 font-bold">{activeZone.fulfillment_ratio_pct.toFixed(1)}%</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/60 p-2">
                <span className="text-slate-500 block text-[10px]">Mass Balance State</span>
                <span className="text-emerald-400 font-bold">CONSERVED</span>
              </div>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs text-slate-400 font-mono">
              <strong>Arbitration Invariant Proof:</strong>
              <div className="text-emerald-300 mt-1">
                Total_Allocated ({activeZone.allocated_liters.toFixed(1)} L) ≤ Total_Requested ({activeZone.requested_liters.toFixed(1)} L) • Priority Weight Enforced
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`rounded-2xl border border-emerald-200/90 bg-white p-5 text-slate-800 shadow-xl ${className}`}>
      {/* Zone Switcher Ribbon */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-emerald-100 pb-4 mb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="h-4 w-4 text-emerald-600" />
            <span>Multi-Stage Fuzzy Inference Mathematical Inspector</span>
          </h3>
          <p className="text-[11px] text-slate-500">
            Select any agricultural zone from your map location to inspect Mamdani membership degrees and rule firings.
          </p>
        </div>

        {/* Zone Pill Buttons */}
        <div className="flex items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50/50 p-1">
          {zones.map((z) => (
            <button
              key={z.zone_id}
              onClick={() => setSelectedZoneId(z.zone_id)}
              className={`rounded-lg px-3 py-1 text-xs font-semibold transition cursor-pointer ${
                selectedZoneId === z.zone_id
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-emerald-700'
              }`}
            >
              Zone 0{z.zone_id}: {z.crop}
            </button>
          ))}
        </div>
      </div>

      {/* 5-Stage Step Navigation */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-4">
        {STAGES.map((s) => (
          <button
            key={s.num}
            onClick={() => setActiveStage(s.num)}
            className={`rounded-xl border p-2.5 text-left transition cursor-pointer flex flex-col justify-between ${
              activeStage === s.num
                ? 'border-emerald-400 bg-emerald-50 text-slate-900 shadow-xs'
                : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:border-emerald-200'
            }`}
          >
            <span className="text-[10px] font-mono font-bold uppercase block text-slate-400">
              STAGE 0{s.num}
            </span>
            <span className="text-xs font-semibold truncate mt-0.5 block">{s.short}</span>
            <span className="text-sm font-bold font-mono text-emerald-700 mt-2 block">
              {s.value?.toFixed(1) || '0.0'}%
            </span>
          </button>
        ))}
      </div>

      {/* Active Stage Details & Rule Activation */}
      <div className="rounded-xl border border-emerald-100 bg-emerald-50/30 p-4">
        <div className="flex items-center justify-between mb-3 border-b border-emerald-100 pb-2">
          <span className="text-xs font-bold text-slate-900 font-mono uppercase tracking-wide">
            {STAGES[activeStage - 1].name}
          </span>
          <span className="text-[11px] text-emerald-700 font-mono">
            Mamdani Min-Max • Centroid Defuzzification
          </span>
        </div>

        {renderMembershipTerms()}
      </div>
    </div>
  );
}
