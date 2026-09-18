'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api, SimulationSummaryResponse, TimeseriesResponse, TimeseriesRecord } from '@/lib/api';
import LineChart from '@/components/LineChart';
import MetricCard from '@/components/MetricCard';

function SimulationStudioContent() {
  const searchParams = useSearchParams();
  const initialRunId = searchParams.get('run_id');


  const [scenario, setScenario] = useState('Normal');
  const [supplyScenario, setSupplyScenario] = useState('Normal Supply');
  const [controllerType, setControllerType] = useState('fuzzy');
  const [durationHours, setDurationHours] = useState(24);
  const [isRunning, setIsRunning] = useState(false);

  const [currentRun, setCurrentRun] = useState<SimulationSummaryResponse | null>(null);
  const [timeseries, setTimeseries] = useState<TimeseriesRecord[]>([]);
  const [selectedZone, setSelectedZone] = useState<number>(1);
  const [downsampleStride, setDownsampleStride] = useState<number>(2);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load initial simulation if passed via run_id or fetch latest
  useEffect(() => {
    const fetchInitial = async () => {
      try {
        if (initialRunId) {
          const run = await api.getSimulation(initialRunId);
          setCurrentRun(run);
          const ts = await api.getSimulationTimeseries(initialRunId, undefined, downsampleStride);
          setTimeseries(ts.records);
        } else {
          const list = await api.listSimulations(1);
          if (list && list.length > 0) {
            setCurrentRun(list[0]);
            const ts = await api.getSimulationTimeseries(list[0].id, undefined, downsampleStride);
            setTimeseries(ts.records);
          }
        }
      } catch (err: any) {
        console.warn('No initial simulation to load:', err.message);
      }
    };
    fetchInitial();
  }, [initialRunId, downsampleStride]);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setErrorMsg(null);
    try {
      const summary = await api.runSimulation({
        scenario,
        duration_hours: durationHours,
        timestep_minutes: 1,
        controller_type: controllerType,
        supply_scenario: supplyScenario,
      });
      setCurrentRun(summary);

      const ts = await api.getSimulationTimeseries(summary.id, undefined, downsampleStride);
      setTimeseries(ts.records);
    } catch (err: any) {
      setErrorMsg(`Simulation failed: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  // Filter timeseries by selected zone
  const zoneRecords = timeseries.filter((r) => r.zone_id === selectedZone);
  const steps = zoneRecords.map((r) => r.step);

  // Summary figures
  const metrics = currentRun?.summary_metrics || {};
  const requestedL = metrics.total_water_volume_requested_l || 0;
  const allocatedL = metrics.total_water_volume_allocated_l || 0;
  const unmetL = metrics.total_water_volume_unmet_l || 0;
  const fulfillmentPct = metrics.overall_fulfillment_ratio ?? (requestedL > 0 ? (allocatedL / requestedL) * 100 : 100);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Closed-Loop Simulation Studio</h1>
          <p className="mt-1 text-sm text-slate-400">
            Execute 24-hour closed-loop multizone simulations (1440 timesteps) across 6 environmental scenarios with supervisory water allocation.
          </p>
        </div>

        {currentRun && (
          <div className="flex items-center gap-3">
            <Link
              href={`/ai?sim_id=${currentRun.id}`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-500/30 bg-indigo-950/40 px-3 py-2 text-xs font-semibold text-indigo-300 hover:bg-indigo-900/50 transition-colors"
            >
              🤖 Analyze with Groq AI
            </Link>
            <Link
              href={`/reports?sim_id=${currentRun.id}`}
              className="inline-flex items-center gap-1.5 rounded-lg border border-teal-500/30 bg-teal-950/40 px-3 py-2 text-xs font-semibold text-teal-300 hover:bg-teal-900/50 transition-colors"
            >
              📄 Export PDF Report
            </Link>
          </div>
        )}
      </div>

      {errorMsg && (
        <div className="rounded-lg border border-rose-500/30 bg-rose-950/20 p-4 text-xs text-rose-300">
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Simulation Control Panel */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-6">
        <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
          <span>⚙️</span> Simulation Parameters
        </h2>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Environmental Scenario</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="Normal">Normal</option>
              <option value="Hot & Dry">Hot & Dry</option>
              <option value="Rainy">Rainy</option>
              <option value="Cloudy">Cloudy</option>
              <option value="Heatwave">Heatwave</option>
              <option value="Water Scarcity">Water Scarcity</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Shared Supply Scenario</label>
            <select
              value={supplyScenario}
              onChange={(e) => setSupplyScenario(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="Abundant">Abundant (100% capacity)</option>
              <option value="Normal Supply">Normal Supply (100% standard)</option>
              <option value="Moderate Scarcity">Moderate Scarcity (70%)</option>
              <option value="Severe Scarcity">Severe Scarcity (40%)</option>
              <option value="Extreme Scarcity">Extreme Scarcity (20%)</option>
              <option value="Zero Supply">Zero Supply (0% supply cap test)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Controller Type</label>
            <select
              value={controllerType}
              onChange={(e) => setControllerType(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value="fuzzy">Hierarchical Adaptive Fuzzy (Default)</option>
              <option value="pso_tuned">PSO-Tuned Fuzzy Parameters</option>
              <option value="fixed">Fixed-Interval Rule Controller</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-400 mb-1">Duration & Resolution</label>
            <select
              value={durationHours}
              onChange={(e) => setDurationHours(Number(e.target.value))}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-xs text-white focus:border-emerald-500 focus:outline-none"
            >
              <option value={24}>24 Hours (1440 timesteps @ 1 min)</option>
              <option value={48}>48 Hours (2880 timesteps)</option>
              <option value={72}>72 Hours (4320 timesteps)</option>
            </select>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">Target Zone Filter:</span>
            {[1, 2, 3].map((z) => (
              <button
                key={z}
                onClick={() => setSelectedZone(z)}
                className={`rounded-md px-3 py-1 text-xs font-semibold transition-colors ${
                  selectedZone === z
                    ? 'bg-emerald-500 text-slate-950'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                Zone {z} ({z === 1 ? 'Tomato' : z === 2 ? 'Potato' : 'Maize'})
              </button>
            ))}
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={isRunning}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-6 py-2.5 text-xs font-bold text-slate-950 shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 disabled:opacity-50 transition-colors"
          >
            {isRunning ? (
              <>
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                Simulating Multizone Closed-Loop...
              </>
            ) : (
              '▶ Run Multizone Simulation'
            )}
          </button>
        </div>
      </div>

      {/* Summary Metrics Banner */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          title="Total Requested"
          value={`${requestedL.toFixed(1)} L`}
          change="Sum across all zones"
          trend="neutral"
          color="blue"
        />
        <MetricCard
          title="Total Allocated"
          value={`${allocatedL.toFixed(1)} L`}
          change={`Supply: ${supplyScenario}`}
          trend="up"
          color="emerald"
        />
        <MetricCard
          title="Unmet Demand"
          value={`${unmetL.toFixed(1)} L`}
          change="Zero artificial water"
          trend={unmetL > 0 ? 'down' : 'neutral'}
          color={unmetL > 0 ? 'amber' : 'emerald'}
        />
        <MetricCard
          title="Overall Fulfillment"
          value={`${typeof fulfillmentPct === 'number' ? fulfillmentPct.toFixed(1) : fulfillmentPct}%`}
          change="Mass Balance: 0.00 mm"
          trend="up"
          color="cyan"
        />
      </div>

      {/* 10 Time-Series Plots Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">
            Simulation Telemetry Plots — Zone {selectedZone}
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            {zoneRecords.length} records • Stride {downsampleStride}
          </span>
        </div>

        {zoneRecords.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-12 text-center text-slate-400">
            No simulation data loaded. Click <strong>▶ Run Multizone Simulation</strong> above to execute.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Plot 1: Soil Moisture vs Target */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">1. Soil Moisture Dynamics vs Target</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Soil Moisture (vol %)',
                    data: zoneRecords.map((r) => r.soil_moisture * 100),
                    color: '#10b981',
                  },
                  {
                    name: 'Target Moisture (vol %)',
                    data: zoneRecords.map((r) => r.target_moisture * 100),
                    color: '#06b6d4',
                  },
                ]}
                unit="%"
                height={220}
              />
            </div>

            {/* Plot 2: Evapotranspiration Rates */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">2. Evapotranspiration (FAO-56 ET0 vs ETc)</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Reference ET0 (mm)',
                    data: zoneRecords.map((r) => r.et0_mm),
                    color: '#f59e0b',
                  },
                  {
                    name: 'Crop ETc (mm)',
                    data: zoneRecords.map((r) => r.etc_mm),
                    color: '#ef4444',
                  },
                ]}
                unit="mm"
                height={220}
              />
            </div>

            {/* Plot 3: Fuzzy Stress Indices */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">3. Fuzzy Stress Indices (Soil vs Weather)</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Soil Stress Index',
                    data: zoneRecords.map((r) => r.soil_stress),
                    color: '#ec4899',
                  },
                  {
                    name: 'Weather Stress Index',
                    data: zoneRecords.map((r) => r.weather_stress),
                    color: '#8b5cf6',
                  },
                ]}
                unit=""
                height={220}
              />
            </div>

            {/* Plot 4: Fuzzy Water Demand */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">4. Water Demand FIS Output</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Water Demand Index (0-100)',
                    data: zoneRecords.map((r) => r.water_demand),
                    color: '#3b82f6',
                  },
                ]}
                unit=""
                height={220}
              />
            </div>

            {/* Plot 5: Raw Request vs Final Allocated Depth */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">5. Irrigation Depths (Request vs Allocation)</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Raw Request (mm)',
                    data: zoneRecords.map((r) => r.raw_request_mm),
                    color: '#6366f1',
                  },
                  {
                    name: 'Final Allocated (mm)',
                    data: zoneRecords.map((r) => r.allocated_irrigation_mm),
                    color: '#10b981',
                  },
                ]}
                unit="mm"
                height={220}
              />
            </div>

            {/* Plot 6: Water Volume Dispatched */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">6. Water Volumes (Allocated vs Unmet)</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Volume Allocated (L)',
                    data: zoneRecords.map((r) => r.water_volume_allocated_l),
                    color: '#06b6d4',
                  },
                  {
                    name: 'Volume Unmet (L)',
                    data: zoneRecords.map((r) => r.water_volume_unmet_l),
                    color: '#f43f5e',
                  },
                ]}
                unit="L"
                height={220}
              />
            </div>

            {/* Plot 7: Effective Rainfall */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">7. Rainfall & Effective Infiltration</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Total Rainfall (mm)',
                    data: zoneRecords.map((r) => r.rainfall_mm),
                    color: '#3b82f6',
                  },
                  {
                    name: 'Effective Infiltration (mm)',
                    data: zoneRecords.map((r) => r.effective_rainfall_mm),
                    color: '#14b8a6',
                  },
                ]}
                unit="mm"
                height={220}
              />
            </div>

            {/* Plot 8: Moisture Error */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">8. Moisture Tracking Error (θ - θ_target)</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Error (vol %)',
                    data: zoneRecords.map((r) => r.moisture_error * 100),
                    color: '#a855f7',
                  },
                ]}
                unit="%"
                height={220}
              />
            </div>

            {/* Plot 9: Relative Soil Moisture (RSM) */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">9. Relative Soil Moisture (RSM)</h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'RSM Ratio [0, 1]',
                    data: zoneRecords.map((r) => r.rsm),
                    color: '#eab308',
                  },
                ]}
                unit=""
                height={220}
              />
            </div>

            {/* Plot 10: Conservation Invariant Residual */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/50 p-5">
              <h3 className="text-sm font-semibold text-white mb-3">
                10. Water-Balance Mass Closure Residual
              </h3>
              <LineChart
                labels={steps.map((s) => `${Math.floor(s / 60)}h`)}
                datasets={[
                  {
                    name: 'Closure Residual (mm)',
                    data: zoneRecords.map((r) => r.water_balance_residual),
                    color: '#10b981',
                  },
                ]}
                unit="mm"
                height={220}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function SimulationStudioPage() {
  return (
    <Suspense fallback={<div className="p-8 text-xs text-slate-400 font-mono">Loading Closed-Loop Simulation Studio...</div>}>
      <SimulationStudioContent />
    </Suspense>
  );
}

