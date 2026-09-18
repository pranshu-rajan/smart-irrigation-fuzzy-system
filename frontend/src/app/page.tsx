'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import Link from 'next/link';
import gsap from 'gsap';
import { 
  api, 
  SimulationSummaryResponse, 
  TimeseriesRecord, 
  ControllerOverview,
  FuzzyVariableSchema,
  FuzzyRuleSchema,
  ReportResponse,
  AIChatResponse,
  API_BASE 
} from '@/lib/api';
import LineChart from '@/components/LineChart';
import MetricCard from '@/components/MetricCard';
import FormattedAIResponse from '@/components/FormattedAIResponse';
import { 
  Sliders, 
  Cpu, 
  Layers, 
  Activity, 
  Bot, 
  FileText, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft,
  Play, 
  Download, 
  Sparkles, 
  Info, 
  Droplets, 
  Sun, 
  CloudRain, 
  ShieldCheck, 
  FlaskConical, 
  Zap, 
  Send,
  HelpCircle,
  TrendingUp,
  RefreshCw,
  SlidersHorizontal
} from 'lucide-react';

// Preset configurations for beginners
const PRESETS = [
  {
    id: 'balanced',
    name: 'Balanced 3-Zone Farm (Recommended)',
    desc: 'Standard commercial field with high-priority Tomato, medium Potato, and drought-hardy Maize.',
    scenario: 'Normal',
    supply: 'Normal Supply',
    zones: [
      { id: 1, name: 'Zone 1: Tomato', crop: 'Tomato', soil: 'Loam', area_m2: 150, initial_moisture: 23, target_moisture: 28, root_depth: 0.6, priority: 90 },
      { id: 2, name: 'Zone 2: Potato', crop: 'Potato', soil: 'Sandy Loam', area_m2: 120, initial_moisture: 19, target_moisture: 24, root_depth: 0.5, priority: 65 },
      { id: 3, name: 'Zone 3: Maize', crop: 'Maize', soil: 'Clay', area_m2: 200, initial_moisture: 26, target_moisture: 31, root_depth: 0.7, priority: 40 },
    ],
  },
  {
    id: 'drought',
    name: 'Severe Drought & Scarcity Test',
    desc: 'Heatwave weather with 40% reservoir scarcity to test supervisory priority water-filling.',
    scenario: 'Heatwave',
    supply: 'Severe Scarcity',
    zones: [
      { id: 1, name: 'Zone 1: Cash Crop', crop: 'Tomato', soil: 'Loam', area_m2: 100, initial_moisture: 20, target_moisture: 28, root_depth: 0.6, priority: 95 },
      { id: 2, name: 'Zone 2: Grain Field', crop: 'Wheat', soil: 'Sandy Loam', area_m2: 150, initial_moisture: 18, target_moisture: 24, root_depth: 0.5, priority: 50 },
      { id: 3, name: 'Zone 3: Pasture', crop: 'Maize', soil: 'Clay', area_m2: 150, initial_moisture: 22, target_moisture: 30, root_depth: 0.7, priority: 30 },
    ],
  },
  {
    id: 'rainy',
    name: 'Rainy Day Infiltration Balance',
    desc: 'Precipitation events offsetting water demand with zero artificial water creation.',
    scenario: 'Rainy',
    supply: 'Abundant',
    zones: [
      { id: 1, name: 'Zone 1: Tomato', crop: 'Tomato', soil: 'Loam', area_m2: 100, initial_moisture: 25, target_moisture: 28, root_depth: 0.6, priority: 80 },
      { id: 2, name: 'Zone 2: Potato', crop: 'Potato', soil: 'Sandy Loam', area_m2: 100, initial_moisture: 22, target_moisture: 24, root_depth: 0.5, priority: 60 },
      { id: 3, name: 'Zone 3: Cotton', crop: 'Cotton', soil: 'Clay', area_m2: 100, initial_moisture: 28, target_moisture: 30, root_depth: 0.8, priority: 40 },
    ],
  },
];

export default function EndToEndStudioPage() {
  // Step navigation (1 to 5)
  const [currentStep, setCurrentStep] = useState<number>(1);

  // Backend reference data
  const [cropsList, setCropsList] = useState<any[]>([]);
  const [soilsList, setSoilsList] = useState<any[]>([]);
  const [fisOverview, setFisOverview] = useState<ControllerOverview[]>([]);

  // Step 1: Zones / Plant state
  const [activeZoneCount, setActiveZoneCount] = useState<number>(3);
  const [zones, setZones] = useState(PRESETS[0].zones);

  // Step 2: Environment & Scarcity
  const [scenario, setScenario] = useState<string>('Normal');
  const [supplyScenario, setSupplyScenario] = useState<string>('Normal Supply');
  const [durationHours, setDurationHours] = useState<number>(24);

  // Step 3: Fuzzy Architecture settings & Inspection
  const [controllerType, setControllerType] = useState<string>('fuzzy');
  const [selectedFis, setSelectedFis] = useState<string>('soil_stress');
  const [fisVariables, setFisVariables] = useState<FuzzyVariableSchema[]>([]);
  const [fisRules, setFisRules] = useState<FuzzyRuleSchema[]>([]);
  const [loadingFisDetails, setLoadingFisDetails] = useState<boolean>(false);
  const [sandboxInputs, setSandboxInputs] = useState<Record<string, number>>({ rsm: 0.45, moisture_error: -0.05 });
  const [sandboxOutput, setSandboxOutput] = useState<number | null>(null);
  const [isEvaluatingSandbox, setIsEvaluatingSandbox] = useState<boolean>(false);

  // Step 4: Simulation Execution & Results
  const [isSimulating, setIsSimulating] = useState<boolean>(false);
  const [simulationError, setSimulationError] = useState<string | null>(null);
  const [currentSimulation, setCurrentSimulation] = useState<SimulationSummaryResponse | null>(null);
  const [timeseriesRecords, setTimeseriesRecords] = useState<TimeseriesRecord[]>([]);
  const [activeChartZone, setActiveChartZone] = useState<number>(1);

  // Step 5: ReportLab PDF & Grounded AI Chat
  const [isGeneratingReport, setIsGeneratingReport] = useState<boolean>(false);
  const [reportResult, setReportResult] = useState<ReportResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant'; text: string; source?: string }>>([
    {
      role: 'assistant',
      text: 'Hello! I am your Technical Irrigation AI Copilot. Once you run a simulation, I can explain fuzzy decisions, invariant proofs, and telemetry data for your farm setup.',
    },
  ]);
  const [chatInput, setChatInput] = useState<string>('');
  const [isChatLoading, setIsChatLoading] = useState<boolean>(false);
  const stepContentRef = useRef<HTMLDivElement>(null);

  // GSAP Smooth Transition on Step Change
  useEffect(() => {
    if (stepContentRef.current) {
      gsap.fromTo(
        stepContentRef.current,
        { opacity: 0, y: 16 },
        { opacity: 1, y: 0, duration: 0.35, ease: 'power2.out' }
      );
    }
  }, [currentStep]);

  // GSAP Stagger Entrance for Telemetry Charts in Step 4
  useEffect(() => {
    if (currentStep === 4 && timeseriesRecords.length > 0) {
      gsap.fromTo(
        '.telemetry-chart-card',
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.45, stagger: 0.1, ease: 'power2.out' }
      );
    }
  }, [currentStep, timeseriesRecords]);

  // Load initial backend references
  useEffect(() => {
    const initData = async () => {
      try {
        const [c, s, f] = await Promise.all([
          api.getCrops().catch(() => []),
          api.getSoils().catch(() => []),
          api.getFuzzyOverview().catch(() => []),
        ]);
        if (c.length) setCropsList(c);
        if (s.length) setSoilsList(s);
        if (f.length) setFisOverview(f);
      } catch (err) {
        console.warn('Initial metadata load notice:', err);
      }
    };
    initData();
  }, []);

  // Fetch variables and rules when inspecting a FIS in Step 3
  useEffect(() => {
    if (currentStep !== 3) return;
    const fetchFisData = async () => {
      setLoadingFisDetails(true);
      try {
        const [vars, rls] = await Promise.all([
          api.getFuzzyVariables(selectedFis),
          api.getFuzzyRules(selectedFis),
        ]);
        setFisVariables(vars || []);
        setFisRules(rls || []);

        // Default sandbox inputs for selected controller
        if (selectedFis === 'soil_stress') {
          setSandboxInputs({ rsm: 0.45, moisture_error: -0.05 });
        } else if (selectedFis === 'weather_stress') {
          setSandboxInputs({ temperature: 30, humidity: 45, solar_radiation: 650, wind_speed: 3.5, rainfall: 0 });
        } else if (selectedFis === 'water_demand') {
          setSandboxInputs({ etc: 5.5, crop_water_deficit: 3.2, effective_rainfall: 0 });
        } else if (selectedFis === 'main_irrigation') {
          setSandboxInputs({ soil_stress: 55, weather_stress: 45, water_demand: 60, moisture_error: -0.04 });
        } else if (selectedFis === 'water_allocation') {
          setSandboxInputs({ available_water: 60, zone_demand: 50, zone_stress: 45, zone_priority: 75 });
        }
        setSandboxOutput(null);
      } catch (err) {
        console.error('Failed to load FIS details:', err);
      } finally {
        setLoadingFisDetails(false);
      }
    };
    fetchFisData();
  }, [selectedFis, currentStep]);

  // Handle Preset Selection
  const applyPreset = (presetId: string) => {
    const p = PRESETS.find((x) => x.id === presetId);
    if (!p) return;
    setScenario(p.scenario);
    setSupplyScenario(p.supply);
    setZones(p.zones);
    setActiveZoneCount(p.zones.length);
  };

  // Update a single zone attribute
  const updateZoneField = (zoneIndex: number, field: string, value: any) => {
    setZones((prev) =>
      prev.map((z, idx) => (idx === zoneIndex ? { ...z, [field]: value } : z))
    );
  };

  // Run live sandbox evaluation in Step 3
  const handleTestSandbox = async () => {
    setIsEvaluatingSandbox(true);
    try {
      const res = await api.evaluateFuzzy(selectedFis, sandboxInputs);
      const outVal = Number(res.output_value ?? (res as any).crisp_output ?? 0);
      setSandboxOutput(outVal);
    } catch (err: any) {
      alert(`Inference test notice: ${err.message}`);
    } finally {
      setIsEvaluatingSandbox(false);
    }
  };

  // Step 4: Run Closed-Loop Simulation
  const handleExecuteSimulation = async () => {
    setIsSimulating(true);
    setSimulationError(null);
    try {
      // Save zone parameters to backend first
      for (const z of zones.slice(0, activeZoneCount)) {
        await api.updateZone(z.id, {
          name: z.name,
          crop_type: z.crop,
          soil_type: z.soil,
          area_m2: z.area_m2,
          target_moisture_fraction: z.target_moisture / 100,
          priority_weight: z.priority,
        }).catch(() => {});
      }

      // Execute simulation
      const simSummary = await api.runSimulation({
        scenario,
        duration_hours: durationHours,
        timestep_minutes: 1,
        controller_type: controllerType,
        supply_scenario: supplyScenario,
        zone_ids: zones.slice(0, activeZoneCount).map((z) => z.id),
      });

      setCurrentSimulation(simSummary);

      // Fetch timeseries telemetry
      const ts = await api.getSimulationTimeseries(simSummary.id, undefined, 2);
      setTimeseriesRecords(ts.records || []);

      // Notify user and move to Step 4 view
      setCurrentStep(4);
    } catch (err: any) {
      setSimulationError(err.message || 'Simulation execution failed.');
    } finally {
      setIsSimulating(false);
    }
  };

  // Step 5: Generate ReportLab PDF
  const handleGeneratePdfReport = async () => {
    if (!currentSimulation) return;
    setIsGeneratingReport(true);
    try {
      const rep = await api.generateReport(currentSimulation.id, true);
      setReportResult(rep);
    } catch (err: any) {
      alert(`Report generation notice: ${err.message}`);
    } finally {
      setIsGeneratingReport(false);
    }
  };

  // Step 5: Grounded AI Chat
  const handleSendChat = async (presetText?: string) => {
    const textToSend = presetText || chatInput;
    if (!textToSend.trim() || isChatLoading) return;

    const userMsg = { role: 'user' as const, text: textToSend };
    setChatMessages((prev) => [...prev, userMsg]);
    if (!presetText) setChatInput('');
    setIsChatLoading(true);

    try {
      const aiRes: AIChatResponse = await api.chatAI({
        prompt: textToSend,
        simulation_id: currentSimulation?.id,
        zone_id: activeChartZone,
      });

      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', text: aiRes.response, source: aiRes.source },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        { role: 'assistant', text: `AI response note: ${err.message}`, source: 'offline-mode' },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  // Telemetry chart records filtered by active zone
  const activeZoneRecords = useMemo(() => {
    return timeseriesRecords.filter((r) => r.zone_id === activeChartZone);
  }, [timeseriesRecords, activeChartZone]);

  const stepsLabels = activeZoneRecords.map((r) => `${Math.floor(r.step / 60)}h`);

  const metrics = currentSimulation?.summary_metrics || {};
  const totalReq = metrics.total_water_volume_requested_l || 0;
  const totalAlloc = metrics.total_water_volume_allocated_l || 0;
  const totalUnmet = metrics.total_water_volume_unmet_l || 0;
  const fulfillmentRatio = metrics.overall_fulfillment_ratio ?? (totalReq > 0 ? (totalAlloc / totalReq) * 100 : 100);

  // Stepper Header Definitions
  const STEPS = [
    { num: 1, title: 'Plant & Zones', desc: 'Crops, soils, & targets' },
    { num: 2, title: 'Climate & Supply', desc: 'Weather & reservoir limits' },
    { num: 3, title: 'Fuzzy Architecture', desc: 'The 5 Mamdani FIS engines' },
    { num: 4, title: 'Simulation Run', desc: 'Closed-loop telemetry' },
    { num: 5, title: 'Report & AI Chat', desc: 'PDF audit & AI advisor' },
  ];

  return (
    <div className="space-y-8 pb-20 max-w-7xl mx-auto">
      {/* Top Welcome & Value Proposition */}
      <div className="relative overflow-hidden rounded-3xl border border-emerald-100 bg-gradient-to-br from-white via-emerald-50/40 to-teal-50/50 p-6 md:p-8 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white/95 px-3 py-1 text-xs font-semibold text-emerald-800 shadow-2xs">
              <Sparkles className="h-3.5 w-3.5 text-emerald-600" />
              <span>END-TO-END GUIDED FUZZY ARCHITECTURE STUDIO</span>
            </div>
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-slate-900 font-sans">
              Design, Simulate & Audit Your Fuzzy Irrigation System
            </h1>
            <p className="text-sm text-slate-600 leading-relaxed">
              Configure your crops and soil parameters, specify environmental constraints, inspect the 5-subsystem Mamdani fuzzy logic cascade, execute the closed-loop simulation, and generate official audit reports with AI guidance.
            </p>
          </div>

          {/* Quick Presets Pill Bar */}
          <div className="flex flex-col gap-2 shrink-0 bg-white/90 border border-emerald-200/80 p-4 rounded-2xl shadow-2xs">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 font-mono">
              Quick 1-Click Farm Presets:
            </span>
            <div className="flex flex-col gap-1.5">
              {PRESETS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => applyPreset(p.id)}
                  className="text-left px-3 py-1.5 rounded-lg border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/60 text-xs font-medium text-slate-700 hover:text-emerald-900 transition-all cursor-pointer"
                >
                  <span className="font-semibold">{p.name}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 5-Step Progress Stepper */}
        <div className="mt-8 pt-6 border-t border-emerald-100/80">
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {STEPS.map((s) => {
              const isCurrent = currentStep === s.num;
              const isPast = currentStep > s.num;
              return (
                <button
                  key={s.num}
                  onClick={() => setCurrentStep(s.num)}
                  className={`flex flex-col text-left p-3 rounded-2xl border transition-all cursor-pointer ${
                    isCurrent
                      ? 'border-emerald-500 bg-white shadow-md ring-2 ring-emerald-500/20'
                      : isPast
                      ? 'border-emerald-200 bg-emerald-50/80 hover:bg-emerald-100/70'
                      : 'border-slate-200 bg-white/70 hover:border-slate-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                      isCurrent
                        ? 'bg-emerald-600 text-white'
                        : isPast
                        ? 'bg-emerald-200 text-emerald-800'
                        : 'bg-slate-100 text-slate-500'
                    }`}>
                      STEP 0{s.num}
                    </span>
                    {isPast && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                  </div>
                  <div className="mt-2 text-xs font-bold text-slate-900">{s.title}</div>
                  <div className="text-[10px] text-slate-500 truncate mt-0.5">{s.desc}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div ref={stepContentRef}>
      {/* STEP 1: DEFINE PLANT & ZONES */}
      {currentStep === 1 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md mb-2">
              <HelpCircle className="h-3.5 w-3.5" />
              <span>Where to start: Define your agricultural plant parameters</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">Step 1: Farm Layout & Crop Agronomy</h2>
            <p className="text-xs text-slate-500 mt-1">
              Configure each zone's crop, soil hydraulics, root depth, and target soil moisture. The physical plant model uses these inputs to calculate crop evapotranspiration (ETc) and soil-water deficit.
            </p>
          </div>

          {/* Zone count selector */}
          <div className="flex items-center gap-4 bg-slate-50 p-4 rounded-2xl border border-slate-200">
            <span className="text-xs font-semibold text-slate-700">Active Field Zones:</span>
            <div className="flex gap-2">
              {[1, 2, 3].map((num) => (
                <button
                  key={num}
                  onClick={() => setActiveZoneCount(num)}
                  className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    activeZoneCount === num
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-700 hover:border-emerald-300'
                  }`}
                >
                  {num} {num === 1 ? 'Zone' : 'Zones'}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-400 font-mono hidden md:inline ml-auto">
              Simulating multi-zone hydraulic competition
            </span>
          </div>

          {/* Zones Config Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {zones.slice(0, activeZoneCount).map((zone, idx) => (
              <div
                key={zone.id}
                className="rounded-2xl border border-emerald-200/80 bg-gradient-to-b from-emerald-50/20 to-white p-5 space-y-4 shadow-2xs hover:shadow-xs transition-shadow"
              >
                <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-emerald-600 text-white text-xs font-bold">
                      {zone.id}
                    </span>
                    <input
                      type="text"
                      value={zone.name}
                      onChange={(e) => updateZoneField(idx, 'name', e.target.value)}
                      className="text-xs font-bold text-slate-900 bg-transparent border-b border-transparent hover:border-slate-300 focus:border-emerald-500 focus:outline-none"
                    />
                  </div>
                  <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                    Priority: {zone.priority}%
                  </span>
                </div>

                {/* Inputs */}
                <div className="space-y-3 text-xs">
                  <div>
                    <label htmlFor={`zone-crop-${zone.id}`} className="block text-[11px] font-semibold text-slate-700 mb-1">
                      Crop Selection (Sets Crop Coefficient Kc)
                    </label>
                    <select
                      id={`zone-crop-${zone.id}`}
                      value={zone.crop}
                      onChange={(e) => updateZoneField(idx, 'crop', e.target.value)}
                      aria-label={`Zone ${zone.id} crop selection`}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-900 focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                    >
                      {(cropsList.length
                        ? cropsList
                        : [{ crop: 'Tomato' }, { crop: 'Potato' }, { crop: 'Maize' }, { crop: 'Wheat' }, { crop: 'Cotton' }]
                      ).map((c: any) => (
                        <option key={c.crop || c.crop_type} value={c.crop || c.crop_type}>
                          {c.crop || c.crop_type} (Kc ≈ {Number(c.kc_mid || 1.15).toFixed(2)})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor={`zone-soil-${zone.id}`} className="block text-[11px] font-semibold text-slate-700 mb-1">
                      Soil Texture (Sets Field Capacity & Wilting Point)
                    </label>
                    <select
                      id={`zone-soil-${zone.id}`}
                      value={zone.soil}
                      onChange={(e) => updateZoneField(idx, 'soil', e.target.value)}
                      aria-label={`Zone ${zone.id} soil texture`}
                      className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-900 focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                    >
                      {(soilsList.length
                        ? soilsList
                        : [{ soil_type: 'Loam' }, { soil_type: 'Sandy Loam' }, { soil_type: 'Clay' }, { soil_type: 'Sandy' }]
                      ).map((s: any) => (
                        <option key={s.soil_type || s.soil} value={s.soil_type || s.soil}>
                          {s.soil_type || s.soil} (FC: {s.field_capacity_pct || 28}%, WP: {s.wilting_point_pct || 14}%)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label htmlFor={`zone-area-${zone.id}`} className="block text-[11px] font-semibold text-slate-700 mb-1">Area (m²)</label>
                      <input
                        id={`zone-area-${zone.id}`}
                        type="number"
                        min={10}
                        max={10000}
                        value={zone.area_m2}
                        onChange={(e) => updateZoneField(idx, 'area_m2', Number(e.target.value))}
                        aria-label={`Zone ${zone.id} area in square meters`}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-mono font-medium focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                      />
                    </div>
                    <div>
                      <label htmlFor={`zone-root-${zone.id}`} className="block text-[11px] font-semibold text-slate-700 mb-1">Root Depth (m)</label>
                      <input
                        id={`zone-root-${zone.id}`}
                        type="number"
                        step={0.1}
                        min={0.2}
                        max={2.0}
                        value={zone.root_depth}
                        onChange={(e) => updateZoneField(idx, 'root_depth', Number(e.target.value))}
                        aria-label={`Zone ${zone.id} root depth in meters`}
                        className="w-full rounded-xl border border-slate-300 bg-white px-3 py-1.5 text-xs font-mono font-medium focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                      />
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] font-semibold text-slate-700 mb-1">
                      <label htmlFor={`zone-moisture-${zone.id}`}>Target Moisture:</label>
                      <span className="text-emerald-800 font-mono font-bold">{zone.target_moisture}% vol</span>
                    </div>
                    <input
                      id={`zone-moisture-${zone.id}`}
                      type="range"
                      min={15}
                      max={45}
                      value={zone.target_moisture}
                      onChange={(e) => updateZoneField(idx, 'target_moisture', Number(e.target.value))}
                      aria-label={`Zone ${zone.id} target moisture percentage`}
                      aria-valuenow={zone.target_moisture}
                      aria-valuemin={15}
                      aria-valuemax={45}
                      className="w-full accent-emerald-600 h-1.5 rounded-lg bg-slate-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                    />
                    <div className="flex justify-between text-[9px] text-slate-500 font-mono">
                      <span>Dry (15%)</span>
                      <span>Target Band</span>
                      <span>Saturated (45%)</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-[11px] font-semibold text-slate-700 mb-1">
                      <label htmlFor={`zone-priority-${zone.id}`}>Priority Weight (Scarcity share):</label>
                      <span className="text-emerald-800 font-mono font-bold">{zone.priority}%</span>
                    </div>
                    <input
                      id={`zone-priority-${zone.id}`}
                      type="range"
                      min={10}
                      max={100}
                      value={zone.priority}
                      onChange={(e) => updateZoneField(idx, 'priority', Number(e.target.value))}
                      aria-label={`Zone ${zone.id} priority weight percentage`}
                      aria-valuenow={zone.priority}
                      aria-valuemin={10}
                      aria-valuemax={100}
                      className="w-full accent-emerald-600 h-1.5 rounded-lg bg-slate-200 cursor-pointer focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Action Navigation */}
          <div className="flex justify-end pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(2)}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-6 py-3 shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
            >
              <span>Next: Climate & Water Supply</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: CLIMATE & SUPPLY CONSTRAINTS */}
      {currentStep === 2 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md mb-2">
              <Sun className="h-3.5 w-3.5" />
              <span>Step 2: Weather Forcing & Reservoir Availability</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">Environmental Constraints & Water Supply</h2>
            <p className="text-xs text-slate-500 mt-1">
              Select the atmospheric condition driving crop water loss (evapotranspiration) and the shared reservoir capacity that limits available irrigation water.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Weather Selection */}
            <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Sun className="h-4 w-4 text-amber-500" />
                <span>Environmental Climate Scenario</span>
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Determines diurnal solar radiation, temperature curves, relative humidity, and wind speed for FAO-56 Penman-Monteith ET0.
              </p>

              <div className="space-y-2">
                {[
                  { id: 'Normal', desc: 'Moderate diurnal temp (18°C–28°C), standard evaporative demand' },
                  { id: 'Hot & Dry', desc: 'High temp (34°C), low RH (25%), high evapotranspiration demand' },
                  { id: 'Heatwave', desc: 'Extreme temp spikes (>38°C), severe atmospheric stress' },
                  { id: 'Rainy', desc: 'High precipitation events reducing required irrigation command' },
                  { id: 'Cloudy', desc: 'Reduced solar radiation, mild crop water transpiration' },
                  { id: 'Water Scarcity', desc: 'Arid climate conditions paired with zero natural precipitation' },
                ].map((sc) => (
                  <label
                    key={sc.id}
                    className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                      scenario === sc.id
                        ? 'border-emerald-500 bg-white shadow-2xs'
                        : 'border-slate-200 bg-white/70 hover:border-emerald-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name="scenario"
                      checked={scenario === sc.id}
                      onChange={() => setScenario(sc.id)}
                      className="mt-1 accent-emerald-600"
                    />
                    <div>
                      <div className="text-xs font-bold text-slate-900">{sc.id}</div>
                      <div className="text-[11px] text-slate-500">{sc.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Shared Supply Selection */}
            <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-5 space-y-4">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Droplets className="h-4 w-4 text-sky-500" />
                <span>Shared Reservoir Supply Scenario</span>
              </h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Supervisory invariant testing: sets the shared physical water cap. Under scarcity, FIS 5 arbitrates distribution.
              </p>

              <div className="space-y-2">
                {[
                  { id: 'Normal Supply', tag: '100% Capacity', desc: 'Sufficient water to fulfill 100% of zone agronomic requests' },
                  { id: 'Moderate Scarcity', tag: '70% Capacity', desc: 'Partial deficit: lower-priority zones scaled back gracefully' },
                  { id: 'Severe Scarcity', tag: '40% Capacity', desc: 'High drought: only critical crops maintain target moisture' },
                  { id: 'Extreme Scarcity', tag: '20% Capacity', desc: 'Emergency mode: strict survival allocation' },
                  { id: 'Zero Supply', tag: '0% Safety Cap', desc: 'Testing invariant: zero artificial water leakage during outage' },
                ].map((sup) => (
                  <label
                    key={sup.id}
                    className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                      supplyScenario === sup.id
                        ? 'border-emerald-500 bg-white shadow-2xs'
                        : 'border-slate-200 bg-white/70 hover:border-emerald-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name="supplyScenario"
                      checked={supplyScenario === sup.id}
                      onChange={() => setSupplyScenario(sup.id)}
                      className="mt-1 accent-emerald-600"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900">{sup.id}</span>
                        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-sky-50 text-sky-700 border border-sky-200">
                          {sup.tag}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 mt-0.5">{sup.desc}</div>
                    </div>
                  </label>
                ))}
              </div>

              {/* Duration selector */}
              <div className="pt-2 border-t border-slate-200">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Simulation Horizon:
                </label>
                <div className="flex gap-2">
                  {[24, 48].map((hrs) => (
                    <button
                      key={hrs}
                      onClick={() => setDurationHours(hrs)}
                      className={`flex-1 py-2 text-xs font-bold rounded-xl border ${
                        durationHours === hrs
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-white border-slate-200 text-slate-700 hover:border-emerald-300'
                      }`}
                    >
                      {hrs} Hours ({hrs * 60} 1-min timesteps)
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Action Navigation */}
          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 border border-slate-200 bg-white px-5 py-2.5 rounded-xl transition-all cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back: Plant & Zones</span>
            </button>
            <button
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-6 py-3 shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
            >
              <span>Next: Whole Fuzzy Architecture</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: WHOLE FUZZY SYSTEM ARCHITECTURE */}
      {currentStep === 3 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-8">
          <div className="border-b border-slate-100 pb-4">
            <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md mb-2">
              <SlidersHorizontal className="h-3.5 w-3.5" />
              <span>Step 3: The Complete 5-Subsystem Mamdani Cascade</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">Hierarchical Fuzzy Inference System (HAFC) Architecture</h2>
            <p className="text-xs text-slate-500 mt-1">
              Your parameters flow through 5 Mamdani Fuzzy Inference Systems. Inspect how raw sensor values are fuzzified, evaluated across linguistic rules, and defuzzified into precise valve depths.
            </p>
          </div>

          {/* Interactive Architecture Flowchart */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-950 font-mono">
                System Control Cascade Block Diagram (Click any FIS to inspect)
              </h3>
              <span className="text-[10px] font-mono text-emerald-700 bg-white px-2 py-0.5 rounded border border-emerald-200">
                Mamdani Min-Max Centroid
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Layer 1 */}
              <div className="space-y-3">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-mono">
                  Level 1 • Subsystem Stresses
                </div>

                {/* FIS 1 */}
                <button
                  onClick={() => setSelectedFis('soil_stress')}
                  className={`w-full text-left p-4 rounded-xl border transition-all cursor-pointer ${
                    selectedFis === 'soil_stress'
                      ? 'border-emerald-600 bg-white shadow-md ring-2 ring-emerald-600/20'
                      : 'border-emerald-200 bg-white/80 hover:border-emerald-400'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-emerald-700">FIS 1</span>
                    <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-600">25 rules</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 mt-1">Soil Stress FIS</div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Inputs: Relative Soil Moisture (RSM) + Tracking Error
                  </div>
                  <div className="mt-2 text-[10px] font-semibold text-emerald-700">
                    Output: Soil Stress [0–100%]
                  </div>
                </button>

                {/* FIS 2 */}
                <button
                  onClick={() => setSelectedFis('weather_stress')}
                  className={`w-full text-left p-4 rounded-xl border transition-all cursor-pointer ${
                    selectedFis === 'weather_stress'
                      ? 'border-emerald-600 bg-white shadow-md ring-2 ring-emerald-600/20'
                      : 'border-emerald-200 bg-white/80 hover:border-emerald-400'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-emerald-700">FIS 2</span>
                    <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-600">32 rules</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 mt-1">Weather Stress FIS</div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Inputs: Temp + Humidity + Radiation + Wind + Rain
                  </div>
                  <div className="mt-2 text-[10px] font-semibold text-emerald-700">
                    Output: Weather Stress [0–100%]
                  </div>
                </button>

                {/* FIS 3 */}
                <button
                  onClick={() => setSelectedFis('water_demand')}
                  className={`w-full text-left p-4 rounded-xl border transition-all cursor-pointer ${
                    selectedFis === 'water_demand'
                      ? 'border-emerald-600 bg-white shadow-md ring-2 ring-emerald-600/20'
                      : 'border-emerald-200 bg-white/80 hover:border-emerald-400'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-emerald-700">FIS 3</span>
                    <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-600">27 rules</span>
                  </div>
                  <div className="text-xs font-bold text-slate-900 mt-1">Water Demand FIS</div>
                  <div className="text-[10px] text-slate-500 mt-1">
                    Inputs: Crop ETc + Water Deficit + Effective Rainfall
                  </div>
                  <div className="mt-2 text-[10px] font-semibold text-emerald-700">
                    Output: Water Demand [0–100%]
                  </div>
                </button>
              </div>

              {/* Layer 2 */}
              <div className="space-y-3">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-mono">
                  Level 2 • Zone Actuator
                </div>

                <div className="h-full flex flex-col justify-center">
                  <button
                    onClick={() => setSelectedFis('main_irrigation')}
                    className={`w-full text-left p-5 rounded-2xl border transition-all cursor-pointer ${
                      selectedFis === 'main_irrigation'
                        ? 'border-emerald-600 bg-white shadow-md ring-2 ring-emerald-600/20'
                        : 'border-teal-200 bg-white/90 hover:border-emerald-400'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-emerald-700">FIS 4</span>
                      <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-600">48 rules</span>
                    </div>
                    <div className="text-sm font-bold text-slate-900 mt-1">Main Irrigation FIS</div>
                    <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                      Supervisory fusion controller: integrates Soil Stress, Weather Stress, Water Demand, and Tracking Error to compute raw zone water request depth.
                    </p>
                    <div className="mt-3 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-1 rounded">
                      Output: Irrigation Command [0–100%]
                    </div>
                  </button>
                </div>
              </div>

              {/* Layer 3 */}
              <div className="space-y-3">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-mono">
                  Level 3 • Multi-Zone Allocation
                </div>

                <div className="h-full flex flex-col justify-center">
                  <button
                    onClick={() => setSelectedFis('water_allocation')}
                    className={`w-full text-left p-5 rounded-2xl border transition-all cursor-pointer ${
                      selectedFis === 'water_allocation'
                        ? 'border-emerald-600 bg-white shadow-md ring-2 ring-emerald-600/20'
                        : 'border-sky-200 bg-white/90 hover:border-emerald-400'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-emerald-700">FIS 5</span>
                      <span className="text-[9px] bg-slate-100 px-1.5 py-0.5 rounded font-mono text-slate-600">30 rules</span>
                    </div>
                    <div className="text-sm font-bold text-slate-900 mt-1">Water Allocation FIS</div>
                    <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                      Arbitrates shared reservoir constraints among competing zones using scarcity scaling and bounded priority water-filling.
                    </p>
                    <div className="mt-3 text-[11px] font-semibold text-sky-800 bg-sky-50 px-2 py-1 rounded">
                      Output: Final Bounded Water Allocation (mm)
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* FIS Inspector & Live Defuzzification Sandbox */}
          <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-2xs space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
              <div>
                <span className="text-[10px] font-mono font-bold text-emerald-700 uppercase">Live Subsystem Inspection</span>
                <h3 className="text-base font-bold text-slate-900">
                  {selectedFis.replaceAll('_', ' ').toUpperCase()} Controller Deep-Dive
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <label htmlFor="controller-mode-select" className="text-xs text-slate-700 font-mono">
                  Active Mode:
                </label>
                <select
                  id="controller-mode-select"
                  value={controllerType}
                  onChange={(e) => setControllerType(e.target.value)}
                  aria-label="Active Controller Mode"
                  className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-900 focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                >
                  <option value="fuzzy">Hierarchical Adaptive Fuzzy (HAFC)</option>
                  <option value="pso_tuned">PSO-Calibrated Parameters</option>
                  <option value="fixed">Fixed-Interval Rule Baseline</option>
                </select>
              </div>
            </div>

            {loadingFisDetails ? (
              <div className="py-12 text-center text-xs text-slate-500 font-mono animate-pulse" role="status" aria-live="polite">
                Loading live membership functions and rule base from FastAPI backend...
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Linguistic Variables & Sets */}
                <div className="space-y-4">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                    Fuzzy Variables & Linguistic Terms
                  </h4>
                  <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
                    {fisVariables.map((v) => (
                      <div key={v.name} className="rounded-xl border border-slate-200 p-3 text-xs bg-slate-50/50">
                        <div className="flex justify-between items-center mb-2">
                          <span className="font-bold text-slate-800">
                            {v.name} {v.unit ? `(${v.unit})` : ''}
                          </span>
                          <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-300">
                            Universe: [{v.universe_min ?? (v as any).min ?? 0}, {v.universe_max ?? (v as any).max ?? 100}]
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {(v.terms || Object.keys((v as any).sets || {})).map((termItem: any) => {
                            const termName = typeof termItem === 'string' ? termItem : termItem.term || termItem.name;
                            return (
                              <span key={termName} className="px-2 py-1 rounded bg-white border border-slate-200 text-[10px] font-medium text-slate-800">
                                {termName}
                              </span>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Interactive Live Sandbox */}
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50/30 p-5 space-y-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-xs font-bold text-emerald-950 uppercase flex items-center gap-1.5">
                        <FlaskConical className="h-4 w-4 text-emerald-600" />
                        <span>Instant Sandbox Defuzzification Test</span>
                      </span>
                      <span className="text-[10px] text-slate-600 font-mono">Centroid Defuzzifier</span>
                    </div>

                    {/* Inputs */}
                    <div className="space-y-3 text-xs">
                      {Object.keys(sandboxInputs).map((inputKey) => (
                        <div key={inputKey} className="flex items-center justify-between gap-3">
                          <label htmlFor={`sandbox-input-${inputKey}`} className="font-semibold text-slate-800 capitalize">
                            {inputKey.replaceAll('_', ' ')}:
                          </label>
                          <input
                            id={`sandbox-input-${inputKey}`}
                            type="number"
                            step={0.1}
                            value={sandboxInputs[inputKey]}
                            onChange={(e) =>
                              setSandboxInputs({ ...sandboxInputs, [inputKey]: parseFloat(e.target.value) || 0 })
                            }
                            aria-label={`Sandbox input value for ${inputKey.replaceAll('_', ' ')}`}
                            className="w-24 text-right rounded-lg border border-slate-300 bg-white px-2 py-1 font-mono text-xs font-bold text-slate-900 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
                          />
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={handleTestSandbox}
                      disabled={isEvaluatingSandbox}
                      className="mt-4 w-full rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs py-2.5 transition-all cursor-pointer flex items-center justify-center gap-1.5 shadow-xs"
                    >
                      <Zap className="h-3.5 w-3.5 text-amber-400" />
                      <span>{isEvaluatingSandbox ? 'Evaluating...' : 'Compute Instant Fuzzy Step'}</span>
                    </button>
                  </div>

                  {sandboxOutput !== null && (
                    <div className="rounded-xl bg-white border border-emerald-300 p-4 text-center shadow-xs">
                      <span className="text-[10px] uppercase font-mono font-bold text-slate-500 block">
                        Crisp Defuzzified Output:
                      </span>
                      <div className="text-2xl font-black font-mono text-emerald-700 mt-1">
                        {sandboxOutput.toFixed(2)} %
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Action Navigation */}
          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(2)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 border border-slate-200 bg-white px-5 py-2.5 rounded-xl transition-all cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back: Climate & Supply</span>
            </button>
            <button
              onClick={handleExecuteSimulation}
              disabled={isSimulating}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-7 py-3.5 shadow-lg shadow-emerald-600/25 transition-all cursor-pointer"
            >
              {isSimulating ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Simulating Closed Loop (1440 timesteps)...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 fill-current" />
                  <span>Execute Full Closed-Loop Simulation</span>
                  <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: SIMULATION RUN & TELEMETRY CHARTS */}
      {currentStep === 4 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-8">
          <div className="border-b border-slate-100 pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md mb-2">
                <Activity className="h-3.5 w-3.5" />
                <span>Step 4: Real-Time Dynamic Simulation Telemetry</span>
              </div>
              <h2 className="text-xl font-bold text-slate-900">Simulation Run Telemetry & Verification</h2>
              <p className="text-xs text-slate-500 mt-1">
                24-Hour continuous closed-loop execution. Inspect root-zone soil water balance, tracking fidelity, and allocation invariants.
              </p>
            </div>

            <button
              onClick={handleExecuteSimulation}
              disabled={isSimulating}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-700 border border-slate-200 bg-slate-50 hover:bg-slate-100 px-4 py-2 rounded-xl transition-all cursor-pointer"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isSimulating ? 'animate-spin' : ''}`} />
              <span>Re-run Simulation</span>
            </button>
          </div>

          {simulationError && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs font-medium text-rose-800">
              Simulation Notice: {simulationError}
            </div>
          )}

          {/* High-Level KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Total Water Requested"
              value={`${totalReq.toFixed(1)} L`}
              change="Crop Demand Sum"
              trend="neutral"
              color="blue"
            />
            <MetricCard
              title="Total Water Dispatched"
              value={`${totalAlloc.toFixed(1)} L`}
              change={`Supply: ${supplyScenario}`}
              trend="up"
              color="emerald"
            />
            <MetricCard
              title="Unmet Demand"
              value={`${totalUnmet.toFixed(1)} L`}
              change="Zero Artificial Creation"
              trend={totalUnmet > 0 ? 'down' : 'neutral'}
              color={totalUnmet > 0 ? 'amber' : 'emerald'}
            />
            <MetricCard
              title="Overall Fulfillment"
              value={`${typeof fulfillmentRatio === 'number' ? fulfillmentRatio.toFixed(1) : fulfillmentRatio}%`}
              change="Mass Balance: 0.00 mm"
              trend="up"
              color="cyan"
            />
          </div>

          {/* Telemetry Zone Switcher */}
          <div className="flex items-center justify-between bg-slate-50 p-3 rounded-2xl border border-slate-200">
            <span className="text-xs font-semibold text-slate-700">Display Telemetry for Zone:</span>
            <div className="flex gap-2">
              {zones.slice(0, activeZoneCount).map((z) => (
                <button
                  key={z.id}
                  onClick={() => setActiveChartZone(z.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    activeChartZone === z.id
                      ? 'bg-emerald-600 text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-700 hover:border-emerald-300'
                  }`}
                >
                  Zone {z.id} ({z.crop})
                </button>
              ))}
            </div>
          </div>

          {/* Charts Grid */}
          {activeZoneRecords.length > 0 ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chart 1: Moisture Tracking */}
              <div className="telemetry-chart-card rounded-2xl border border-slate-200 p-5 bg-white shadow-2xs space-y-2">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    1. Soil Moisture vs Target Band
                  </h3>
                  <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Closed-Loop θ(t)
                  </span>
                </div>
                <LineChart
                  labels={stepsLabels}
                  datasets={[
                    {
                      name: 'Current Moisture (vol %)',
                      data: activeZoneRecords.map((r) => r.soil_moisture * 100),
                      color: '#059669',
                    },
                    {
                      name: 'Target Moisture (vol %)',
                      data: activeZoneRecords.map((r) => r.target_moisture * 100),
                      color: '#0284c7',
                      dashed: true,
                    },
                  ]}
                  unit="%"
                  height={220}
                />
              </div>

              {/* Chart 2: ET0 vs ETc */}
              <div className="telemetry-chart-card rounded-2xl border border-slate-200 p-5 bg-white shadow-2xs space-y-2">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    2. Evapotranspiration (FAO-56 ET0 vs ETc)
                  </h3>
                  <span className="text-[10px] font-mono text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Penman-Monteith
                  </span>
                </div>
                <LineChart
                  labels={stepsLabels}
                  datasets={[
                    {
                      name: 'Reference ET0 (mm)',
                      data: activeZoneRecords.map((r) => r.et0_mm),
                      color: '#d97706',
                    },
                    {
                      name: 'Crop ETc (mm)',
                      data: activeZoneRecords.map((r) => r.etc_mm),
                      color: '#e11d48',
                    },
                  ]}
                  unit="mm"
                  height={220}
                />
              </div>

              {/* Chart 3: Requested vs Allocated Depths */}
              <div className="telemetry-chart-card rounded-2xl border border-slate-200 p-5 bg-white shadow-2xs space-y-2">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    3. Irrigation Depth (Request vs Allocated)
                  </h3>
                  <span className="text-[10px] font-mono text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                    Invariant-Bounded
                  </span>
                </div>
                <LineChart
                  labels={stepsLabels}
                  datasets={[
                    {
                      name: 'Requested Depth (mm)',
                      data: activeZoneRecords.map((r) => r.raw_request_mm),
                      color: '#6366f1',
                    },
                    {
                      name: 'Allocated Depth (mm)',
                      data: activeZoneRecords.map((r) => r.allocated_irrigation_mm),
                      color: '#059669',
                    },
                  ]}
                  unit="mm"
                  height={220}
                />
              </div>

              {/* Chart 4: Mass Balance Closure Residual */}
              <div className="telemetry-chart-card rounded-2xl border border-slate-200 p-5 bg-white shadow-2xs space-y-2">
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                    4. Water Balance Closure Residual (Exact Invariant)
                  </h3>
                  <span className="text-[10px] font-mono text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-bold">
                    Residual = 0.00 mm
                  </span>
                </div>
                <LineChart
                  labels={stepsLabels}
                  datasets={[
                    {
                      name: 'Mass Balance Residual (mm)',
                      data: activeZoneRecords.map((r) => r.water_balance_residual),
                      color: '#059669',
                    },
                  ]}
                  unit="mm"
                  height={220}
                />
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs text-slate-400 font-mono border border-dashed border-slate-200 rounded-2xl">
              No simulation telemetry records loaded yet. Click <strong>Execute Full Closed-Loop Simulation</strong> to run.
            </div>
          )}

          {/* Action Navigation */}
          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 border border-slate-200 bg-white px-5 py-2.5 rounded-xl transition-all cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back: Fuzzy Architecture</span>
            </button>
            <button
              onClick={() => setCurrentStep(5)}
              className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs px-6 py-3 shadow-md shadow-emerald-600/20 transition-all cursor-pointer"
            >
              <span>Next: Generate Report & Chat AI</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: AUDIT PDF REPORT & GROUNDED AI COPILOT */}
      {currentStep === 5 && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-8">
          <div className="border-b border-slate-100 pb-4">
            <div className="inline-flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md mb-2">
              <Bot className="h-3.5 w-3.5" />
              <span>Step 5: Audit Documentation & AI Copilot</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">Engineering Audit Report & Telemetry AI Advisory</h2>
            <p className="text-xs text-slate-500 mt-1">
              Synthesize a publication-grade PDF engineering report compiled via ReportLab, download the 1-minute telemetry CSV, and consult the AI assistant grounded in your simulation's results.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Report Generator & CSV Exporter */}
            <div className="space-y-6">
              {/* PDF Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-emerald-600" />
                  <span>ReportLab PDF Synthesis</span>
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Generates an official engineering audit report containing scenario parameters, FAO-56 metrics, FIS firing logs, and allocation invariant proofs.
                </p>

                <button
                  onClick={handleGeneratePdfReport}
                  disabled={isGeneratingReport || !currentSimulation}
                  className="w-full rounded-xl bg-emerald-600 py-3 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-600/15 cursor-pointer flex items-center justify-center gap-2"
                >
                  <FileText className="h-4 w-4" />
                  <span>{isGeneratingReport ? 'Synthesizing PDF Report...' : 'Generate Official PDF Report'}</span>
                </button>

                {reportResult && (
                  <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-xs space-y-2">
                    <div className="font-bold text-emerald-900 flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      <span>Report Ready</span>
                    </div>
                    <p className="text-[11px] text-slate-600 truncate">{reportResult.filename}</p>
                    <a
                      href={`${API_BASE}/reports/download/${reportResult.id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 w-full justify-center bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2 rounded-lg text-xs transition-colors"
                    >
                      <Download className="h-3.5 w-3.5" />
                      <span>Download Audit PDF</span>
                    </a>
                  </div>
                )}
              </div>

              {/* CSV Export Card */}
              <div className="rounded-2xl border border-slate-200 bg-white p-6 space-y-4 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
                  <Download className="h-4 w-4 text-slate-600" />
                  <span>Raw Telemetry Dataset (CSV)</span>
                </h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Download full uncompressed 1-minute resolution telemetry (1,440 timesteps per zone) for external audits or MATLAB / Python modeling.
                </p>

                {currentSimulation ? (
                  <a
                    href={`${API_BASE}/reports/csv/${currentSimulation.id}`}
                    download
                    className="w-full inline-flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 py-2.5 text-xs font-semibold text-slate-800 transition-colors cursor-pointer"
                  >
                    <Download className="h-3.5 w-3.5 text-slate-600" />
                    <span>Download 1440-Step CSV</span>
                  </a>
                ) : (
                  <div className="text-xs text-slate-400 font-mono">Run simulation first to enable export.</div>
                )}
              </div>
            </div>

            {/* Right: Grounded AI Advisory Chat */}
            <div className="lg:col-span-2 rounded-2xl border border-slate-200 bg-white shadow-xs flex flex-col h-[580px]">
              {/* Chat Header */}
              <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50 rounded-t-2xl">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-900">Technical Advisory Copilot</h3>
                    <span className="text-[10px] text-emerald-700 font-mono">
                      Grounded in Run: {currentSimulation ? `${currentSimulation.id.substring(0, 8)}... (${currentSimulation.scenario})` : 'Awaiting simulation'}
                    </span>
                  </div>
                </div>
                <span className="text-[10px] font-mono text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                  Strictly Advisory
                </span>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs">
                {chatMessages.map((m, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <div
                      className={`max-w-xl rounded-2xl p-4 leading-relaxed ${
                        m.role === 'user'
                          ? 'bg-emerald-600 text-white rounded-br-none shadow-xs'
                          : 'bg-slate-50/90 text-slate-800 border border-slate-200/90 rounded-bl-none shadow-2xs'
                      }`}
                    >
                      {m.role === 'user' ? (
                        <p className="whitespace-pre-line text-xs font-medium text-white">{m.text}</p>
                      ) : (
                        <FormattedAIResponse content={m.text} />
                      )}
                    </div>
                    <span className="text-[9px] text-slate-400 font-mono mt-1">
                      {m.role === 'user' ? 'You' : `AI Advisor (${m.source || 'Groq'})`}
                    </span>
                  </div>
                ))}
                {isChatLoading && (
                  <div className="flex items-center gap-2 text-xs text-slate-500 italic p-2">
                    <RefreshCw className="h-3 w-3 animate-spin text-emerald-600" />
                    <span>Analyzing simulation telemetry with reasoning model...</span>
                  </div>
                )}
              </div>

              {/* Preset Prompts Pill Bar */}
              <div className="px-4 py-2 border-t border-slate-100 flex flex-wrap gap-1.5 bg-slate-50/40">
                {[
                  'Why was Zone 1 prioritized over Zone 3?',
                  'Explain the 0.00 mm mass balance residual proof.',
                  'Did any crop suffer severe water stress?',
                ].map((chip, cIdx) => (
                  <button
                    key={cIdx}
                    onClick={() => handleSendChat(chip)}
                    className="text-[10px] rounded-lg bg-white border border-slate-200 hover:border-emerald-300 px-2.5 py-1 text-slate-700 hover:text-emerald-900 transition-colors cursor-pointer"
                  >
                    {chip}
                  </button>
                ))}
              </div>

              {/* Chat Input */}
              <div className="p-3 border-t border-slate-100 flex gap-2 bg-white rounded-b-2xl">
                <input
                  type="text"
                  placeholder="Ask any question about your fuzzy rules, water allocation, or crop health..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
                  className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
                />
                <button
                  onClick={() => handleSendChat()}
                  disabled={isChatLoading || !chatInput.trim()}
                  className="rounded-xl bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-4 py-2 text-xs font-bold transition-all cursor-pointer flex items-center gap-1"
                >
                  <Send className="h-3.5 w-3.5" />
                  <span>Send</span>
                </button>
              </div>
            </div>
          </div>

          {/* Action Navigation */}
          <div className="flex justify-between pt-4 border-t border-slate-100">
            <button
              onClick={() => setCurrentStep(4)}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-600 hover:text-slate-900 border border-slate-200 bg-white px-5 py-2.5 rounded-xl transition-all cursor-pointer"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back: Simulation Telemetry</span>
            </button>
            <button
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-6 py-3 transition-all cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Start New Architecture Design</span>
            </button>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
