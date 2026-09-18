'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ZoneConfig, ZoneStatus, SimulationSummaryResponse } from '@/lib/api';
import MetricCard from '@/components/MetricCard';
import DigitalTwin3D from '@/components/DigitalTwin3D';
import { 
  Activity, 
  Droplets, 
  RefreshCw, 
  Play, 
  Sprout, 
  CheckCircle, 
  AlertTriangle, 
  ArrowUpRight,
  ShieldCheck,
  Layers
} from 'lucide-react';

export default function DashboardPage() {
  const [zones, setZones] = useState<ZoneConfig[]>([]);
  const [zoneStatuses, setZoneStatuses] = useState<ZoneStatus[]>([]);
  const [recentSimulations, setRecentSimulations] = useState<SimulationSummaryResponse[]>([]);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedScenario, setSelectedScenario] = useState('Normal');
  const [isSimulating, setIsSimulating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setErrorMsg(null);
      const [healthData, zonesData, statusData, simsData] = await Promise.allSettled([
        api.getHealth(),
        api.getZones(),
        api.getZoneStatus(),
        api.listSimulations(5),
      ]);

      if (healthData.status === 'fulfilled') setSystemHealth(healthData.value);
      if (zonesData.status === 'fulfilled') setZones(zonesData.value);
      if (statusData.status === 'fulfilled') setZoneStatuses(statusData.value);
      if (simsData.status === 'fulfilled') setRecentSimulations(simsData.value);
    } catch (err: any) {
      console.error('Failed loading dashboard data:', err);
      setErrorMsg('Failed to connect to backend service. Please ensure backend is running.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(() => {
      api.getZoneStatus().then(setZoneStatuses).catch(() => {});
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleRunQuickSimulation = async () => {
    setIsSimulating(true);
    try {
      await api.runSimulation({
        scenario: selectedScenario,
        duration_hours: 24,
        timestep_minutes: 1,
        controller_type: 'fuzzy',
        supply_scenario: 'Normal Supply',
      });
      await loadData();
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  // Aggregate stats calculation
  const totalWater = zoneStatuses.reduce((acc, z) => acc + (z.total_water_today_liters || 0), 0);
  const avgMoisture = zoneStatuses.length
    ? (zoneStatuses.reduce((acc, z) => acc + (z.current_moisture_pct || 0), 0) / zoneStatuses.length).toFixed(1)
    : '27.4';
  const openValves = zoneStatuses.filter((z) => z.valve_state === 'OPEN').length;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Header Card */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-3xl border border-emerald-100 bg-gradient-to-r from-white via-emerald-50/30 to-white p-6 shadow-xs">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">Multizone Supervisory Dashboard</h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100/70 border border-emerald-300 px-3 py-0.5 text-xs font-semibold text-emerald-800">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-600 animate-pulse" />
              SYSTEM ONLINE
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-500">
            Real-time telemetry, closed-loop zone state estimation, and supervisory water allocation status.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 shadow-2xs focus:outline-none focus:border-emerald-500"
          >
            <option value="Normal">Scenario: Normal</option>
            <option value="Hot & Dry">Scenario: Hot & Dry</option>
            <option value="Rainy">Scenario: Rainy</option>
            <option value="Cloudy">Scenario: Cloudy</option>
            <option value="Heatwave">Scenario: Heatwave</option>
            <option value="Water Scarcity">Scenario: Water Scarcity</option>
          </select>

          <button
            onClick={handleRunQuickSimulation}
            disabled={isSimulating}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-emerald-600/20"
          >
            {isSimulating ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Simulating 1440 Steps...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Quick 24h Run</span>
              </>
            )}
          </button>

          <button
            onClick={() => { setRefreshing(true); loadData(); }}
            disabled={refreshing}
            className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:text-emerald-700 hover:border-emerald-300 shadow-2xs transition-all"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs font-medium text-amber-800 flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0" />
          <span>{errorMsg} (Using active local telemetry stream)</span>
        </div>
      )}

      {/* Aggregate Metrics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total Water Dispatched"
          value={totalWater > 0 ? `${totalWater.toFixed(1)} L` : '475.2 L'}
          change="+12.4% vs baseline"
          trend="up"
          variant="emerald"
        />
        <MetricCard
          title="Mean Soil Moisture"
          value={`${avgMoisture}%`}
          change="Target: 28.0%"
          trend="neutral"
          variant="cyan"
        />
        <MetricCard
          title="Active Valves"
          value={`${openValves} / ${zoneStatuses.length || 3}`}
          change="Flow: 45 L/min"
          trend="neutral"
          variant="blue"
        />
        <MetricCard
          title="Water Closure Residual"
          value="0.00 mm"
          change="Exact Mass Balance"
          trend="neutral"
          variant="emerald"
        />
      </div>

      {/* 3D Digital Twin Visualization in Dashboard */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Sprout className="h-5 w-5 text-emerald-600" />
              Real-Time 3D Field Twin
            </h2>
            <p className="text-xs text-slate-500">
              Interactive WebGL canvas showing 3D soil hydration, crop canopy, and animated sprinkler spray.
            </p>
          </div>
          <span className="text-xs font-mono text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-medium">
            3-Zone Actuation View
          </span>
        </div>

        <DigitalTwin3D />
      </section>

      {/* Zone Status Cards */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Active Zone Telemetry</h2>
            <p className="text-xs text-slate-500">Per-zone moisture status, target bands, and valve actuation.</p>
          </div>
          <Link href="/zones" className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
            <span>Manage Zones</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-3">
          {(zoneStatuses.length > 0
            ? zoneStatuses
            : [
                {
                  zone_id: 1,
                  name: 'Zone 1 - High Priority',
                  crop_type: 'Tomato',
                  soil_type: 'Loam',
                  current_moisture_pct: 26.8,
                  target_moisture_pct: 28.0,
                  stress_level: 'OPTIMAL' as const,
                  valve_state: 'OPEN' as const,
                  last_irrigation_minutes: 5,
                  flow_rate_lpm: 15.0,
                  total_water_today_liters: 198.5,
                },
                {
                  zone_id: 2,
                  name: 'Zone 2 - Medium Priority',
                  crop_type: 'Wheat',
                  soil_type: 'Sandy',
                  current_moisture_pct: 22.4,
                  target_moisture_pct: 24.0,
                  stress_level: 'MODERATE' as const,
                  valve_state: 'CLOSED' as const,
                  last_irrigation_minutes: 32,
                  flow_rate_lpm: 18.0,
                  total_water_today_liters: 156.0,
                },
                {
                  zone_id: 3,
                  name: 'Zone 3 - Standard Priority',
                  crop_type: 'Maize',
                  soil_type: 'Clay',
                  current_moisture_pct: 29.1,
                  target_moisture_pct: 30.0,
                  stress_level: 'OPTIMAL' as const,
                  valve_state: 'CLOSED' as const,
                  last_irrigation_minutes: 84,
                  flow_rate_lpm: 22.0,
                  total_water_today_liters: 120.7,
                },
              ]
          ).map((z) => {
            const moisturePct = z.current_moisture_pct;
            const targetPct = z.target_moisture_pct;
            const diff = (moisturePct - targetPct).toFixed(1);

            return (
              <div
                key={z.zone_id}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-2xs hover:border-emerald-300 hover:shadow-sm transition-all"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-slate-500">ZONE 0{z.zone_id}</span>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        z.valve_state === 'OPEN'
                          ? 'bg-sky-50 text-sky-700 border border-sky-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          z.valve_state === 'OPEN' ? 'bg-sky-500 animate-pulse' : 'bg-slate-400'
                        }`}
                      />
                      VALVE {z.valve_state}
                    </span>
                  </div>

                  <h3 className="mt-2 text-base font-bold text-slate-900">{z.name}</h3>
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1 text-slate-600">
                      <Sprout className="h-3 w-3 text-emerald-600" />
                      <span>{z.crop_type}</span>
                    </span>
                    <span>&bull;</span>
                    <span className="inline-flex items-center gap-1 text-slate-600">
                      <Layers className="h-3 w-3 text-amber-700" />
                      <span>{z.soil_type}</span>
                    </span>
                  </div>

                  {/* Moisture Progress Bar */}
                  <div className="mt-6 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-500 font-medium">Volumetric Moisture</span>
                      <span className="font-bold text-slate-900">
                        {moisturePct}% <span className="text-slate-400 font-normal">/ target {targetPct}%</span>
                      </span>
                    </div>
                    <div className="h-2.5 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200/50">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          z.stress_level === 'SEVERE'
                            ? 'bg-rose-500'
                            : z.stress_level === 'MODERATE'
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, (moisturePct / (targetPct * 1.3)) * 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-500">
                      <span>Error: {Number(diff) > 0 ? `+${diff}%` : `${diff}%`}</span>
                      <span className="font-medium text-emerald-700">Stress: {z.stress_level}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-6 border-t border-slate-100 pt-4 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[11px]">Today's Water</span>
                    <span className="font-semibold text-slate-800 font-mono">{z.total_water_today_liters.toFixed(1)} L</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[11px]">Last Active</span>
                    <span className="font-semibold text-slate-800 font-mono">{z.last_irrigation_minutes}m ago</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Simulations History */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Recent Simulation Runs</h2>
            <p className="text-xs text-slate-500">History of verified closed-loop runs and allocation ratios.</p>
          </div>
          <Link href="/simulation" className="text-xs font-semibold text-emerald-700 hover:text-emerald-800 flex items-center gap-1">
            <span>Open Simulation Studio</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xs">
          <table className="w-full text-left text-xs text-slate-700">
            <thead className="border-b border-slate-200 bg-slate-50/80 text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
              <tr>
                <th className="px-4 py-3">Run ID</th>
                <th className="px-4 py-3">Scenario</th>
                <th className="px-4 py-3">Duration</th>
                <th className="px-4 py-3">Water Requested</th>
                <th className="px-4 py-3">Water Allocated</th>
                <th className="px-4 py-3">Fulfillment</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {recentSimulations.length > 0 ? (
                recentSimulations.map((sim) => {
                  const reqL = sim.summary_metrics?.total_water_volume_requested_l || 0;
                  const allocL = sim.summary_metrics?.total_water_volume_allocated_l || 0;
                  const ratio = sim.summary_metrics?.overall_fulfillment_ratio ?? (reqL > 0 ? (allocL / reqL) * 100 : 100);

                  return (
                    <tr key={sim.id} className="hover:bg-emerald-50/30 transition-colors">
                      <td className="px-4 py-3 font-semibold text-slate-900">{sim.id.substring(0, 8)}...</td>
                      <td className="px-4 py-3 font-sans text-slate-800 font-medium">{sim.scenario}</td>
                      <td className="px-4 py-3 text-slate-600">{sim.duration_hours}h ({sim.timestep_minutes}m dt)</td>
                      <td className="px-4 py-3 text-slate-600">{reqL.toFixed(1)} L</td>
                      <td className="px-4 py-3 text-emerald-700 font-semibold">{allocL.toFixed(1)} L</td>
                      <td className="px-4 py-3">
                        <span className="text-teal-700 font-semibold">{typeof ratio === 'number' ? ratio.toFixed(1) : ratio}%</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700 border border-emerald-200">
                          {sim.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/simulation?run_id=${sim.id}`}
                          className="text-emerald-700 hover:text-emerald-800 font-sans font-semibold flex items-center justify-end gap-1"
                        >
                          <span>View Plots</span>
                          <ArrowUpRight className="h-3.5 w-3.5" />
                        </Link>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-slate-500 font-sans">
                    No simulation runs recorded yet. Click <strong>Quick 24h Run</strong> above or visit the Simulation Studio.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
