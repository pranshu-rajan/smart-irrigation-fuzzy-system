'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import IndiaInteractiveMap, { SelectedLocation } from '@/components/IndiaInteractiveMap';
import FuzzyArchitectureLiveCascade from '@/components/FuzzyArchitectureLiveCascade';
import MetricCard from '@/components/MetricCard';
import SoilHydrologyProfile from '@/components/SoilHydrologyProfile';
import FuzzyStageDeepInspector from '@/components/FuzzyStageDeepInspector';
import PredictiveMoistureGraph from '@/components/PredictiveMoistureGraph';
import WaterConservationLedger from '@/components/WaterConservationLedger';
import ActuatorDigitalFlowStation from '@/components/ActuatorDigitalFlowStation';
import DistrictComparisonMatrix from '@/components/DistrictComparisonMatrix';
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
  Gauge,
  Award,
  Zap,
  Flame,
  Scale,
  Umbrella
} from 'lucide-react';

const DEFAULT_LOCATION: SelectedLocation = {
  district: 'Ludhiana',
  state: 'Punjab',
  agro_climatic_zone: 'Zone VI: Trans-Gangetic Plains Region',
  latitude: 30.9010,
  longitude: 75.8573,
};

const AVAILABLE_CROPS = [
  'Wheat',
  'Basmati Rice',
  'Paddy',
  'Sugarcane',
  'Cotton',
  'Tomato',
  'Potato',
  'Mustard',
  'Maize',
  'Soybean',
  'Groundnut',
  'Chilli',
  'Gram / Chickpea',
  'Bajra',
];

export default function DashboardPage() {
  const [selectedLoc, setSelectedLoc] = useState<SelectedLocation>(DEFAULT_LOCATION);
  const [evalData, setEvalData] = useState<any>(null);
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [advisory, setAdvisory] = useState<any>(null);
  const [loadingAdvisory, setLoadingAdvisory] = useState<boolean>(false);
  const [evalHistory, setEvalHistory] = useState<Array<{ district: string; state: string; timestamp: string; et0: number; allocated: number }>>([]);
  const [reservoirStoragePct, setReservoirStoragePct] = useState<number>(75);
  const [tavilyCredits, setTavilyCredits] = useState<{ remaining: number; total: number }>({ remaining: 942, total: 1000 });

  // In-session cache for AI Advisories to prevent redundant Tavily credit consumption
  const advisoryCacheRef = useRef<Record<string, any>>({});

  // 2026 Interactive Features State
  const [climateScenario, setClimateScenario] = useState<'live' | 'heatwave' | 'monsoon' | 'drought' | 'windy'>('live');
  const [zoneCropOverrides, setZoneCropOverrides] = useState<{ zone1?: string; zone2?: string; zone3?: string }>({});

  // Evaluate fuzzy system architecture for selected location with climate & crop overrides
  const evaluateLocation = useCallback(async (
    loc: SelectedLocation, 
    resStorage: number = 75,
    scenario: 'live' | 'heatwave' | 'monsoon' | 'drought' | 'windy' = 'live',
    crops: { zone1?: string; zone2?: string; zone3?: string } = {}
  ) => {
    setIsEvaluating(true);
    setErrorMsg(null);

    let tempOverride: number | undefined;
    let humOverride: number | undefined;
    let solarOverride: number | undefined;
    let rainOverride: number | undefined;
    let effectiveRes = resStorage;

    if (scenario === 'heatwave') {
      tempOverride = 42.0;
      humOverride = 20.0;
      solarOverride = 950.0;
      rainOverride = 0.0;
    } else if (scenario === 'monsoon') {
      tempOverride = 23.5;
      humOverride = 96.0;
      solarOverride = 180.0;
      rainOverride = 35.0;
    } else if (scenario === 'drought') {
      effectiveRes = 22.0;
      tempOverride = 39.0;
      humOverride = 25.0;
      rainOverride = 0.0;
    } else if (scenario === 'windy') {
      tempOverride = 33.0;
      humOverride = 35.0;
      solarOverride = 750.0;
    }

    try {
      const data = await api.evaluateIndiaLocation({
        location_query: loc.district,
        latitude: loc.latitude,
        longitude: loc.longitude,
        reservoir_storage_pct: effectiveRes,
        temperature_override: tempOverride,
        humidity_override: humOverride,
        solar_radiation_override: solarOverride,
        rainfall_override: rainOverride,
        zone1_crop_override: crops.zone1,
        zone2_crop_override: crops.zone2,
        zone3_crop_override: crops.zone3,
        field_name: loc.fieldName || (loc.tehsilVillage ? `${loc.tehsilVillage} Farm Basin` : undefined),
        field_area_m2: loc.fieldAreaAcres ? loc.fieldAreaAcres * 4046.86 : undefined,
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

  // Fetch Groq AI Agronomist advisory (with session caching to protect Tavily search credits)
  const fetchAdvisory = async (evaluation: any) => {
    const distKey = `${evaluation.location?.district || selectedLoc.district}_${evaluation.zone_allocations?.[0]?.crop || 'crop'}`;
    
    // Check in-session cache first (0 network calls, 0 Tavily credits consumed)
    if (advisoryCacheRef.current[distKey]) {
      setAdvisory(advisoryCacheRef.current[distKey]);
      return;
    }

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
      // Store in session cache
      advisoryCacheRef.current[distKey] = adv;
      setAdvisory(adv);
    } catch (err) {
      console.warn('Could not fetch agromet advisory:', err);
    } finally {
      setLoadingAdvisory(false);
    }
  };

  // Helper to format AI advisory text with clean typography, bold highlights, and sanitized formulas
  const renderFormattedSummary = (rawText: string) => {
    if (!rawText) return null;

    // Sanitize any residual LaTeX or raw markdown delimiters
    let clean = rawText
      .replace(/\\\[/g, '')
      .replace(/\\\]/g, '')
      .replace(/\\approx/g, '≈')
      .replace(/\\times/g, '×')
      .replace(/\\text\{([^}]+)\}/g, '$1')
      .replace(/\\;/g, ' ')
      .replace(/---/g, '')
      .replace(/###\s*[^\n]+/g, '');

    const paragraphs = clean.split('\n\n').filter((p) => p.trim().length > 0);

    return (
      <div className="space-y-3">
        {paragraphs.map((para, pIdx) => {
          // Parse **bold** markers
          const parts = para.split(/(\*\*.*?\*\*)/g);
          return (
            <p key={pIdx} className="text-xs sm:text-sm text-slate-700 leading-relaxed">
              {parts.map((part, idx) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                  return (
                    <strong key={idx} className="font-semibold text-emerald-800">
                      {part.slice(2, -2)}
                    </strong>
                  );
                }
                return part;
              })}
            </p>
          );
        })}
      </div>
    );
  };

  // Helper to parse each critical farming tip into a category title and actionable description
  const parseTip = (rawTip: string) => {
    let clean = rawTip.trim();
    // Check for **Title** - Body or **Title**: Body or Title: Body
    const match = clean.match(/^\*\*([^*]+)\*\*[:\s–—-]+(.+)$/) || clean.match(/^([A-Za-z\s]+)[:–—-]+(.+)$/);
    if (match) {
      return {
        title: match[1].trim(),
        body: match[2].trim().replace(/\*\*/g, ''),
      };
    }
    // If it's just **Title** without body, clean it
    const titleOnly = clean.match(/^\*\*([^*]+)\*\*$/);
    if (titleOnly) {
      return {
        title: titleOnly[1].trim(),
        body: `Follow regional ICAR package of practices to optimize ${titleOnly[1].toLowerCase()}.`,
      };
    }
    return {
      title: 'Practical Field Advisory',
      body: clean.replace(/\*\*/g, ''),
    };
  };

  // Initial load on mount
  useEffect(() => {
    evaluateLocation(DEFAULT_LOCATION, reservoirStoragePct, climateScenario, zoneCropOverrides);
    // Fetch live Tavily credit ledger status
    api.getTavilyCreditStatus()
      .then((data) => {
        if (data && data.credits_remaining !== undefined) {
          setTavilyCredits({ remaining: data.credits_remaining, total: data.total_credits || 1000 });
        }
      })
      .catch(() => {});
  }, [evaluateLocation]);

  // Handle map selection
  const handleLocationSelect = (loc: SelectedLocation) => {
    setSelectedLoc(loc);
    evaluateLocation(loc, reservoirStoragePct, climateScenario, zoneCropOverrides);
  };

  // Climate Scenario Switcher
  const handleClimateChange = (scenario: 'live' | 'heatwave' | 'monsoon' | 'drought' | 'windy') => {
    setClimateScenario(scenario);
    evaluateLocation(selectedLoc, reservoirStoragePct, scenario, zoneCropOverrides);
  };

  // Crop Selector per Zone
  const handleCropChange = (zoneId: number, cropName: string) => {
    const updated = {
      ...zoneCropOverrides,
      [`zone${zoneId}`]: cropName,
    };
    setZoneCropOverrides(updated);
    evaluateLocation(selectedLoc, reservoirStoragePct, climateScenario, updated);
  };

  // Derived Telemetry Values
  const weather = evalData?.weather;
  const physics = evalData?.physics_agronomy;
  const stages = evalData?.fuzzy_stages;
  const zones = evalData?.zone_allocations || [];
  const locInfo = evalData?.location;
  const hourlyTelemetry = evalData?.hourly_telemetry || [];

  return (
    <div className="space-y-6 pb-20">
      {/* 1. Header Command Ribbon */}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between rounded-3xl border border-emerald-200/90 bg-gradient-to-r from-emerald-50 via-teal-50/40 to-white p-6 shadow-sm text-slate-800">
        <div>
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-emerald-100 border border-emerald-200 text-emerald-700">
              <Globe className="h-5 w-5 animate-pulse" />
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-900 font-sans">
              National Precision Irrigation Command Hub
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 border border-emerald-200 px-3 py-0.5 text-xs font-semibold text-emerald-800">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              5-STAGE FUZZY PIPELINE ACTIVE
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-600 max-w-3xl">
            Real-time geospatial intelligence across India, live Open-Meteo & Tavily atmospheric forcing, ICAR agro-climatic soil physics, and closed-loop supervisory fuzzy valve control.
          </p>
          <div className="mt-2.5 flex flex-wrap items-center gap-2 text-xs">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-white border border-emerald-200 px-2.5 py-1 text-emerald-800 font-semibold text-[11px] shadow-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Sprout className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
              <span className="uppercase tracking-wider font-mono text-[10px] text-emerald-700 font-bold">Plot Locked:</span>
              <span className="text-slate-900 font-medium">{locInfo?.field_name || selectedLoc.fieldName || `${selectedLoc.district} Central Farmland`}</span>
            </span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-700 font-medium text-[11px]">
              {selectedLoc.tehsilVillage ? `${selectedLoc.tehsilVillage}, ` : ''}{selectedLoc.district}, {selectedLoc.state}
            </span>
            <span className="text-slate-300">•</span>
            <span className="font-mono text-cyan-800 text-[11px] bg-cyan-50 px-1.5 py-0.5 rounded border border-cyan-200">
              GPS: {selectedLoc.latitude.toFixed(4)}°N, {selectedLoc.longitude.toFixed(4)}°E
            </span>
            {selectedLoc.fieldAreaAcres && (
              <>
                <span className="text-slate-300">•</span>
                <span className="text-amber-800 text-[11px] font-medium bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                  {selectedLoc.fieldAreaAcres} Acres ({Math.round(selectedLoc.fieldAreaAcres * 4046.86).toLocaleString()} m²)
                </span>
              </>
            )}
          </div>
        </div>

        {/* Quick Location Action Controls */}
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Reservoir Storage Slider */}
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-white px-3 py-2 text-xs text-slate-700 shadow-xs">
            <Droplets className="h-3.5 w-3.5 text-cyan-600 shrink-0" />
            <span className="text-[11px] text-slate-500 font-medium">Reservoir:</span>
            <input
              type="range"
              min={20}
              max={100}
              value={reservoirStoragePct}
              onChange={(e) => {
                const val = Number(e.target.value);
                setReservoirStoragePct(val);
                evaluateLocation(selectedLoc, val, climateScenario, zoneCropOverrides);
              }}
              className="h-1.5 w-24 accent-emerald-500 cursor-pointer"
              title={`Reservoir Storage: ${reservoirStoragePct}%`}
            />
            <span className="font-mono text-emerald-700 font-semibold">{reservoirStoragePct}%</span>
          </div>

          {/* Re-Evaluate Trigger Button */}
          <button
            onClick={() => evaluateLocation(selectedLoc, reservoirStoragePct, climateScenario, zoneCropOverrides)}
            disabled={isEvaluating}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 px-4 py-2 text-xs font-semibold text-white shadow-md transition disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isEvaluating ? 'animate-spin' : ''}`} />
            <span>{isEvaluating ? 'Evaluating FIS...' : 'Re-Evaluate Farm'}</span>
          </button>
        </div>
      </div>

      {/* Real-Time Environmental Climate Stress Simulation Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl border border-emerald-200/90 bg-white/95 backdrop-blur-xl px-5 py-3.5 shadow-sm">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-emerald-600 animate-spin-slow" />
          <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
            Atmospheric Forcing Engine:
          </span>
          <span className="text-[11px] text-slate-500 hidden sm:inline">
            Inject real-time climate stresses to evaluate dynamic fuzzy responses
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            onClick={() => handleClimateChange('live')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              climateScenario === 'live'
                ? 'bg-emerald-600 text-white shadow-xs font-bold'
                : 'bg-emerald-50/60 text-slate-700 hover:text-emerald-800 hover:bg-emerald-100/60 border border-emerald-200/80'
            }`}
          >
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Live Open-Meteo</span>
          </button>

          <button
            onClick={() => handleClimateChange('heatwave')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              climateScenario === 'heatwave'
                ? 'bg-amber-600 text-white shadow-xs font-bold'
                : 'bg-amber-50/60 text-amber-900 hover:bg-amber-100/60 border border-amber-200/80'
            }`}
          >
            <Sun className="h-3.5 w-3.5 text-amber-500" />
            <span>Heatwave (42°C)</span>
          </button>

          <button
            onClick={() => handleClimateChange('monsoon')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              climateScenario === 'monsoon'
                ? 'bg-cyan-600 text-white shadow-xs font-bold'
                : 'bg-cyan-50/60 text-cyan-900 hover:bg-cyan-100/60 border border-cyan-200/80'
            }`}
          >
            <CloudRain className="h-3.5 w-3.5 text-cyan-600" />
            <span>Monsoon Deluge (35mm)</span>
          </button>

          <button
            onClick={() => handleClimateChange('drought')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              climateScenario === 'drought'
                ? 'bg-rose-600 text-white shadow-xs font-bold'
                : 'bg-rose-50/60 text-rose-900 hover:bg-rose-100/60 border border-rose-200/80'
            }`}
          >
            <AlertTriangle className="h-3.5 w-3.5 text-rose-500" />
            <span>Drought Scarcity (22% Pond)</span>
          </button>

          <button
            onClick={() => handleClimateChange('windy')}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer flex items-center gap-1.5 ${
              climateScenario === 'windy'
                ? 'bg-indigo-600 text-white shadow-xs font-bold'
                : 'bg-indigo-50/60 text-indigo-900 hover:bg-indigo-100/60 border border-indigo-200/80'
            }`}
          >
            <Wind className="h-3.5 w-3.5 text-indigo-600" />
            <span>High Wind Deficit</span>
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
        isEvaluating={isEvaluating}
      />

      {/* 2.5 Live 5-Stage Fuzzy Architecture Cascade (Instant Map Region Output) */}
      <FuzzyArchitectureLiveCascade
        location={locInfo || selectedLoc}
        weather={weather}
        physics={physics}
        fuzzyStages={stages}
        zones={zones}
        totalRequestedLiters={evalData?.total_requested_liters}
        totalAllocatedLiters={evalData?.total_allocated_liters}
        fulfillmentRatioPct={evalData?.overall_fulfillment_ratio_pct}
        reservoirStoragePct={reservoirStoragePct}
        isEvaluating={isEvaluating}
        onReEvaluate={() => evaluateLocation(selectedLoc, reservoirStoragePct, climateScenario, zoneCropOverrides)}
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

      {/* 4. Advanced Feature A: Deep 5-Stage FIS Subsystem Inspector for Every Zone */}
      <FuzzyStageDeepInspector
        zones={zones}
        weatherStress={stages?.stage2_weather_stress_pct || 48.0}
        et0Val={physics?.et0_fao56_mm_day || 4.5}
        reservoirStorage={reservoirStoragePct}
        weather={weather}
        location={locInfo || selectedLoc}
      />

      {/* 5. Advanced Feature B: 24-Hour Predictive Closed-Loop Soil Moisture Forecast */}
      <PredictiveMoistureGraph
        hourlyTelemetry={hourlyTelemetry}
        fieldCapacity={locInfo?.field_capacity_pct || 28.0}
        wiltingPoint={locInfo?.wilting_point_pct || 12.0}
        crop1Name={zones[0]?.crop || 'Kharif Crop'}
        crop2Name={zones[1]?.crop || 'Rabi Crop'}
        crop3Name={zones[2]?.crop || 'Zaid Crop'}
      />

      {/* 6. Advanced Feature C: Real-Time Soil Hydrology & Hydraulic Horizon Profile */}
      <SoilHydrologyProfile
        soilType={locInfo?.dominant_soil || 'Alluvial (Inceptisol)'}
        currentMoisture={zones[0]?.current_moisture_pct || 24.5}
        fieldCapacity={locInfo?.field_capacity_pct || 28.0}
        wiltingPoint={locInfo?.wilting_point_pct || 12.0}
        saturation={locInfo?.saturation_pct || 45.0}
      />

      {/* 7. Dynamic ICAR Agricultural Zones (Location-Tailored Crops & Actuators) */}
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

                  <div className="mt-2 flex items-center justify-between gap-2">
                    <h3 className="text-sm font-bold text-slate-900 truncate">{z.name}</h3>
                    <div className="flex items-center gap-1 shrink-0">
                      <span className="text-[10px] text-slate-400 font-mono">Crop:</span>
                      <select
                        value={zoneCropOverrides[`zone${z.zone_id}` as keyof typeof zoneCropOverrides] || z.crop}
                        onChange={(e) => handleCropChange(z.zone_id, e.target.value)}
                        className="rounded-lg border border-slate-200 bg-slate-50 px-2 py-1 text-[11px] font-semibold text-slate-800 hover:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-500 cursor-pointer shadow-2xs"
                        title="Change crop for this zone"
                      >
                        {AVAILABLE_CROPS.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
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

      {/* 8. Real-Time Actuator & Solenoid Telemetry Station (New 2026 Supervisory Feature) */}
      <ActuatorDigitalFlowStation
        zones={zones}
        isSupplyConstrained={evalData?.is_supply_constrained}
        totalAllocatedLiters={evalData?.total_allocated_liters || 0}
      />

      {/* 9. Advanced Feature D & E: Supervisory Water Balance & Mass Conservation Ledger */}
      <WaterConservationLedger
        totalRequested={evalData?.total_requested_liters || 420.0}
        totalAllocated={evalData?.total_allocated_liters || 384.2}
        availableSupply={evalData?.available_supply_liters || 6000.0}
        district={locInfo?.district || selectedLoc.district}
        state={locInfo?.state || selectedLoc.state}
        crop={zones[0]?.crop || 'Wheat'}
      />

      {/* 10. Multi-District National Fuzzy Comparative Matrix (New 2026 GIS Benchmark Feature) */}
      <DistrictComparisonMatrix
        currentDistrict={locInfo?.district || selectedLoc.district}
        currentState={locInfo?.state || selectedLoc.state}
        currentEvaluation={evalData}
        onSelectDistrict={(districtName) => {
          const loc: SelectedLocation = {
            district: districtName,
            state: 'India',
            latitude: selectedLoc.latitude,
            longitude: selectedLoc.longitude,
          };
          evaluateLocation(loc, reservoirStoragePct, climateScenario, zoneCropOverrides);
        }}
      />

      {/* 9. AI Agronomist Copilot (Groq Llama 3.3 70B & Tavily Live Knowledge) */}
      <div className="rounded-3xl border border-emerald-200/90 bg-white p-6 shadow-sm text-slate-800">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-emerald-100 pb-3 mb-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 border border-emerald-200">
              <Bot className="h-4.5 w-4.5" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold text-slate-900 flex flex-wrap items-center gap-2">
                <span>AI Agronomist Field Copilot</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 border border-emerald-200 px-2 py-0.5 text-[10px] font-semibold text-emerald-800">
                  <Sparkles className="h-2.5 w-2.5" />
                  Groq 70B • Tavily Live Search
                </span>
                <span className="inline-flex items-center gap-1 rounded-full bg-cyan-50 border border-cyan-200 px-2 py-0.5 text-[10px] font-semibold text-cyan-800 font-mono">
                  <ShieldCheck className="h-2.5 w-2.5 text-cyan-600" />
                  Tavily Guard: {tavilyCredits.remaining}/{tavilyCredits.total} Credits (7-Day Disk Cache Active)
                </span>
              </h2>
            </div>
          </div>
          <Link
            href="/ai"
            className="text-xs font-semibold text-emerald-700 hover:text-emerald-900 flex items-center gap-1"
          >
            <span>Open Dedicated AI Advisory</span>
            <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {loadingAdvisory ? (
          <div className="flex items-center gap-3 py-4 text-xs text-slate-500">
            <RefreshCw className="h-4 w-4 animate-spin text-emerald-600" />
            <span>Consulting Groq agronomy knowledge base & real-time crop advisory...</span>
          </div>
        ) : advisory ? (
          <div className="space-y-4">
            {/* Rich Formatted Summary Paragraphs */}
            <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/30 p-4 sm:p-5 shadow-2xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800 font-mono block mb-2">
                Grounded Agronomic Evaluation
              </span>
              {renderFormattedSummary(advisory.advisory_summary)}
            </div>

            {/* Structured High-Aesthetic Advisory Cards */}
            {advisory.critical_farming_tips && advisory.critical_farming_tips.length > 0 && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                {advisory.critical_farming_tips
                  .filter((t: string) => t && t.trim().length > 10)
                  .slice(0, 4)
                  .map((tip: string, idx: number) => {
                    const parsed = parseTip(tip);
                    return (
                      <div
                        key={idx}
                        className="flex items-start gap-3 rounded-2xl bg-white border border-emerald-200/80 p-4 text-xs text-slate-800 shadow-2xs hover:border-emerald-400 hover:bg-emerald-50/20 transition-all"
                      >
                        <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 shrink-0 mt-0.5 border border-emerald-200">
                          <CheckCircle2 className="h-4 w-4" />
                        </div>
                        <div className="space-y-1">
                          <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-emerald-800 font-mono">
                            {parsed.title}
                          </span>
                          <p className="text-xs text-slate-600 leading-relaxed">
                            {parsed.body}
                          </p>
                        </div>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        ) : (
          <p className="text-xs text-slate-500">
            Select any district on the interactive map above to generate instant AI agronomist field schedules.
          </p>
        )}
      </div>

      {/* 10. Recent National Evaluations Feed (Interactive History) */}
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
