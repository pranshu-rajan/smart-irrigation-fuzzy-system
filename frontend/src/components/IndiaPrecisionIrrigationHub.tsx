'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import {
  MapPin,
  Search,
  CloudSun,
  Droplets,
  Wind,
  Sun,
  Activity,
  Layers,
  Cpu,
  ShieldCheck,
  Sparkles,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  Compass,
  Sprout,
  TrendingDown,
} from 'lucide-react';

interface IndiaDistrict {
  district: string;
  state: string;
  agro_climatic_zone: string;
  latitude: number;
  longitude: number;
}

interface IndiaEvaluationData {
  location: {
    district: string;
    state: string;
    latitude: number;
    longitude: number;
    elevation_m: number;
    agro_climatic_zone: string;
    zone_number: number;
    dominant_soil: string;
    field_capacity_pct: number;
    wilting_point_pct: number;
    saturation_pct: number;
    primary_kharif_crop: string;
    primary_rabi_crop: string;
    primary_zaid_crop: string;
  };
  weather: {
    temperature_c: number;
    humidity_percent: number;
    solar_radiation_w_m2: number;
    wind_speed_m_s: number;
    rainfall_mm: number;
    atmospheric_pressure_kpa: number;
    source: string;
    timestamp: string;
    is_live: boolean;
  };
  physics_agronomy: {
    et0_fao56_mm_day: number;
    effective_rainfall_mm: number;
    vapor_pressure_deficit_kpa: number;
    active_season: string;
    elevation_m: number;
    soil_orders: string;
  };
  fuzzy_stages: {
    stage1_soil_stress_pct: number;
    stage2_weather_stress_pct: number;
    stage3_water_demand_pct: number;
    stage4_main_command_pct: number;
    stage5_water_allocation_active: boolean;
  };
  zone_allocations: Array<{
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
  }>;
  total_requested_liters: number;
  total_allocated_liters: number;
  available_supply_liters: number;
  is_supply_constrained: boolean;
  hourly_telemetry: Array<{
    hour: number;
    time_label: string;
    temperature_c: number;
    solar_radiation_w_m2: number;
    rainfall_mm: number;
    et0_mm: number;
    zone1_moisture: number;
    zone2_moisture: number;
    zone3_moisture: number;
    irrigation_liters: number;
  }>;
  decision_summary: string;
  water_savings_vs_onoff_pct: number;
  water_savings_vs_pid_pct: number;
}

const QUICK_REGIONS = [
  { name: 'Ludhiana', label: '🌾 Ludhiana (Punjab)', sub: 'Alluvial • Wheat/Rice' },
  { name: 'Pune', label: '🍇 Pune (Maharashtra)', sub: 'Black Soil • Sugarcane/Veg' },
  { name: 'Varanasi', label: '🌽 Varanasi (UP)', sub: 'Gangetic Loam • Wheat/Paddy' },
  { name: 'Mandya', label: '🌿 Mandya (Karnataka)', sub: 'Red Loam • Paddy/Ragi' },
  { name: 'Guntur', label: '🌶️ Guntur (Andhra)', sub: 'Black Vertisol • Chilli/Cotton' },
  { name: 'Jaipur', label: '🏜️ Jaipur (Rajasthan)', sub: 'Arid Sand • Mustard/Bajra' },
];

export default function IndiaPrecisionIrrigationHub() {
  const [searchQuery, setSearchQuery] = useState('Ludhiana');
  const [reservoirStorage, setReservoirStorage] = useState(65.0);
  const [loading, setLoading] = useState(false);
  const [evalData, setEvalData] = useState<IndiaEvaluationData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [districtsList, setDistrictsList] = useState<IndiaDistrict[]>([]);

  // Load districts list on mount
  useEffect(() => {
    async function loadDistricts() {
      try {
        const list = await api.getIndiaDistricts();
        setDistrictsList(list);
      } catch (err) {
        // Fallback gracefully
      }
    }
    loadDistricts();
    handleExecute('Ludhiana');
  }, []);

  const handleExecute = async (queryToUse?: string) => {
    const q = (queryToUse || searchQuery).trim();
    if (!q) return;

    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await api.evaluateIndiaLocation({
        location_query: q,
        reservoir_storage_pct: reservoirStorage,
      });
      setEvalData(resp);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to evaluate national fuzzy architecture for this location.');
    } finally {
      setLoading(false);
    }
  };

  const getLevelBadge = (val: number) => {
    if (val < 25) return { text: 'LOW', bg: 'bg-emerald-950/80 border-emerald-500/40 text-emerald-400' };
    if (val < 55) return { text: 'MODERATE', bg: 'bg-blue-950/80 border-blue-500/40 text-blue-400' };
    if (val < 75) return { text: 'HIGH', bg: 'bg-amber-950/80 border-amber-500/40 text-amber-400' };
    return { text: 'CRITICAL', bg: 'bg-rose-950/80 border-rose-500/40 text-rose-400' };
  };

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl border border-emerald-500/30 bg-gradient-to-r from-emerald-950/60 via-slate-900 to-indigo-950/50 p-6 shadow-2xl backdrop-blur-xl">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-400 mb-2">
              <Compass className="h-3.5 w-3.5 animate-spin" style={{ animationDuration: '8s' }} />
              National Precision Agriculture • Real-Time India Infrastructure
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
              India Real-Time Multi-Zone Fuzzy Irrigation Architecture
            </h2>
            <p className="mt-1 text-sm text-slate-300 max-w-3xl">
              Enter any Indian district, village, city, or PIN code. The system executes live meteorological ingestion via Open-Meteo, 
              couples ICAR 15 Agro-Climatic & NBSS soil physics, and executes the complete 5-stage closed-loop Mamdani Fuzzy Control Cascade.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <span className="block text-xs text-slate-400">Mass Conservation</span>
              <span className="text-sm font-semibold text-emerald-400">|Residual| &lt; 10⁻⁶ mm</span>
            </div>
            <div className="h-10 w-px bg-slate-700 hidden sm:block" />
            <div className="text-right hidden sm:block">
              <span className="block text-xs text-slate-400">Fuzzy Inference</span>
              <span className="text-sm font-semibold text-cyan-400">162 Mamdani Rules</span>
            </div>
          </div>
        </div>
      </div>

      {/* Location Input & Fast Selectors */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-emerald-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
              placeholder="Enter any Indian district, city, state, or PIN code (e.g. Pune, Ludhiana, 141004)..."
              className="w-full rounded-lg border border-slate-700 bg-slate-950/80 pl-11 pr-4 py-3 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-slate-800 bg-slate-950 text-xs">
              <Droplets className="h-4 w-4 text-cyan-400" />
              <span className="text-slate-400">Reservoir:</span>
              <input
                type="number"
                min="10"
                max="100"
                value={reservoirStorage}
                onChange={(e) => setReservoirStorage(Number(e.target.value))}
                className="w-14 bg-slate-900 border border-slate-700 rounded px-1.5 py-0.5 text-center text-white font-mono"
              />
              <span className="text-slate-400">%</span>
            </div>

            <button
              onClick={() => handleExecute()}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 px-5 py-3 text-sm font-semibold text-white transition-all shadow-lg shadow-emerald-950/40"
            >
              {loading ? (
                <>
                  <RotateCw className="h-4 w-4 animate-spin" />
                  Evaluating Architecture...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-white" />
                  Evaluate Location
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Location Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-slate-800/60">
          <span className="text-xs font-semibold text-slate-400 mr-1">Quick Benchmarks:</span>
          {QUICK_REGIONS.map((item) => (
            <button
              key={item.name}
              onClick={() => {
                setSearchQuery(item.name);
                handleExecute(item.name);
              }}
              className={`rounded-lg border px-3 py-1.5 text-xs text-left transition-all ${
                searchQuery.toLowerCase() === item.name.toLowerCase()
                  ? 'border-emerald-500 bg-emerald-950/40 text-emerald-300 font-semibold shadow-sm'
                  : 'border-slate-800 bg-slate-950/60 text-slate-300 hover:border-slate-700 hover:text-white'
              }`}
            >
              <div className="font-medium">{item.label}</div>
              <div className="text-[10px] text-slate-400">{item.sub}</div>
            </button>
          ))}
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-rose-500/40 bg-rose-950/40 p-4 text-sm text-rose-300 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 text-rose-400" />
          <span>{errorMsg}</span>
        </div>
      )}

      {evalData && (
        <div className="space-y-6">
          {/* Top Location & Agro-Climatic Profile */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-emerald-400" /> Resolved Indian Region
              </div>
              <div className="text-lg font-bold text-white mt-1">
                {evalData.location.district}, {evalData.location.state}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                {evalData.location.latitude.toFixed(2)}°N, {evalData.location.longitude.toFixed(2)}°E • {evalData.location.elevation_m}m elevation
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Compass className="h-3.5 w-3.5 text-indigo-400" /> ICAR Agro-Climatic Zone
              </div>
              <div className="text-sm font-bold text-indigo-300 mt-1 line-clamp-1">
                Zone #{evalData.location.zone_number}: {evalData.location.agro_climatic_zone}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                Seasonal Cycle: <span className="text-emerald-400 font-medium">{evalData.physics_agronomy.active_season}</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <Sprout className="h-3.5 w-3.5 text-amber-400" /> Dominant Regional Soil
              </div>
              <div className="text-sm font-bold text-amber-300 mt-1">
                {evalData.location.dominant_soil}
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                FC: <span className="text-white font-mono">{evalData.location.field_capacity_pct}%</span> • WP: <span className="text-white font-mono">{evalData.location.wilting_point_pct}%</span>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 shadow">
              <div className="text-xs text-slate-400 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-cyan-400" /> Benchmark Savings
              </div>
              <div className="text-base font-bold text-emerald-400 mt-1 flex items-center gap-2">
                <span>+{evalData.water_savings_vs_onoff_pct}% vs On-Off</span>
              </div>
              <div className="text-xs text-slate-400 mt-0.5">
                <span>+{evalData.water_savings_vs_pid_pct}% vs PID Controller</span>
              </div>
            </div>
          </div>

          {/* Live Meteorology & FAO-56 Physics Strip */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <CloudSun className="h-5 w-5 text-amber-400" />
                <h3 className="font-semibold text-white text-sm sm:text-base">
                  Live Meteorological Readings (Open-Meteo High-Resolution Feed)
                </h3>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border border-emerald-500/40 bg-emerald-950/60 text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                {evalData.weather.is_live ? 'LIVE SATELLITE/NWP' : 'IMD CLIMATOLOGICAL'} • {evalData.weather.timestamp}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-1">
              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-center">
                <span className="text-[11px] text-slate-400 block">Temperature</span>
                <span className="text-xl font-bold font-mono text-amber-400">{evalData.weather.temperature_c}°C</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-center">
                <span className="text-[11px] text-slate-400 block">Humidity</span>
                <span className="text-xl font-bold font-mono text-cyan-400">{evalData.weather.humidity_percent}%</span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-center">
                <span className="text-[11px] text-slate-400 block">Solar Radiation</span>
                <span className="text-xl font-bold font-mono text-yellow-300">{evalData.weather.solar_radiation_w_m2} <span className="text-xs font-normal">W/m²</span></span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-center">
                <span className="text-[11px] text-slate-400 block">2m Wind Speed</span>
                <span className="text-xl font-bold font-mono text-indigo-300">{evalData.weather.wind_speed_m_s} <span className="text-xs font-normal">m/s</span></span>
              </div>
              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-center">
                <span className="text-[11px] text-slate-400 block">Rainfall</span>
                <span className="text-xl font-bold font-mono text-blue-400">{evalData.weather.rainfall_mm} <span className="text-xs font-normal">mm</span></span>
              </div>
              <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/30 p-3 text-center">
                <span className="text-[11px] text-emerald-400 block font-semibold">FAO-56 ET₀</span>
                <span className="text-xl font-bold font-mono text-emerald-300">{evalData.physics_agronomy.et0_fao56_mm_day} <span className="text-xs font-normal">mm/d</span></span>
              </div>
            </div>
          </div>

          {/* 5-Stage Fuzzy Inference Architecture Cascade */}
          <div className="rounded-xl border border-indigo-500/30 bg-slate-900/90 p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-indigo-400" />
                <h3 className="font-semibold text-white">
                  5-Stage Hierarchical Mamdani Fuzzy Control Cascade (162 Rules)
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">Min-Max Implication • Centroid Defuzzification</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {/* Stage 1 */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Stage 1 • FIS 1</div>
                <div className="text-xs text-slate-400">Root-Zone Soil Stress</div>
                <div className="text-2xl font-bold font-mono text-white">
                  {evalData.fuzzy_stages.stage1_soil_stress_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage1_soil_stress_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage1_soil_stress_pct).text}
                </div>
                <div className="text-[10px] text-slate-400 pt-1">
                  Inputs: RSM + Moisture Tracking Error e(t) [25 Rules]
                </div>
              </div>

              {/* Stage 2 */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider">Stage 2 • FIS 2</div>
                <div className="text-xs text-slate-400">Atmospheric Stress</div>
                <div className="text-2xl font-bold font-mono text-white">
                  {evalData.fuzzy_stages.stage2_weather_stress_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage2_weather_stress_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage2_weather_stress_pct).text}
                </div>
                <div className="text-[10px] text-slate-400 pt-1">
                  Inputs: T + RH + Rs + u₂ + Rain [34 Rules]
                </div>
              </div>

              {/* Stage 3 */}
              <div className="rounded-xl border border-slate-800 bg-slate-950/80 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider">Stage 3 • FIS 3</div>
                <div className="text-xs text-slate-400">Crop Water Demand</div>
                <div className="text-2xl font-bold font-mono text-white">
                  {evalData.fuzzy_stages.stage3_water_demand_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage3_water_demand_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage3_water_demand_pct).text}
                </div>
                <div className="text-[10px] text-slate-400 pt-1">
                  Inputs: ETc + Deficit + Peff [39 Rules]
                </div>
              </div>

              {/* Stage 4 */}
              <div className="rounded-xl border border-indigo-500/40 bg-indigo-950/20 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-indigo-400 uppercase tracking-wider">Stage 4 • FIS 4</div>
                <div className="text-xs text-slate-400">Supervisory Valve Command</div>
                <div className="text-2xl font-bold font-mono text-indigo-300">
                  {evalData.fuzzy_stages.stage4_main_command_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage4_main_command_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage4_main_command_pct).text}
                </div>
                <div className="text-[10px] text-slate-400 pt-1">
                  4-Layer Protection Kernel [32 Rules]
                </div>
              </div>

              {/* Stage 5 */}
              <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/20 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider">Stage 5 • FIS 5</div>
                <div className="text-xs text-slate-400">Bounded Water-Filling</div>
                <div className="text-2xl font-bold font-mono text-emerald-300">
                  {evalData.total_allocated_liters.toLocaleString()} L
                </div>
                <div className="text-[10px] font-mono text-emerald-400">
                  {evalData.is_supply_constrained ? 'RATIONED SUPPLY' : 'OPTIMAL SUPPLY'}
                </div>
                <div className="text-[10px] text-slate-400 pt-1">
                  Enforces Σ Alloc ≤ Available [32 Rules]
                </div>
              </div>
            </div>
          </div>

          {/* Multi-Zone Bounded Allocation Table */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/90 p-5 shadow-lg space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-semibold text-white flex items-center gap-2">
                  <Layers className="h-4 w-4 text-emerald-400" />
                  Multi-Zone Agricultural Plot Allocations ({evalData.location.district})
                </h3>
                <p className="text-xs text-slate-400">
                  Arbitrating limited local reservoir ({evalData.available_supply_liters.toLocaleString()} L available) across competing Indian crop zones.
                </p>
              </div>
              <div className="text-right text-xs">
                <span className="text-slate-400">Total Requested: </span>
                <span className="font-mono text-white font-bold">{evalData.total_requested_liters.toLocaleString()} L</span>
                <span className="text-slate-400 ml-2">Total Granted: </span>
                <span className="font-mono text-emerald-400 font-bold">{evalData.total_allocated_liters.toLocaleString()} L</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-400">
                    <th className="py-2 px-3">Zone / Crop</th>
                    <th className="py-2 px-3">Season & Kc</th>
                    <th className="py-2 px-3">Moisture State</th>
                    <th className="py-2 px-3">Soil Stress</th>
                    <th className="py-2 px-3">Fuzzy Cmd</th>
                    <th className="py-2 px-3">Requested</th>
                    <th className="py-2 px-3">Allocated</th>
                    <th className="py-2 px-3">Fulfillment</th>
                    <th className="py-2 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {evalData.zone_allocations.map((z) => (
                    <tr key={z.zone_id} className="hover:bg-slate-800/30">
                      <td className="py-3 px-3 font-sans font-semibold text-white">
                        {z.name}
                        <span className="block text-[10px] text-slate-400 font-normal">{z.area_m2} m² • {z.soil_type}</span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-slate-300 font-sans">{z.crop}</span>
                        <span className="block text-[10px] text-indigo-400">Kc = {z.kc} ({z.season})</span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-white">{z.current_moisture_pct}%</span>
                        <span className="text-slate-500 text-[10px] block">Target: {z.target_moisture_pct}%</span>
                      </td>
                      <td className="py-3 px-3 text-amber-300">{z.soil_stress_pct}%</td>
                      <td className="py-3 px-3 text-indigo-300">{z.main_command_pct}%</td>
                      <td className="py-3 px-3 text-slate-300">{z.requested_liters} L</td>
                      <td className="py-3 px-3 text-emerald-400 font-bold">{z.allocated_liters} L</td>
                      <td className="py-3 px-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          z.fulfillment_ratio_pct >= 99 ? 'bg-emerald-950 text-emerald-400' : 'bg-amber-950 text-amber-400'
                        }`}>
                          {z.fulfillment_ratio_pct}%
                        </span>
                      </td>
                      <td className="py-3 px-3 font-sans text-[11px] font-medium text-slate-300">{z.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Decision Summary Callout */}
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 text-xs text-slate-300 flex items-start gap-3">
            <Sparkles className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-white block mb-0.5">Automated Agronomic Decision Rationale:</span>
              <p className="leading-relaxed">{evalData.decision_summary}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
