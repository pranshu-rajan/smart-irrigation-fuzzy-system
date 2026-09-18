'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, SimulationSummaryResponse, ReportResponse, API_BASE } from '@/lib/api';

function ReportsContent() {
  const searchParams = useSearchParams();
  const initialSimId = searchParams.get('sim_id');


  const [simulations, setSimulations] = useState<SimulationSummaryResponse[]>([]);
  const [selectedSimId, setSelectedSimId] = useState<string>(initialSimId || '');
  const [includeAi, setIncludeAi] = useState<boolean>(true);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedReport, setGeneratedReport] = useState<ReportResponse | null>(null);

  useEffect(() => {
    const fetchSims = async () => {
      try {
        const list = await api.listSimulations(10);
        setSimulations(list);
        if (!selectedSimId && list.length > 0) {
          setSelectedSimId(list[0].id);
        }
      } catch (err) {
        console.error('Failed to load simulations for reporting:', err);
      }
    };
    fetchSims();
  }, []);

  const handleGenerateReport = async () => {
    if (!selectedSimId) {
      alert('Please select a simulation run first.');
      return;
    }
    setIsGenerating(true);
    try {
      const res = await api.generateReport(selectedSimId, includeAi);
      setGeneratedReport(res);
      alert('PDF Audit Report compiled and verified successfully!');
    } catch (err: any) {
      alert(`Report generation error: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const selectedRun = simulations.find((s) => s.id === selectedSimId);

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Engineering Audit PDF Reports & Telemetry Export
        </h1>
        <p className="mt-1 text-sm text-slate-400">
          Automated publication-grade PDF report synthesis via ReportLab and high-frequency CSV telemetry dispatch.
        </p>
      </div>

      {/* Generator & Exporter Controls */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* PDF Generator Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span>📄</span> PDF Report Generator
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 block mb-1">Target Simulation Run</label>
              <select
                value={selectedSimId}
                onChange={(e) => setSelectedSimId(e.target.value)}
                className="w-full rounded border border-slate-700 bg-slate-800 px-3 py-2 text-white font-mono"
              >
                {simulations.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.scenario} — {s.duration_hours}h ({s.id.substring(0, 8)}...)
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-slate-300 cursor-pointer pt-2">
              <input
                type="checkbox"
                checked={includeAi}
                onChange={(e) => setIncludeAi(e.target.checked)}
                className="rounded border-slate-700 accent-emerald-500"
              />
              <span>Include Advisory AI Technical Commentary & Interpretation</span>
            </label>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={isGenerating || !selectedSimId}
            className="w-full rounded-lg bg-emerald-500 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 transition-colors"
          >
            {isGenerating ? 'Synthesizing PDF Report with ReportLab...' : '⚡ Generate Engineering Audit PDF'}
          </button>

          {generatedReport && (
            <div className="mt-4 rounded-lg bg-emerald-950/40 border border-emerald-500/30 p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between text-emerald-400 font-semibold">
                <span>✅ Report Ready: {generatedReport.filename}</span>
                <span className="font-mono text-[11px]">{generatedReport.created_at.substring(0, 10)}</span>
              </div>
              <p className="text-slate-300 text-[11px]">{generatedReport.title}</p>
              <a
                href={`${API_BASE}/reports/download/${generatedReport.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-500 px-4 py-2 rounded transition-colors"
              >
                ⬇️ Download Official PDF Report
              </a>
            </div>
          )}
        </div>

        {/* CSV Exporter Card */}
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
            <span>📊</span> Raw Telemetry CSV Dispatch
          </h2>

          <p className="text-xs text-slate-400 leading-relaxed">
            Download full uncompressed 1-minute timestep telemetry (1,440 timesteps per zone) containing soil moisture, FAO-56 ET0, crop ETc, fuzzy stress indices, raw request depth, allocated depth, and water balance residual.
          </p>

          {selectedRun ? (
            <div className="rounded-lg bg-slate-950 p-4 border border-slate-800 space-y-2 text-xs font-mono">
              <div className="flex justify-between text-slate-300">
                <span>Scenario:</span>
                <span className="text-white font-bold">{selectedRun.scenario}</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Duration:</span>
                <span className="text-white">{selectedRun.duration_hours}h (1440 timesteps)</span>
              </div>
              <div className="flex justify-between text-slate-300">
                <span>Total Water Dispatched:</span>
                <span className="text-emerald-400">
                  {selectedRun.summary_metrics?.total_water_volume_allocated_l?.toFixed(1) || 0} L
                </span>
              </div>

              <div className="pt-3">
                <a
                  href={`${API_BASE}/reports/csv/${selectedRun.id}`}
                  download
                  className="w-full inline-flex items-center justify-center gap-1 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 py-2 text-xs font-semibold text-white transition-colors"
                >
                  📥 Export 1440-Step Telemetry CSV
                </a>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-500">Select a simulation to export CSV.</div>
          )}
        </div>
      </div>

      {/* PDF Document Structure Blueprint */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6 space-y-4">
        <h2 className="text-lg font-bold text-white">Official Audit Report Sections Blueprint</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1">
            <span className="font-semibold text-white">Section 1: Executive Summary</span>
            <p className="text-slate-400 text-[11px]">Overview of scenario boundary conditions, total water requested vs allocated, and aggregate MAE.</p>
          </div>
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1">
            <span className="font-semibold text-white">Section 2: FAO-56 & Soil Dynamics</span>
            <p className="text-slate-400 text-[11px]">Penman-Monteith ET0, crop coefficient Kc, and dynamic root-zone water balance audit.</p>
          </div>
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1">
            <span className="font-semibold text-white">Section 3: Fuzzy Inference Performance</span>
            <p className="text-slate-400 text-[11px]">Evaluation of 5 Mamdani FIS subsystems, rule firing frequencies, and tracking metrics.</p>
          </div>
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1">
            <span className="font-semibold text-white">Section 4: Allocation & Invariants</span>
            <p className="text-slate-400 text-[11px]">Verification of the 5 mathematical invariants: supply cap, demand ceiling, and zero leakage.</p>
          </div>
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1">
            <span className="font-semibold text-white">Section 5: Offline PSO Calibration</span>
            <p className="text-slate-400 text-[11px]">18-parameter shift delta, cost convergence trajectory, and multi-objective score.</p>
          </div>
          <div className="rounded-lg bg-slate-950 p-3 border border-slate-800 space-y-1">
            <span className="font-semibold text-white">Section 6: Advisory AI Assessment</span>
            <p className="text-slate-400 text-[11px]">Technical agronomic insights and recommendation commentary synthesized by Groq LLM.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ReportsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-xs text-slate-400 font-mono">Loading Reports & Telemetry center...</div>}>
      <ReportsContent />
    </Suspense>
  );
}

