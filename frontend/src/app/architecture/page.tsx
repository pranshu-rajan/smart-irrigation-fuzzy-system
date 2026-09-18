import React from 'react';

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
          <span className="text-xs text-slate-500 font-medium">Phases 0–14 Verified</span>
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
          <span>🏛️</span> Hierarchical Control Topology
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
            <h3 className="text-sm font-bold text-slate-900 font-sans">4 Zone Mamdani FIS</h3>
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

      {/* Mathematical Invariant Proofs */}
      <div className="rounded-2xl border border-slate-200/90 bg-white p-8 shadow-xs space-y-6">
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <span>⚖️</span> The 5 Supervisory Water Allocation Invariants
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
