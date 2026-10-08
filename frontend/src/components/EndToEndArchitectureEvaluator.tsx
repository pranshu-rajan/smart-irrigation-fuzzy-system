'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { 
  Cpu, 
  Layers, 
  Activity, 
  CheckCircle2, 
  ArrowRight, 
  Play, 
  Zap, 
  Info,
  Droplets,
  Sun,
  Wind,
  CloudRain,
  Database,
  Scale,
  Sparkles,
  BarChart3
} from 'lucide-react';

interface ZoneAllocationOutput {
  zone_id: number;
  name: string;
  crop: string;
  priority_pct: number;
  fis_alloc_factor: number;
  requested_l: number;
  allocated_l: number;
  fulfillment_ratio: number;
  status: string;
}

interface ArchitectureResponse {
  inputs: Record<string, number>;
  soil_stress: number;
  soil_stress_level: string;
  weather_stress: number;
  weather_stress_level: string;
  water_demand: number;
  water_demand_level: string;
  etc_mm_day: number;
  main_command: number;
  main_command_level: string;
  zone_allocations: ZoneAllocationOutput[];
  total_requested_l: number;
  total_allocated_l: number;
  available_supply_l: number;
  is_constrained: boolean;
  decision_summary: string;
}

interface BenchmarkResponse {
  scenario: string;
  duration_hours: number;
  controllers: {
    fuzzy: { total_water_l: number; rmse_pct: number; valve_switches: number; savings_vs_onoff_pct: number; savings_vs_pid_pct: number };
    pid: { total_water_l: number; rmse_pct: number; valve_switches: number; savings_vs_onoff_pct: number };
    onoff: { total_water_l: number; rmse_pct: number; valve_switches: number };
  };
  savings_vs_onoff_pct: number;
  savings_vs_pid_pct: number;
}

export default function EndToEndArchitectureEvaluator() {
  // Input parameters
  const [sm, setSm] = useState(45.0);
  const [target, setTarget] = useState(60.0);
  const [temp, setTemp] = useState(32.0);
  const [rh, setRh] = useState(38.0);
  const [solar, setSolar] = useState(820.0);
  const [wind, setWind] = useState(3.2);
  const [rain, setRain] = useState(0.0);
  const [reservoir, setReservoir] = useState(50.0);

  const [loading, setLoading] = useState(false);
  const [evalResult, setEvalResult] = useState<ArchitectureResponse | null>(null);
  const [benchLoading, setBenchLoading] = useState(false);
  const [benchResult, setBenchResult] = useState<BenchmarkResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Evaluate on mount
  useEffect(() => {
    handleEvaluate();
  }, []);

  const handleEvaluate = async (overrideInputs?: any) => {
    setLoading(true);
    setErrorMsg(null);
    const inputs = overrideInputs || {
      soil_moisture: sm,
      target_moisture: target,
      temperature: temp,
      humidity: rh,
      solar_radiation: solar,
      wind_speed: wind,
      rainfall: rain,
      reservoir_storage_pct: reservoir,
    };
    try {
      const res = await api.evaluateArchitecture(inputs);
      setEvalResult(res);
    } catch (err: any) {
      setErrorMsg(`Evaluation failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (preset: {
    sm: number;
    target: number;
    temp: number;
    rh: number;
    solar: number;
    wind: number;
    rain: number;
    reservoir: number;
  }) => {
    setSm(preset.sm);
    setTarget(preset.target);
    setTemp(preset.temp);
    setRh(preset.rh);
    setSolar(preset.solar);
    setWind(preset.wind);
    setRain(preset.rain);
    setReservoir(preset.reservoir);
    handleEvaluate({
      soil_moisture: preset.sm,
      target_moisture: preset.target,
      temperature: preset.temp,
      humidity: preset.rh,
      solar_radiation: preset.solar,
      wind_speed: preset.wind,
      rainfall: preset.rain,
      reservoir_storage_pct: preset.reservoir,
    });
  };

  const handleRunBenchmark = async () => {
    setBenchLoading(true);
    try {
      const res = await api.runBenchmarkComparison({ scenario: 'Normal', duration_hours: 24, timestep_minutes: 60 });
      setBenchResult(res);
    } catch (err: any) {
      setErrorMsg(`Benchmark failed: ${err.message}`);
    } finally {
      setBenchLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-emerald-200/90 bg-white p-6 sm:p-8 shadow-xs space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-800 border border-emerald-200">
              MATLAB & Full-Stack 100% Parity
            </span>
            <span className="text-xs text-slate-400">•</span>
            <span className="text-xs text-slate-500 font-medium">Closed-Loop 5-Stage Hierarchy</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Zap className="h-5 w-5 text-emerald-600" />
            Live Fuzzy System Architecture Evaluator
          </h2>
          <p className="mt-1 text-xs text-slate-600">
            Feed any arbitrary sensor inputs to instantaneously evaluate the entire 5-FIS inference cascade in &lt; 50ms.
          </p>
        </div>

        {/* Presets */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-semibold text-slate-500 mr-1">Presets:</span>
          <button
            onClick={() => applyPreset({ sm: 55, target: 60, temp: 25, rh: 55, solar: 650, wind: 2.5, rain: 0, reservoir: 85 })}
            className="px-2.5 py-1 text-[11px] font-medium rounded-lg border border-slate-200 hover:bg-slate-50 text-slate-700 transition"
          >
            Normal Day
          </button>
          <button
            onClick={() => applyPreset({ sm: 22, target: 60, temp: 42, rh: 18, solar: 980, wind: 4.5, rain: 0, reservoir: 60 })}
            className="px-2.5 py-1 text-[11px] font-medium rounded-lg border border-amber-200 bg-amber-50/50 hover:bg-amber-100/60 text-amber-900 transition"
          >
            Heatwave
          </button>
          <button
            onClick={() => applyPreset({ sm: 50, target: 60, temp: 22, rh: 92, solar: 180, wind: 5.0, rain: 30, reservoir: 95 })}
            className="px-2.5 py-1 text-[11px] font-medium rounded-lg border border-sky-200 bg-sky-50/50 hover:bg-sky-100/60 text-sky-900 transition"
          >
            Rainstorm
          </button>
          <button
            onClick={() => applyPreset({ sm: 30, target: 60, temp: 36, rh: 28, solar: 850, wind: 3.5, rain: 0, reservoir: 20 })}
            className="px-2.5 py-1 text-[11px] font-medium rounded-lg border border-rose-200 bg-rose-50/50 hover:bg-rose-100/60 text-rose-900 transition"
          >
            Low Reservoir
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
          {errorMsg}
        </div>
      )}

      {/* Sliders Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 rounded-xl bg-slate-50/70 border border-slate-200/80">
        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Soil Moisture</span>
            <span className="font-bold font-mono text-emerald-700">{sm.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="10"
            max="80"
            step="0.5"
            value={sm}
            onChange={(e) => setSm(parseFloat(e.target.value))}
            className="w-full accent-emerald-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Target Setpoint</span>
            <span className="font-bold font-mono text-emerald-700">{target.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="30"
            max="75"
            step="0.5"
            value={target}
            onChange={(e) => setTarget(parseFloat(e.target.value))}
            className="w-full accent-emerald-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Temperature</span>
            <span className="font-bold font-mono text-amber-700">{temp.toFixed(1)}°C</span>
          </div>
          <input
            type="range"
            min="5"
            max="50"
            step="0.5"
            value={temp}
            onChange={(e) => setTemp(parseFloat(e.target.value))}
            className="w-full accent-amber-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Humidity</span>
            <span className="font-bold font-mono text-sky-700">{rh.toFixed(1)}%</span>
          </div>
          <input
            type="range"
            min="10"
            max="100"
            step="1"
            value={rh}
            onChange={(e) => setRh(parseFloat(e.target.value))}
            className="w-full accent-sky-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Solar Radiation</span>
            <span className="font-bold font-mono text-orange-700">{solar.toFixed(0)} W/m²</span>
          </div>
          <input
            type="range"
            min="0"
            max="1200"
            step="10"
            value={solar}
            onChange={(e) => setSolar(parseFloat(e.target.value))}
            className="w-full accent-orange-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Wind Speed</span>
            <span className="font-bold font-mono text-indigo-700">{wind.toFixed(1)} m/s</span>
          </div>
          <input
            type="range"
            min="0.2"
            max="20"
            step="0.2"
            value={wind}
            onChange={(e) => setWind(parseFloat(e.target.value))}
            className="w-full accent-indigo-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Rainfall</span>
            <span className="font-bold font-mono text-blue-700">{rain.toFixed(1)} mm</span>
          </div>
          <input
            type="range"
            min="0"
            max="40"
            step="1"
            value={rain}
            onChange={(e) => setRain(parseFloat(e.target.value))}
            className="w-full accent-blue-600 cursor-pointer"
          />
        </div>

        <div className="space-y-1">
          <div className="flex justify-between text-[11px] font-medium text-slate-600">
            <span>Reservoir Level</span>
            <span className="font-bold font-mono text-teal-700">{reservoir.toFixed(0)}%</span>
          </div>
          <input
            type="range"
            min="5"
            max="100"
            step="1"
            value={reservoir}
            onChange={(e) => setReservoir(parseFloat(e.target.value))}
            className="w-full accent-teal-600 cursor-pointer"
          />
        </div>
      </div>

      {/* Action Button */}
      <div className="flex justify-end gap-3">
        <button
          onClick={() => handleEvaluate()}
          disabled={loading}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs transition shadow-sm cursor-pointer disabled:opacity-50"
        >
          {loading ? <Activity className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4 fill-white" />}
          <span>Evaluate 5-Stage Hierarchy</span>
        </button>
      </div>

      {/* RESULTS DISPLAY */}
      {evalResult && (
        <div className="space-y-6 pt-2">
          {/* 4 Stage Gauges / Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Stage 1 */}
            <div className="rounded-xl border border-rose-200/90 bg-rose-50/40 p-4 space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase text-rose-800 block">Stage 1 • FIS 1</span>
              <div className="text-xl font-bold font-mono text-slate-900">{evalResult.soil_stress.toFixed(1)}%</div>
              <div className="text-[11px] font-medium text-slate-600">Soil Moisture Stress</div>
              <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
                {evalResult.soil_stress_level}
              </span>
            </div>

            {/* Stage 2 */}
            <div className="rounded-xl border border-amber-200/90 bg-amber-50/40 p-4 space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase text-amber-800 block">Stage 2 • FIS 2</span>
              <div className="text-xl font-bold font-mono text-slate-900">{evalResult.weather_stress.toFixed(1)}%</div>
              <div className="text-[11px] font-medium text-slate-600">Weather Evaporative Stress</div>
              <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                {evalResult.weather_stress_level}
              </span>
            </div>

            {/* Stage 3 */}
            <div className="rounded-xl border border-sky-200/90 bg-sky-50/40 p-4 space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase text-sky-800 block">Stage 3 • FIS 3</span>
              <div className="text-xl font-bold font-mono text-slate-900">{evalResult.water_demand.toFixed(1)}%</div>
              <div className="text-[11px] font-medium text-slate-600">Crop Water Demand (ETc: {evalResult.etc_mm_day} mm)</div>
              <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-200">
                {evalResult.water_demand_level}
              </span>
            </div>

            {/* Stage 4 */}
            <div className="rounded-xl border border-emerald-200/90 bg-emerald-50/40 p-4 space-y-1.5">
              <span className="text-[10px] font-mono font-bold uppercase text-emerald-800 block">Stage 4 • FIS 4</span>
              <div className="text-xl font-bold font-mono text-slate-900">{evalResult.main_command.toFixed(1)}%</div>
              <div className="text-[11px] font-medium text-slate-600">Main Valve Opening Command</div>
              <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                {evalResult.main_command_level}
              </span>
            </div>
          </div>

          {/* STAGE 5: Multi-Zone Allocation Table */}
          <div className="rounded-xl border border-slate-200/90 bg-white overflow-hidden shadow-2xs space-y-3 p-4">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 flex items-center gap-2">
                <Scale className="h-4 w-4 text-emerald-600" />
                <span>Stage 5: Multi-Zone Arbitration & Shared Reservoir Allocation</span>
              </h4>
              <span className="text-[11px] font-mono font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                Reservoir: {evalResult.inputs.reservoir_storage_pct}% (Capacity: {evalResult.available_supply_l.toFixed(0)} L)
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-sans">
                <thead className="bg-slate-50 text-[10px] font-mono uppercase text-slate-600 border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Zone / Crop</th>
                    <th className="py-2.5 px-3">Priority</th>
                    <th className="py-2.5 px-3">FIS 5 Factor</th>
                    <th className="py-2.5 px-3">Requested (L)</th>
                    <th className="py-2.5 px-3">Allocated (L)</th>
                    <th className="py-2.5 px-3">Fulfillment</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {evalResult.zone_allocations.map((z) => (
                    <tr key={z.zone_id} className="hover:bg-slate-50/60">
                      <td className="py-2.5 px-3 font-semibold text-slate-900">{z.name}</td>
                      <td className="py-2.5 px-3 font-mono">{z.priority_pct}%</td>
                      <td className="py-2.5 px-3 font-mono text-emerald-700 font-bold">{z.fis_alloc_factor}%</td>
                      <td className="py-2.5 px-3 font-mono">{z.requested_l.toFixed(1)} L</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-slate-900">{z.allocated_l.toFixed(1)} L</td>
                      <td className="py-2.5 px-3 font-mono">{z.fulfillment_ratio.toFixed(1)}%</td>
                      <td className="py-2.5 px-3">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          z.status.includes('FULL') ? 'bg-emerald-100 text-emerald-800' :
                          z.status.includes('PARTIAL') ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                        }`}>
                          {z.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Total Accounting */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs font-mono pt-2 border-t border-slate-100 text-slate-600">
              <div>Total Requested: <span className="font-bold text-slate-900">{evalResult.total_requested_l.toFixed(1)} L</span></div>
              <div>Total Granted: <span className="font-bold text-emerald-700">{evalResult.total_allocated_l.toFixed(1)} L</span></div>
              <div>Available Capacity: <span className="font-bold text-teal-800">{evalResult.available_supply_l.toFixed(1)} L</span></div>
            </div>
          </div>

          {/* Decision Summary Card */}
          <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-1">
            <span className="text-[10px] font-mono font-bold uppercase text-slate-600 block">Agronomic & Control Decision Rationale</span>
            <p className="text-xs text-slate-800 leading-relaxed font-sans">{evalResult.decision_summary}</p>
          </div>
        </div>
      )}

      {/* CONTROLLER BENCHMARK COMPARISON (Fuzzy vs PID vs On-Off) */}
      <div className="border-t border-slate-200/80 pt-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-emerald-600" />
              <span>Controller Benchmark Comparison (Fuzzy vs PID vs On-Off)</span>
            </h3>
            <p className="text-xs text-slate-500">
              Verifies water conservation efficiency across the 3 control topologies over a 24-hour closed loop.
            </p>
          </div>

          <button
            onClick={handleRunBenchmark}
            disabled={benchLoading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-800 font-semibold text-xs transition cursor-pointer disabled:opacity-50"
          >
            {benchLoading ? <Activity className="h-4 w-4 animate-spin text-emerald-600" /> : <Play className="h-4 w-4 fill-slate-700" />}
            <span>Run 24h Benchmark</span>
          </button>
        </div>

        {benchResult && (
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-left text-xs font-sans">
              <thead className="bg-slate-50 text-[10px] font-mono uppercase text-slate-600 border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Controller Architecture</th>
                  <th className="py-2.5 px-4">Total Water (L)</th>
                  <th className="py-2.5 px-4">Water Saved vs Benchmark</th>
                  <th className="py-2.5 px-4">Tracking RMSE (%)</th>
                  <th className="py-2.5 px-4">Valve Switches</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                <tr className="bg-emerald-50/40 font-semibold">
                  <td className="py-2.5 px-4 text-emerald-900 font-bold">Hierarchical Fuzzy Logic (Our System)</td>
                  <td className="py-2.5 px-4 font-mono font-bold text-emerald-800">{benchResult.controllers.fuzzy.total_water_l.toFixed(1)} L</td>
                  <td className="py-2.5 px-4 font-mono font-bold text-emerald-800">BENCHMARK</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.fuzzy.rmse_pct.toFixed(2)}%</td>
                  <td className="py-2.5 px-4 font-mono text-emerald-700">{benchResult.controllers.fuzzy.valve_switches}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 text-slate-700">Classical PID Controller (with Anti-Windup)</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.pid.total_water_l.toFixed(1)} L</td>
                  <td className="py-2.5 px-4 font-mono text-amber-700 font-bold">-{benchResult.savings_vs_pid_pct.toFixed(1)}% (Wasted)</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.pid.rmse_pct.toFixed(2)}%</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.pid.valve_switches}</td>
                </tr>
                <tr>
                  <td className="py-2.5 px-4 text-slate-700">On-Off (Bang-Bang Hysteresis)</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.onoff.total_water_l.toFixed(1)} L</td>
                  <td className="py-2.5 px-4 font-mono text-rose-700 font-bold">-{benchResult.savings_vs_onoff_pct.toFixed(1)}% (Wasted)</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.onoff.rmse_pct.toFixed(2)}%</td>
                  <td className="py-2.5 px-4 font-mono">{benchResult.controllers.onoff.valve_switches}</td>
                </tr>
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
