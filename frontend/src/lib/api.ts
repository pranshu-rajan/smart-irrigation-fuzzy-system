/**
 * API client library for Smart Multizone Fuzzy Irrigation Platform.
 * Connects Next.js frontend to FastAPI backend.
 */

export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api';

// --- Interfaces ---

export interface ZoneConfig {
  id: number;
  name: string;
  crop_type: string;
  soil_type: string;
  area_m2: number;
  target_moisture_fraction: number;
  flow_rate_lpm: number;
  priority_weight: number;
  is_active: boolean;
}

export interface ZoneStatus {
  zone_id: number;
  name: string;
  crop_type: string;
  soil_type: string;
  current_moisture_pct: number;
  target_moisture_pct: number;
  stress_level: 'OPTIMAL' | 'MODERATE' | 'SEVERE';
  valve_state: 'OPEN' | 'CLOSED';
  last_irrigation_minutes: number;
  flow_rate_lpm: number;
  total_water_today_liters: number;
}

export interface SimulationRunRequest {
  scenario?: string;
  duration_hours?: number;
  timestep_minutes?: number;
  controller_type?: string;
  supply_scenario?: string;
  supply_factor_override?: number;
  seed?: number;
  zone_ids?: number[];
}

export interface SimulationSummaryResponse {
  id: string;
  user_id: string;
  scenario: string;
  duration_hours: number;
  timestep_minutes: number;
  status: string;
  controller_type: string;
  supply_scenario: string;
  summary_metrics: {
    total_water_volume_requested_l?: number;
    total_water_volume_allocated_l?: number;
    total_water_volume_unmet_l?: number;
    overall_fulfillment_ratio?: number;
    mean_system_mae?: number;
    zones?: Record<string, any>;
    [key: string]: any;
  };
  started_at: string;
  completed_at?: string;
  created_at: string;
}

export interface TimeseriesRecord {
  step: number;
  timestamp: string;
  zone_id: number;
  soil_moisture: number;
  target_moisture: number;
  moisture_error: number;
  rsm: number;
  soil_stress: number;
  weather_stress: number;
  water_demand: number;
  irrigation_command: number;
  raw_request_mm: number;
  allocated_irrigation_mm: number;
  unmet_demand_mm: number;
  water_volume_requested_l: number;
  water_volume_allocated_l: number;
  water_volume_unmet_l: number;
  et0_mm: number;
  etc_mm: number;
  rainfall_mm: number;
  effective_rainfall_mm: number;
  water_balance_residual: number;
}

export interface TimeseriesResponse {
  simulation_id: string;
  total_records: number;
  zone_count: number;
  timesteps: number;
  records: TimeseriesRecord[];
}

export interface ControllerOverview {
  id?: string;
  name: string;
  title?: string;
  display_name?: string;
  description: string;
  inputs?: any;
  output?: any;
  outputs?: any;
  rule_count?: number;
}

export interface FuzzyVariableSchema {
  name: string;
  universe_min: number;
  universe_max: number;
  unit: string;
  is_output: boolean;
  terms: Array<{
    term: string;
    mf_type: string;
    params: number[];
    points: Array<{ x: number; y: number }>;
  }>;
}

export interface FuzzyRuleSchema {
  rule_index: number;
  antecedent: string;
  consequent: string;
  weight: number;
}

export interface FuzzyEvaluateResponse {
  controller: string;
  inputs: Record<string, number>;
  output_value: number;
  linguistic_summary: string;
  fired_rules: Array<{
    rule_index: number;
    antecedent: string;
    consequent: string;
    firing_strength: number;
  }>;
}

export interface ZoneAllocationDetail {
  zone_id: number;
  area_m2: number;
  requested_depth_mm: number;
  requested_volume_l: number;
  raw_allocation_factor_pct: number;
  allocated_depth_mm: number;
  allocated_volume_l: number;
  unmet_depth_mm: number;
  unmet_volume_l: number;
  fulfillment_ratio: number;
}

export interface AllocationEvaluateResponse {
  available_water_pct: number;
  available_supply_l: number;
  total_requested_l: number;
  total_allocated_l: number;
  total_unmet_l: number;
  system_fulfillment_ratio: number;
  is_supply_constrained: boolean;
  zones: ZoneAllocationDetail[];
}

export interface ParameterComparisonItem {
  name: string;
  target_var: string;
  linguistic_set: string;
  point_index: number;
  min_bound: number;
  max_bound: number;
  baseline_value: number;
  optimized_value: number;
  delta: number;
}

export interface ConvergencePoint {
  iteration: number;
  best_fitness: number;
  mean_fitness: number;
  global_best_fitness: number;
  elapsed_seconds: number;
}

export interface OptimizationSummaryResponse {
  id: string;
  user_id: string;
  status: string;
  seed: number;
  swarm_size: number;
  max_iterations: number;
  baseline_fitness: number;
  optimized_fitness: number;
  fitness_improvement_pct: number;
  convergence: ConvergencePoint[];
  parameters: ParameterComparisonItem[];
  created_at: string;
  completed_at?: string;
}

export interface AIChatResponse {
  response: string;
  conversation_id: string;
  grounded_context_summary?: Record<string, any>;
  source: string;
}

export interface ReportResponse {
  id: string;
  simulation_id?: string;
  title: string;
  filename: string;
  download_url: string;
  metadata: Record<string, any>;
  created_at: string;
}

// --- Fetch Utility ---

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
      ...options,
    });
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`API Error ${res.status}: ${errorText}`);
    }
    return await res.json();
  } catch (err: any) {
    if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
      const friendlyErr = new Error(
        `FastAPI backend is offline at ${API_BASE}. Ensure the backend server is running via 'python -m uvicorn backend.app.main:app --port 8000'.`
      );
      console.warn(`Connection to backend failed:`, friendlyErr.message);
      throw friendlyErr;
    }
    console.error(`Failed to fetch ${url}:`, err);
    throw err;
  }
}

// --- API Service Methods ---

export const api = {
  // Health
  getHealth: () => fetchApi<{ status: string; version: string; subsystems: any }>('/health'),

  // Zones & Config
  getZones: () => fetchApi<ZoneConfig[]>('/zones'),
  getZoneStatus: () => fetchApi<ZoneStatus[]>('/zones/status'),
  updateZone: (id: number, data: Partial<ZoneConfig>) =>
    fetchApi<ZoneConfig>(`/zones/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  getCrops: () => fetchApi<any[]>('/crops'),
  getSoils: () => fetchApi<any[]>('/soils'),
  getScenarios: () => fetchApi<any[]>('/scenarios'),

  // Simulations
  runSimulation: (params: SimulationRunRequest = {}) =>
    fetchApi<SimulationSummaryResponse>('/simulations/run', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  listSimulations: (limit: number = 20) =>
    fetchApi<SimulationSummaryResponse[]>(`/simulations?limit=${limit}`),
  getSimulation: (simId: string) =>
    fetchApi<SimulationSummaryResponse>(`/simulations/${simId}`),
  getSimulationTimeseries: (simId: string, zoneId?: number, stride: number = 1) => {
    let q = `/simulations/${simId}/timeseries?stride=${stride}`;
    if (zoneId !== undefined && zoneId !== null) q += `&zone_id=${zoneId}`;
    return fetchApi<TimeseriesResponse>(q);
  },
  runSingleScenario: (scenarioName: string) =>
    fetchApi<SimulationSummaryResponse>(`/simulations/scenario?scenario_name=${encodeURIComponent(scenarioName)}`, {
      method: 'POST',
    }),
  runAllScenarios: () =>
    fetchApi<{ status: string; scenarios_evaluated: number; results: Record<string, any> }>('/simulations/all-scenarios', {
      method: 'POST',
    }),

  // Fuzzy Inference Subsystems
  getFuzzyOverview: () => fetchApi<ControllerOverview[]>('/fuzzy/overview'),
  getFuzzyVariables: (controller: string) =>
    fetchApi<FuzzyVariableSchema[]>(`/fuzzy/${controller}/variables`),
  getFuzzyRules: (controller: string) =>
    fetchApi<FuzzyRuleSchema[]>(`/fuzzy/${controller}/rules`),
  evaluateFuzzy: (targetController: string, inputs: Record<string, number>) =>
    fetchApi<FuzzyEvaluateResponse>('/fuzzy/evaluate', {
      method: 'POST',
      body: JSON.stringify({ target_controller: targetController, inputs }),
    }),

  // Supervisory Water Allocation
  getAllocationConfig: () => fetchApi<any>('/allocation/config'),
  evaluateAllocation: (params: {
    available_water_pct: number;
    available_supply_l?: number;
    requests_mm: Record<number, number>;
    stresses_pct?: Record<number, number>;
    priorities_pct?: Record<number, number>;
  }) =>
    fetchApi<AllocationEvaluateResponse>('/allocation/evaluate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  sweepAllocation: (requests_mm: Record<number, number>, priorities_pct?: Record<number, number>) =>
    fetchApi<{ sweep_points: any[] }>('/allocation/sweep', {
      method: 'POST',
      body: JSON.stringify({ requests_mm, priorities_pct }),
    }),
  getAllocationResults: (simulationId: string) =>
    fetchApi<any>(`/allocation/results/${simulationId}`),

  // PSO Optimization
  getOptimizationSummary: () => fetchApi<OptimizationSummaryResponse>('/optimization/summary'),
  getOptimizationParameters: () => fetchApi<ParameterComparisonItem[]>('/optimization/parameters'),
  runOptimization: (params: { swarm_size?: number; max_iterations?: number; seed?: number } = {}) =>
    fetchApi<OptimizationSummaryResponse>('/optimization/run', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Advisory AI & RAG
  chatAI: (params: { prompt: string; simulation_id?: string; zone_id?: number; conversation_id?: string }) =>
    fetchApi<AIChatResponse>('/ai/chat', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  explainTelemetry: (params: { simulation_id: string; zone_id?: number }) =>
    fetchApi<any>('/ai/explain', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  // Reports & Export
  generateReport: (simulationId: string, includeAi: boolean = true, optimizationId?: string) =>
    fetchApi<ReportResponse>('/reports/generate', {
      method: 'POST',
      body: JSON.stringify({
        simulation_id: simulationId,
        include_ai_summary: includeAi,
        optimization_id: optimizationId,
      }),
    }),
  getReportDownloadUrl: (reportId: string) => `${API_BASE}/reports/download/${reportId}`,
  getSimulationCsvUrl: (simulationId: string) => `${API_BASE}/reports/csv/${simulationId}`,
};
