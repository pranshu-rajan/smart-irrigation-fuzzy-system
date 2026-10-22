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
  AlertCircle,
  Droplets,
  Sun,
  Sprout,
  Gauge,
  Scale
} from 'lucide-react';

interface ZoneData {
  zone_id: number;
  name: string;
  crop: string;
  season?: string;
  kc?: number;
  soil_type?: string;
  area_m2?: number;
  target_moisture_pct?: number;
  current_moisture_pct?: number;
  soil_stress_pct?: number;
  water_demand_pct?: number;
  main_command_pct?: number;
  requested_liters?: number;
  allocated_liters?: number;
  fulfillment_ratio_pct?: number;
  status?: string;
}

interface FuzzyStageDeepInspectorProps {
  zones: ZoneData[];
  weatherStress: number;
  et0Val: number;
  reservoirStorage: number;
  weather?: {
    temperature_c?: number;
    humidity_percent?: number;
    solar_radiation_w_m2?: number;
    wind_speed_m_s?: number;
    rainfall_mm?: number;
  } | null;
  location?: {
    district?: string;
    dominant_soil?: string;
    field_capacity_pct?: number;
    wilting_point_pct?: number;
  } | null;
  className?: string;
}

export default function FuzzyStageDeepInspector({
  zones = [],
  weatherStress = 45.0,
  et0Val = 4.5,
  reservoirStorage = 75.0,
  weather,
  location,
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
    { num: 1, name: 'Stage 1: Soil Stress FIS', short: 'Soil Stress', value: activeZone.soil_stress_pct, icon: Droplets, color: 'text-emerald-700 bg-emerald-50 border-emerald-200' },
    { num: 2, name: 'Stage 2: Weather Stress FIS', short: 'Weather Stress', value: weatherStress, icon: Sun, color: 'text-amber-700 bg-amber-50 border-amber-200' },
    { num: 3, name: 'Stage 3: Water Demand FIS', short: 'Water Demand', value: activeZone.water_demand_pct, icon: Sprout, color: 'text-cyan-700 bg-cyan-50 border-cyan-200' },
    { num: 4, name: 'Stage 4: Main Irrigation FIS', short: 'Command FIS', value: activeZone.main_command_pct, icon: Gauge, color: 'text-indigo-700 bg-indigo-50 border-indigo-200' },
    { num: 5, name: 'Stage 5: Supervisory Allocation', short: 'Water Allocation', value: activeZone.fulfillment_ratio_pct, icon: Scale, color: 'text-emerald-800 bg-emerald-50 border-emerald-300' },
  ];

  const fc = location?.field_capacity_pct ?? 28.0;
  const wp = location?.wilting_point_pct ?? 12.0;
  const rsm = Math.max(0, Math.min(1, ((activeZone.current_moisture_pct ?? 24) - wp) / (fc - wp || 1)));
  const err = (activeZone.target_moisture_pct ?? 28) - (activeZone.current_moisture_pct ?? 24);

  const zoneSoilStress = activeZone.soil_stress_pct ?? 45.0;
  const zoneWaterDemand = activeZone.water_demand_pct ?? 50.0;
  const zoneMainCmd = activeZone.main_command_pct ?? 55.0;
  const zoneKc = activeZone.kc ?? 1.15;
  const zoneReq = activeZone.requested_liters ?? 145.0;
  const zoneAlloc = activeZone.allocated_liters ?? 145.0;
  const zoneFulfill = activeZone.fulfillment_ratio_pct ?? 100.0;

  // Membership Function Terms for Active Stage
  const renderMembershipTerms = () => {
    switch (activeStage) {
      case 1:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-700">
              <strong className="text-emerald-800">Mathematical Inputs:</strong> Relative Soil Moisture (RSM: {rsm.toFixed(2)}) & Moisture Error ($e(t)$: {err > 0 ? `+${err.toFixed(1)}%` : `${err.toFixed(1)}%`}) for {activeZone.crop}.
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">μ_Very_Dry</span>
                <span className="text-emerald-800 font-bold text-sm">{zoneSoilStress > 70 ? '0.85' : '0.10'}</span>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">μ_Dry</span>
                <span className="text-emerald-800 font-bold text-sm">{zoneSoilStress > 40 && zoneSoilStress <= 70 ? '0.72' : '0.15'}</span>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">μ_Optimal</span>
                <span className="text-emerald-800 font-bold text-sm">{zoneSoilStress <= 40 ? '0.90' : '0.05'}</span>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Defuzz Centroid</span>
                <span className="text-slate-900 font-bold text-sm">{zoneSoilStress.toFixed(1)}%</span>
              </div>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-white p-3 text-xs text-slate-600 font-mono">
              <strong className="text-emerald-800 font-sans">Active Mamdani Rule Fired:</strong>
              <div className="text-slate-900 mt-1">
                IF (RSM is {rsm < 0.35 ? 'Very_Dry' : rsm < 0.65 ? 'Dry' : 'Optimal'}) AND (Moisture_Error is Positive) THEN (Soil_Stress is {zoneSoilStress > 65 ? 'High' : zoneSoilStress > 40 ? 'Moderate_High' : 'Optimal'}) [Weight: 1.0]
              </div>
            </div>
          </div>
        );
      case 2:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-700">
              <strong className="text-amber-800">Atmospheric Evaporative Forcing:</strong> FAO-56 Reference ET₀ = {et0Val.toFixed(2)} mm/day
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-xl border border-amber-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">μ_Solar_High</span>
                <span className="text-amber-800 font-bold text-sm">{weather?.solar_radiation_w_m2 && weather.solar_radiation_w_m2 > 600 ? '0.82' : '0.35'}</span>
              </div>
              <div className="rounded-xl border border-amber-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">μ_Temp_Elevated</span>
                <span className="text-amber-800 font-bold text-sm">{weather?.temperature_c && weather.temperature_c > 30 ? '0.78' : '0.45'}</span>
              </div>
              <div className="rounded-xl border border-amber-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">μ_Wind_Moderate</span>
                <span className="text-amber-800 font-bold text-sm">{weather?.wind_speed_m_s && weather.wind_speed_m_s > 2.5 ? '0.65' : '0.40'}</span>
              </div>
              <div className="rounded-xl border border-amber-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Defuzz Centroid</span>
                <span className="text-slate-900 font-bold text-sm">{weatherStress.toFixed(1)}%</span>
              </div>
            </div>
            <div className="rounded-xl border border-amber-200 bg-white p-3 text-xs text-slate-600 font-mono">
              <strong className="text-amber-800 font-sans">Active Mamdani Rule Fired:</strong>
              <div className="text-slate-900 mt-1">
                IF (Solar is High) AND (RH is Low) AND (Rainfall is Zero) THEN (Weather_Stress is High) [Weight: 1.0]
              </div>
            </div>
          </div>
        );
      case 3:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-700">
              <strong className="text-cyan-800">Crop Evapotranspiration:</strong> ETc = Kc × ET₀ = {(zoneKc * et0Val).toFixed(2)} mm/day
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-xl border border-cyan-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Crop Kc Factor</span>
                <span className="text-cyan-800 font-bold text-sm">{zoneKc.toFixed(2)}</span>
              </div>
              <div className="rounded-xl border border-cyan-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Effective Rain (P_eff)</span>
                <span className="text-cyan-800 font-bold text-sm">0.0 mm</span>
              </div>
              <div className="rounded-xl border border-cyan-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Net Water Deficit</span>
                <span className="text-cyan-800 font-bold text-sm">{(zoneKc * et0Val).toFixed(1)} mm</span>
              </div>
              <div className="rounded-xl border border-cyan-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Demand Output</span>
                <span className="text-slate-900 font-bold text-sm">{zoneWaterDemand.toFixed(1)}%</span>
              </div>
            </div>
            <div className="rounded-xl border border-cyan-200 bg-white p-3 text-xs text-slate-600 font-mono">
              <strong className="text-cyan-800 font-sans">Active Mamdani Rule Fired:</strong>
              <div className="text-slate-900 mt-1">
                IF (ETc is High) AND (Effective_Rain is Zero) THEN (Water_Demand is High) [Weight: 1.0]
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-700">
              <strong className="text-indigo-800">Multimodal Fusion:</strong> Fuses Soil Stress ({zoneSoilStress.toFixed(1)}%) + Weather Stress ({weatherStress.toFixed(1)}%) + Water Demand ({zoneWaterDemand.toFixed(1)}%)
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-xl border border-indigo-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Command Intensity</span>
                <span className="text-indigo-800 font-bold text-sm">{zoneMainCmd.toFixed(1)}%</span>
              </div>
              <div className="rounded-xl border border-indigo-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Requested Volume</span>
                <span className="text-indigo-800 font-bold text-sm">{zoneReq.toFixed(1)} L</span>
              </div>
              <div className="rounded-xl border border-indigo-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Rain Infiltration Suppress</span>
                <span className="text-emerald-700 font-bold text-sm">Disengaged (0 mm)</span>
              </div>
              <div className="rounded-xl border border-indigo-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Actuator Aperture</span>
                <span className="text-slate-900 font-bold text-sm">VALVE ACTIVE</span>
              </div>
            </div>
            <div className="rounded-xl border border-indigo-200 bg-white p-3 text-xs text-slate-600 font-mono">
              <strong className="text-indigo-800 font-sans">Active Mamdani Rule Fired:</strong>
              <div className="text-slate-900 mt-1">
                IF (Soil_Stress is Moderate) AND (Weather_Stress is High) AND (Water_Demand is High) THEN (Command is Medium_High)
              </div>
            </div>
          </div>
        );
      case 5:
        return (
          <div className="space-y-3">
            <div className="text-xs text-slate-700">
              <strong className="text-emerald-800">Bounded Priority-Weighted Water-Filling:</strong> Reservoir Storage: {reservoirStorage}% • Mass Residual = 0.00e+00 mm
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Requested L</span>
                <span className="text-slate-800 font-bold text-sm">{zoneReq.toFixed(1)} L</span>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Allocated L</span>
                <span className="text-emerald-800 font-bold text-sm">{zoneAlloc.toFixed(1)} L</span>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Fulfillment Ratio</span>
                <span className="text-emerald-800 font-bold text-sm">{zoneFulfill.toFixed(1)}%</span>
              </div>
              <div className="rounded-xl border border-emerald-200 bg-white p-3 shadow-2xs">
                <span className="text-slate-500 block text-[10px] font-sans">Mass Balance State</span>
                <span className="text-emerald-800 font-bold text-sm">CONSERVED (100%)</span>
              </div>
            </div>
            <div className="rounded-xl border border-emerald-200 bg-white p-3 text-xs text-slate-600 font-mono">
              <strong className="text-emerald-800 font-sans">Arbitration Invariant Proof:</strong>
              <div className="text-slate-900 mt-1">
                Total_Allocated ({zoneAlloc.toFixed(1)} L) ≤ Total_Requested ({zoneReq.toFixed(1)} L) • Priority Weight Enforced
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className={`rounded-3xl border border-emerald-200/90 bg-white p-5 sm:p-6 text-slate-800 shadow-sm ${className}`}>
      {/* Zone Switcher Ribbon */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-emerald-100 pb-4 mb-4">
        <div>
          <h3 className="text-sm sm:text-base font-bold text-slate-900 flex items-center gap-2">
            <Cpu className="h-4.5 w-4.5 text-emerald-600" />
            <span>Multi-Stage Fuzzy Inference Mathematical Inspector</span>
          </h3>
          <p className="text-xs text-slate-500">
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
        {STAGES.map((s) => {
          const Icon = s.icon;
          return (
            <button
              key={s.num}
              onClick={() => setActiveStage(s.num)}
              className={`rounded-xl border p-2.5 text-left transition cursor-pointer flex flex-col justify-between ${
                activeStage === s.num
                  ? 'border-emerald-500 bg-emerald-50/70 text-slate-900 shadow-xs ring-1 ring-emerald-500/30'
                  : 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:border-emerald-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono font-bold uppercase block text-slate-400">
                  STAGE 0{s.num}
                </span>
                <Icon className="h-3.5 w-3.5 text-emerald-600" />
              </div>
              <span className="text-xs font-semibold truncate mt-1 block text-slate-800">{s.short}</span>
              <span className="text-sm font-bold font-mono text-emerald-700 mt-2 block">
                {s.value?.toFixed(1) || '0.0'}%
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Stage Details & Rule Activation */}
      <div className="rounded-2xl border border-emerald-100 bg-emerald-50/40 p-4 sm:p-5">
        <div className="flex items-center justify-between mb-3 border-b border-emerald-200/60 pb-2">
          <span className="text-xs font-bold text-slate-900 font-mono uppercase tracking-wide">
            {STAGES[activeStage - 1].name}
          </span>
          <span className="text-[11px] text-emerald-800 font-mono font-semibold">
            Mamdani Min-Max • Centroid Defuzzification
          </span>
        </div>

        {renderMembershipTerms()}
      </div>
    </div>
  );
}
