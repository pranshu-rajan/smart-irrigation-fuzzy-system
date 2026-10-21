'use client';

import React, { useState } from 'react';
import { api } from '@/lib/api';
import { 
  Globe, 
  MapPin, 
  Layers, 
  Droplets, 
  Sprout, 
  Activity, 
  ArrowRight, 
  RefreshCw, 
  CheckCircle2,
  TrendingDown,
  Scale
} from 'lucide-react';

interface DistrictComparisonMatrixProps {
  currentDistrict: string;
  currentState: string;
  currentEvaluation: any;
  onSelectDistrict?: (districtName: string) => void;
}

const COMPARABLE_DISTRICTS = [
  { district: 'Ludhiana', state: 'Punjab', zone: 'Trans-Gangetic Plain', soil: 'Alluvial Soil' },
  { district: 'Nashik', state: 'Maharashtra', zone: 'Western Plateau & Hills', soil: 'Black Cotton Soil (Vertisol)' },
  { district: 'Jodhpur', state: 'Rajasthan', zone: 'Western Dry Region', soil: 'Desert Soil (Aridisol)' },
  { district: 'Guntur', state: 'Andhra Pradesh', zone: 'Southern Plateau & Hills', soil: 'Red & Coastal Soil' },
  { district: 'Mandya', state: 'Karnataka', zone: 'Southern Plateau', soil: 'Red Loamy Soil' },
  { district: 'Jorhat', state: 'Assam', zone: 'Eastern Himalayan Region', soil: 'Alluvial Humid Soil' },
];

export default function DistrictComparisonMatrix({
  currentDistrict,
  currentState,
  currentEvaluation,
  onSelectDistrict,
}: DistrictComparisonMatrixProps) {
  const [selectedBenchmark, setSelectedBenchmark] = useState<string>('Nashik');
  const [benchmarkData, setBenchmarkData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Fetch benchmark evaluation
  const handleCompare = async (targetDistrict: string) => {
    setSelectedBenchmark(targetDistrict);
    setIsLoading(true);
    try {
      const data = await api.evaluateIndiaLocation({
        location_query: targetDistrict,
        reservoir_storage_pct: 75,
      });
      setBenchmarkData(data);
    } catch (err) {
      console.warn('Failed to load benchmark comparison:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const curr = currentEvaluation;
  const currWeather = curr?.weather;
  const currPhysics = curr?.physics_agronomy;
  const currStages = curr?.fuzzy_stages;

  const bench = benchmarkData;
  const benchWeather = bench?.weather;
  const benchPhysics = bench?.physics_agronomy;
  const benchStages = bench?.fuzzy_stages;

  return (
    <div className="rounded-3xl border border-slate-700/70 bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 p-6 sm:p-7 shadow-2xl text-white space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-400">
              <Scale className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-white tracking-tight flex items-center gap-2">
                <span>National Multi-District Fuzzy Comparative Matrix</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 px-2.5 py-0.5 text-[10px] font-semibold text-indigo-400">
                  ICAR Benchmark
                </span>
              </h2>
            </div>
          </div>
          <p className="text-xs text-slate-400 max-w-2xl">
            Compare live atmospheric evaporative forcing, soil hydrology, and fuzzy supervisory dispatch between distinct Indian agro-climatic zones.
          </p>
        </div>

        {/* Quick Benchmark Picker */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Compare with:</span>
          <select
            value={selectedBenchmark}
            onChange={(e) => handleCompare(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-1.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 cursor-pointer font-semibold"
          >
            {COMPARABLE_DISTRICTS.filter((d) => d.district.toLowerCase() !== currentDistrict.toLowerCase()).map((d) => (
              <option key={d.district} value={d.district}>
                {d.district} ({d.state})
              </option>
            ))}
          </select>

          <button
            onClick={() => handleCompare(selectedBenchmark)}
            disabled={isLoading}
            className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm transition disabled:opacity-50 cursor-pointer flex items-center gap-1.5"
          >
            <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Load</span>
          </button>
        </div>
      </div>

      {/* Comparative Side-by-Side Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Current Active Location */}
        <div className="rounded-2xl border border-emerald-500/40 bg-slate-900/80 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-emerald-400 font-bold block">
                ACTIVE SITE LOCKED
              </span>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-0.5">
                <MapPin className="h-4 w-4 text-emerald-400" />
                <span>{currentDistrict}, {currentState}</span>
              </h3>
            </div>
            <span className="rounded-full bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 text-[11px] font-mono text-emerald-300 font-semibold">
              Zone {curr?.location?.zone_number || 6}
            </span>
          </div>

          <div className="space-y-2.5 text-xs font-mono">
            <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
              <span className="text-slate-400">Soil Order:</span>
              <span className="text-slate-200 font-bold">{curr?.location?.dominant_soil || 'Alluvial'}</span>
            </div>
            <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
              <span className="text-slate-400">Available Water Capacity (FC/WP):</span>
              <span className="text-cyan-300 font-bold">
                {curr?.location?.field_capacity_pct || 28}% / {curr?.location?.wilting_point_pct || 12}%
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
              <span className="text-slate-400">Atmospheric ET₀ (FAO-56):</span>
              <span className="text-emerald-400 font-bold">
                {currPhysics?.et0_fao56_mm_day ? `${currPhysics.et0_fao56_mm_day.toFixed(2)} mm/day` : '4.50 mm/day'}
              </span>
            </div>
            <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
              <span className="text-slate-400">Weather Stress FIS:</span>
              <span className="text-amber-400 font-bold">{currStages?.stage2_weather_stress_pct || 48}%</span>
            </div>
            <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
              <span className="text-slate-400">Supervisory Valve Command:</span>
              <span className="text-cyan-400 font-bold">{currStages?.stage4_main_command_pct || 55}%</span>
            </div>
            <div className="flex justify-between pt-1">
              <span className="text-slate-400">Water Conservation vs On-Off:</span>
              <span className="text-emerald-300 font-bold font-sans">
                +{curr?.water_savings_vs_onoff_pct || 49.7}%
              </span>
            </div>
          </div>
        </div>

        {/* Selected Benchmark Location */}
        <div className="rounded-2xl border border-indigo-500/40 bg-slate-900/80 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono uppercase tracking-wider text-indigo-400 font-bold block">
                BENCHMARK COMPARATOR
              </span>
              <h3 className="text-lg font-bold text-white flex items-center gap-2 mt-0.5">
                <Globe className="h-4 w-4 text-indigo-400" />
                <span>{selectedBenchmark}</span>
              </h3>
            </div>
            <span className="rounded-full bg-indigo-500/10 border border-indigo-500/30 px-2.5 py-1 text-[11px] font-mono text-indigo-300 font-semibold">
              {bench?.location?.agro_climatic_zone?.split(':')[0] || 'Zone ICAR'}
            </span>
          </div>

          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-10 text-xs text-slate-400 space-y-2">
              <RefreshCw className="h-6 w-6 animate-spin text-indigo-400" />
              <span>Fetching live meteorology & ICAR soil for {selectedBenchmark}...</span>
            </div>
          ) : bench ? (
            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
                <span className="text-slate-400">Soil Order:</span>
                <span className="text-slate-200 font-bold">{bench?.location?.dominant_soil || 'Vertisol'}</span>
              </div>
              <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
                <span className="text-slate-400">Available Water Capacity (FC/WP):</span>
                <span className="text-cyan-300 font-bold">
                  {bench?.location?.field_capacity_pct}% / {bench?.location?.wilting_point_pct}%
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
                <span className="text-slate-400">Atmospheric ET₀ (FAO-56):</span>
                <span className="text-indigo-400 font-bold">
                  {benchPhysics?.et0_fao56_mm_day ? `${benchPhysics.et0_fao56_mm_day.toFixed(2)} mm/day` : '4.20 mm/day'}
                </span>
              </div>
              <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
                <span className="text-slate-400">Weather Stress FIS:</span>
                <span className="text-amber-400 font-bold">{benchStages?.stage2_weather_stress_pct || 45}%</span>
              </div>
              <div className="flex justify-between border-b border-slate-800/60 pb-1.5">
                <span className="text-slate-400">Supervisory Valve Command:</span>
                <span className="text-cyan-400 font-bold">{benchStages?.stage4_main_command_pct || 50}%</span>
              </div>
              <div className="flex justify-between pt-1">
                <span className="text-slate-400">Water Conservation vs On-Off:</span>
                <span className="text-indigo-300 font-bold font-sans">
                  +{bench?.water_savings_vs_onoff_pct || 48.5}%
                </span>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 text-xs text-slate-400 space-y-2">
              <Scale className="h-6 w-6 text-slate-600" />
              <span>Click &quot;Load&quot; above to fetch live comparative data.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
