'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { api } from '@/lib/api';
import Link from 'next/link';
import { Network, Scale, ArrowDown, CheckCircle2, Settings2, PlayCircle, GitBranch, FlaskConical, FileCheck2, ChevronLeft, ChevronRight, Play, Save, SlidersHorizontal } from 'lucide-react';

export default function ArchitecturePage() {
  return (
    <div className="space-y-10 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200/80">
            Control Systems Theory
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-500 font-medium">Live verification available</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 font-sans">
          System Architecture & Mathematical Foundations
        </h1>
        <p className="mt-2 text-base text-slate-600">
          Theoretical framework, hierarchical control topology, and rigorous invariant proofs of the Smart Multizone Fuzzy Irrigation Platform.
        </p>
      </div>

      {/* High-Level Architecture Flowchart */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-8 shadow-xs space-y-6">
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Network className="h-5 w-5 text-emerald-600" />
          <span>Hierarchical Control Topology</span>
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-xs font-mono">
          {/* Layer 1: Physics */}
          <div className="rounded-xl bg-sky-50/60 p-5 border border-sky-200/80 space-y-2 shadow-2xs">
            <span className="text-[10px] text-sky-800 uppercase font-bold block">Layer 1 • Physical Domain</span>
            <h3 className="text-sm font-bold text-slate-900 font-sans">Meteorology & Soil Balance</h3>
            <p className="text-slate-700 text-[11px] font-sans leading-relaxed">
              • Diurnal solar radiation, temperature, RH, wind speed.<br />
              • FAO-56 Penman-Monteith ET0.<br />
              • Crop-specific ETc (Kc coefficient).<br />
              • Dynamic root-zone soil-water mass balance.
            </p>
          </div>

          {/* Layer 2: Zone Fuzzy Controllers */}
          <div className="rounded-xl bg-emerald-50/60 p-5 border border-emerald-200/80 space-y-2 shadow-2xs">
            <span className="text-[10px] text-emerald-800 uppercase font-bold block">Layer 2 • Zone Level</span>
            <h3 className="text-sm font-bold text-slate-900 font-sans">4 Zone-Level Mamdani FIS + 1 Supervisory FIS</h3>
            <p className="text-slate-700 text-[11px] font-sans leading-relaxed">
              • Soil Stress FIS (RSM x Depletion).<br />
              • Weather Stress FIS (T x RH x Wind).<br />
              • Water Demand FIS (Soil x Weather).<br />
              • Main Irrigation FIS (Demand x Error x RSM).
            </p>
          </div>

          {/* Layer 3: Supervisory Water Allocation */}
          <div className="rounded-xl bg-teal-50/60 p-5 border border-teal-200/80 space-y-2 shadow-2xs">
            <span className="text-[10px] text-teal-800 uppercase font-bold block">Layer 3 • Supervisory Level</span>
            <h3 className="text-sm font-bold text-slate-900 font-sans">Supervisory Allocation</h3>
            <p className="text-slate-700 text-[11px] font-sans leading-relaxed">
              • Layer B: Mamdani Scarcity FIS.<br />
              • Layer C: Deterministic Bounded Priority-Weighted Water-Filling.<br />
              • Enforces strict supply and demand invariants.
            </p>
          </div>

          {/* Layer 4: Offline Optimization & Advisory AI */}
          <div className="rounded-xl bg-purple-50/60 p-5 border border-purple-200/80 space-y-2 shadow-2xs">
            <span className="text-[10px] text-purple-800 uppercase font-bold block">Layer 4 • Offline Support</span>
            <h3 className="text-sm font-bold text-slate-900 font-sans">PSO Tuning & Advisory AI</h3>
            <p className="text-slate-700 text-[11px] font-sans leading-relaxed">
              • Offline PSO: 18-parameter calibration.<br />
              • Groq LLM: Telemetry-grounded technical Q&A.<br />
              • ReportLab: Publication-grade PDF audit reports.<br />
              • Strictly advisory & decoupled.
            </p>
          </div>
        </div>
      </div>

      {/* End-to-End System Design & Simulation Workflow */}
      <div className="rounded-2xl border border-emerald-200/80 bg-white p-8 shadow-xs space-y-7">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-800 border border-emerald-200">Design → Simulate → Verify</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <GitBranch className="h-5 w-5 text-emerald-600" />
            End-to-End Fuzzy Irrigation System Design Workflow
          </h2>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed max-w-4xl">
            This is the complete workflow a user follows to design a software-only multizone fuzzy irrigation system from requirements, configure the agronomic plant model and fuzzy controllers, execute the closed-loop simulation, and verify the resulting control system.
          </p>
        </div>

        {/* Requirement contract */}
        <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-5">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Settings2 className="h-4 w-4 text-slate-600" />
            01 — Define the irrigation requirements
          </h3>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-[11px]">
            {[
              ['Farm layout', 'Number of zones, zone area and active zones'],
              ['Crop requirements', 'Crop, Kc, root depth and growth stage'],
              ['Soil requirements', 'Texture, FC, WP, saturation and infiltration'],
              ['Control objectives', 'Target moisture, priority and actuator limits'],
              ['Environment', 'Weather scenario, rainfall and ET demand'],
              ['Water resource', 'Supply scenario and scarcity constraints'],
              ['Simulation', 'Duration, timestep and reproducibility seed'],
              ['Controller', 'Hierarchical fuzzy or comparison controller'],
            ].map(([title, body]) => (
              <div key={title} className="rounded-lg bg-white border border-slate-200 p-3">
                <div className="font-bold text-slate-800">{title}</div>
                <div className="mt-1 text-slate-500 leading-relaxed">{body}</div>
              </div>
            ))}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Link href="/zones" className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-2 text-[11px] font-bold text-white hover:bg-emerald-700 transition-colors">
              Configure Zones <span>→</span>
            </Link>
            <Link href="/simulation" className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-[11px] font-bold text-slate-700 hover:border-emerald-300 transition-colors">
              Configure Simulation <span>→</span>
            </Link>
          </div>
        </div>

        {/* Sequential workflow */}
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-900">02–09 — Transform requirements into a closed-loop controller</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              ['02', 'Environment & preprocessing', 'Generate T, RH, radiation, wind and rainfall; prepare the environmental timeline.', 'Physical model', '/simulation'],
              ['03', 'ET₀ → ETc', 'Compute reference evapotranspiration using FAO-56 Penman-Monteith and crop demand using Kc.', 'models/et0.py + etc.py', '/simulation'],
              ['04', 'Soil-water plant model', 'Initialize each zone and propagate storage, infiltration, actual ET and drainage through the water balance.', 'models/soil.py + water_balance.py', '/dashboard'],
              ['05', 'Fuzzy inference', 'Fuzzify inputs, evaluate the linguistic rule base, aggregate consequents and defuzzify each FIS output.', '5 Mamdani FIS', '/fuzzy'],
              ['06', 'Zone irrigation command', 'Combine demand, weather/soil stress and tracking error into a normalized irrigation command.', 'Main Irrigation FIS', '/fuzzy'],
              ['07', 'Supervisory allocation', 'Coordinate zone requests under shared supply using scarcity inference and bounded priority-weighted water filling.', 'Allocation FIS + Layer C', '/allocation'],
              ['08', 'Virtual actuation + feedback', 'Apply allocated water to each zone, update the soil state, and feed the new state into the next timestep.', 'Closed-loop simulation', '/simulation'],
              ['09', 'Evaluate & document', 'Measure tracking, water use, unmet demand, conservation residuals, scenario performance and generate the engineering report.', 'Validation + reporting', '/reports'],
            ].map(([n, title, body, tech, href]) => (
              <Link href={href} key={n} className="group rounded-xl border border-slate-200 bg-white p-4 hover:border-emerald-300 hover:shadow-sm transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 rounded px-2 py-0.5">STEP {n}</span>
                  <ArrowDown className="h-3.5 w-3.5 text-slate-300 group-hover:text-emerald-500 transition-colors" />
                </div>
                <h4 className="mt-3 text-xs font-bold text-slate-900">{title}</h4>
                <p className="mt-1.5 text-[11px] leading-relaxed text-slate-600">{body}</p>
                <div className="mt-3 text-[9px] font-mono text-slate-400">{tech}</div>
              </Link>
            ))}
          </div>
        </div>

        {/* Closed loop */}
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
          <div className="flex items-center gap-2 text-sm font-bold text-emerald-900">
            <PlayCircle className="h-4 w-4" />
            10 — Execute the complete simulation loop
          </div>
          <div className="mt-4 flex flex-col md:flex-row md:items-center gap-2 text-[11px] font-mono">
            {['Requirements', 'Weather', 'ET₀ / ETc', 'Soil State', '5 FIS', 'Allocation', 'Irrigation', 'State Update', 'Feedback'].map((item, i, arr) => (
              <React.Fragment key={item}>
                <div className="rounded-lg border border-emerald-200 bg-white px-3 py-2 text-center font-bold text-slate-700 shadow-2xs">{item}</div>
                {i < arr.length - 1 && <span className="hidden md:block text-emerald-500 font-bold">→</span>}
              </React.Fragment>
            ))}
          </div>
          <div className="mt-3 text-[11px] text-slate-600 leading-relaxed">
            Repeat the state transition at every configured timestep. The output of one timestep is not used to predict the future state; it becomes the causal initial state of the next timestep. This is the closed-loop control path.
          </div>
          <div className="mt-4">
            <Link href="/simulation" className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-[11px] font-bold text-white hover:bg-slate-800 transition-colors">
              <PlayCircle className="h-3.5 w-3.5" /> Run Closed-Loop Simulation
            </Link>
          </div>
        </div>

        {/* Offline optimization and verification */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="rounded-xl border border-purple-200 bg-purple-50/40 p-5">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><FlaskConical className="h-4 w-4 text-purple-600" /> 11 — Offline PSO tuning</h3>
            <p className="mt-2 text-[11px] leading-relaxed text-slate-600">Use the simulation as the objective-evaluation environment. PSO tunes the defined fuzzy membership parameters offline; the resulting parameters are then used by the online fuzzy controller.</p>
            <Link href="/optimization" className="mt-3 inline-flex text-[11px] font-bold text-purple-800 hover:underline">Open optimization →</Link>
          </div>
          <div className="rounded-xl border border-sky-200 bg-sky-50/40 p-5">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2"><FileCheck2 className="h-4 w-4 text-sky-600" /> 12 — Verify the designed system</h3>
            <p className="mt-2 text-[11px] leading-relaxed text-slate-600">Verify every FIS, numerical model, conservation invariant, multizone interaction, API contract and user-facing feature before accepting the complete design.</p>
            <div className="mt-3 flex flex-wrap gap-2 text-[10px] font-semibold">
              {['FIS inference', 'Mass balance', 'Supply cap', 'Demand ceiling', '3-zone isolation', 'API integration', 'UI flow', 'Report output'].map((x) => <span key={x} className="inline-flex items-center gap-1 rounded-full bg-white border border-sky-200 px-2 py-1 text-sky-800"><CheckCircle2 className="h-3 w-3" />{x}</span>)}
            </div>
          </div>
        </div>
      </div>

      {/* The 5 Fuzzy Inference Subsystems */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-slate-900">The 5 Mamdani Fuzzy Inference Subsystems</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-3 hover:border-emerald-300 hover:shadow-sm transition-all">
            <span className="rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-0.5 text-xs font-semibold">
              FIS 1
            </span>
            <h3 className="text-base font-bold text-slate-900">Soil Stress FIS</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Evaluates physiological moisture deficiency. Takes <strong>Relative Soil Moisture (RSM [0, 1])</strong> and <strong>Management Allowed Depletion (MAD %)</strong> to compute the Soil Stress Index (0–100).
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-3 hover:border-emerald-300 hover:shadow-sm transition-all">
            <span className="rounded-full bg-sky-50 text-sky-800 border border-sky-200 px-2.5 py-0.5 text-xs font-semibold">
              FIS 2
            </span>
            <h3 className="text-base font-bold text-slate-900">Weather Stress FIS</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Quantifies atmospheric evaporative demand. Combines <strong>Air Temperature (°C)</strong>, <strong>Relative Humidity (%)</strong>, and <strong>Wind Speed (m/s)</strong> into the Weather Stress Index (0–100).
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-3 hover:border-emerald-300 hover:shadow-sm transition-all">
            <span className="rounded-full bg-blue-50 text-blue-800 border border-blue-200 px-2.5 py-0.5 text-xs font-semibold">
              FIS 3
            </span>
            <h3 className="text-base font-bold text-slate-900">Water Demand FIS</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Integrates edaphic and atmospheric stresses. Takes <strong>Soil Stress</strong> and <strong>Weather Stress</strong> to synthesize instantaneous Crop Water Demand (0–100).
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-3 hover:border-emerald-300 hover:shadow-sm transition-all">
            <span className="rounded-full bg-purple-50 text-purple-800 border border-purple-200 px-2.5 py-0.5 text-xs font-semibold">
              FIS 4
            </span>
            <h3 className="text-base font-bold text-slate-900">Main Irrigation FIS</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Primary zone actuator decision maker. Evaluates <strong>Water Demand</strong>, <strong>Tracking Error (θ - θ_target)</strong>, and <strong>RSM</strong> to output raw Irrigation Command (0–100%).
            </p>
          </div>

          <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-3 hover:border-emerald-300 hover:shadow-sm transition-all">
            <span className="rounded-full bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-0.5 text-xs font-semibold">
              FIS 5
            </span>
            <h3 className="text-base font-bold text-slate-900">Water Allocation FIS</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Layer B supervisory coordinator. Evaluates <strong>Shared Supply Scarcity (%)</strong> and <strong>Zone Water Request (mm)</strong> to compute raw allocation scaling factor prior to Layer C water-filling.
            </p>
          </div>
        </div>
      </div>

      {/* User-driven end-to-end system designer */}
      <EndToEndDesigner />

      {/* Predefined FIS Library & Explainability */}
      <PredefinedFISLibrary />

      {/* Live Verification Console */}
      <LiveVerificationConsole />

      {/* Mathematical Invariant Proofs */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-8 shadow-xs space-y-6">
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Scale className="h-5 w-5 text-emerald-600" />
          <span>The 5 Supervisory Water Allocation Invariants</span>
        </h2>

        <div className="space-y-4 text-xs text-slate-700">
          <div className="rounded-xl bg-slate-50/80 p-5 border border-slate-200/80 space-y-2 shadow-2xs">
            <h4 className="font-bold text-slate-900 text-sm">Invariant 1: Supply-Cap Strictness</h4>
            <code className="block bg-white border border-slate-200 p-2.5 rounded-lg text-emerald-800 font-mono font-bold shadow-2xs">
              Σ(Allocated_z) ≤ W_available,  ∀ timesteps t (tolerance = 1e-6)
            </code>
            <p className="text-slate-600 leading-relaxed">
              The total volume of water dispatched across all zones cannot exceed the instantaneous shared supply capacity, preventing system pressure collapse.
            </p>
          </div>

          <div className="rounded-xl bg-slate-50/80 p-5 border border-slate-200/80 space-y-2 shadow-2xs">
            <h4 className="font-bold text-slate-900 text-sm">Invariant 2: Demand-Ceiling Strictness</h4>
            <code className="block bg-white border border-slate-200 p-2.5 rounded-lg text-sky-800 font-mono font-bold shadow-2xs">
              0 ≤ Allocated_z ≤ Request_z,  ∀ zones z
            </code>
            <p className="text-slate-600 leading-relaxed">
              No individual zone can receive more irrigation water than its agronomically calculated crop-water demand, preventing root saturation and water wastage.
            </p>
          </div>

          <div className="rounded-xl bg-slate-50/80 p-5 border border-slate-200/80 space-y-2 shadow-2xs">
            <h4 className="font-bold text-slate-900 text-sm">Invariant 3: Zero Artificial Water Creation</h4>
            <code className="block bg-white border border-slate-200 p-2.5 rounded-lg text-blue-800 font-mono font-bold shadow-2xs">
              Request_z = 0 ⇒ Allocated_z = 0,  ∀ zones z
            </code>
            <p className="text-slate-600 leading-relaxed">
              When a zone’s moisture is satisfied (zero demand), it receives exactly 0 mm of water regardless of whether a supply surplus exists.
            </p>
          </div>

          <div className="rounded-xl bg-slate-50/80 p-5 border border-slate-200/80 space-y-2 shadow-2xs">
            <h4 className="font-bold text-slate-900 text-sm">Invariant 4: Zero Supply Preservation</h4>
            <code className="block bg-white border border-slate-200 p-2.5 rounded-lg text-rose-800 font-mono font-bold shadow-2xs">
              W_available = 0 ⇒ Allocated_z = 0,  ∀ zones z
            </code>
            <p className="text-slate-600 leading-relaxed">
              During total supply outages or empty reservoirs, the allocation engine immediately clamps all zone dispatches to 0.00 mm.
            </p>
          </div>

          <div className="rounded-xl bg-slate-50/80 p-5 border border-slate-200/80 space-y-2 shadow-2xs">
            <h4 className="font-bold text-slate-900 text-sm">Invariant 5: Monotonic Priority-Weighted Scarcity Scaling</h4>
            <code className="block bg-white border border-slate-200 p-2.5 rounded-lg text-amber-800 font-mono font-bold shadow-2xs">
              Priority_z1 &gt; Priority_z2  ⇒  (Allocated_z1 / Request_z1) ≥ (Allocated_z2 / Request_z2)
            </code>
            <p className="text-slate-600 leading-relaxed">
              Under constrained water supply, higher-priority cash crops (e.g. Tomato) maintain a strictly higher fulfillment ratio than lower-priority forage crops (e.g. Maize).
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}


function EndToEndDesigner() {
  type Crop = Record<string, any>;
  type Soil = Record<string, any>;
  const [step, setStep] = useState(1);
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [crops, setCrops] = useState<Crop[]>([]);
  const [soils, setSoils] = useState<Soil[]>([]);
  const [fisOverview, setFisOverview] = useState<any[]>([]);
  const [form, setForm] = useState({
    zones: 3,
    objective: 'Balance moisture tracking and water efficiency',
    scenario: 'Normal',
    supplyScenario: 'Normal Supply',
    durationHours: 24,
    timestepMinutes: 1,
    controller: 'fuzzy',
    zonesConfig: [
      { zone_id: 1, name: 'Zone 1', crop: 'Tomato', soil: 'Loam', area_m2: 100, initial_moisture: 24, target_moisture: 28, root_zone_depth: 0.6, kc: 1.15, priority: 90 },
      { zone_id: 2, name: 'Zone 2', crop: 'Potato', soil: 'Sandy Loam', area_m2: 100, initial_moisture: 20, target_moisture: 24, root_zone_depth: 0.5, kc: 1.15, priority: 60 },
      { zone_id: 3, name: 'Zone 3', crop: 'Maize', soil: 'Clay', area_m2: 100, initial_moisture: 27, target_moisture: 31, root_zone_depth: 0.7, kc: 1.20, priority: 40 },
    ],
  });
  const [run, setRun] = useState<any>(null);

  useEffect(() => {
    Promise.all([api.getCrops(), api.getSoils(), api.getFuzzyOverview()]).then(([c, s, f]) => { setCrops(c); setSoils(s); setFisOverview(f); }).catch(() => {});
  }, []);

  const activeZones = form.zonesConfig.slice(0, form.zones);
  const currentZone = activeZones[Math.min(step - 1, activeZones.length - 1)];
  const updateZone = (index: number, patch: Record<string, any>) => {
    setForm(prev => ({ ...prev, zonesConfig: prev.zonesConfig.map((z, i) => i === index ? { ...z, ...patch } : z) }));
  };

  const soilDefaults = (name: string) => {
    const s = soils.find(x => String(x.soil_type || x.soil || '').toLowerCase() === name.toLowerCase());
    return s ? { field_capacity: Number(s.field_capacity_pct), wilting_point: Number(s.wilting_point_pct), saturation: Number(s.saturation_pct) } : { field_capacity: 28, wilting_point: 14, saturation: 46 };
  };

  const cropKc = (name: string) => {
    const c = crops.find(x => String(x.crop || '').toLowerCase() === name.toLowerCase());
    return Number(c?.kc_mid ?? c?.kc ?? 1.0);
  };

  const validateRequirements = () => {
    setError('');
    for (const z of activeZones) {
      if (!(z.area_m2 > 0) || !(z.target_moisture > z.initial_moisture) || !(z.root_zone_depth > 0) || !(z.kc > 0)) {
        setError(`Check ${z.name}: area, root depth and Kc must be positive, and target moisture must be above initial moisture for this design workflow.`);
        return false;
      }
    }
    return true;
  };

  const saveConfiguration = async (advance = true) => {
    if (!validateRequirements()) return false;
    setSaving(true); setError(''); setMessage('');
    try {
      const existing = await api.getZones();
      for (const z of activeZones) {
        const soil = soilDefaults(z.soil);
        const payload = { name: z.name, crop: z.crop, soil: z.soil, area_m2: z.area_m2, ...soil, initial_moisture: z.initial_moisture, target_moisture: z.target_moisture, root_zone_depth: z.root_zone_depth, kc: z.kc, priority: z.priority };
        if (existing.some((e: any) => Number(e.zone_id ?? e.id) === z.zone_id)) await api.updateZone(z.zone_id, payload);
        else await api.createZone({ zone_id: z.zone_id, ...payload });
      }
      setMessage('Requirements saved. The configured zones are now the plant-model inputs for the simulation engine.');
      if (advance) setStep(5);
      return true;
    } catch (e: any) { setError(e.message || 'Could not save the configuration.'); return false; } finally { setSaving(false); }
  };

  const runDesign = async () => {
    if (!validateRequirements()) return;
    setRunning(true); setError(''); setMessage('');
    try {
      const saved = await saveConfiguration(false);
      if (!saved) return;
      const summary = await api.runSimulation({ scenario: form.scenario, duration_hours: form.durationHours, timestep_minutes: form.timestepMinutes, controller_type: form.controller, supply_scenario: form.supplyScenario, seed: 42, zone_ids: activeZones.map(z => z.zone_id) });
      setRun(summary); setStep(6);
      setMessage(`Closed-loop simulation ${summary.id} completed. Results are available in Simulation Studio.`);
    } catch (e: any) { setError(e.message || 'End-to-end simulation failed.'); } finally { setRunning(false); }
  };

  const steps = [
    ['1', 'Requirements', 'Define objective, zones and constraints'],
    ['2', 'Environment', 'Choose weather and shared supply'],
    ['3', 'Plant Model', 'Crop + soil + ET₀/ETc + balance'],
    ['4', 'Fuzzy Design', 'Inspect the five Mamdani FIS layers'],
    ['5', 'Closed Loop', 'Run zone control + allocation + feedback'],
    ['6', 'Verify & Report', 'Inspect results, optimize and export'],
  ];

  return (
    <div className="rounded-2xl border border-emerald-200 bg-gradient-to-b from-emerald-50/50 to-white p-8 shadow-xs space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center rounded-md bg-white px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-800 border border-emerald-200">Interactive system designer</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2"><SlidersHorizontal className="h-5 w-5 text-emerald-600" /> Design → Configure → Simulate → Verify</h2>
          <p className="mt-2 text-sm text-slate-600 max-w-4xl leading-relaxed">Start from an irrigation requirement, configure the agronomic plant model, connect it to the validated hierarchical Mamdani controllers, execute the closed loop and hand the resulting simulation to verification, optimization and reporting.</p>
        </div>
        <div className="text-[10px] font-mono text-slate-500 bg-white border border-slate-200 rounded-lg px-3 py-2">Software-only • 3 zones max in this guided workflow</div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
        {steps.map(([n, title, body]) => (
          <button key={n} onClick={() => setStep(Number(n))} className={`text-left rounded-xl border p-3 transition-all ${step === Number(n) ? 'border-emerald-400 bg-white shadow-sm' : 'border-slate-200 bg-white/70 hover:border-emerald-200'}`}>
            <div className="text-[10px] font-mono font-bold text-emerald-700">STEP {n}</div><div className="mt-1 text-xs font-bold text-slate-900">{title}</div><div className="mt-1 text-[10px] text-slate-500 leading-relaxed">{body}</div>
          </button>
        ))}
      </div>

      {step === 1 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5">
          <div><h3 className="text-sm font-bold text-slate-900">Step 1 — Define irrigation requirements</h3><p className="text-xs text-slate-500 mt-1">These requirements become the configuration contract for the plant and control models.</p></div>
          <div className="grid md:grid-cols-3 gap-4">
            <label className="text-xs font-semibold text-slate-700">Number of zones<select value={form.zones} onChange={e => setForm({...form, zones: Number(e.target.value)})} className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"><option value={1}>1</option><option value={2}>2</option><option value={3}>3</option></select></label>
            <label className="text-xs font-semibold text-slate-700 md:col-span-2">Control objective<select value={form.objective} onChange={e => setForm({...form, objective: e.target.value})} className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"><option>Balance moisture tracking and water efficiency</option><option>Prioritize crop protection under scarcity</option><option>Minimize water consumption</option><option>Maintain target soil moisture</option></select></label>
          </div>
          <div className="grid md:grid-cols-3 gap-3">{activeZones.map((z, i) => <div key={z.zone_id} className="rounded-xl border border-slate-200 p-4"><div className="text-xs font-bold text-slate-900 mb-3">Zone {z.zone_id}</div><div className="grid grid-cols-2 gap-2">{[['name','Name'],['area_m2','Area (m²)'],['initial_moisture','Initial moisture (%)'],['target_moisture','Target moisture (%)'],['root_zone_depth','Root depth (m)'],['priority','Priority (%)']].map(([key,label]) => <label key={key} className="text-[10px] font-semibold text-slate-600">{label}<input type="number" value={(z as any)[key]} onChange={e => updateZone(i,{[key]: key==='name'?e.target.value:Number(e.target.value)})} className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1.5 text-[11px]" /></label>)}<label className="text-[10px] font-semibold text-slate-600 col-span-2">Crop<select value={z.crop} onChange={e => updateZone(i,{crop:e.target.value,kc:cropKc(e.target.value)})} className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1.5 text-[11px]">{(crops.length?crops:[{crop:'Tomato'},{crop:'Wheat'},{crop:'Maize'},{crop:'Potato'},{crop:'Cotton'}]).map((c:any)=><option key={c.crop}>{c.crop}</option>)}</select></label><label className="text-[10px] font-semibold text-slate-600 col-span-2">Soil<select value={z.soil} onChange={e => updateZone(i,{soil:e.target.value})} className="mt-1 w-full rounded-md border border-slate-200 px-2 py-1.5 text-[11px]">{(soils.length?soils:[{soil_type:'Loam'},{soil_type:'Sandy'},{soil_type:'Clay'},{soil_type:'Sandy Loam'}]).map((s:any)=><option key={s.soil_type}>{s.soil_type}</option>)}</select></label></div><div className="mt-3 text-[10px] text-slate-500">Kc = <strong>{Number(z.kc).toFixed(2)}</strong> • priority = <strong>{z.priority}%</strong></div></div>)}</div>
          <div className="flex justify-end"><button onClick={() => { if(validateRequirements()) setStep(2); }} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white">Continue <ChevronRight className="h-3.5 w-3.5" /></button></div>
        </div>
      )}

      {step === 2 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5"><div><h3 className="text-sm font-bold text-slate-900">Step 2 — Environment & resource constraints</h3><p className="text-xs text-slate-500 mt-1">Select the environmental forcing and shared-water condition used by the closed-loop plant.</p></div><div className="grid md:grid-cols-3 gap-4"><label className="text-xs font-semibold text-slate-700">Weather scenario<select value={form.scenario} onChange={e=>setForm({...form,scenario:e.target.value})} className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"><option>Normal</option><option>Hot & Dry</option><option>Rainy</option><option>Cloudy</option><option>Heatwave</option><option>Water Scarcity</option></select></label><label className="text-xs font-semibold text-slate-700">Shared water<select value={form.supplyScenario} onChange={e=>setForm({...form,supplyScenario:e.target.value})} className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"><option>Abundant</option><option>Normal Supply</option><option>Moderate Scarcity</option><option>Severe Scarcity</option><option>Extreme Scarcity</option><option>Zero Supply</option></select></label><label className="text-xs font-semibold text-slate-700">Simulation duration<select value={form.durationHours} onChange={e=>setForm({...form,durationHours:Number(e.target.value)})} className="mt-1.5 w-full rounded-lg border border-slate-200 px-3 py-2 text-xs"><option value={1}>1 hour (verification)</option><option value={6}>6 hours</option><option value={24}>24 hours</option><option value={48}>48 hours</option></select></label></div><div className="rounded-lg bg-sky-50 border border-sky-100 p-4 text-[11px] text-sky-900 leading-relaxed"><strong>Physical pipeline:</strong> weather timeline → FAO-56 ET₀ → crop ETc → rainfall/effective rainfall → dynamic root-zone water balance. The selected supply condition is then applied at the supervisory allocation layer.</div><div className="flex justify-between"><button onClick={()=>setStep(1)} className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold text-slate-700"><ChevronLeft className="h-3.5 w-3.5"/> Back</button><button onClick={()=>setStep(3)} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white">Continue <ChevronRight className="h-3.5 w-3.5"/></button></div></div>
      )}

      {step === 3 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5"><div><h3 className="text-sm font-bold text-slate-900">Step 3 — Build the agronomic plant model</h3><p className="text-xs text-slate-500 mt-1">The selected crop and soil parameters define the dynamic plant state seen by the fuzzy controllers.</p></div><div className="grid md:grid-cols-3 gap-3">{activeZones.map(z=><div key={z.zone_id} className="rounded-xl bg-slate-50 border border-slate-200 p-4"><div className="text-xs font-bold">{z.name}</div><div className="mt-3 space-y-1 text-[11px] text-slate-600"><div>Crop: <strong>{z.crop}</strong> • Kc: <strong>{Number(z.kc).toFixed(2)}</strong></div><div>Soil: <strong>{z.soil}</strong></div><div>Area: <strong>{z.area_m2} m²</strong> • Root depth: <strong>{z.root_zone_depth} m</strong></div><div>Moisture: <strong>{z.initial_moisture}% → {z.target_moisture}%</strong></div><div>Priority: <strong>{z.priority}%</strong></div></div></div>)}</div><div className="grid md:grid-cols-3 gap-3"><div className="rounded-lg border p-4"><div className="text-[10px] font-bold text-sky-700 uppercase">Plant model</div><div className="mt-2 text-xs text-slate-700">ET₀ → ETc → soil storage → infiltration/drainage → updated moisture</div></div><div className="rounded-lg border p-4"><div className="text-[10px] font-bold text-emerald-700 uppercase">Control state</div><div className="mt-2 text-xs text-slate-700">RSM + moisture error + environmental stress feed the fuzzy decision layers.</div></div><div className="rounded-lg border p-4"><div className="text-[10px] font-bold text-amber-700 uppercase">Resource state</div><div className="mt-2 text-xs text-slate-700">Zone requests are coordinated against shared available water.</div></div></div><div className="flex justify-between"><button onClick={()=>setStep(2)} className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold text-slate-700"><ChevronLeft className="h-3.5 w-3.5"/> Back</button><button onClick={()=>setStep(4)} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-bold text-white">Inspect FIS design <ChevronRight className="h-3.5 w-3.5"/></button></div></div>
      )}

      {step === 4 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5"><div><h3 className="text-sm font-bold text-slate-900">Step 4 — Configure the fuzzy-control architecture</h3><p className="text-xs text-slate-500 mt-1">The guided designer connects your requirements to the validated five-controller Mamdani architecture. Membership functions and rule bases remain auditable on the Fuzzy page.</p></div><div className="grid md:grid-cols-5 gap-2">{[['FIS 1','Soil Stress','RSM + depletion'],['FIS 2','Weather Stress','T + RH + wind + radiation/rain'],['FIS 3','Water Demand','soil + weather / crop demand'],['FIS 4','Main Irrigation','demand + error + RSM'],['FIS 5','Water Allocation','scarcity + zone request']].map(([n,t,i])=>{ const key = String(t).toLowerCase().replace(' ','_'); const live = fisOverview.find((f:any)=>String(f.name||'').toLowerCase().replace(' ','_')===key); return <Link href="/fuzzy" key={n} className="rounded-xl border border-slate-200 p-3 hover:border-emerald-300 transition-colors"><div className="flex items-center justify-between"><span className="text-[10px] font-mono font-bold text-emerald-700">{n}</span>{live && <span className="text-[9px] font-mono text-emerald-700">{live.rule_count} rules</span>}</div><div className="mt-1 text-xs font-bold">{t}</div><div className="mt-1 text-[10px] text-slate-500">{i}</div></Link>})}</div>
        <div className="grid md:grid-cols-3 gap-3">
          <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-4 text-[11px] text-purple-900"><div className="font-bold">Fuzzification</div><div className="mt-1">Crisp requirements and plant states are mapped into linguistic membership degrees.</div></div>
          <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-4 text-[11px] text-purple-900"><div className="font-bold">Rule inference</div><div className="mt-1">The validated Mamdani rule bases fire using minimum implication and maximum aggregation.</div></div>
          <div className="rounded-lg border border-purple-100 bg-purple-50/60 p-4 text-[11px] text-purple-900"><div className="font-bold">Defuzzification</div><div className="mt-1">The aggregated output is converted to a crisp control value using centroid defuzzification.</div></div>
        </div>
        <div className="rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-[11px] text-emerald-900"><strong>Design contract:</strong> this guided workflow uses the repository's validated five-FIS architecture as the controller template. User requirements configure the plant, zones and resource constraints; the FIS definitions remain auditable and testable on the Fuzzy page rather than being hidden inside the UI.</div><div className="rounded-lg bg-purple-50 border border-purple-100 p-4 text-[11px] text-purple-900 leading-relaxed"><strong>Inference chain:</strong> fuzzification → membership evaluation → rule firing → Mamdani aggregation → centroid defuzzification → normalized control output. The output is passed to the next supervisory stage rather than directly bypassing the plant model.</div><div className="flex justify-between"><button onClick={()=>setStep(3)} className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold text-slate-700"><ChevronLeft className="h-3.5 w-3.5"/> Back</button><button onClick={saveConfiguration} disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-bold text-white disabled:opacity-50"><Save className="h-3.5 w-3.5"/>{saving?'Saving…':'Save requirements & continue'}</button></div></div>
      )}

      {step === 5 && (
        <div className="rounded-xl border border-emerald-200 bg-white p-5 space-y-5"><div><h3 className="text-sm font-bold text-slate-900">Step 5 — Execute the closed-loop controller</h3><p className="text-xs text-slate-500 mt-1">This invokes the real multizone simulation engine using the configured zones and selected scenario.</p></div><div className="grid md:grid-cols-4 gap-3">{[['Plant','Weather → ET₀ → ETc → soil state'],['Zone FIS','4 Mamdani controllers'],['Supervisor','Scarcity FIS + bounded water filling'],['Feedback','Applied water → next soil state']].map(([a,b])=><div key={a} className="rounded-lg border p-4"><div className="text-[10px] uppercase font-bold text-emerald-700">{a}</div><div className="mt-1 text-xs text-slate-700">{b}</div></div>)}</div><div className="rounded-xl bg-slate-900 p-5 text-white"><div className="text-xs font-bold">Ready to run</div><div className="mt-2 grid grid-cols-2 md:grid-cols-5 gap-3 text-[10px] font-mono"><div>Zones: {activeZones.length}</div><div>Scenario: {form.scenario}</div><div>Supply: {form.supplyScenario}</div><div>Duration: {form.durationHours}h</div><div>dt: {form.timestepMinutes}min</div></div></div><div className="flex justify-between"><button onClick={()=>setStep(4)} className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold text-slate-700"><ChevronLeft className="h-3.5 w-3.5"/> Back</button><button onClick={runDesign} disabled={running} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white disabled:opacity-50"><Play className="h-3.5 w-3.5 fill-current"/>{running?'Running closed loop…':'Run End-to-End Simulation'}</button></div></div>
      )}

      {step === 6 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5 space-y-5"><div><h3 className="text-sm font-bold text-slate-900">Step 6 — Verify, optimize and report</h3><p className="text-xs text-slate-500 mt-1">A completed run becomes the evidence object for the remaining engineering workflows.</p></div>{run && <div className="grid md:grid-cols-4 gap-3">{[['Run ID',run.id],['Status',run.status],['Requested',`${Number(run.summary_metrics?.total_water_volume_requested_l||0).toFixed(1)} L`],['Allocated',`${Number(run.summary_metrics?.total_water_volume_allocated_l||0).toFixed(1)} L`]].map(([a,b])=><div key={a} className="rounded-lg bg-slate-50 border p-4"><div className="text-[10px] uppercase font-bold text-slate-500">{a}</div><div className="mt-1 text-sm font-bold text-slate-900 break-all">{b}</div></div>)}</div>}<div className="grid md:grid-cols-4 gap-2"><Link href={run?`/simulation?run_id=${run.id}`:'/simulation'} className="rounded-lg border p-3 text-xs font-bold hover:border-emerald-300">Inspect telemetry →</Link><Link href="/optimization" className="rounded-lg border p-3 text-xs font-bold hover:border-emerald-300">Tune with PSO →</Link><Link href="/scenarios" className="rounded-lg border p-3 text-xs font-bold hover:border-emerald-300">Benchmark scenarios →</Link><Link href={run?`/reports?sim_id=${run.id}`:'/reports'} className="rounded-lg border p-3 text-xs font-bold hover:border-emerald-300">Generate report →</Link></div><div className="rounded-lg bg-emerald-50 border border-emerald-100 p-4 text-[11px] text-emerald-900"><strong>Verification principle:</strong> the design is considered complete only when the physical model, all fuzzy layers, supervisory constraints, feedback trajectory and reported metrics agree with the same simulation run.</div><div className="flex justify-between"><button onClick={()=>setStep(5)} className="inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-xs font-bold text-slate-700"><ChevronLeft className="h-3.5 w-3.5"/> Re-run</button><Link href="/dashboard" className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2 text-xs font-bold text-white">Open dashboard <ChevronRight className="h-3.5 w-3.5"/></Link></div></div>
      )}

      {(message || error) && <div className={`rounded-lg border px-4 py-3 text-xs font-medium ${error ? 'border-rose-200 bg-rose-50 text-rose-800' : 'border-emerald-200 bg-emerald-50 text-emerald-800'}`}>{error || message}</div>}
    </div>
  );
}


function PredefinedFISLibrary() {
  const [overview, setOverview] = useState<any[]>([]);
  const [selected, setSelected] = useState('soil_stress');
  const [variables, setVariables] = useState<any[]>([]);
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    api.getFuzzyOverview().then(setOverview).catch((e) => setError(e?.message || 'Could not load FIS library'));
  }, []);

  useEffect(() => {
    setLoading(true);
    setError('');
    Promise.all([api.getFuzzyVariables(selected), api.getFuzzyRules(selected)])
      .then(([v, r]) => { setVariables(v); setRules(r); })
      .catch((e) => { setVariables([]); setRules([]); setError(e?.message || 'Could not load FIS definition'); })
      .finally(() => setLoading(false));
  }, [selected]);

  const current = overview.find((x) => String(x.name).toLowerCase() === selected);

  return (
    <div className="rounded-2xl border border-slate-200/90 bg-white p-8 shadow-xs space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-emerald-800 border border-emerald-200">Validated controller library</span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <SlidersHorizontal className="h-5 w-5 text-emerald-600" />
          Why the user does not need to design membership functions from scratch
        </h2>
        <p className="mt-2 text-sm text-slate-600 max-w-4xl leading-relaxed">
          The platform uses a predefined, validated five-FIS architecture. Users define the irrigation problem and plant/resource requirements; the system supplies the appropriate variables, physical ranges, linguistic sets and rule base. Every definition remains inspectable below and is served directly by the backend fuzzy engine.
        </p>
      </div>

      <div className="rounded-xl border border-emerald-100 bg-emerald-50/60 p-4 text-[11px] text-emerald-950 leading-relaxed">
        <strong>Design principle:</strong> requirements are user-configurable; fuzzy-control definitions are engineering-controlled. This prevents physically inconsistent MF ranges or arbitrary rules while keeping the complete Mamdani inference architecture transparent and auditable.
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
        {overview.length ? overview.map((fis) => {
          const key = String(fis.name).toLowerCase();
          const active = key === selected;
          return (
            <button key={key} onClick={() => setSelected(key)} className={`text-left rounded-xl border p-4 transition-all ${active ? 'border-emerald-400 bg-emerald-50/60 shadow-sm' : 'border-slate-200 bg-white hover:border-emerald-200'}`}>
              <div className="text-[10px] font-mono font-bold text-emerald-700">{fis.title || key}</div>
              <div className="mt-2 text-[10px] text-slate-600 leading-relaxed">{fis.description}</div>
              <div className="mt-3 text-[10px] font-mono text-slate-500">{fis.rule_count} rules • {fis.inference_type || 'Mamdani'}</div>
            </button>
          );
        }) : [
          ['soil_stress','FIS 1: Soil Stress FIS'], ['weather_stress','FIS 2: Weather Stress FIS'], ['water_demand','FIS 3: Water Demand FIS'], ['main_irrigation','FIS 4: Main Irrigation FIS'], ['water_allocation','FIS 5: Water Allocation FIS']
        ].map(([key, title]) => <button key={key} onClick={() => setSelected(key)} className="text-left rounded-xl border border-slate-200 p-4"><div className="text-[10px] font-mono font-bold text-emerald-700">{title}</div></button>)}
      </div>

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-800">{error}</div>}

      <div className="rounded-xl border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 border-b border-slate-200 px-5 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-2">
          <div>
            <div className="text-[10px] font-mono font-bold uppercase tracking-wider text-emerald-700">Selected FIS</div>
            <div className="text-sm font-bold text-slate-900 mt-1">{current?.title || selected}</div>
          </div>
          <div className="text-[10px] font-mono text-slate-500">{current?.rule_count ?? rules.length} rules • {current?.inference_type || 'Mamdani'} • {current?.defuzzification || 'Centroid'}</div>
        </div>

        {loading ? <div className="p-8 text-center text-xs text-slate-500">Loading the live FIS definition…</div> : (
          <div className="p-5 space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {variables.map((v: any) => (
                <div key={v.name} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-start justify-between gap-2">
                    <div><div className="text-xs font-bold text-slate-900">{v.display_name || v.name}</div><div className="text-[10px] text-slate-500 mt-1">{v.fis_role} • {v.unit || '—'}</div></div>
                    <span className="text-[10px] font-mono font-bold text-emerald-700">[{v.min}, {v.max}]</span>
                  </div>
                  <div className="mt-3 space-y-2">
                    {Object.entries(v.sets || {}).map(([name, set]: any) => (
                      <div key={name} className="flex items-center justify-between rounded-md bg-slate-50 px-2.5 py-2 text-[10px]">
                        <span className="font-semibold text-slate-700">{name.replaceAll('_',' ')}</span>
                        <span className="font-mono text-slate-500">{set.type} ({(set.parameters || []).join(', ')})</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div>
              <div className="flex items-center justify-between mb-3"><h3 className="text-sm font-bold text-slate-900">Linguistic rule base</h3><span className="text-[10px] font-mono text-slate-500">Showing {Math.min(rules.length, 8)} of {rules.length}</span></div>
              <div className="space-y-2">
                {rules.slice(0, 8).map((r: any) => <div key={r.id} className="rounded-lg border border-slate-200 p-3 text-[10px] text-slate-700 leading-relaxed"><span className="font-mono font-bold text-emerald-700 mr-2">R{r.id}</span>{r.conditions_text}<span className="font-semibold text-slate-900"> → {String(r.consequent).replaceAll('_',' ')}</span></div>)}
                {!rules.length && <div className="text-xs text-slate-500">No rule data returned by the backend.</div>}
              </div>
            </div>

            <div className="grid md:grid-cols-4 gap-2 text-[10px]">
              {[
                ['1. Fuzzification', 'Physical input values are mapped to linguistic membership degrees.'],
                ['2. Rule firing', 'Validated IF–THEN rules combine antecedent memberships.'],
                ['3. Aggregation', 'Mamdani consequents are combined using the configured maximum operator.'],
                ['4. Defuzzification', 'The aggregated output becomes a crisp control value using centroid defuzzification.'],
              ].map(([title, body]) => <div key={title} className="rounded-lg border border-slate-200 bg-slate-50/70 p-3"><div className="font-bold text-slate-800">{title}</div><div className="mt-1 text-slate-500 leading-relaxed">{body}</div></div>)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


function LiveVerificationConsole() {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const runVerification = async () => {
    setRunning(true);
    setError('');
    try {
      const data = await api.verifySystem();
      setResult(data);
    } catch (err: any) {
      setResult(null);
      setError(err?.message || 'Verification request failed');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200/90 bg-white p-8 shadow-xs space-y-5">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center rounded-md bg-sky-50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-sky-800 border border-sky-200">Live engineering check</span>
          </div>
          <h2 className="text-xl font-bold text-slate-900">13 — Verify the implemented architecture</h2>
          <p className="mt-1.5 text-sm text-slate-600 max-w-3xl">
            The verification button executes the real backend fuzzy engines, weather/ET₀ pipeline and a deterministic 1-hour, 3-zone supervisory closed-loop smoke test. Green results are generated from actual execution, not hard-coded UI labels.
          </p>
        </div>
        <button
          onClick={runVerification}
          disabled={running}
          className="shrink-0 inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-2.5 text-xs font-bold text-white hover:bg-slate-800 disabled:opacity-50 transition-colors"
        >
          <FlaskConical className="h-3.5 w-3.5" />
          {running ? 'Running verification…' : 'Run End-to-End Verification'}
        </button>
      </div>

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-medium text-rose-800">{error}</div>}

      {result && (
        <div className="space-y-4">
          <div className={`rounded-xl border p-4 ${result.status === 'PASS' ? 'border-emerald-200 bg-emerald-50/60' : 'border-rose-200 bg-rose-50/60'}`}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className={`h-5 w-5 ${result.status === 'PASS' ? 'text-emerald-600' : 'text-rose-600'}`} />
              <span className="text-sm font-bold text-slate-900">System Verification: {result.status}</span>
              <span className="ml-auto text-[10px] font-mono text-slate-500">{result.elapsed_seconds}s</span>
            </div>
            <p className="mt-1 text-[11px] text-slate-600">{result.verification_type}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {(result.checks || []).map((check: any) => (
              <div key={check.name} className="rounded-xl border border-slate-200 bg-white p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className={`h-4 w-4 ${check.status === 'PASS' ? 'text-emerald-600' : 'text-rose-600'}`} />
                  <span className="text-xs font-bold text-slate-900">{check.name.replaceAll('_', ' ')}</span>
                </div>
                <p className="mt-2 text-[10px] leading-relaxed text-slate-500">{check.detail}</p>
              </div>
            ))}
          </div>
          <div className="rounded-xl bg-slate-50 border border-slate-200 p-4 text-[10px] font-mono text-slate-600">
            <div>FIS rules: {Object.entries(result.fuzzy_rule_counts || {}).map(([k, v]) => `${k}=${v}`).join(' • ')}</div>
            <div className="mt-1">Simulation: {result.simulation?.zones?.length || 0} zones • {result.simulation?.telemetry_rows || 0} telemetry rows • {result.simulation?.duration_hours} h • {result.simulation?.timestep_minutes} min dt</div>
          </div>
        </div>
      )}
    </div>
  );
}
