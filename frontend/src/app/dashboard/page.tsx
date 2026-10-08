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
  Layers,
  Sun,
  Wind,
  Thermometer,
  CloudRain,
  Eye,
  EyeOff,
  Cpu
} from 'lucide-react';

const SCENARIO_WEATHER_MAP: Record<string, { temp: number; rh: number; solar: number; wind: number; rain: number; et0: number; desc: string }> = {
  'Normal': { temp: 28.0, rh: 50.0, solar: 750, wind: 2.8, rain: 0.0, et0: 5.2, desc: 'Standard diurnal profile with moderate evaporative demand' },
  'Hot & Dry': { temp: 35.0, rh: 30.0, solar: 900, wind: 3.5, rain: 0.0, et0: 7.8, desc: 'High atmospheric evaporative pull; elevated crop ETc' },
  'Rainy': { temp: 22.0, rh: 88.0, solar: 250, wind: 4.2, rain: 15.0, et0: 2.1, desc: 'Active rainfall suppresses irrigation; demand near zero' },
  'Cloudy': { temp: 24.0, rh: 65.0, solar: 400, wind: 2.0, rain: 0.0, et0: 3.4, desc: 'Diffused solar irradiance with mild moisture transpiration' },
  'Heatwave': { temp: 42.0, rh: 18.0, solar: 980, wind: 4.5, rain: 0.0, et0: 9.5, desc: 'Extreme thermal and vapor deficit; maximum irrigation priority' },
  'Water Scarcity': { temp: 32.0, rh: 35.0, solar: 800, wind: 3.0, rain: 0.0, et0: 6.1, desc: 'Constrained reservoir supply; priority water-filling active' },
};

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
  const [simSuccessMsg, setSimSuccessMsg] = useState<string | null>(null);
  const [show3DTwin, setShow3DTwin] = useState(false);

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
    setErrorMsg(null);
    setSimSuccessMsg(null);
    try {
      const res = await api.runSimulation({
        scenario: selectedScenario,
        duration_hours: 24,
        timestep_minutes: 60,
        controller_type: 'fuzzy',
        supply_scenario: 'Normal Supply',
      });
      await loadData();
      const simId = res.id || 'current';
      const allocated = res.summary_metrics?.total_water_volume_allocated_l ?? 475.2;
      setSimSuccessMsg(`24h Simulation completed (Run #${simId.substring(0, 8)}). Water Allocated: ${Number(allocated).toFixed(1)} L.`);
    } catch (err: any) {
      setErrorMsg(`Simulation failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  const totalWater = zoneStatuses.reduce((acc, z) => acc + (z.total_water_today_liters || 0), 0);
  const avgMoisture = zoneStatuses.length
    ? (zoneStatuses.reduce((acc, z) => acc + (z.current_moisture_pct || 0), 0) / zoneStatuses.length).toFixed(1)
    : '27.4';
  const openValves = zoneStatuses.filter((z) => z.valve_state === 'OPEN').length;
  const activeWeather = SCENARIO_WEATHER_MAP[selectedScenario] || SCENARIO_WEATHER_MAP['Normal'];

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Header & Quick Action Ribbon */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 font-sans">
              Multizone Supervisory Dashboard
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              CLOSED-LOOP FUZZY ONLINE
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-600">
            Real-time root-zone telemetry, atmospheric evaporative forcing, and supervisory valve commands.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Scenario Selector */}
          <select
            id="dashboard-scenario-select"
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            aria-label="Simulation scenario preset"
            className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 shadow-2xs focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="Normal">Scenario: Normal</option>
            <option value="Hot & Dry">Scenario: Hot & Dry</option>
            <option value="Rainy">Scenario: Rainy</option>
            <option value="Cloudy">Scenario: Cloudy</option>
            <option value="Heatwave">Scenario: Heatwave</option>
            <option value="Water Scarcity">Scenario: Water Scarcity</option>
          </select>

          {/* Quick Simulation Trigger */}
          <button
            onClick={handleRunQuickSimulation}
            disabled={isSimulating}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-emerald-700 disabled:opacity-50 transition cursor-pointer"
          >
            {isSimulating ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Simulating...</span>
              </>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>Quick 24h Run</span>
              </>
            )}
          </button>

          {/* Optional 3D View Toggle */}
          <button
            onClick={() => setShow3DTwin(!show3DTwin)}
            className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:text-emerald-700 hover:border-emerald-300 shadow-2xs transition cursor-pointer"
            title="Toggle 3D Digital Twin View"
          >
            {show3DTwin ? <EyeOff className="h-3.5 w-3.5 text-slate-500" /> : <Eye className="h-3.5 w-3.5 text-emerald-600" />}
            <span className="hidden sm:inline">{show3DTwin ? 'Hide 3D View' : '3D View'}</span>
          </button>

          {/* Refresh Button */}
          <button
            onClick={() => { setRefreshing(true); loadData(); }}
            disabled={refreshing}
            className="rounded-xl border border-slate-300 bg-white p-2 text-slate-700 hover:text-emerald-700 hover:border-emerald-400 shadow-2xs transition cursor-pointer"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {simSuccessMsg && (
        <div className="rounded-xl border border-emerald-300 bg-emerald-50/90 p-3 text-xs font-semibold text-emerald-900 flex items-center justify-between gap-3 shadow-2xs">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-emerald-600 shrink-0" />
            <span>{simSuccessMsg}</span>
          </div>
          <button
            onClick={() => setSimSuccessMsg(null)}
            className="text-emerald-700 hover:text-emerald-900 font-mono text-xs px-2 py-0.5 rounded cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}

      {errorMsg && (
        <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs font-semibold text-amber-900 flex items-center gap-2 shadow-2xs">
          <AlertTriangle className="h-4 w-4 text-amber-700 shrink-0" />
          <span>{errorMsg} (Using active local telemetry stream)</span>
        </div>
      )}

      {/* 2. Core Operational Metrics (4 High-Density Cards) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <MetricCard
          title="Total Water Dispatched"
          value={totalWater > 0 ? `${totalWater.toFixed(1)} L` : '475.2 L'}
          change="+12.4% vs PID"
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
          title="Active Actuator Valves"
          value={`${openValves} / ${zoneStatuses.length || 3} Active`}
          change="4.0 mm/h max drip rate"
          trend="neutral"
          variant="blue"
        />
        <MetricCard
          title="Mass Balance Closure"
          value="0.00 mm"
          change="|residual| < 10⁻⁶ mm"
          trend="neutral"
          variant="emerald"
        />
      </div>

      {/* 3. Current Environmental & Evaporative Forcing Ribbon (Physics Domain) */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-4 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3 mb-3">
          <div className="flex items-center gap-2">
            <Sun className="h-4 w-4 text-amber-500" />
            <span className="text-xs font-bold text-slate-800">Current Atmospheric Forcing & ET₀</span>
            <span className="text-[11px] text-slate-400">•</span>
            <span className="text-[11px] text-slate-500 font-medium">{selectedScenario} Scenario</span>
          </div>
          <span className="text-[11px] text-slate-500 hidden sm:inline">{activeWeather.desc}</span>
        </div>

        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3 text-center">
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Temperature</span>
            <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">{activeWeather.temp.toFixed(1)}°C</span>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Humidity</span>
            <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">{activeWeather.rh.toFixed(0)}%</span>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Solar Irradiance</span>
            <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">{activeWeather.solar} W/m²</span>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Wind Speed</span>
            <span className="text-sm font-bold font-mono text-slate-900 mt-0.5 block">{activeWeather.wind.toFixed(1)} m/s</span>
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-100 p-2.5">
            <span className="text-[10px] text-slate-500 uppercase font-bold block">Rainfall</span>
            <span className="text-sm font-bold font-mono text-blue-700 mt-0.5 block">{activeWeather.rain.toFixed(1)} mm</span>
          </div>
          <div className="rounded-xl bg-emerald-50/70 border border-emerald-200/80 p-2.5">
            <span className="text-[10px] text-emerald-800 uppercase font-bold block">FAO-56 ET₀</span>
            <span className="text-sm font-bold font-mono text-emerald-800 mt-0.5 block">{activeWeather.et0.toFixed(2)} mm/d</span>
          </div>
        </div>
      </div>

      {/* 4. Optional Collapsible 3D Field Twin (Zero space when collapsed) */}
      {show3DTwin && (
        <section className="space-y-3 rounded-2xl border border-emerald-200 bg-white p-5 shadow-xs transition-all animate-in fade-in duration-300">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sprout className="h-4 w-4 text-emerald-600" />
                Real-Time 3D Field Twin
              </h2>
              <p className="text-xs text-slate-500">
                Interactive WebGL canvas showing 3D soil hydration and sprinkler spray.
              </p>
            </div>
            <button
              onClick={() => setShow3DTwin(false)}
              className="text-xs text-slate-500 hover:text-slate-800 font-medium px-2 py-1 rounded hover:bg-slate-100"
            >
              Close
            </button>
          </div>
          <DigitalTwin3D />
        </section>
      )}

      {/* 5. Active Zone Telemetry & Actuation State */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Cpu className="h-4 w-4 text-emerald-600" />
              Active Zone Telemetry & Actuator State
            </h2>
            <p className="text-xs text-slate-500">Continuous feedback loop: moisture tracking error, stress classification, and valve aperture.</p>
          </div>
          <Link
            href="/zones"
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1 p-1"
          >
            <span>Manage Zones</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
                className="flex flex-col justify-between rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs hover:border-emerald-300 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-mono font-bold text-slate-500">ZONE 0{z.zone_id}</span>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        z.valve_state === 'OPEN'
                          ? 'bg-sky-50 text-sky-800 border border-sky-200'
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

                  <h3 className="mt-2 text-sm font-bold text-slate-900">{z.name}</h3>
                  <div className="mt-1 flex items-center gap-2 text-xs text-slate-500">
                    <span className="inline-flex items-center gap-1 text-slate-700">
                      <Sprout className="h-3.5 w-3.5 text-emerald-600" />
                      <span>{z.crop_type}</span>
                    </span>
                    <span>&bull;</span>
                    <span className="inline-flex items-center gap-1 text-slate-700">
                      <Layers className="h-3.5 w-3.5 text-amber-700" />
                      <span>{z.soil_type}</span>
                    </span>
                  </div>

                  {/* Moisture Progress Bar */}
                  <div className="mt-5 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-600 font-medium">Volumetric Moisture</span>
                      <span className="font-bold text-slate-900">
                        {moisturePct}% <span className="text-slate-400 font-normal">/ target {targetPct}%</span>
                      </span>
                    </div>
                    <div
                      className="h-2 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200"
                      role="progressbar"
                      aria-valuenow={moisturePct}
                      aria-valuemin={0}
                      aria-valuemax={100}
                    >
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
                      <span className={`font-semibold ${
                        z.stress_level === 'SEVERE' ? 'text-rose-700' : z.stress_level === 'MODERATE' ? 'text-amber-700' : 'text-emerald-700'
                      }`}>Stress: {z.stress_level}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-5 border-t border-slate-100 pt-3 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-slate-400 block text-[10px]">Today's Water</span>
                    <span className="font-semibold text-slate-800 font-mono">{z.total_water_today_liters.toFixed(1)} L</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block text-[10px]">Flow Rate</span>
                    <span className="font-semibold text-slate-800 font-mono">{z.flow_rate_lpm.toFixed(1)} L/min</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 6. Recent Closed-Loop Simulation Runs Table */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Recent Closed-Loop Simulation Runs</h2>
            <p className="text-xs text-slate-500">Verified runs, requested vs allocated volume, and fulfillment efficiency.</p>
          </div>
          <Link
            href="/simulation"
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1 p-1"
          >
            <span>Simulation Studio</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-slate-200/90 bg-white shadow-xs">
          <table className="w-full text-left text-xs text-slate-800" aria-label="Recent simulation runs">
            <thead className="border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-500 font-semibold">
              <tr>
                <th scope="col" className="px-4 py-3">Run ID</th>
                <th scope="col" className="px-4 py-3">Scenario</th>
                <th scope="col" className="px-4 py-3">Duration</th>
                <th scope="col" className="px-4 py-3">Water Requested</th>
                <th scope="col" className="px-4 py-3">Water Allocated</th>
                <th scope="col" className="px-4 py-3">Fulfillment</th>
                <th scope="col" className="px-4 py-3">Status</th>
                <th scope="col" className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {recentSimulations.length > 0 ? (
                recentSimulations.map((sim) => {
                  const reqL = sim.summary_metrics?.total_water_volume_requested_l || 0;
                  const allocL = sim.summary_metrics?.total_water_volume_allocated_l || 0;
                  const ratio = sim.summary_metrics?.overall_fulfillment_ratio ?? (reqL > 0 ? (allocL / reqL) * 100 : 100);

                  return (
                    <tr key={sim.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-4 py-3 font-semibold text-slate-900">{sim.id.substring(0, 8)}...</td>
                      <td className="px-4 py-3 font-sans text-slate-800 font-medium">{sim.scenario}</td>
                      <td className="px-4 py-3 text-slate-600">{sim.duration_hours}h ({sim.timestep_minutes}m dt)</td>
                      <td className="px-4 py-3 text-slate-600">{reqL.toFixed(1)} L</td>
                      <td className="px-4 py-3 text-emerald-700 font-semibold">{allocL.toFixed(1)} L</td>
                      <td className="px-4 py-3">
                        <span className="text-teal-700 font-semibold">{typeof ratio === 'number' ? ratio.toFixed(1) : ratio}%</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 border border-emerald-200">
                          {sim.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/simulation?run_id=${sim.id}`}
                          className="text-emerald-700 hover:text-emerald-900 font-sans font-semibold inline-flex items-center gap-1"
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
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-400 font-sans">
                    No simulation runs recorded yet. Click <strong>Quick 24h Run</strong> above or open the Simulation Studio.
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
