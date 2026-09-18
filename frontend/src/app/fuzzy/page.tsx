'use client';

import React, { useState, useEffect } from 'react';
import { api, ControllerOverview, FuzzyVariableSchema, FuzzyRuleSchema, FuzzyEvaluateResponse } from '@/lib/api';
import { TrendingUp, FlaskConical, Zap, ScrollText } from 'lucide-react';

export default function FuzzyExplorerPage() {
  const [controllers, setControllers] = useState<any[]>([]);
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
        setControllers(list || []);
        if (list && list.length > 0) {
          setSelectedController(list[0].name || list[0].id || 'soil_stress');
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

        // Defensive normalization for variables
        const normalizedVars: FuzzyVariableSchema[] = (varsData || []).map((v: any) => {
          const universe_min = Number(v.universe_min ?? v.min ?? 0);
          const universe_max = Number(v.universe_max ?? v.max ?? 1);
          const is_output = Boolean(v.is_output ?? (v.fis_role === 'consequent' || v.fis_role === 'output'));

          let terms = v.terms;
          if (!terms && v.sets) {
            terms = Object.entries(v.sets).map(([termKey, termVal]: [string, any]) => {
              const pts = (v.curve_points && v.curve_points[termKey]) || [];
              const points = pts.map(([x, y]: [number, number]) => ({ x, y }));
              return {
                term: termVal.name || termKey,
                mf_type: termVal.type || 'triangular',
                params: termVal.parameters || [],
                points,
              };
            });
          }

          return {
            name: v.name || 'variable',
            universe_min,
            universe_max,
            unit: v.unit || '',
            is_output,
            terms: terms || [],
          };
        });

        // Defensive normalization for rules
        const normalizedRules: FuzzyRuleSchema[] = (rulesData || []).map((r: any, idx: number) => ({
          rule_index: r.rule_index ?? (r.id ? r.id - 1 : idx),
          antecedent: r.antecedent || r.conditions_text || r.description || 'IF conditions',
          consequent: r.consequent || '',
          weight: Number(r.weight ?? 1.0),
        }));

        setVariables(normalizedVars);
        setRules(normalizedRules);

        // Initialize default sandbox inputs to mid-range
        const defaults: Record<string, number> = {};
        normalizedVars.filter((v) => !v.is_output).forEach((v) => {
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
      const res: any = await api.evaluateFuzzy(selectedController, inputValues);
      const output_val = Number(res.crisp_output ?? res.output_value ?? 0);
      const fired_rules = (res.active_rules || res.fired_rules || []).map((ar: any, idx: number) => ({
        rule_index: ar.rule_id ? ar.rule_id - 1 : idx,
        antecedent: ar.conditions || ar.antecedent || '',
        consequent: ar.consequent || '',
        firing_strength: Number(ar.weight ?? ar.firing_strength ?? 1.0),
      }));

      setEvalResult({
        controller: res.controller_name || selectedController,
        inputs: res.inputs || inputValues,
        output_value: output_val,
        linguistic_summary: res.linguistic_summary || `Crisp Output: ${output_val.toFixed(2)} ${res.unit || ''}`,
        fired_rules,
      });
    } catch (err: any) {
      alert(`Inference evaluation error: ${err.message}`);
    } finally {
      setIsEvaluating(false);
    }
  };

  const activeCtrl = controllers.find((c) => (c.name || c.id) === selectedController);
  const filteredRules = rules.filter(
    (r) =>
      (r.antecedent || '').toLowerCase().includes(ruleSearch.toLowerCase()) ||
      (r.consequent || '').toLowerCase().includes(ruleSearch.toLowerCase())
  );

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200/80">
            Fuzzy Inference Engine
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-500 font-medium">5 Mamdani FIS Subsystems</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Fuzzy Control Diagnostics Center</h1>
        <p className="mt-1 text-sm text-slate-600">
          Inspect membership functions, linguistic rule matrices, and real-time defuzzification across all 5 Mamdani FIS subsystems.
        </p>
      </div>

      {/* Subsystems Navigation Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        {controllers.map((ctrl) => {
          const ctrlId = ctrl.name || ctrl.id;
          const isActive = selectedController === ctrlId;
          const title = ctrl.display_name || ctrl.title || ctrl.name;
          return (
            <button
              key={ctrlId}
              onClick={() => setSelectedController(ctrlId)}
              className={`rounded-xl px-4 py-2 text-xs font-semibold transition-all cursor-pointer ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'border border-slate-200 bg-white text-slate-700 hover:border-emerald-300 hover:bg-slate-50'
              }`}
            >
              {title}
              <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                isActive ? 'bg-emerald-800 text-emerald-100' : 'bg-slate-100 text-slate-600'
              }`}>
                {ctrl.rule_count || 25} rules
              </span>
            </button>
          );
        })}
      </div>

      {activeCtrl && (
        <div className="rounded-2xl border border-emerald-200/80 bg-emerald-50/40 p-4 text-xs text-slate-700 flex flex-wrap items-center justify-between gap-4 shadow-2xs">
          <div>
            <span className="font-bold text-emerald-950 uppercase tracking-wider">
              {activeCtrl.display_name || activeCtrl.title || activeCtrl.name}
            </span>
            <p className="text-slate-600 text-xs mt-0.5">{activeCtrl.description}</p>
          </div>
          <div className="flex flex-wrap gap-4 font-mono text-[11px] text-slate-600">
            <span>Inputs: <strong className="text-slate-900">{Array.isArray(activeCtrl.inputs) ? activeCtrl.inputs.length : 2}</strong></span>
            <span>Outputs: <strong className="text-slate-900">{Array.isArray(activeCtrl.outputs) ? activeCtrl.outputs.length : 1}</strong></span>
            <span>Rules: <strong className="text-slate-900">{activeCtrl.rule_count || rules.length}</strong></span>
            <span>Defuzzifier: <strong className="text-emerald-700 font-bold">Centroid (CoA)</strong></span>
          </div>
        </div>
      )}

      {/* Membership Functions Visualizer */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-emerald-600" />
          <span>Membership Function Curves (MF Universe)</span>
        </h2>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {variables.map((v) => (
            <div
              key={v.name}
              className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-2xs space-y-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-900">
                  {v.name} {v.unit ? `(${v.unit})` : ''}
                </span>
                <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${
                  v.is_output
                    ? 'bg-purple-50 text-purple-700 border border-purple-200'
                    : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                }`}>
                  {v.is_output ? 'CONSEQUENT OUTPUT' : 'ANTECEDENT INPUT'}
                </span>
              </div>

              {/* SVG Curve Plot */}
              <div className="h-44 w-full rounded-xl bg-slate-50/80 border border-slate-200 p-2 relative flex items-center justify-center">
                <svg className="w-full h-full" viewBox="0 0 400 140" preserveAspectRatio="none">
                  {/* Grid Lines */}
                  <line x1="20" y1="20" x2="380" y2="20" stroke="#e2e8f0" strokeDasharray="3 3" strokeWidth="0.75" />
                  <line x1="20" y1="70" x2="380" y2="70" stroke="#e2e8f0" strokeDasharray="3 3" strokeWidth="0.75" />
                  <line x1="20" y1="120" x2="380" y2="120" stroke="#cbd5e1" strokeWidth="1.25" />

                  {/* MF Curves */}
                  {(v.terms || []).map((term, tIdx) => {
                    const colors = ['#059669', '#0284c7', '#d97706', '#db2777', '#7c3aed'];
                    const strokeColor = colors[tIdx % colors.length];

                    const pathPoints = (term.points || []).map((pt) => {
                      const range = v.universe_max - v.universe_min || 1;
                      const xNorm = 20 + ((pt.x - v.universe_min) / range) * 360;
                      const yNorm = 120 - pt.y * 100;
                      return `${xNorm},${yNorm}`;
                    });

                    return (
                      <g key={term.term}>
                        <polyline
                          points={pathPoints.join(' ')}
                          fill="none"
                          stroke={strokeColor}
                          strokeWidth="2.25"
                        />
                      </g>
                    );
                  })}
                </svg>

                {/* Y Axis Labels */}
                <div className="absolute left-2 top-2 text-[9px] font-mono text-slate-500">1.0 μ</div>
                <div className="absolute left-2 bottom-4 text-[9px] font-mono text-slate-500">0.0 μ</div>
              </div>

              {/* Terms Legend */}
              <div className="flex flex-wrap items-center gap-3 text-xs pt-1">
                {(v.terms || []).map((term, tIdx) => {
                  const colors = ['bg-emerald-600', 'bg-sky-600', 'bg-amber-600', 'bg-pink-600', 'bg-purple-600'];
                  return (
                    <div key={term.term} className="flex items-center gap-1.5 font-mono text-[11px] text-slate-700">
                      <span className={`h-2.5 w-2.5 rounded-full ${colors[tIdx % colors.length]}`} />
                      <span className="font-sans font-semibold text-slate-800">{term.term}</span>
                      {term.params && term.params.length > 0 && (
                        <span className="text-slate-400 font-mono text-[10px]">[{term.params.join(', ')}]</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Interactive Sandbox & Defuzzifier */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <FlaskConical className="h-5 w-5 text-emerald-600" />
            <span>Live Defuzzification Sandbox</span>
          </h2>
          <span className="text-xs text-slate-500 font-mono bg-slate-100 px-2.5 py-1 rounded-md">Real-time Mamdani CoA Engine</span>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {/* Sliders for Inputs */}
          <div className="lg:col-span-2 space-y-4">
            {variables.filter((v) => !v.is_output).map((v) => {
              const currentVal = inputValues[v.name] ?? v.universe_min;
              const range = v.universe_max - v.universe_min || 1;
              const stepVal = range / 100;

              return (
                <div key={v.name} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-800">{v.name} {v.unit ? `(${v.unit})` : ''}</span>
                    <span className="font-mono text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/70">{currentVal}</span>
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
                    className="w-full accent-emerald-600 bg-slate-200 h-2 rounded-lg cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                    <span>min: {v.universe_min}</span>
                    <span>max: {v.universe_max}</span>
                  </div>
                </div>
              );
            })}

            <button
              onClick={handleEvaluate}
              disabled={isEvaluating}
              className="mt-4 w-full rounded-xl bg-emerald-600 py-3 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-600/15 cursor-pointer flex items-center justify-center gap-1.5"
            >
              {isEvaluating ? (
                'Evaluating Defuzzification...'
              ) : (
                <>
                  <Zap className="h-3.5 w-3.5" />
                  <span>Compute Fuzzy Inference Step</span>
                </>
              )}
            </button>
          </div>

          {/* Defuzzification Output Box */}
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50/40 p-5 flex flex-col justify-between shadow-2xs">
            <div>
              <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider block">
                Defuzzified Output
              </span>
              <div className="mt-2 text-3xl font-mono font-extrabold text-emerald-950">
                {evalResult && typeof evalResult.output_value === 'number' ? evalResult.output_value.toFixed(3) : '—'}
              </div>
              <div className="mt-2 text-xs font-semibold text-emerald-700">
                {evalResult?.linguistic_summary || 'Adjust sliders and click Compute'}
              </div>
            </div>

            {evalResult && evalResult.fired_rules && evalResult.fired_rules.length > 0 && (
              <div className="mt-4 pt-4 border-t border-emerald-200/80 space-y-2">
                <span className="text-[11px] font-bold text-slate-700 block">
                  Active Rules ({evalResult.fired_rules.length} fired):
                </span>
                <div className="max-h-36 overflow-y-auto space-y-1.5 font-mono text-[10px] text-slate-700">
                  {evalResult.fired_rules.map((fr) => (
                    <div key={fr.rule_index} className="rounded-lg bg-white border border-emerald-100 p-2 flex justify-between shadow-2xs">
                      <span className="truncate max-w-[180px] font-sans font-medium text-slate-800">
                        R{fr.rule_index + 1}: {fr.consequent}
                      </span>
                      <span className="text-emerald-700 font-bold">
                        μ={typeof fr.firing_strength === 'number' ? fr.firing_strength.toFixed(3) : '1.000'}
                      </span>
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
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <ScrollText className="h-5 w-5 text-emerald-600" />
              <span>Linguistic Rule Base Matrix ({rules.length} Rules)</span>
            </h2>
            <p className="text-xs text-slate-500">Mamdani inference rules governing controller decisions.</p>
          </div>

          <input
            type="text"
            placeholder="Search rules (e.g. LOW, HIGH, AND)..."
            value={ruleSearch}
            onChange={(e) => setRuleSearch(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-emerald-500 shadow-2xs sm:w-64"
          />
        </div>

        <div className="overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-xs">
          <div className="max-h-96 overflow-y-auto">
            <table className="w-full text-left text-xs text-slate-700">
              <thead className="sticky top-0 border-b border-slate-200 bg-slate-50 text-[11px] uppercase tracking-wider text-slate-600">
                <tr>
                  <th className="px-4 py-3 w-16">#</th>
                  <th className="px-4 py-3">Antecedent (IF Conditions)</th>
                  <th className="px-4 py-3">Consequent (THEN Action)</th>
                  <th className="px-4 py-3 w-20 text-right">Weight</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                {filteredRules.map((r) => (
                  <tr key={r.rule_index} className="hover:bg-emerald-50/40 transition-colors">
                    <td className="px-4 py-2.5 font-bold text-slate-400">{r.rule_index + 1}</td>
                    <td className="px-4 py-2.5 text-slate-700 font-sans">{r.antecedent}</td>
                    <td className="px-4 py-2.5 text-emerald-700 font-semibold font-sans">{r.consequent}</td>
                    <td className="px-4 py-2.5 text-right text-slate-500">
                      {typeof r.weight === 'number' ? r.weight.toFixed(1) : '1.0'}
                    </td>
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
