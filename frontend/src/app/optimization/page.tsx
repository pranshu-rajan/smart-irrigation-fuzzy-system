'use client';

import React, { useState, useEffect } from 'react';
import { api, OptimizationSummaryResponse, ParameterComparisonItem } from '@/lib/api';
import MetricCard from '@/components/MetricCard';
import LineChart from '@/components/LineChart';

export default function OptimizationPage() {
  const [summary, setSummary] = useState<OptimizationSummaryResponse | null>(null);
  const [parameters, setParameters] = useState<ParameterComparisonItem[]>([]);
  const [isOptimizing, setIsOptimizing] = useState<boolean>(false);
  const [swarmSize, setSwarmSize] = useState<number>(15);
  const [iterations, setIterations] = useState<number>(20);
  const [seed, setSeed] = useState<number>(42);
  const [loading, setLoading] = useState<boolean>(true);

  const loadOptimizationData = async () => {
    try {
      const [sumData, paramData] = await Promise.all([
        api.getOptimizationSummary(),
        api.getOptimizationParameters(),
      ]);
      setSummary(sumData);
      setParameters(paramData);
    } catch (err) {
      console.error('Failed loading optimization summary:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOptimizationData();
  }, []);

  const handleTriggerPSO = async () => {
    setIsOptimizing(true);
    try {
      const res = await api.runOptimization({
        swarm_size: swarmSize,
        max_iterations: iterations,
        seed: seed,
      });
      setSummary(res);
      const params = await api.getOptimizationParameters();
      setParameters(params);
      alert('Offline PSO parameter optimization completed successfully!');
    } catch (err: any) {
      alert(`PSO execution error: ${err.message}`);
    } finally {
      setIsOptimizing(false);
    }
  };

  const convergence = summary?.convergence || [];
  const baselineFit = summary?.baseline_fitness ?? 2.845;
  const optimizedFit = summary?.optimized_fitness ?? 2.423;
  const improvement = summary?.fitness_improvement_pct ?? ((baselineFit - optimizedFit) / baselineFit) * 100;

  return (
    <div className="space-y-8 pb-16">
      {/* Top Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">
              Offline PSO Parameter Tuning
            </h1>
            <span className="rounded-full bg-purple-950 px-2.5 py-0.5 text-xs font-semibold text-purple-400 border border-purple-500/30">
              OFFLINE DECOUPLED
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Particle Swarm Optimization calibrating 18 membership function vertices of MainIrrigationFIS. Strictly offline.
          </p>
        </div>

        <button
          onClick={handleTriggerPSO}
          disabled={isOptimizing}
          className="inline-flex items-center gap-2 rounded-lg bg-purple-600 px-5 py-2.5 text-xs font-bold text-white shadow-lg shadow-purple-600/20 hover:bg-purple-500 disabled:opacity-50 transition-colors"
        >
          {isOptimizing ? (
            <>
              <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
              </svg>
              Optimizing Swarm...
            </>
          ) : (
            '⚡ Run Offline PSO Calibration'
          )}
        </button>
      </div>

      {/* Strict Decoupling Advisory Box */}
      <div className="rounded-xl border border-purple-500/30 bg-purple-950/20 p-4 text-xs text-purple-200">
        <strong className="text-white block mb-1">🔒 Architectural Invariant Guarantee:</strong>
        PSO is strictly executed offline during tuning intervals. The tuned parameter vector is committed to MainIrrigationFIS; PSO never acts as an online real-time controller.
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <MetricCard
          title="Baseline Fitness"
          value={baselineFit.toFixed(4)}
          change="Canonical initial FIS"
          trend="neutral"
          color="amber"
        />
        <MetricCard
          title="Optimized Fitness"
          value={optimizedFit.toFixed(4)}
          change="Global best particle"
          trend="up"
          color="emerald"
        />
        <MetricCard
          title="Cost Improvement"
          value={`+${improvement.toFixed(2)}%`}
          change="Multi-objective score"
          trend="up"
          color="purple"
        />
        <MetricCard
          title="Tuned Parameters"
          value={`${parameters.length || 18} Vertices`}
          change="MainIrrigationFIS"
          trend="neutral"
          color="blue"
        />
      </div>

      {/* Hyperparameter Controls & Convergence Plot */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left: PSO Hyperparameters */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
            Swarm Configuration
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Swarm Population Size</label>
              <input
                type="number"
                min={5}
                max={50}
                value={swarmSize}
                onChange={(e) => setSwarmSize(Number(e.target.value))}
                className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Max Iterations</label>
              <input
                type="number"
                min={5}
                max={50}
                value={iterations}
                onChange={(e) => setIterations(Number(e.target.value))}
                className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
              />
            </div>

            <div>
              <label className="text-slate-400 block mb-1">Random Seed</label>
              <input
                type="number"
                value={seed}
                onChange={(e) => setSeed(Number(e.target.value))}
                className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
              />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
            <span className="font-semibold text-slate-300 block">Fitness Weights:</span>
            <div className="flex justify-between"><span>Tracking Error:</span><span className="font-mono text-white">50%</span></div>
            <div className="flex justify-between"><span>Water Volume:</span><span className="font-mono text-white">25%</span></div>
            <div className="flex justify-between"><span>Deficit Penalty:</span><span className="font-mono text-white">15%</span></div>
            <div className="flex justify-between"><span>Chatter/Smoothness:</span><span className="font-mono text-white">10%</span></div>
          </div>
        </div>

        {/* Right: Convergence Curve */}
        <div className="lg:col-span-2 rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300">
              Convergence History (Fitness vs Iterations)
            </h2>
            <span className="text-xs font-mono text-purple-400">
              Best Fitness: {optimizedFit.toFixed(4)}
            </span>
          </div>

          {convergence.length > 0 ? (
            <LineChart
              labels={convergence.map((c) => `Iter ${c.iteration}`)}
              datasets={[
                {
                  name: 'Global Best Fitness',
                  data: convergence.map((c) => c.global_best_fitness),
                  color: '#a855f7',
                },
                {
                  name: 'Mean Swarm Fitness',
                  data: convergence.map((c) => c.mean_fitness),
                  color: '#64748b',
                },
              ]}
              unit=""
              height={250}
            />
          ) : (
            <div className="h-64 flex items-center justify-center text-xs text-slate-500 font-mono">
              Convergence trajectory ready upon calibration.
            </div>
          )}
        </div>
      </div>

      {/* 18 Parameters Specification & Comparison Table */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white">
          18-Dimensional Parameter Space (Baseline vs PSO-Tuned)
        </h2>

        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="border-b border-slate-800 bg-slate-900 text-[11px] uppercase tracking-wider text-slate-400 font-mono">
              <tr>
                <th className="px-4 py-3">Parameter Name</th>
                <th className="px-4 py-3">Target Variable</th>
                <th className="px-4 py-3">Linguistic Term</th>
                <th className="px-4 py-3">Point</th>
                <th className="px-4 py-3">Bounds [Min, Max]</th>
                <th className="px-4 py-3">Baseline</th>
                <th className="px-4 py-3 text-emerald-400">Optimized</th>
                <th className="px-4 py-3 text-right">Delta (%)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {parameters.map((p, idx) => {
                const deltaPct = p.baseline_value !== 0 ? ((p.optimized_value - p.baseline_value) / p.baseline_value) * 100 : 0;
                return (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-2.5 font-bold text-white">{p.name}</td>
                    <td className="px-4 py-2.5 text-slate-400">{p.target_var}</td>
                    <td className="px-4 py-2.5 text-slate-300">{p.linguistic_set}</td>
                    <td className="px-4 py-2.5 text-purple-400">p{p.point_index}</td>
                    <td className="px-4 py-2.5 text-slate-500">[{p.min_bound}, {p.max_bound}]</td>
                    <td className="px-4 py-2.5 text-slate-300">{p.baseline_value.toFixed(3)}</td>
                    <td className="px-4 py-2.5 text-emerald-400 font-bold">{p.optimized_value.toFixed(3)}</td>
                    <td className={`px-4 py-2.5 text-right font-semibold ${deltaPct >= 0 ? 'text-cyan-400' : 'text-amber-400'}`}>
                      {deltaPct >= 0 ? `+${deltaPct.toFixed(1)}%` : `${deltaPct.toFixed(1)}%`}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
