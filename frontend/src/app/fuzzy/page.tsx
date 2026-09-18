'use client';

import React, { useState, useEffect } from 'react';
import { api, ControllerOverview, FuzzyVariableSchema, FuzzyRuleSchema, FuzzyEvaluateResponse } from '@/lib/api';

export default function FuzzyExplorerPage() {
  const [controllers, setControllers] = useState<ControllerOverview[]>([]);
  const [selectedController, setSelectedController] = useState<string>('soil_stress');
  const [variables, setVariables] = useState<FuzzyVariableSchema[]>([]);
  const [rules, setRules] = useState<FuzzyRuleSchema[]>([]);
  const [ruleSearch, setRuleSearch] = useState('');
  
  // Sandbox inputs and evaluation state
  const [inputValues, setInputValues] = useState<Record<string, number>>({});
  const [evalResult, setEvalResult] = useState<FuzzyEvaluateResponse | null>(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [loading, setLoading] = useState(true);

  // Load controllers overview
  useEffect(() => {
    const fetchControllers = async () => {
      try {
        const list = await api.getFuzzyOverview();
        setControllers(list);
        if (list.length > 0) {
          setSelectedController(list[0].name);
        }
      } catch (err) {
        console.error('Failed to load controllers:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchControllers();
  }, []);

  // Load controller variables, rules, and default inputs
  useEffect(() => {
    if (!selectedController) return;

    const loadControllerDetails = async () => {
      try {
        const [varsData, rulesData] = await Promise.all([
          api.getFuzzyVariables(selectedController),
          api.getFuzzyRules(selectedController),
        ]);
        setVariables(varsData);
        setRules(rulesData);

        // Initialize default sandbox inputs to mid-range
        const defaults: Record<string, number> = {};
        varsData.filter((v) => !v.is_output).forEach((v) => {
          defaults[v.name] = Number(((v.universe_min + v.universe_max) / 2).toFixed(2));
        });
        setInputValues(defaults);
        setEvalResult(null);
      } catch (err) {
        console.error('Failed to load controller details:', err);
      }
    };
    loadControllerDetails();
  }, [selectedController]);

  // Handle live evaluation
  const handleEvaluate = async () => {
    setIsEvaluating(true);
    try {
      const res = await api.evaluateFuzzy(selectedController, inputValues);
      setEvalResult(res);
    } catch (err: any) {
      alert(`Inference evaluation error: ${err.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const activeCtrl = controllers.find((c) => c.name === selectedController);
  const filteredRules = rules.filter(
    (r) =>
      r.antecedent.toLowerCase().includes(ruleSearch.toLowerCase()) ||
      r.consequent.toLowerCase().includes(ruleSearch.toLowerCase())
  );

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Fuzzy Control Diagnostics Center</h1>
        <p className="mt-1 text-sm text-slate-400">
          Inspect membership functions, linguistic rule matrices, and real-time defuzzification across all 5 Mamdani FIS subsystems.
        </p>
      </div>

      {/* Subsystems Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-3">
        {controllers.map((ctrl) => {
          const isActive = selectedController === ctrl.name;
          return (
            <button
              key={ctrl.name}
              onClick={() => setSelectedController(ctrl.name)}
              className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-emerald-500 text-slate-950 shadow-md shadow-emerald-500/20'
                  : 'border border-slate-800 bg-slate-900/60 text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              {ctrl.display_name}
              <span className={`ml-2 rounded-full px-1.5 py-0.2 text-[10px] ${
                isActive ? 'bg-slate-950 text-emerald-400' : 'bg-slate-800 text-slate-400'
              }`}>
                {ctrl.rule_count} rules
              </span>
            </button>
          );
        })}
      </div>

      {activeCtrl && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-300 flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="font-bold text-white uppercase tracking-wider">{activeCtrl.display_name}</span>
            <p className="text-slate-400 text-xs mt-0.5">{activeCtrl.description}</p>
          </div>
          <div className="flex gap-4 font-mono text-[11px] text-slate-400">
            <span>Inputs: <strong className="text-white">{activeCtrl.inputs.length}</strong></span>
            <span>Outputs: <strong className="text-white">{activeCtrl.outputs.length}</strong></span>
            <span>Rules: <strong className="text-white">{activeCtrl.rule_count}</strong></span>
            <span>Defuzzifier: <strong className="text-emerald-400">Centroid (CoA)</strong></span>
          </div>
        </div>
      )}

      {/* Membership Functions Visualizer */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center gap-2">
          <span>📈</span> Membership Function Curves (MF Universe)
        </h2>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {variables.map((v) => (
            <div
              key={v.name}
              className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-white">
                  {v.name} {v.unit ? `(${v.unit})` : ''}
                </span>
                <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                  v.is_output
                    ? 'bg-purple-950 text-purple-400 border border-purple-500/30'
                    : 'bg-blue-950 text-blue-400 border border-blue-500/30'
                }`}>
                  {v.is_output ? 'CONSEQUENT OUTPUT' : 'ANTECEDENT INPUT'}
                </span>
              </div>

              {/* SVG Curve Plot */}
              <div className="h-44 w-full rounded-lg bg-slate-950/80 border border-slate-800 p-2 relative flex items-center justify-center">
                <svg className="w-full h-full" viewBox="0 0 400 140" preserveAspectRatio="none">
                  {/* Grid Lines */}
                  <line x1="20" y1="20" x2="380" y2="20" stroke="#334155" strokeDasharray="3 3" strokeWidth="0.5" />
                  <line x1="20" y1="70" x2="380" y2="70" stroke="#334155" strokeDasharray="3 3" strokeWidth="0.5" />
                  <line x1="20" y1="120" x2="380" y2="120" stroke="#475569" strokeWidth="1" />

                  {/* MF Curves */}
                  {v.terms.map((term, tIdx) => {
                    const colors = ['#10b981', '#06b6d4', '#f59e0b', '#ec4899', '#8b5cf6'];
                    const strokeColor = colors[tIdx % colors.length];

                    const pathPoints = term.points.map((pt) => {
                      const xNorm = 20 + ((pt.x - v.universe_min) / (v.universe_max - v.universe_min || 1)) * 360;
                      const yNorm = 120 - pt.y * 100;
                      return `${xNorm},${yNorm}`;
                    });

                    return (
                      <g key={term.term}>
                        <polyline
                          points={pathPoints.join(' ')}
                          fill="none"
                          stroke={strokeColor}
                          strokeWidth="2"
                        />
                      </g>
                    );
                  })}
                </svg>

                {/* Y Axis Labels */}
                <div className="absolute left-1 top-2 text-[9px] font-mono text-slate-500">1.0 μ</div>
                <div className="absolute left-1 bottom-4 text-[9px] font-mono text-slate-500">0.0 μ</div>
              </div>

              {/* Terms Legend */}
              <div className="flex flex-wrap items-center gap-3 text-xs">
                {v.terms.map((term, tIdx) => {
                  const colors = ['bg-emerald-500', 'bg-cyan-500', 'bg-amber-500', 'bg-pink-500', 'bg-purple-500'];
                  return (
                    <div key={term.term} className="flex items-center gap-1.5 font-mono text-[11px] text-slate-300">
                      <span className={`h-2.5 w-2.5 rounded-full ${colors[tIdx % colors.length]}`} />
                      <span>{term.term}</span>
                      <span className="text-slate-500">[{term.params.join(', ')}]</span>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Sandbox & Defuzzifier */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🧪</span> Live Defuzzification Sandbox
          </h2>
          <span className="text-xs text-slate-400 font-mono">Real-time Mamdani CoA Engine</span>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Sliders for Inputs */}
          <div className="lg:col-span-2 space-y-4">
            {variables.filter((v) => !v.is_output).map((v) => {
              const currentVal = inputValues[v.name] ?? v.universe_min;
              const stepVal = (v.universe_max - v.universe_min) / 100;

              return (
                <div key={v.name} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-300">{v.name} {v.unit ? `(${v.unit})` : ''}</span>
                    <span className="font-mono text-emerald-400 font-bold">{currentVal}</span>
                  </div>
                  <input
                    type="range"
                    min={v.universe_min}
                    max={v.universe_max}
                    step={stepVal}
                    value={currentVal}
                    onChange={(e) =>
                      setInputValues({ ...inputValues, [v.name]: parseFloat(e.target.value) })
                    }
                    className="w-full accent-emerald-500 bg-slate-800 h-2 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-500 font-mono">
                    <span>{v.universe_min}</span>
                    <span>{v.universe_max}</span>
                  </div>
                </div>
              );
            })}

            <button
              onClick={handleEvaluate}
              disabled={isEvaluating}
              className="mt-4 w-full rounded-lg bg-emerald-500 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 transition-colors"
            >
              {isEvaluating ? 'Evaluating Defuzzification...' : '⚡ Compute Fuzzy Inference Step'}
            </button>
          </div>

          {/* Defuzzification Output Box */}
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-5 flex flex-col justify-between">
            <div>
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block">
                Defuzzified Output
              </span>
              <div className="mt-2 text-3xl font-mono font-extrabold text-white">
                {evalResult ? evalResult.output_value.toFixed(3) : '—'}
              </div>
              <div className="mt-2 text-xs font-semibold text-emerald-400">
                {evalResult?.linguistic_summary || 'Adjust sliders and click Compute'}
              </div>
            </div>

            {evalResult && evalResult.fired_rules && (
              <div className="mt-4 pt-4 border-t border-slate-800 space-y-2">
                <span className="text-[11px] font-semibold text-slate-400 block">
                  Active Rules ({evalResult.fired_rules.length} fired):
                </span>
                <div className="max-h-36 overflow-y-auto space-y-1 font-mono text-[10px] text-slate-300">
                  {evalResult.fired_rules.map((fr) => (
                    <div key={fr.rule_index} className="rounded bg-slate-900 p-1.5 flex justify-between">
                      <span className="truncate max-w-[180px]">R{fr.rule_index + 1}: {fr.consequent}</span>
                      <span className="text-cyan-400 font-bold">μ={fr.firing_strength.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Rule Base Table */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <span>📜</span> Linguistic Rule Base Matrix ({rules.length} Rules)
            </h2>
            <p className="text-xs text-slate-400">Mamdani inference rules governing controller decisions.</p>
          </div>

          <input
            type="text"
            placeholder="Search rules (e.g. LOW, HIGH, AND)..."
            value={ruleSearch}
            onChange={(e) => setRuleSearch(e.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 sm:w-64"
          />
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40">
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="sticky top-0 border-b border-slate-800 bg-slate-900 text-[11px] uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="px-4 py-3 w-16">#</th>
                  <th className="px-4 py-3">Antecedent (IF Conditions)</th>
                  <th className="px-4 py-3">Consequent (THEN Action)</th>
                  <th className="px-4 py-3 w-20 text-right">Weight</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {filteredRules.map((r) => (
                  <tr key={r.rule_index} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-2.5 font-bold text-slate-400">{r.rule_index + 1}</td>
                    <td className="px-4 py-2.5 text-slate-200">{r.antecedent}</td>
                    <td className="px-4 py-2.5 text-emerald-400 font-semibold">{r.consequent}</td>
                    <td className="px-4 py-2.5 text-right text-slate-400">{r.weight.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
