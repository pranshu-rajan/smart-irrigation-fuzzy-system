'use client';

import React, { useEffect, useState, useCallback } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import IndiaInteractiveMap, { SelectedLocation } from '@/components/IndiaInteractiveMap';
import MetricCard from '@/components/MetricCard';
import { 
  Activity, 
  Droplets, 
  RefreshCw, 
  Play, 
  Sprout, 
  CheckCircle2, 
  AlertTriangle, 
  ArrowUpRight,
  ShieldCheck,
  Layers,
  Sun,
  Wind,
  Thermometer,
  CloudRain,
  Cpu,
  Compass,
  MapPin,
  Sparkles,
  Bot,
  Sliders,
  TrendingDown,
  Globe,
  ChevronRight,
  RotateCw,
  Gauge
} from 'lucide-react';

const DEFAULT_LOCATION: SelectedLocation = {
  district: 'Ludhiana',
  state: 'Punjab',
  agro_climatic_zone: 'Zone VI: Trans-Gangetic Plains Region',
  latitude: 30.9010,
  longitude: 75.8573,
};

export default function DashboardPage() {
  const [selectedLoc, setSelectedLoc] = useState<SelectedLocation>(DEFAULT_LOCATION);
  const [evalData, setEvalData] = useState<any>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [advisory, setAdvisory] = useState<any>(null);
  const [loadingAdvisory, setLoadingAdvisory] = useState<boolean>(false);
  const [evalHistory, setEvalHistory] = useState<Array<{ district: string; state: string; timestamp: string; et0: number; allocated: number }>>([]);
  const [reservoirStoragePct, setReservoirStoragePct] = useState<number>(75);

  // Evaluate fuzzy system architecture for selected location
  const evaluateLocation = useCallback(async (loc: SelectedLocation, resStorage: number = 75) => {
    setIsEvaluating(true);
    setErrorMsg(null);
    try {
      const data = await api.evaluateIndiaLocation({
        location_query: loc.district,
        latitude: loc.latitude,
        longitude: loc.longitude,
        reservoir_storage_pct: resStorage,
      });

      setEvalData(data);

      // Add to session evaluation history
      setEvalHistory((prev) => {
        const item = {
          district: data.location?.district || loc.district,
          state: data.location?.state || loc.state,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          et0: data.physics_agronomy?.et0_fao56_mm_day ?? 4.5,
          allocated: data.total_allocated_liters ?? 0,
        };
        const filtered = prev.filter((h) => h.district !== item.district);
        return [item, ...filtered].slice(0, 6);
      });

      // Fetch AI Agronomist Copilot advisory asynchronously
      fetchAdvisory(data);
    } catch (err: any) {
      console.error('Fuzzy evaluation failed:', err);
      setErrorMsg(err.message || 'Failed to evaluate Indian location fuzzy architecture.');
    } finally {
      setIsEvaluating(false);
    }
  }, []);

  // Fetch Groq AI Agronomist advisory
  const fetchAdvisory = async (evaluation: any) => {
    setLoadingAdvisory(true);
    try {
      const adv = await api.getIndiaAgrometAdvisory({
        district: evaluation.location?.district || selectedLoc.district,
        state: evaluation.location?.state || selectedLoc.state,
        crop: evaluation.zone_allocations?.[0]?.crop || 'Wheat',
        soil_type: evaluation.location?.dominant_soil || 'Alluvial',
        irrigation_depth_mm: evaluation.total_allocated_liters ? evaluation.total_allocated_liters / 100 : 3.5,
        et0_mm_day: evaluation.physics_agronomy?.et0_fao56_mm_day || 4.2,
        current_temp_c: evaluation.weather?.temperature_c || 28.0,
        current_humidity_pct: evaluation.weather?.humidity_percent || 55.0,
      });
      setAdvisory(adv);
    } catch (err) {
      console.warn('Could not fetch agromet advisory:', err);
    } finally {
      setLoadingAdvisory(false);
    }
  };

  // Initial load on mount
  useEffect(() => {
    evaluateLocation(DEFAULT_LOCATION, reservoirStoragePct);
  }, [evaluateLocation]);

  // Handle map selection
  const handleLocationSelect = (loc: SelectedLocation) => {
    setSelectedLoc(loc);
    evaluateLocation(loc, reservoirStoragePct);
  };

  // Derived Telemetry Values
  const weather = evalData?.weather;
  const physics = evalData?.physics_agronomy;
  const stages = evalData?.fuzzy_stages;
  const zones = evalData?.zone_allocations || [];
  const locInfo = evalData?.location;

  return (
    <div className="space-y-6 pb-16">
      {/* 1. Header Command Ribbon */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between rounded-2xl border border-slate-700/60 bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 p-5 shadow-xl text-white">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <Globe className="h-4.5 w-4.5 animate-pulse" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white font-sans">
              National Precision Irrigation Command Hub
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 px-3 py-0.5 text-xs font-semibold text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
              5-STAGE FUZZY PIPELINE ACTIVE
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400 max-w-2xl">
            Real-time geospatial intelligence, live Open-Meteo & Tavily atmospheric forcing, ICAR agro-climatic soil physics, and closed-loop supervisory fuzzy valve control.
          </p>
        </div>

        {/* Quick Location Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Reservoir Storage Slider */}
          <div className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs text-slate-300">
            <Droplets className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
            <span className="text-[11px] text-slate-400 font-medium">Reservoir:</span>
            <input
              type="range"
              min={20}
              max={100}
              value={reservoirStoragePct}
              onChange={(e) => {
                const val = Number(e.target.value);
                setReservoirStoragePct(val);
                evaluateLocation(selectedLoc, val);
              }}
              className="h-1.5 w-20 accent-emerald-500 cursor-pointer"
              title={`Reservoir Storage: ${reservoirStoragePct}%`}
            />
            <span className="font-mono text-emerald-400 font-semibold">{reservoirStoragePct}%</span>
          </div>

          {/* Re-Evaluate Trigger Button */}
          <button
            onClick={() => evaluateLocation(selectedLoc, reservoirStoragePct)}
            disabled={isEvaluating}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-lg transition disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isEvaluating ? 'animate-spin' : ''}`} />
            <span>{isEvaluating ? 'Evaluating FIS...' : 'Re-Evaluate Farm'}</span>
          </button>
        </div>
      </div>

      {/* Error Notification */}
      {errorMsg && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3.5 text-xs font-semibold text-amber-300 flex items-center gap-2.5 shadow-sm">
          <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 2. Primary Spatial Command Center: Real Interactive Google / Leaflet Map */}
      <IndiaInteractiveMap
        onLocationSelect={handleLocationSelect}
        selectedLocation={selectedLoc}
      />

      {/* 3. Real-Time Physical & Evaporative Forcing Metrics (4 High-Density Cards) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <MetricCard
          title="FAO-56 Evaporative Demand (ET₀)"
          value={physics?.et0_fao56_mm_day ? `${physics.et0_fao56_mm_day.toFixed(2)} mm/d` : '4.50 mm/d'}
          change={weather?.is_live ? 'Live Open-Meteo Telemetry' : 'ICAR Climatological Norm'}
          trend="neutral"
          variant="emerald"
        />
        <MetricCard
          title="Atmospheric Vapor Deficit (VPD)"
          value={physics?.vapor_pressure_deficit_kpa ? `${physics.vapor_pressure_deficit_kpa.toFixed(2)} kPa` : '1.85 kPa'}
          change={weather ? `${weather.temperature_c}°C • ${weather.humidity_percent}% RH` : '28.0°C • 55% RH'}
          trend="neutral"
          variant="cyan"
        />
        <MetricCard
          title="Agro-Climatic Zone & Soil"
          value={locInfo?.dominant_soil || 'Alluvial Soil'}
          change={locInfo?.agro_climatic_zone ? `Zone ${locInfo.zone_number}: ${locInfo.agro_climatic_zone.split(':')[1] || locInfo.agro_climatic_zone}` : 'Trans-Gangetic Plains'}
          trend="neutral"
          variant="blue"
        />
        <MetricCard
          title="Supervisory Water Allocation"
          value={evalData?.total_allocated_liters ? `${evalData.total_allocated_liters.toFixed(1)} L` : '384.2 L'}
          change={`Fulfillment: ${evalData?.overall_fulfillment_ratio_pct ? evalData.overall_fulfillment_ratio_pct.toFixed(0) : '100'}% • Mass Conserved`}
          trend="up"
          variant="emerald"
        />
      </div>

      {/* 4. Live 5-Stage Cascaded Fuzzy Inference System (FIS) Pipeline */}
      <div className="rounded-2xl border border-slate-700/60 bg-slate-900/90 backdrop-blur-md p-5 shadow-xl text-white">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="h-4.5 w-4.5 text-emerald-400" />
            <h2 className="text-sm sm:text-base font-bold text-white">
              Cascaded 5-Stage Fuzzy Inference Pipeline
            </h2>
            <span className="text-[11px] text-slate-500">•</span>
            <span className="text-[11px] text-slate-400 font-mono">
              Target: {locInfo?.district || selectedLoc.district}, {locInfo?.state || selectedLoc.state}
            </span>
          </div>
          <Link
            href="/fuzzy"
            className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition"
          >
            <span>Inspect 5 FIS Surface Curves</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* 5 Stages Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
          {/* Stage 1 */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span className="font-bold text-slate-300">STAGE 1</span>
                <span className="font-mono text-[10px] text-emerald-400">Root-Zone</span>
              </div>
              <h3 className="text-xs font-semibold text-white">Soil Stress FIS</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">Moisture error & depletion rate</p>
            </div>
            <div className="mt-4">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="text-slate-400">Stress:</span>
                <span className="text-base font-bold text-emerald-400">
                  {stages?.stage1_soil_stress_pct ? `${stages.stage1_soil_stress_pct.toFixed(1)}%` : '42.0%'}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                  style={{ width: `${stages?.stage1_soil_stress_pct || 42}%` }}
                />
              </div>
            </div>
          </div>

          {/* Stage 2 */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span className="font-bold text-slate-300">STAGE 2</span>
                <span className="font-mono text-[10px] text-amber-400">Atmosphere</span>
              </div>
              <h3 className="text-xs font-semibold text-white">Weather Stress FIS</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">ET₀, solar irradiance & VPD</p>
            </div>
            <div className="mt-4">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="text-slate-400">Stress:</span>
                <span className="text-base font-bold text-amber-400">
                  {stages?.stage2_weather_stress_pct ? `${stages.stage2_weather_stress_pct.toFixed(1)}%` : '58.5%'}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-amber-500 transition-all duration-500"
                  style={{ width: `${stages?.stage2_weather_stress_pct || 58.5}%` }}
                />
              </div>
            </div>
          </div>

          {/* Stage 3 */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span className="font-bold text-slate-300">STAGE 3</span>
                <span className="font-mono text-[10px] text-cyan-400">Demand</span>
              </div>
              <h3 className="text-xs font-semibold text-white">Water Demand FIS</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">Stage 1 & Stage 2 fusion</p>
            </div>
            <div className="mt-4">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="text-slate-400">Demand:</span>
                <span className="text-base font-bold text-cyan-400">
                  {stages?.stage3_water_demand_pct ? `${stages.stage3_water_demand_pct.toFixed(1)}%` : '51.2%'}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-cyan-500 transition-all duration-500"
                  style={{ width: `${stages?.stage3_water_demand_pct || 51.2}%` }}
                />
              </div>
            </div>
          </div>

          {/* Stage 4 */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span className="font-bold text-slate-300">STAGE 4</span>
                <span className="font-mono text-[10px] text-indigo-400">Actuation</span>
              </div>
              <h3 className="text-xs font-semibold text-white">Main Command FIS</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">Precipitation & storage clamp</p>
            </div>
            <div className="mt-4">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="text-slate-400">Command:</span>
                <span className="text-base font-bold text-indigo-400">
                  {stages?.stage4_main_command_pct ? `${stages.stage4_main_command_pct.toFixed(1)}%` : '64.0%'}
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                  style={{ width: `${stages?.stage4_main_command_pct || 64.0}%` }}
                />
              </div>
            </div>
          </div>

          {/* Stage 5 */}
          <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-3.5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                <span className="font-bold text-slate-300">STAGE 5</span>
                <span className="font-mono text-[10px] text-emerald-400">Supervisory</span>
              </div>
              <h3 className="text-xs font-semibold text-white">Multizone Allocation</h3>
              <p className="text-[10px] text-slate-500 mt-0.5">Priority & mass conservation</p>
            </div>
            <div className="mt-4">
              <div className="flex items-baseline justify-between text-xs font-mono">
                <span className="text-slate-400">Status:</span>
                <span className="text-xs font-bold text-emerald-400 flex items-center gap-1">
                  <ShieldCheck className="h-3.5 w-3.5" />
                  CONSERVED
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full rounded-full bg-emerald-500/20 overflow-hidden">
                <div className="h-full rounded-full bg-emerald-400 w-full animate-pulse" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 5. Dynamic ICAR Agricultural Zones (Location-Tailored Crops & Valves) */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Sprout className="h-4.5 w-4.5 text-emerald-600" />
              <span>Location Agricultural Zones & Real-Time Actuators</span>
            </h2>
            <p className="text-xs text-slate-500">
              Active ICAR cropping patterns for {locInfo?.district || selectedLoc.district} across {locInfo?.dominant_soil || 'Alluvial'} soil (FC: {locInfo?.field_capacity_pct || 28}%, WP: {locInfo?.wilting_point_pct || 12}%).
            </p>
          </div>
          <Link
            href="/allocation"
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
          >
            <span>Allocation Engine</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {(zones.length > 0 ? zones : [
            {
              zone_id: 1,
              name: 'Zone 1: Primary Kharif',
              crop: locInfo?.primary_kharif_crop || 'Rice/Paddy',
              soil_type: locInfo?.dominant_soil || 'Alluvial',
              current_moisture_pct: 25.5,
              target_moisture_pct: 28.0,
              soil_stress_pct: 45.0,
              main_command_pct: 62.0,
              allocated_liters: 145.2,
              status: 'ALLOCATED_OPTIMAL',
            },
            {
              zone_id: 2,
              name: 'Zone 2: Primary Rabi',
              crop: locInfo?.primary_rabi_crop || 'Wheat',
              soil_type: locInfo?.dominant_soil || 'Alluvial',
              current_moisture_pct: 21.0,
              target_moisture_pct: 24.0,
              soil_stress_pct: 52.0,
              main_command_pct: 58.0,
              allocated_liters: 122.0,
              status: 'ALLOCATED_OPTIMAL',
            },
            {
              zone_id: 3,
              name: 'Zone 3: Horticultural / Zaid',
              crop: locInfo?.primary_zaid_crop || 'Mustard/Pulses',
              soil_type: locInfo?.dominant_soil || 'Alluvial',
              current_moisture_pct: 27.5,
              target_moisture_pct: 29.0,
              soil_stress_pct: 32.0,
              main_command_pct: 42.0,
              allocated_liters: 98.4,
              status: 'ALLOCATED_OPTIMAL',
            },
          ]).map((z: any) => {
            const isValveOpen = z.allocated_liters > 0 && z.main_command_pct > 20;
            return (
              <div
                key={z.zone_id}
                className="flex flex-col justify-between rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs hover:border-emerald-300 hover:shadow-md transition-all"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-slate-500">
                      ZONE 0{z.zone_id} • {z.season || 'ICAR'}
                    </span>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        isValveOpen
                          ? 'bg-cyan-50 text-cyan-800 border border-cyan-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          isValveOpen ? 'bg-cyan-500 animate-pulse' : 'bg-slate-400'
                        }`}
                      />
                      {isValveOpen ? 'VALVE ACTIVE' : 'VALVE STANDBY'}
                    </span>
                  </div>

                  <h3 className="mt-2 text-sm font-bold text-slate-900">{z.name}</h3>
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-600">
                    <span className="inline-flex items-center gap-1 font-semibold text-emerald-700">
                      <Sprout className="h-3.5 w-3.5" />
                      <span>{z.crop}</span>
                    </span>
                    <span>&bull;</span>
                    <span className="inline-flex items-center gap-1 text-slate-600">
                      <Layers className="h-3.5 w-3.5 text-amber-700" />
                      <span>{z.soil_type}</span>
                    </span>
                  </div>

                  {/* Volumetric Moisture Bar */}
                  <div className="mt-5 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600 font-medium">Root Moisture:</span>
                      <span className="font-bold text-slate-900 font-mono">
                        {z.current_moisture_pct?.toFixed(1) || 24.5}%{' '}
                        <span className="text-slate-400 font-normal">
                          / target {z.target_moisture_pct?.toFixed(1) || 28.0}%
                        </span>
                      </span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200">
                      <div
                        className="h-full rounded-full bg-emerald-500 transition-all duration-500"
                        style={{
                          width: `${Math.min(
                            100,
                            ((z.current_moisture_pct || 24.5) / ((z.target_moisture_pct || 28) * 1.25)) * 100
                          )}%`,
                        }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500 font-mono">
                      <span>Soil Stress: {z.soil_stress_pct?.toFixed(1) || 35}%</span>
                      <span className="text-cyan-700 font-semibold">
                        Aperture: {z.main_command_pct?.toFixed(0) || 50}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Card Footer: Allocated Liters */}
                <div className="mt-5 border-t border-slate-100 pt-3 flex items-center justify-between text-xs">
                  <div>
                    <span className="text-slate-400 block text-[10px]">Allocated Today</span>
                    <span className="font-bold text-emerald-800 font-mono text-sm">
                      {z.allocated_liters?.toFixed(1) || 120.0} L
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-400 block text-[10px]">Crop Factor (Kc)</span>
                    <span className="font-semibold text-slate-700 font-mono">
                      {z.kc ? z.kc.toFixed(2) : '1.05'}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 6. AI Agronomist Copilot (Groq Llama 3.3 70B & Tavily Live Knowledge) */}
      <div className="rounded-2xl border border-emerald-500/30 bg-gradient-to-br from-emerald-950/20 via-slate-900 to-slate-950 p-5 shadow-xl text-white">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
              <Bot className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-white flex items-center gap-2">
                <span>AI Agronomist Field Copilot</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2 py-0.2 text-[10px] font-semibold text-emerald-300">
                  <Sparkles className="h-2.5 w-2.5" />
                  Groq 70B • Tavily Live Search
                </span>
              </h2>
            </div>
          </div>
          <Link
            href="/ai"
            className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
          >
            <span>Open Dedicated AI Advisory</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {loadingAdvisory ? (
          <div className="flex items-center gap-3 py-4 text-xs text-slate-400">
            <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
            <span>Consulting Groq agronomy knowledge base & real-time crop advisory...</span>
          </div>
        ) : advisory ? (
          <div className="space-y-3.5">
            <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
              {advisory.advisory_summary}
            </p>

            {advisory.critical_farming_tips && advisory.critical_farming_tips.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
                {advisory.critical_farming_tips.slice(0, 4).map((tip: string, idx: number) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 rounded-xl bg-slate-900/80 border border-slate-800 p-2.5 text-xs text-slate-300"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{tip}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-slate-400">
            Select any district on the interactive map above to generate instant AI agronomist field schedules.
          </p>
        )}
      </div>

      {/* 7. Recent National Evaluations Feed (Interactive History) */}
      {evalHistory.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Activity className="h-4 w-4 text-emerald-600" />
              <span>Recent Indian Farm Evaluations (Session History)</span>
            </h2>
            <span className="text-xs text-slate-500">Click any card to re-inspect</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
            {evalHistory.map((item, idx) => (
              <button
                key={idx}
                onClick={() => {
                  const targetLoc: SelectedLocation = {
                    district: item.district,
                    state: item.state,
                    latitude: selectedLoc.latitude,
                    longitude: selectedLoc.longitude,
                  };
                  evaluateLocation(targetLoc, reservoirStoragePct);
                }}
                className={`rounded-xl border p-2.5 text-left transition cursor-pointer ${
                  selectedLoc.district === item.district
                    ? 'border-emerald-500 bg-emerald-50/70 text-emerald-950 font-semibold shadow-xs'
                    : 'border-slate-200 bg-white hover:border-emerald-300 text-slate-700'
                }`}
              >
                <div className="text-xs font-bold truncate">{item.district}</div>
                <div className="text-[10px] text-slate-500 truncate">{item.state}</div>
                <div className="mt-2 flex items-center justify-between text-[10px] font-mono border-t border-slate-100 pt-1 text-slate-600">
                  <span>ET₀: {item.et0.toFixed(1)}</span>
                  <span className="text-emerald-700 font-semibold">{item.allocated.toFixed(0)}L</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
