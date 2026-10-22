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
  Globe,
  Brain,
  ExternalLink,
  ChevronDown,
  ChevronUp,
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
  { name: 'Ludhiana', label: 'Ludhiana (Punjab)', sub: 'Alluvial • Wheat/Rice' },
  { name: 'Pune', label: 'Pune (Maharashtra)', sub: 'Black Soil • Sugarcane/Veg' },
  { name: 'Varanasi', label: 'Varanasi (UP)', sub: 'Gangetic Loam • Wheat/Paddy' },
  { name: 'Mandya', label: 'Mandya (Karnataka)', sub: 'Red Loam • Paddy/Ragi' },
  { name: 'Guntur', label: 'Guntur (Andhra)', sub: 'Black Vertisol • Chilli/Cotton' },
  { name: 'Jaipur', label: 'Jaipur (Rajasthan)', sub: 'Arid Sand • Mustard/Bajra' },
];

export default function IndiaPrecisionIrrigationHub() {
  const [searchQuery, setSearchQuery] = useState('Ludhiana');
  const [reservoirStorage, setReservoirStorage] = useState(65.0);
  const [loading, setLoading] = useState(false);
  const [evalData, setEvalData] = useState<IndiaEvaluationData | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [districtsList, setDistrictsList] = useState<IndiaDistrict[]>([]);
  const [advisoryLoading, setAdvisoryLoading] = useState(false);
  const [advisoryData, setAdvisoryData] = useState<{
    district: string;
    state: string;
    crop: string;
    advisory_summary: string;
    critical_farming_tips: string[];
    model_name: string;
    reasoning?: string;
    web_sources: Array<{ title: string; url: string; content: string }>;
  } | null>(null);
  const [showReasoning, setShowReasoning] = useState(false);

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
    setAdvisoryData(null);
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

  const handleFetchAgrometAdvisory = async () => {
    if (!evalData) return;
    setAdvisoryLoading(true);
    try {
      const crop = evalData.location.primary_rabi_crop || evalData.location.primary_kharif_crop || 'Wheat';
      const res = await api.getIndiaAgrometAdvisory({
        district: evalData.location.district,
        state: evalData.location.state,
        crop: crop,
        soil_type: evalData.location.dominant_soil,
        irrigation_depth_mm: evalData.fuzzy_stages.stage3_water_demand_pct || 0,
        et0_mm_day: evalData.physics_agronomy.et0_fao56_mm_day,
        current_temp_c: evalData.weather.temperature_c,
        current_humidity_pct: evalData.weather.humidity_percent,
      });
      setAdvisoryData(res);
    } catch (err: any) {
      console.error('Failed to fetch agromet advisory:', err);
    } finally {
      setAdvisoryLoading(false);
    }
  };

  const getLevelBadge = (val: number) => {
    if (val < 25) return { text: 'LOW', bg: 'bg-emerald-50 border-emerald-200 text-emerald-800' };
    if (val < 55) return { text: 'MODERATE', bg: 'bg-blue-50 border-blue-200 text-blue-800' };
    if (val < 75) return { text: 'HIGH', bg: 'bg-amber-50 border-amber-200 text-amber-800' };
    return { text: 'CRITICAL', bg: 'bg-rose-50 border-rose-200 text-rose-800' };
  };

  return (
    <div className="space-y-6">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl border border-emerald-200/90 bg-gradient-to-r from-emerald-50 via-teal-50/50 to-white p-6 shadow-sm">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-100/70 px-3 py-1 text-xs font-semibold text-emerald-800 mb-2">
              <Compass className="h-3.5 w-3.5 animate-spin text-emerald-700" style={{ animationDuration: '8s' }} />
              National Precision Agriculture • Real-Time India Infrastructure
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              India Real-Time Multi-Zone Fuzzy Irrigation Architecture
            </h2>
            <p className="mt-1 text-sm text-slate-600 max-w-3xl">
              Enter any Indian district, village, city, or PIN code. The system executes live meteorological ingestion via Open-Meteo, 
              couples ICAR 15 Agro-Climatic & NBSS soil physics, and executes the complete 5-stage closed-loop Mamdani Fuzzy Control Cascade.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <span className="block text-xs text-slate-500">Mass Conservation</span>
              <span className="text-sm font-semibold text-emerald-700">|Residual| &lt; 10⁻⁶ mm</span>
            </div>
            <div className="h-10 w-px bg-emerald-200 hidden sm:block" />
            <div className="text-right hidden sm:block">
              <span className="block text-xs text-slate-500">Fuzzy Inference</span>
              <span className="text-sm font-semibold text-teal-700">162 Mamdani Rules</span>
            </div>
          </div>
        </div>
      </div>

      {/* Location Input & Fast Selectors */}
      <div className="rounded-xl border border-emerald-200 bg-white p-5 shadow-sm space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="relative flex-1">
            <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-emerald-600" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleExecute()}
              placeholder="Enter any Indian district, city, state, or PIN code (e.g. Pune, Ludhiana, 141004)..."
              className="w-full rounded-lg border border-emerald-200 bg-emerald-50/30 pl-11 pr-4 py-3 text-sm text-slate-900 placeholder-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-emerald-200 bg-emerald-50/50 text-xs">
              <Droplets className="h-4 w-4 text-cyan-600" />
              <span className="text-slate-600">Reservoir:</span>
              <input
                type="number"
                min="10"
                max="100"
                value={reservoirStorage}
                onChange={(e) => setReservoirStorage(Number(e.target.value))}
                className="w-14 bg-white border border-emerald-200 rounded px-1.5 py-0.5 text-center text-slate-900 font-mono shadow-2xs"
              />
              <span className="text-slate-500">%</span>
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
          {/* Top Location & Agro-Climatic Profile */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-emerald-200 bg-white p-4 shadow-xs">
              <div className="text-xs text-slate-500 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-emerald-600" /> Resolved Indian Region
              </div>
              <div className="text-lg font-bold text-slate-900 mt-1">
                {evalData.location.district}, {evalData.location.state}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                {evalData.location.latitude.toFixed(2)}°N, {evalData.location.longitude.toFixed(2)}°E • {evalData.location.elevation_m}m elevation
              </div>
            </div>

            <div className="rounded-xl border border-emerald-200 bg-white p-4 shadow-xs">
              <div className="text-xs text-slate-500 flex items-center gap-1.5">
                <Compass className="h-3.5 w-3.5 text-teal-600" /> ICAR Agro-Climatic Zone
              </div>
              <div className="text-sm font-bold text-teal-800 mt-1 line-clamp-1">
                Zone #{evalData.location.zone_number}: {evalData.location.agro_climatic_zone}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                Seasonal Cycle: <span className="text-emerald-700 font-medium">{evalData.physics_agronomy.active_season}</span>
              </div>
            </div>

            <div className="rounded-xl border border-emerald-200 bg-white p-4 shadow-xs">
              <div className="text-xs text-slate-500 flex items-center gap-1.5">
                <Sprout className="h-3.5 w-3.5 text-amber-600" /> Dominant Regional Soil
              </div>
              <div className="text-sm font-bold text-slate-900 mt-1">
                {evalData.location.dominant_soil}
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                FC: <span className="text-emerald-700 font-mono font-bold">{evalData.location.field_capacity_pct}%</span> • WP: <span className="text-rose-600 font-mono font-bold">{evalData.location.wilting_point_pct}%</span>
              </div>
            </div>

            <div className="rounded-xl border border-emerald-200 bg-white p-4 shadow-xs">
              <div className="text-xs text-slate-500 flex items-center gap-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" /> Benchmark Savings
              </div>
              <div className="text-base font-bold text-emerald-700 mt-1 flex items-center gap-2">
                <span>+{evalData.water_savings_vs_onoff_pct}% vs On-Off</span>
              </div>
              <div className="text-xs text-slate-500 mt-0.5">
                <span>+{evalData.water_savings_vs_pid_pct}% vs PID Controller</span>
              </div>
            </div>
          </div>

          {/* Live Meteorology & FAO-56 Physics Strip */}
          <div className="rounded-xl border border-emerald-200 bg-white p-5 shadow-xs space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-emerald-100 pb-3">
              <div className="flex items-center gap-2">
                <CloudSun className="h-5 w-5 text-amber-500" />
                <h3 className="font-semibold text-slate-900 text-sm sm:text-base">
                  Live Meteorological Readings (Open-Meteo High-Resolution Feed)
                </h3>
              </div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium border border-emerald-200 bg-emerald-50 text-emerald-800">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                {evalData.weather.is_live ? 'LIVE SATELLITE/NWP' : 'IMD CLIMATOLOGICAL'} • {evalData.weather.timestamp}
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 pt-1">
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/30 p-3 text-center">
                <span className="text-[11px] text-slate-500 block">Temperature</span>
                <span className="text-xl font-bold font-mono text-amber-700">{evalData.weather.temperature_c}°C</span>
              </div>
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/30 p-3 text-center">
                <span className="text-[11px] text-slate-500 block">Humidity</span>
                <span className="text-xl font-bold font-mono text-teal-700">{evalData.weather.humidity_percent}%</span>
              </div>
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/30 p-3 text-center">
                <span className="text-[11px] text-slate-500 block">Solar Radiation</span>
                <span className="text-xl font-bold font-mono text-amber-600">{evalData.weather.solar_radiation_w_m2} <span className="text-xs font-normal">W/m²</span></span>
              </div>
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/30 p-3 text-center">
                <span className="text-[11px] text-slate-500 block">2m Wind Speed</span>
                <span className="text-xl font-bold font-mono text-indigo-700">{evalData.weather.wind_speed_m_s} <span className="text-xs font-normal">m/s</span></span>
              </div>
              <div className="rounded-lg border border-emerald-100 bg-emerald-50/30 p-3 text-center">
                <span className="text-[11px] text-slate-500 block">Rainfall</span>
                <span className="text-xl font-bold font-mono text-blue-700">{evalData.weather.rainfall_mm} <span className="text-xs font-normal">mm</span></span>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-100/60 p-3 text-center">
                <span className="text-[11px] text-emerald-800 block font-semibold">FAO-56 ET₀</span>
                <span className="text-xl font-bold font-mono text-emerald-800">{evalData.physics_agronomy.et0_fao56_mm_day} <span className="text-xs font-normal">mm/d</span></span>
              </div>
            </div>
          </div>

          {/* 5-Stage Fuzzy Inference Architecture Cascade */}
          <div className="rounded-xl border border-emerald-200 bg-white p-5 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-emerald-100 pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="h-5 w-5 text-emerald-600" />
                <h3 className="font-semibold text-slate-900">
                  5-Stage Hierarchical Mamdani Fuzzy Control Cascade (162 Rules)
                </h3>
              </div>
              <span className="text-xs text-slate-500 font-mono">Min-Max Implication • Centroid Defuzzification</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {/* Stage 1 */}
              <div className="rounded-xl border border-emerald-100 bg-emerald-50/30 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wider">Stage 1 • FIS 1</div>
                <div className="text-xs text-slate-500">Root-Zone Soil Stress</div>
                <div className="text-2xl font-bold font-mono text-slate-900">
                  {evalData.fuzzy_stages.stage1_soil_stress_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage1_soil_stress_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage1_soil_stress_pct).text}
                </div>
                <div className="text-[10px] text-slate-500 pt-1">
                  Inputs: RSM + Moisture Tracking Error e(t) [25 Rules]
                </div>
              </div>

              {/* Stage 2 */}
              <div className="rounded-xl border border-amber-100 bg-amber-50/30 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-amber-700 uppercase tracking-wider">Stage 2 • FIS 2</div>
                <div className="text-xs text-slate-500">Atmospheric Stress</div>
                <div className="text-2xl font-bold font-mono text-slate-900">
                  {evalData.fuzzy_stages.stage2_weather_stress_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage2_weather_stress_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage2_weather_stress_pct).text}
                </div>
                <div className="text-[10px] text-slate-500 pt-1">
                  Inputs: T + RH + Rs + u₂ + Rain [34 Rules]
                </div>
              </div>

              {/* Stage 3 */}
              <div className="rounded-xl border border-teal-100 bg-teal-50/30 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-teal-700 uppercase tracking-wider">Stage 3 • FIS 3</div>
                <div className="text-xs text-slate-500">Crop Water Demand</div>
                <div className="text-2xl font-bold font-mono text-slate-900">
                  {evalData.fuzzy_stages.stage3_water_demand_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage3_water_demand_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage3_water_demand_pct).text}
                </div>
                <div className="text-[10px] text-slate-500 pt-1">
                  Inputs: ETc + Deficit + Peff [39 Rules]
                </div>
              </div>

              {/* Stage 4 */}
              <div className="rounded-xl border border-indigo-100 bg-indigo-50/30 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-indigo-700 uppercase tracking-wider">Stage 4 • FIS 4</div>
                <div className="text-xs text-slate-500">Supervisory Valve Command</div>
                <div className="text-2xl font-bold font-mono text-indigo-900">
                  {evalData.fuzzy_stages.stage4_main_command_pct}%
                </div>
                <div className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold border ${getLevelBadge(evalData.fuzzy_stages.stage4_main_command_pct).bg}`}>
                  {getLevelBadge(evalData.fuzzy_stages.stage4_main_command_pct).text}
                </div>
                <div className="text-[10px] text-slate-500 pt-1">
                  4-Layer Protection Kernel [32 Rules]
                </div>
              </div>

              {/* Stage 5 */}
              <div className="rounded-xl border border-emerald-200 bg-emerald-100/40 p-4 space-y-2 relative overflow-hidden">
                <div className="text-[11px] font-semibold text-emerald-800 uppercase tracking-wider">Stage 5 • FIS 5</div>
                <div className="text-xs text-slate-500">Bounded Water-Filling</div>
                <div className="text-2xl font-bold font-mono text-emerald-800">
                  {evalData.total_allocated_liters.toLocaleString()} L
                </div>
                <div className="text-[10px] font-mono text-emerald-700 font-bold">
                  {evalData.is_supply_constrained ? 'RATIONED SUPPLY' : 'OPTIMAL SUPPLY'}
                </div>
                <div className="text-[10px] text-slate-500 pt-1">
                  Enforces Σ Alloc ≤ Available [32 Rules]
                </div>
              </div>
            </div>
          </div>

          {/* Multi-Zone Bounded Allocation Table */}
          <div className="rounded-xl border border-emerald-200 bg-white p-5 shadow-xs space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-emerald-100 pb-3">
              <div>
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Layers className="h-4 w-4 text-emerald-600" />
                  Multi-Zone Agricultural Plot Allocations ({evalData.location.district})
                </h3>
                <p className="text-xs text-slate-500">
                  Arbitrating limited local reservoir ({evalData.available_supply_liters.toLocaleString()} L available) across competing Indian crop zones.
                </p>
              </div>
              <div className="text-right text-xs">
                <span className="text-slate-500">Total Requested: </span>
                <span className="font-mono text-slate-900 font-bold">{evalData.total_requested_liters.toLocaleString()} L</span>
                <span className="text-slate-500 ml-2">Total Granted: </span>
                <span className="font-mono text-emerald-700 font-bold">{evalData.total_allocated_liters.toLocaleString()} L</span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-emerald-100 text-slate-500 bg-emerald-50/40">
                    <th className="py-2.5 px-3">Zone / Crop</th>
                    <th className="py-2.5 px-3">Season & Kc</th>
                    <th className="py-2.5 px-3">Moisture State</th>
                    <th className="py-2.5 px-3">Soil Stress</th>
                    <th className="py-2.5 px-3">Fuzzy Cmd</th>
                    <th className="py-2.5 px-3">Requested</th>
                    <th className="py-2.5 px-3">Allocated</th>
                    <th className="py-2.5 px-3">Fulfillment</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-emerald-50 font-mono text-slate-800">
                  {evalData.zone_allocations.map((z) => (
                    <tr key={z.zone_id} className="hover:bg-emerald-50/50 transition">
                      <td className="py-3 px-3 font-sans font-semibold text-slate-900">
                        {z.name}
                        <span className="block text-[10px] text-slate-500 font-normal">{z.area_m2} m² • {z.soil_type}</span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-slate-700 font-sans">{z.crop}</span>
                        <span className="block text-[10px] text-teal-700">Kc = {z.kc} ({z.season})</span>
                      </td>
                      <td className="py-3 px-3">
                        <span className="text-slate-900">{z.current_moisture_pct}%</span>
                        <span className="text-slate-400 text-[10px] block">Target: {z.target_moisture_pct}%</span>
                      </td>
                      <td className="py-3 px-3 text-amber-700 font-bold">{z.soil_stress_pct}%</td>
                      <td className="py-3 px-3 text-teal-700 font-bold">{z.main_command_pct}%</td>
                      <td className="py-3 px-3 text-slate-600">{z.requested_liters} L</td>
                      <td className="py-3 px-3 text-emerald-700 font-bold">{z.allocated_liters} L</td>
                      <td className="py-3 px-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          z.fulfillment_ratio_pct >= 99 ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                        }`}>
                          {z.fulfillment_ratio_pct}%
                        </span>
                      </td>
                      <td className="py-3 px-3 font-sans text-[11px] font-medium text-slate-600">{z.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Decision Summary Callout */}
          <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 text-xs text-slate-700 flex items-start gap-3 shadow-2xs">
            <Sparkles className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-900 block mb-0.5">Automated Agronomic Decision Rationale:</span>
              <p className="leading-relaxed">{evalData.decision_summary}</p>
            </div>
          </div>

          {/* LIVE ICAR AGROMET ADVISORY COPILOT (GPT-OSS-120B & TAVILY) */}
          <div className="rounded-2xl border border-emerald-200 bg-white p-5 sm:p-6 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-100 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="inline-flex items-center gap-1 rounded-md bg-teal-50 px-2.5 py-0.5 text-[10px] font-bold text-teal-800 border border-teal-200 uppercase">
                    <Globe className="h-3 w-3" /> Tavily Web Search Live
                  </span>
                  <span className="text-xs text-slate-300">•</span>
                  <span className="inline-flex items-center gap-1 rounded-md bg-purple-50 px-2.5 py-0.5 text-[10px] font-bold text-purple-800 border border-purple-200 uppercase">
                    <Brain className="h-3 w-3" /> Groq: openai/gpt-oss-120b
                  </span>
                  <span className="text-xs text-slate-300">•</span>
                  <span className="text-[10px] text-emerald-700 font-semibold">ICAR / IMD Agromet Service</span>
                </div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <span className="inline-flex items-center justify-center h-4 w-4 rounded-full bg-emerald-100 text-emerald-800 text-[9px] font-mono font-bold border border-emerald-300">IN</span>
                  <span>Live Regional ICAR Agromet Intelligence</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Synthesize real-time agricultural advisories for {evalData.location.district}, {evalData.location.state} with 120B reasoning grounded in live web bulletins.
                </p>
              </div>

              {!advisoryData && (
                <button
                  onClick={handleFetchAgrometAdvisory}
                  disabled={advisoryLoading}
                  className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 hover:from-teal-500 hover:to-emerald-500 text-white font-bold text-xs transition shadow-md shadow-emerald-600/20 cursor-pointer disabled:opacity-50 shrink-0"
                >
                  {advisoryLoading ? (
                    <>
                      <Activity className="h-4 w-4 animate-spin" />
                      <span>Retrieving ICAR Bulletins...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4" />
                      <span>Consult Live ICAR AI Advisor</span>
                    </>
                  )}
                </button>
              )}
            </div>

            {advisoryLoading && (
              <div className="p-4 rounded-xl border border-teal-200 bg-teal-50/50 text-xs text-teal-900 flex items-center gap-3 animate-pulse">
                <Globe className="h-5 w-5 text-teal-600 animate-spin" />
                <div>
                  <span className="font-semibold block">Querying Tavily for {evalData.location.district} Agromet Bulletins...</span>
                  <span className="text-[11px] text-teal-700">Synthesizing with Groq openai/gpt-oss-120b reasoning model...</span>
                </div>
              </div>
            )}

            {advisoryData && (
              <div className="space-y-4">
                {/* Executive Summary */}
                <div className="rounded-xl border border-emerald-100 bg-emerald-50/30 p-4 space-y-2">
                  <span className="text-[10px] font-mono uppercase text-teal-800 font-bold tracking-wider block">
                    Agrometeorological Synthesis ({advisoryData.crop} • {evalData.location.dominant_soil})
                  </span>
                  <p className="text-xs text-slate-700 leading-relaxed font-sans whitespace-pre-line">
                    {advisoryData.advisory_summary}
                  </p>
                </div>

                {/* Critical Farming Tips */}
                {advisoryData.critical_farming_tips && advisoryData.critical_farming_tips.length > 0 && (
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 space-y-2">
                    <span className="text-[10px] font-mono uppercase text-emerald-800 font-bold tracking-wider block">
                      Field Management Checklist (ICAR Best Practices)
                    </span>
                    <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-700">
                      {advisoryData.critical_farming_tips.map((tip, tIdx) => (
                        <li key={tIdx} className="flex items-start gap-2 bg-white p-2.5 rounded-lg border border-emerald-100 shadow-2xs">
                          <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
                          <span className="leading-snug">{tip}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* 120B Chain-of-Thought Reasoning */}
                {advisoryData.reasoning && (
                  <div className="rounded-xl border border-purple-200 bg-purple-50/30 p-3">
                    <button
                      onClick={() => setShowReasoning(!showReasoning)}
                      className="flex items-center justify-between w-full text-xs font-semibold text-purple-900 hover:text-purple-700 transition cursor-pointer"
                    >
                      <span className="flex items-center gap-1.5">
                        <Brain className="h-4 w-4 text-purple-600" />
                        <span>120B Chain-of-Thought Reasoning Trace</span>
                      </span>
                      {showReasoning ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                    {showReasoning && (
                      <div className="mt-2.5 p-3 rounded-lg bg-white border border-purple-200 text-[10px] font-mono text-purple-950 leading-relaxed whitespace-pre-wrap max-h-52 overflow-y-auto">
                        {advisoryData.reasoning}
                      </div>
                    )}
                  </div>
                )}

                {/* Tavily Verified Web Sources */}
                {advisoryData.web_sources && advisoryData.web_sources.length > 0 && (
                  <div className="pt-2 border-t border-emerald-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-1 text-[11px] text-slate-500">
                      <Globe className="h-3.5 w-3.5 text-teal-600" />
                      <span>Live Agricultural Sources:</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {advisoryData.web_sources.map((src, sIdx) => (
                        <a
                          key={sIdx}
                          href={src.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white border border-emerald-200 text-[10px] text-teal-700 hover:text-emerald-700 hover:border-emerald-300 transition shadow-2xs"
                        >
                          <span className="truncate max-w-[220px]">{src.title}</span>
                          <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
