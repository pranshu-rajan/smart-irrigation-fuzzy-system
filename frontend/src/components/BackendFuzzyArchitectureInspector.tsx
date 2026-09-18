'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, ControllerOverview, FuzzyVariableSchema, FuzzyEvaluateResponse } from '@/lib/api';
import { 
  Code2, 
  Terminal, 
  Cpu, 
  Layers, 
  Activity, 
  CheckCircle2, 
  ArrowRight, 
  ArrowDown, 
  Play, 
  FileCode, 
  Sparkles, 
  Database, 
  Network,
  Sliders,
  ShieldCheck,
  RefreshCw,
  Zap,
  Info
} from 'lucide-react';

interface FISBackendDetail {
  id: string;
  name: string;
  title: string;
  pyFile: string;
  serviceFile: string;
  className: string;
  layer: string;
  role: string;
  defaultInputs: Record<string, number>;
  pythonCode: string;
  mathExplanation: {
    fuzzification: string;
    implication: string;
    aggregation: string;
    defuzzification: string;
  };
}

const FIS_BACKEND_DETAILS: Record<string, FISBackendDetail> = {
  soil_stress: {
    id: 'soil_stress',
    name: 'soil_stress',
    title: 'FIS 1: Soil Stress FIS',
    pyFile: 'fuzzy_engine/soil_stress.py',
    serviceFile: 'backend/app/services/fuzzy_service.py',
    className: 'SoilStressFIS',
    layer: 'Layer 2 • Local Zone Stress Evaluation',
    role: 'Evaluates physiological root-zone moisture deficit using Relative Soil Moisture (RSM) and Tracking Error.',
    defaultInputs: { rsm: 0.35, moisture_error: 5.0 },
    pythonCode: `# fuzzy_engine/soil_stress.py
import numpy as np
from fuzzy_engine.variables import FuzzyUniverse, FuzzyVariable

class SoilStressFIS:
    """Evaluates crop root-zone moisture deficiency."""
    def __init__(self, resolution: int = 501):
        self.resolution = resolution
        self.universe_stress = np.linspace(0.0, 100.0, resolution)
        # 16 Mamdani rules mapping (RSM x Error) -> Soil Stress
        self.rules = self._load_rule_base()

    def evaluate(self, inputs: dict) -> dict:
        rsm = float(inputs.get("rsm", 0.5))
        error = float(inputs.get("moisture_error", 0.0))
        
        # 1. Vectorized Fuzzification
        mu_rsm = self.fuzzify_rsm(rsm)          # terms: very_low, low, optimal, high
        mu_err = self.fuzzify_error(error)      # terms: large_neg, neg, zero, pos, large_pos
        
        # 2. Mamdani Min-Implication across 16 Rules
        aggregated_curve = np.zeros_like(self.universe_stress)
        for rule in self.rules:
            weight = min(mu_rsm[rule["rsm"]], mu_err[rule["error"]])
            if weight > 0:
                consequent_shape = self.get_consequent_mf(rule["consequent"])
                truncated_shape = np.minimum(weight, consequent_shape)
                aggregated_curve = np.maximum(aggregated_curve, truncated_shape)
        
        # 3. Centroid (Center of Area) Defuzzification
        total_area = np.sum(aggregated_curve)
        if total_area == 0:
            return 0.0
        crisp_output = np.sum(self.universe_stress * aggregated_curve) / total_area
        return float(np.round(crisp_output, 2))`,
    mathExplanation: {
      fuzzification: 'Piecewise linear triangular (trimf) and trapezoidal (trapmf) membership degrees μ ∈ [0, 1].',
      implication: 'Gödel t-norm (Mamdani Min): μ_rule = min(μ_RSM, μ_Error), truncating consequent fuzzy set.',
      aggregation: 'Max-t-conorm: μ_agg(y) = max_r(μ_implied,r(y)) combining active consequents into an envelope.',
      defuzzification: 'Discretized Center of Gravity: y* = Σ(y_i · μ_agg(y_i)) / Σ(μ_agg(y_i)) across 501 points.',
    },
  },
  weather_stress: {
    id: 'weather_stress',
    name: 'weather_stress',
    title: 'FIS 2: Weather Stress FIS',
    pyFile: 'fuzzy_engine/weather_stress.py',
    serviceFile: 'backend/app/services/fuzzy_service.py',
    className: 'WeatherStressFIS',
    layer: 'Layer 2 • Local Atmospheric Stress Evaluation',
    role: 'Quantifies atmospheric evaporative demand and climatic stress across 5 meteorological sensors.',
    defaultInputs: { temperature: 32.0, humidity: 30.0, solar_radiation: 850.0, wind_speed: 3.5, rainfall: 0.0 },
    pythonCode: `# fuzzy_engine/weather_stress.py
class WeatherStressFIS:
    """Assesses climate forcing: vapor pressure deficit, insolation, and wind."""
    def __init__(self, resolution: int = 501):
        self.resolution = resolution
        self.universe_weather = np.linspace(0.0, 100.0, resolution)
        
    def evaluate(self, inputs: dict) -> dict:
        t = float(inputs.get("temperature", 25.0))
        rh = float(inputs.get("humidity", 50.0))
        rad = float(inputs.get("solar_radiation", 600.0))
        wind = float(inputs.get("wind_speed", 2.0))
        rain = float(inputs.get("rainfall", 0.0))
        
        # Fuzzify 5 meteorological dimensions
        mu_t = self.fuzzify_temp(t)          # Cool, Mild, Warm, Hot, Extreme
        mu_rh = self.fuzzify_rh(rh)          # Arid, Low, Moderate, Humid, Saturated
        mu_rad = self.fuzzify_rad(rad)       # Dark, Overcast, Moderate, High, Intense
        mu_wind = self.fuzzify_wind(wind)    # Calm, Light, Moderate, Strong, Gale
        mu_rain = self.fuzzify_rain(rain)    # None, Light, Moderate, Heavy
        
        # Mamdani Rule Base (25 rules)
        # Rain presence aggressively suppresses weather stress to 0%
        # High Temperature + Low Humidity + High Radiation amplifies stress`,
    mathExplanation: {
      fuzzification: '5 antecedent universes: T [-10, 50°C], RH [0, 100%], Rad [0, 1200 W/m²], Wind [0, 25 m/s], Rain [0, 50 mm].',
      implication: 'Rain presence acts as a dominant inhibition rule; dry heat activates severe desiccating terms.',
      aggregation: 'Maximum envelope aggregation across 25 rules governing FAO-56 atmospheric drying.',
      defuzzification: 'Discrete centroid integration yielding crisp Weather Stress Index ∈ [0, 100]%.',
    },
  },
  water_demand: {
    id: 'water_demand',
    name: 'water_demand',
    title: 'FIS 3: Water Demand FIS',
    pyFile: 'fuzzy_engine/water_demand.py',
    serviceFile: 'backend/app/services/fuzzy_service.py',
    className: 'WaterDemandFIS',
    layer: 'Layer 2 • Agronomic Demand Synthesis',
    role: 'Synthesizes crop evapotranspiration (ETc), root-zone depletion, and effective rainfall into water demand.',
    defaultInputs: { etc: 6.5, crop_water_deficit: 15.0, effective_rainfall: 0.0 },
    pythonCode: `# fuzzy_engine/water_demand.py
class WaterDemandFIS:
    """Synthesizes crop ETc, soil water deficit, and effective precipitation."""
    def __init__(self, resolution: int = 501):
        self.universe = np.linspace(0.0, 100.0, resolution)
        
    def evaluate(self, inputs: dict) -> dict:
        etc = float(inputs.get("etc", 5.0))
        deficit = float(inputs.get("crop_water_deficit", 10.0))
        p_eff = float(inputs.get("effective_rainfall", 0.0))
        
        # Antecedents:
        # etc: [0, 20] mm/day (Low, Moderate, High, Extreme)
        # deficit: [0, 50] mm (Surplus, Zero, Mild, Moderate, Severe)
        # effective_rainfall: [0, 50] mm (None, Trace, Light, Heavy)
        
        # Rule Base evaluates replacement demand needed to balance root zone`,
    mathExplanation: {
      fuzzification: 'ETc [0, 20 mm/day], Deficit [0, 50 mm], Effective Rain [0, 50 mm].',
      implication: 'Mamdani minimum implication between crop transpiration requirement and existing soil reservoir storage.',
      aggregation: 'Max-union of 20 agronomic rules ensuring zero artificial water creation when rainfall covers demand.',
      defuzzification: 'Centroid defuzzification producing Crop Water Demand Index ∈ [0, 100]%.',
    },
  },
  main_irrigation: {
    id: 'main_irrigation',
    name: 'main_irrigation',
    title: 'FIS 4: Main Irrigation FIS',
    pyFile: 'fuzzy_engine/irrigation.py',
    serviceFile: 'backend/app/services/fuzzy_service.py',
    className: 'MainIrrigationFIS',
    layer: 'Layer 2 • Zone Supervisory Actuator Command',
    role: 'Core supervisory decision maker fusing soil stress, weather stress, water demand, and error into an actuator command.',
    defaultInputs: { soil_stress: 65.0, weather_stress: 50.0, water_demand: 70.0, moisture_error: 4.5 },
    pythonCode: `# fuzzy_engine/irrigation.py
class MainIrrigationFIS:
    """Primary supervisory controller outputting raw irrigation command [0, 100]%.
    Calibrated offline via 18-parameter PSO."""
    RULES = [
        # LAYER 1: Oversaturation Suppression (negative error shuts off valve)
        {"id": 1, "antecedents": {"moisture_error": "large_neg"}, "consequent": "off"},
        {"id": 2, "antecedents": {"moisture_error": "neg", "soil_stress": ["low", "mod"]}, "consequent": "off"},
        
        # LAYER 2: Balanced Maintenance Regulation
        # LAYER 3: Moisture Deficit Replacement Kernel
        # LAYER 4: Severe Moisture Depletion Override (error pos + demand high -> max)
        # LAYER 5: Climatic Forcing & Environmental Modulation
    ]
    
    def evaluate(self, inputs: dict) -> dict:
        # Fuzzify 4 heterogeneous physical indicators
        # Evaluate 32 rules
        # Defuzzify with 501 points centroid -> Raw Irrigation Command %
        # Command % is subsequently converted to physical depth (mm) via zone flow rate`,
    mathExplanation: {
      fuzzification: 'Fuses 4 inputs: Soil Stress [0, 100%], Weather Stress [0, 100%], Demand [0, 100%], Error [-30, +30%].',
      implication: 'Hierarchical 5-layer rule structure: Oversaturation Suppression -> Deficit Replacement -> Climate Forcing.',
      aggregation: 'Max envelope over 32 rules. When moisture_error < 0, "off" rules decisively dominate.',
      defuzzification: 'Centroid defuzzification producing Raw Irrigation Command ∈ [0, 100]% (converted to depth in mm).',
    },
  },
  water_allocation: {
    id: 'water_allocation',
    name: 'water_allocation',
    title: 'FIS 5: Water Allocation FIS',
    pyFile: 'fuzzy_engine/water_allocation.py',
    serviceFile: 'backend/app/services/fuzzy_service.py',
    className: 'WaterAllocationFIS',
    layer: 'Layer 3 • Supervisory Shared Supply Coordinator',
    role: 'Arbitrates shared constrained water supply among competing zones based on priority, scarcity, and demand.',
    defaultInputs: { available_water: 40.0, zone_demand: 75.0, zone_stress: 60.0, zone_priority: 90.0 },
    pythonCode: `# fuzzy_engine/water_allocation.py & fuzzy_engine/allocation.py
class WaterAllocationFIS:
    """Layer B Scarcity FIS + Layer C Deterministic Bounded Water-Filling."""
    
    def evaluate_allocation(self, available_supply_l: float, requests_l: dict, priorities: dict):
        total_requested = sum(requests_l.values())
        
        # 1. Abundance check: if supply >= total requested, fulfill 100%
        if available_supply_l >= total_requested:
            return {z: requests_l[z] for z in requests_l}
            
        # 2. Layer B: Scarcity FIS computes base rationing scale
        scarcity_pct = (1.0 - (available_supply_l / max(total_requested, 1e-6))) * 100.0
        
        # 3. Layer C: Priority-Weighted Bounded Water-Filling
        # Strictly enforces 5 Invariants:
        # - Invariant 1: sum(allocated) <= available_supply
        # - Invariant 2: 0 <= allocated_z <= requested_z
        # - Invariant 3: requested == 0 => allocated == 0
        # - Invariant 4: available_supply == 0 => allocated == 0
        # - Invariant 5: priority_1 > priority_2 => fulfillment_1 >= fulfillment_2
        return self._water_filling_dispatch(available_supply_l, requests_l, priorities)`,
    mathExplanation: {
      fuzzification: 'Available Water [0, 100%], Zone Demand [0, 100%], Zone Stress [0, 100%], Priority [0, 100%].',
      implication: 'Layer B computes continuous scarcity penalty; Layer C enforces hard mathematical conservation invariants.',
      aggregation: 'Multi-zone arbitration resolving competitive hydraulic allocation.',
      defuzzification: 'Deterministic Bounded Water-Filling outputting exact liters per zone (tolerance <= 1e-6 L).',
    },
  },
};

export default function BackendFuzzyArchitectureInspector() {
  const [selectedFisKey, setSelectedFisKey] = useState<string>('soil_stress');
  const [activeTab, setActiveTab] = useState<'pipeline' | 'code' | 'math' | 'live_test'>('pipeline');
  
  // Live test states
  const [inputs, setInputs] = useState<Record<string, number>>(FIS_BACKEND_DETAILS['soil_stress'].defaultInputs);
  const [evalResult, setEvalResult] = useState<FuzzyEvaluateResponse | null>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  const selectedFis = FIS_BACKEND_DETAILS[selectedFisKey];

  // Update inputs when changing selected FIS
  useEffect(() => {
    setInputs(selectedFis.defaultInputs);
    setEvalResult(null);
    setEvalError(null);
  }, [selectedFisKey]);

  // Execute live backend test
  const handleTestEvaluation = async () => {
    setIsEvaluating(true);
    setEvalError(null);
    try {
      const res = await api.evaluateFuzzy(selectedFis.id, inputs);
      setEvalResult(res);
    } catch (err: any) {
      setEvalError(`Backend evaluation error: ${err.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  return (
    <section id="backend-fuzzy-engine" className="rounded-3xl border border-slate-200 bg-white p-6 sm:p-8 shadow-xs space-y-8">
      {/* Header & Badges */}
      <div className="border-b border-slate-100 pb-5">
        <div className="flex flex-wrap items-center gap-2 mb-2">
          <span className="inline-flex items-center gap-1.5 rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-800 border border-emerald-200">
            <Code2 className="h-3.5 w-3.5 text-emerald-600" />
            Backend Architecture Inspector
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            fuzzy_engine/ • Python 3.11 • NumPy Vectorized
          </span>
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">
          How the Whole Fuzzy System Architecture Works on the Backend
        </h2>
        <p className="mt-1.5 text-xs sm:text-sm text-slate-600 leading-relaxed max-w-4xl">
          The backend does not treat fuzzy logic as a black-box. It executes a strictly verified 5-subsystem Mamdani cascade in pure Python and NumPy. Follow the dataflow from physical sensors through fuzzification, Gödel t-norm inference, and centroid defuzzification into bounded supervisory water-filling.
        </p>
      </div>

      {/* Interactive 5-Stage Architecture Flowchart */}
      <div className="rounded-2xl border border-emerald-200 bg-gradient-to-br from-emerald-50/40 via-teal-50/30 to-white p-5 sm:p-6 space-y-4 shadow-2xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="h-4 w-4 text-emerald-600" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-950 font-mono">
              Backend Execution Pipeline & Cascaded Dataflow
            </h3>
          </div>
          <span className="text-[10px] font-mono text-emerald-700 bg-white px-2 py-0.5 rounded border border-emerald-200 font-semibold">
            5 Mamdani FIS Cascade
          </span>
        </div>

        {/* Responsive Pipeline Steps */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-xs">
          {/* Stage 1 */}
          <div className="rounded-xl bg-white border border-slate-200 p-4 space-y-2 shadow-2xs flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                Stage 1: Telemetry
              </span>
              <h4 className="font-bold text-slate-900 mt-2 text-xs">Sensors & Meteorology</h4>
              <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                Capacitive soil moisture θ(t), target θ_target, solar radiation, temp, RH, wind, and rainfall.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-100 text-[10px] font-mono text-slate-500">
              models/et0.py & soil.py
            </div>
          </div>

          {/* Stage 2 */}
          <div 
            onClick={() => { setSelectedFisKey('soil_stress'); setActiveTab('code'); }}
            className={`rounded-xl border p-4 space-y-2 shadow-2xs flex flex-col justify-between cursor-pointer transition-all ${
              selectedFisKey === 'soil_stress' || selectedFisKey === 'weather_stress'
                ? 'border-emerald-500 bg-emerald-50/70 ring-1 ring-emerald-500'
                : 'bg-white border-slate-200 hover:border-emerald-300'
            }`}
          >
            <div>
              <span className="text-[10px] font-mono font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded">
                Stage 2: Stresses
              </span>
              <h4 className="font-bold text-slate-900 mt-2 text-xs">FIS 1 & FIS 2</h4>
              <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                <strong>SoilStressFIS</strong> (RSM × error) & <strong>WeatherStressFIS</strong> (5 climate sensors) output stress indices [0, 100]%.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-100 text-[10px] font-mono text-emerald-800 font-semibold">
              fuzzy_engine/soil_stress.py
            </div>
          </div>

          {/* Stage 3 */}
          <div 
            onClick={() => { setSelectedFisKey('water_demand'); setActiveTab('code'); }}
            className={`rounded-xl border p-4 space-y-2 shadow-2xs flex flex-col justify-between cursor-pointer transition-all ${
              selectedFisKey === 'water_demand'
                ? 'border-emerald-500 bg-emerald-50/70 ring-1 ring-emerald-500'
                : 'bg-white border-slate-200 hover:border-emerald-300'
            }`}
          >
            <div>
              <span className="text-[10px] font-mono font-bold text-sky-800 bg-sky-100 px-2 py-0.5 rounded">
                Stage 3: Demand
              </span>
              <h4 className="font-bold text-slate-900 mt-2 text-xs">FIS 3: Water Demand</h4>
              <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                Combines FAO-56 crop ETc, soil moisture deficit, and effective precipitation into net Water Demand.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-100 text-[10px] font-mono text-sky-800 font-semibold">
              fuzzy_engine/water_demand.py
            </div>
          </div>

          {/* Stage 4 */}
          <div 
            onClick={() => { setSelectedFisKey('main_irrigation'); setActiveTab('code'); }}
            className={`rounded-xl border p-4 space-y-2 shadow-2xs flex flex-col justify-between cursor-pointer transition-all ${
              selectedFisKey === 'main_irrigation'
                ? 'border-emerald-500 bg-emerald-50/70 ring-1 ring-emerald-500'
                : 'bg-white border-slate-200 hover:border-emerald-300'
            }`}
          >
            <div>
              <span className="text-[10px] font-mono font-bold text-purple-800 bg-purple-100 px-2 py-0.5 rounded">
                Stage 4: Actuation
              </span>
              <h4 className="font-bold text-slate-900 mt-2 text-xs">FIS 4: Main Irrigation</h4>
              <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                Fuses stresses, demand, and error across 32 rules into raw irrigation command % and depth (mm).
              </p>
            </div>
            <div className="pt-2 border-t border-slate-100 text-[10px] font-mono text-purple-800 font-semibold">
              fuzzy_engine/irrigation.py
            </div>
          </div>

          {/* Stage 5 */}
          <div 
            onClick={() => { setSelectedFisKey('water_allocation'); setActiveTab('code'); }}
            className={`rounded-xl border p-4 space-y-2 shadow-2xs flex flex-col justify-between cursor-pointer transition-all ${
              selectedFisKey === 'water_allocation'
                ? 'border-emerald-500 bg-emerald-50/70 ring-1 ring-emerald-500'
                : 'bg-white border-slate-200 hover:border-emerald-300'
            }`}
          >
            <div>
              <span className="text-[10px] font-mono font-bold text-amber-900 bg-amber-100 px-2 py-0.5 rounded">
                Stage 5: Allocation
              </span>
              <h4 className="font-bold text-slate-900 mt-2 text-xs">FIS 5 + Water-Filling</h4>
              <p className="text-[11px] text-slate-600 mt-1 leading-relaxed">
                Supervisory scarcity arbitration enforcing supply caps, demand ceilings, and priority monotonicity.
              </p>
            </div>
            <div className="pt-2 border-t border-slate-100 text-[10px] font-mono text-amber-900 font-semibold">
              fuzzy_engine/water_allocation.py
            </div>
          </div>
        </div>
      </div>

      {/* Subsystem Selector Buttons */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
            Select FIS Subsystem to Inspect Backend Code & Execution:
          </span>
          <span className="text-xs font-mono text-slate-500">
            Active: <strong className="text-emerald-700">{selectedFis.className}</strong>
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5">
          {Object.keys(FIS_BACKEND_DETAILS).map((key) => {
            const item = FIS_BACKEND_DETAILS[key];
            const isActive = selectedFisKey === key;
            return (
              <button
                key={key}
                onClick={() => setSelectedFisKey(key)}
                className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                  isActive
                    ? 'border-emerald-500 bg-emerald-600 text-white shadow-md shadow-emerald-600/20 ring-2 ring-emerald-500/20'
                    : 'border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-slate-50'
                }`}
              >
                <div className={`text-[10px] font-mono font-bold ${isActive ? 'text-emerald-100' : 'text-emerald-700'}`}>
                  {item.className}
                </div>
                <div className="text-xs font-bold mt-1 truncate">
                  {item.title.split(':')[1]?.trim() || item.name}
                </div>
                <div className={`text-[10px] mt-1 truncate ${isActive ? 'text-emerald-100' : 'text-slate-500'}`}>
                  {item.pyFile}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Subsystem Metadata Banner */}
      <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 text-xs flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div className="space-y-0.5">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 text-sm">{selectedFis.title}</span>
            <span className="font-mono text-[10px] bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded border border-emerald-200 font-semibold">
              {selectedFis.layer}
            </span>
          </div>
          <p className="text-slate-600 text-[11px]">{selectedFis.role}</p>
        </div>

        <div className="flex flex-wrap gap-2 text-[11px] font-mono">
          <span className="bg-white px-2.5 py-1 rounded-md border border-slate-200 text-slate-700">
            Source: <strong className="text-slate-900">{selectedFis.pyFile}</strong>
          </span>
          <span className="bg-white px-2.5 py-1 rounded-md border border-slate-200 text-slate-700">
            Service: <strong className="text-slate-900">{selectedFis.serviceFile}</strong>
          </span>
        </div>
      </div>

      {/* Mode View Tabs (Pipeline vs Python Code vs Math vs Live Test) */}
      <div className="border-b border-slate-200">
        <div className="flex gap-2 sm:gap-4 overflow-x-auto pb-px">
          {[
            { id: 'pipeline', label: 'Inference Architecture', icon: Layers },
            { id: 'code', label: 'Backend Python Source', icon: FileCode },
            { id: 'math', label: 'Defuzzification Math', icon: Cpu },
            { id: 'live_test', label: 'Live Backend Evaluation', icon: Zap },
          ].map((tab) => {
            const isActive = activeTab === tab.id;
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`inline-flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                  isActive
                    ? 'border-emerald-600 text-emerald-700 font-bold'
                    : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-emerald-600' : 'text-slate-400'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* TAB CONTENT 1: PIPELINE EXPLANATION */}
      {activeTab === 'pipeline' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase font-bold text-emerald-700">Step 1: Input Fuzzification</span>
              <h4 className="text-xs font-bold text-slate-900">Piecewise Vectorized MFs</h4>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Crisp floating-point inputs are evaluated against linear triangular trimf(x; a, b, c) and trapezoidal trapmf(x; a, b, c, d) curves using NumPy masks for maximum speed.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase font-bold text-sky-700">Step 2: Gödel Mamdani Min</span>
              <h4 className="text-xs font-bold text-slate-900">Rule Implication & Aggregation</h4>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                Rules combine fuzzy terms using the minimum conjunction operator (μ_rule = min(μ_1, μ_2)). Consequents are truncated via min and aggregated across all rules via the maximum operator.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <span className="text-[10px] font-mono uppercase font-bold text-purple-700">Step 3: Defuzzification</span>
              <h4 className="text-xs font-bold text-slate-900">501-Point Centroid (COA)</h4>
              <p className="text-[11px] text-slate-600 leading-relaxed">
                The continuous aggregated envelope is numerically integrated over 501 discretized points to yield a single crisp output float: y* = Σ(y_i · μ(y_i)) / Σ(μ(y_i)).
              </p>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 2: PYTHON BACKEND SOURCE CODE */}
      {activeTab === 'code' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-bold text-slate-700 flex items-center gap-1.5">
              <Terminal className="h-4 w-4 text-emerald-600" />
              <span>{selectedFis.pyFile}</span>
            </span>
            <span className="text-[11px] font-mono text-slate-500">Python 3.11 • Standard NumPy</span>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 sm:p-5 font-mono text-xs text-slate-200 overflow-x-auto shadow-md">
            <pre className="text-[11px] leading-relaxed text-emerald-300">
              <code>{selectedFis.pythonCode}</code>
            </pre>
          </div>
        </div>
      )}

      {/* TAB CONTENT 3: MATHEMATICAL EXPLANATION */}
      {activeTab === 'math' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                1. Fuzzification Formulas
              </h4>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono text-[11px] text-slate-800">
                μ_trimf(x; a, b, c) = max(0, min((x-a)/(b-a), (c-x)/(c-b)))
                <br />
                μ_trapmf(x; a, b, c, d) = max(0, min((x-a)/(b-a), 1, (d-x)/(d-c)))
              </div>
              <p className="text-[11px] text-slate-600">{selectedFis.mathExplanation.fuzzification}</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-sky-500" />
                2. Rule Implication & Gödel t-norm
              </h4>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono text-[11px] text-slate-800">
                μ_rule = min(μ_ant1, μ_ant2, ..., μ_antN)
                <br />
                μ_implied(y) = min(μ_rule, μ_consequent(y))
              </div>
              <p className="text-[11px] text-slate-600">{selectedFis.mathExplanation.implication}</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-amber-500" />
                3. Maximum Envelope Aggregation
              </h4>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono text-[11px] text-slate-800">
                μ_aggregated(y) = max_r ( μ_implied, r(y) )
              </div>
              <p className="text-[11px] text-slate-600">{selectedFis.mathExplanation.aggregation}</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-4 space-y-2">
              <h4 className="font-bold text-slate-900 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-purple-500" />
                4. Centroid Defuzzification (COA)
              </h4>
              <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 font-mono text-[11px] text-slate-800">
                y* = [ Σ (y_i · μ_agg(y_i)) ] / [ Σ μ_agg(y_i) ]
              </div>
              <p className="text-[11px] text-slate-600">{selectedFis.mathExplanation.defuzzification}</p>
            </div>
          </div>
        </div>
      )}

      {/* TAB CONTENT 4: LIVE BACKEND EVALUATION TEST */}
      {activeTab === 'live_test' && (
        <div className="space-y-4">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-5 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h4 className="text-sm font-bold text-emerald-950 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-emerald-600" />
                  <span>Execute Real-Time Backend Inference for {selectedFis.className}</span>
                </h4>
                <p className="text-xs text-slate-600 mt-0.5">
                  Sends live inputs to <code className="font-mono bg-white px-1 py-0.5 rounded border border-emerald-200">POST /api/fuzzy/evaluate</code>
                </p>
              </div>

              <button
                onClick={handleTestEvaluation}
                disabled={isEvaluating}
                className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2.5 text-xs font-bold transition-all shadow-xs cursor-pointer focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
              >
                {isEvaluating ? (
                  <>
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    <span>Evaluating in Python...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Evaluate on Backend</span>
                  </>
                )}
              </button>
            </div>

            {evalError && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800">
                {evalError}
              </div>
            )}

            {/* Input fields */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.keys(inputs).map((key) => (
                <div key={key} className="bg-white p-3 rounded-xl border border-slate-200 space-y-1">
                  <label className="text-[10px] font-mono font-bold text-slate-600 block uppercase">
                    {key.replace('_', ' ')}
                  </label>
                  <input
                    type="number"
                    step={0.1}
                    value={inputs[key]}
                    onChange={(e) => setInputs({ ...inputs, [key]: parseFloat(e.target.value) || 0 })}
                    className="w-full text-xs font-mono font-bold text-slate-900 border border-slate-200 rounded-lg p-1.5 focus:border-emerald-500 focus:outline-none"
                  />
                </div>
              ))}
            </div>

            {/* Live Output Display */}
            {evalResult && (
              <div className="rounded-xl bg-white border border-emerald-300 p-4 space-y-3 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-[10px] font-mono uppercase font-bold text-emerald-800 block">
                      Defuzzified Crisp Result from Backend:
                    </span>
                    <div className="text-2xl font-black font-mono text-emerald-700 mt-1">
                      {evalResult.output_value.toFixed(2)} {(evalResult as any).unit || '%'}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] font-mono text-slate-500 block">Active Rules Triggered:</span>
                    <span className="text-xs font-bold text-slate-800">
                      {evalResult.fired_rules?.length || 0} rules fired
                    </span>
                  </div>
                </div>

                {evalResult.fired_rules && evalResult.fired_rules.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[11px] font-bold text-slate-700 block">Rule Activations (Mamdani Min):</span>
                    <div className="max-h-36 overflow-y-auto space-y-1 text-[10px] font-mono text-slate-700">
                      {evalResult.fired_rules.map((fr: any, idx: number) => (
                        <div key={idx} className="flex justify-between bg-slate-50 p-2 rounded border border-slate-200">
                          <span className="truncate max-w-[280px] sm:max-w-md">
                            R{fr.rule_index !== undefined ? fr.rule_index + 1 : idx + 1}: {fr.antecedent} → {fr.consequent}
                          </span>
                          <span className="font-bold text-emerald-700">
                            μ = {typeof fr.firing_strength === 'number' ? fr.firing_strength.toFixed(3) : '1.000'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
