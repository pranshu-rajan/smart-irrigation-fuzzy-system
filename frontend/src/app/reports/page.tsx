'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, SimulationSummaryResponse, ReportResponse, API_BASE } from '@/lib/api';
import { FileText, Zap, CheckCircle2, Download, BarChart3 } from 'lucide-react';

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
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200/80">
            Publication Engine
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-500 font-medium">ReportLab PDF Synthesis & 1-Min CSV Export</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Engineering Audit PDF Reports & Telemetry Export
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Automated publication-grade PDF report synthesis via ReportLab and high-frequency CSV telemetry dispatch.
        </p>
      </div>

      {/* Generator & Exporter Controls */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* PDF Generator Card */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-2">
            <FileText className="h-4 w-4 text-emerald-600" />
            <span>PDF Report Generator</span>
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Target Simulation Run</label>
              <select
                value={selectedSimId}
                onChange={(e) => setSelectedSimId(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                {simulations.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.scenario} — {s.duration_hours}h ({s.id.substring(0, 8)}...)
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-slate-700 cursor-pointer pt-2 font-medium">
              <input
                type="checkbox"
                checked={includeAi}
                onChange={(e) => setIncludeAi(e.target.checked)}
                className="rounded border-slate-300 accent-emerald-600 h-4 w-4"
              />
              <span>Include Advisory AI Technical Commentary & Interpretation</span>
            </label>
          </div>

          <button
            onClick={handleGenerateReport}
            disabled={isGenerating || !selectedSimId}
            className="w-full rounded-xl bg-emerald-600 py-3 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-600/15 cursor-pointer flex items-center justify-center gap-1.5"
          >
            {isGenerating ? (
              'Synthesizing PDF Report with ReportLab...'
            ) : (
              <>
                <Zap className="h-3.5 w-3.5" />
                <span>Generate Engineering Audit PDF</span>
              </>
            )}
          </button>

          {generatedReport && (
            <div className="mt-4 rounded-xl bg-emerald-50/80 border border-emerald-200 p-4 space-y-2 text-xs shadow-2xs">
              <div className="flex items-center justify-between text-emerald-900 font-bold">
                <span className="inline-flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  <span>Report Ready: {generatedReport.filename}</span>
                </span>
                <span className="font-mono text-[11px] text-emerald-700">{generatedReport.created_at.substring(0, 10)}</span>
              </div>
              <p className="text-slate-600 text-[11px]">{generatedReport.title}</p>
              <a
                href={`${API_BASE}/reports/download/${generatedReport.id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 px-4 py-2 rounded-lg transition-colors shadow-xs"
              >
                <Download className="h-3.5 w-3.5" />
                <span>Download Official PDF Report</span>
              </a>
            </div>
          )}
        </div>

        {/* CSV Exporter Card */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-emerald-600" />
            <span>Raw Telemetry CSV Dispatch</span>
          </h2>

          <p className="text-xs text-slate-600 leading-relaxed">
            Download full uncompressed 1-minute timestep telemetry (1,440 timesteps per zone) containing soil moisture, FAO-56 ET0, crop ETc, fuzzy stress indices, raw request depth, allocated depth, and water balance residual.
          </p>

          {selectedRun ? (
            <div className="rounded-xl bg-slate-50/80 p-4 border border-slate-200 space-y-2 text-xs font-mono">
              <div className="flex justify-between text-slate-700">
                <span>Scenario:</span>
                <span className="text-slate-900 font-bold">{selectedRun.scenario}</span>
              </div>
              <div className="flex justify-between text-slate-700">
                <span>Duration:</span>
                <span className="text-slate-900 font-semibold">{selectedRun.duration_hours}h (1440 timesteps)</span>
              </div>
              <div className="flex justify-between text-slate-700">
                <span>Total Water Dispatched:</span>
                <span className="text-emerald-700 font-bold">
                  {selectedRun.summary_metrics?.total_water_volume_allocated_l?.toFixed(1) || 0} L
                </span>
              </div>

              <div className="pt-3">
                <a
                  href={`${API_BASE}/reports/csv/${selectedRun.id}`}
                  download
                  className="w-full inline-flex items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 hover:border-emerald-300 py-2.5 text-xs font-semibold text-slate-800 transition-colors shadow-2xs"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Export 1440-Step Telemetry CSV</span>
                </a>
              </div>
            </div>
          ) : (
            <div className="text-xs text-slate-400 font-medium">Select a simulation to export CSV.</div>
          )}
        </div>
      </div>

      {/* PDF Document Structure Blueprint */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-6 shadow-xs space-y-4">
        <h2 className="text-lg font-bold text-slate-900">Official Audit Report Sections Blueprint</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-700">
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 space-y-1">
            <span className="font-bold text-slate-900 block">Section 1: Executive Summary</span>
            <p className="text-slate-600 text-[11px]">Overview of scenario boundary conditions, total water requested vs allocated, and aggregate MAE.</p>
          </div>
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 space-y-1">
            <span className="font-bold text-slate-900 block">Section 2: FAO-56 & Soil Dynamics</span>
            <p className="text-slate-600 text-[11px]">Penman-Monteith ET0, crop coefficient Kc, and dynamic root-zone water balance audit.</p>
          </div>
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 space-y-1">
            <span className="font-bold text-slate-900 block">Section 3: Fuzzy Inference Performance</span>
            <p className="text-slate-600 text-[11px]">Evaluation of 5 Mamdani FIS subsystems, rule firing frequencies, and tracking metrics.</p>
          </div>
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 space-y-1">
            <span className="font-bold text-slate-900 block">Section 4: Allocation & Invariants</span>
            <p className="text-slate-600 text-[11px]">Verification of the 5 mathematical invariants: supply cap, demand ceiling, and zero leakage.</p>
          </div>
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 space-y-1">
            <span className="font-bold text-slate-900 block">Section 5: Offline PSO Calibration</span>
            <p className="text-slate-600 text-[11px]">18-parameter shift delta, cost convergence trajectory, and multi-objective score.</p>
          </div>
          <div className="rounded-xl bg-slate-50/70 p-4 border border-slate-200/80 space-y-1">
            <span className="font-bold text-slate-900 block">Section 6: Advisory AI Assessment</span>
            <p className="text-slate-600 text-[11px]">Technical agronomic insights and recommendation commentary synthesized by Groq LLM.</p>
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

