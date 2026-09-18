import Link from 'next/link';

export default function HomePage() {
  const stats = [
    { label: 'Fuzzy Inference Subsystems', value: '5 Engines', detail: 'Mamdani Min-Max Centroid' },
    { label: 'Closed-Loop Zones', value: '3 Active', detail: 'Dynamic feedback at 1-min dt' },
    { label: 'Allocation Invariants', value: '100% Verified', detail: 'Zero artificial water creation' },
    { label: 'Water Balance Closure', value: '0.00 mm', detail: 'Exact mass-balance residual' },
    { label: 'Environmental Scenarios', value: '6 Profiles', detail: 'Normal, Heatwave, Scarcity, etc.' },
    { label: 'Offline PSO Optimization', value: '18 Parameters', detail: 'Grounded FIS tuning' },
  ];

  const modules = [
    {
      title: 'Multizone Dashboard',
      description: 'Real-time telemetry, soil moisture profiles, depletion percentages, valve states, and supervisory alerts across all zones.',
      href: '/dashboard',
      tag: 'Monitoring',
      color: 'border-emerald-500/30 bg-emerald-950/10 text-emerald-400',
    },
    {
      title: 'Simulation Studio',
      description: 'Run 24-hour closed-loop multizone simulations under 6 environmental scenarios with 10 interactive time-series plots.',
      href: '/simulation',
      tag: 'Closed Loop',
      color: 'border-cyan-500/30 bg-cyan-950/10 text-cyan-400',
    },
    {
      title: 'Fuzzy Inference Diagnostics',
      description: 'Inspect membership functions, rule bases, and live defuzzification sandboxes for all 5 Mamdani FIS engines.',
      href: '/fuzzy',
      tag: '5 FIS Engines',
      color: 'border-amber-500/30 bg-amber-950/10 text-amber-400',
    },
    {
      title: 'Supervisory Water Allocation',
      description: 'Two-layer allocation engine combining Mamdani Scarcity FIS with deterministic bounded priority-weighted water-filling.',
      href: '/allocation',
      tag: 'Hierarchical',
      color: 'border-blue-500/30 bg-blue-950/10 text-blue-400',
    },
    {
      title: 'Offline PSO Parameter Tuning',
      description: 'Offline Particle Swarm Optimization tuning 18 membership function parameters of MainIrrigationFIS with convergence tracking.',
      href: '/optimization',
      tag: 'PSO Tuning',
      color: 'border-purple-500/30 bg-purple-950/10 text-purple-400',
    },
    {
      title: 'Scenario Comparison Matrix',
      description: 'Benchmark all 6 environmental scenarios side-by-side: ET0, ETc, stress indices, volume requested vs allocated, and MAE.',
      href: '/scenarios',
      tag: 'Benchmarking',
      color: 'border-rose-500/30 bg-rose-950/10 text-rose-400',
    },
    {
      title: 'Grounded AI Advisory',
      description: 'Technical assistant powered by Groq LLM grounded in real-time simulation telemetry. Strictly advisory and explanatory.',
      href: '/ai',
      tag: 'Advisory AI',
      color: 'border-indigo-500/30 bg-indigo-950/10 text-indigo-400',
    },
    {
      title: 'Audit PDF Reports & CSV',
      description: 'Generate publication-grade engineering PDF audit reports with ReportLab and export high-frequency CSV telemetry.',
      href: '/reports',
      tag: 'Reporting',
      color: 'border-teal-500/30 bg-teal-950/10 text-teal-400',
    },
  ];

  return (
    <div className="space-y-12 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900 via-slate-900/90 to-slate-950 p-8 md:p-12 shadow-2xl">
        <div className="absolute -right-24 -top-24 h-96 w-96 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />
        <div className="absolute -left-24 -bottom-24 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />

        <div className="relative z-10 max-w-4xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/30 px-3 py-1 text-xs font-semibold text-emerald-400 tracking-wide">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            ENGINEERING PLATFORM • PHASES 0–14 COMPLIANT
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-5xl lg:text-6xl font-sans">
            Smart Multizone Irrigation & Water Resource Management
          </h1>

          <p className="text-lg text-slate-300 sm:text-xl font-light leading-relaxed">
            Hierarchical Adaptive Fuzzy Control platform combining FAO-56 Penman-Monteith physics, dynamic soil-water balance, 5 Mamdani fuzzy inference systems, bounded priority-weighted shared water allocation, and offline PSO optimization.
          </p>

          <div className="flex flex-wrap gap-4 pt-4">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-lg bg-emerald-500 px-6 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/20 hover:bg-emerald-400 transition-colors"
            >
              Open Live Dashboard
            </Link>
            <Link
              href="/simulation"
              className="inline-flex items-center justify-center rounded-lg border border-slate-700 bg-slate-800/80 px-6 py-3 text-sm font-semibold text-slate-200 hover:bg-slate-800 hover:border-slate-600 transition-colors"
            >
              Launch Simulation Studio
            </Link>
            <Link
              href="/architecture"
              className="inline-flex items-center justify-center rounded-lg border border-slate-800 bg-slate-900/50 px-5 py-3 text-sm font-medium text-slate-400 hover:text-slate-200 hover:border-slate-700 transition-colors"
            >
              System Architecture →
            </Link>
          </div>
        </div>
      </section>

      {/* Metrics Banner */}
      <section className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((st, idx) => (
          <div
            key={idx}
            className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur transition-all hover:border-slate-700"
          >
            <div className="text-xs font-medium text-slate-400">{st.label}</div>
            <div className="mt-1 text-xl font-bold text-white tracking-tight">{st.value}</div>
            <div className="mt-1 text-[11px] text-slate-500 font-mono">{st.detail}</div>
          </div>
        ))}
      </section>

      {/* Feature Modules Grid */}
      <section className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-white">Platform Subsystems</h2>
            <p className="text-sm text-slate-400">Direct access to core simulation, control, diagnostic, and optimization interfaces.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          {modules.map((m, i) => (
            <Link
              key={i}
              href={m.href}
              className="group relative flex flex-col justify-between rounded-xl border border-slate-800/80 bg-slate-900/50 p-6 transition-all duration-200 hover:-translate-y-1 hover:border-slate-700 hover:bg-slate-900/80 hover:shadow-xl"
            >
              <div>
                <span className={`inline-block rounded-md border px-2.5 py-0.5 text-xs font-semibold ${m.color}`}>
                  {m.tag}
                </span>
                <h3 className="mt-4 text-lg font-bold text-white group-hover:text-emerald-400 transition-colors">
                  {m.title}
                </h3>
                <p className="mt-2 text-sm text-slate-400 leading-relaxed">
                  {m.description}
                </p>
              </div>
              <div className="mt-6 flex items-center gap-1 text-xs font-semibold text-slate-400 group-hover:text-white">
                Launch module <span className="transition-transform group-hover:translate-x-1">→</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* Engineering Invariants & Guarantees */}
      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-8">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <span className="text-emerald-400">🛡️</span> Mathematical Invariants & Design Principles
        </h3>
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-6 text-sm text-slate-300">
          <div className="space-y-2 border-l-2 border-emerald-500/40 pl-4">
            <h4 className="font-semibold text-white">Supply Cap Strictness</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Total allocated volume never exceeds available supply under any condition:
              <code className="block mt-1 p-1 bg-slate-950 rounded text-emerald-400 font-mono">
                Σ(Allocated_z) ≤ W_available (tol = 1e-6)
              </code>
            </p>
          </div>
          <div className="space-y-2 border-l-2 border-cyan-500/40 pl-4">
            <h4 className="font-semibold text-white">Zero Artificial Water</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Allocated water per zone is strictly bounded by raw request:
              <code className="block mt-1 p-1 bg-slate-950 rounded text-cyan-400 font-mono">
                0 ≤ Allocated_z ≤ Request_z
              </code>
              No zone receives water when request or supply is zero.
            </p>
          </div>
          <div className="space-y-2 border-l-2 border-purple-500/40 pl-4">
            <h4 className="font-semibold text-white">Offline AI & PSO Decoupling</h4>
            <p className="text-slate-400 text-xs leading-relaxed">
              Particle Swarm Optimization and Groq LLM are strictly decoupled from real-time actuator loops. Real-time control is executed exclusively by deterministic Mamdani FIS logic.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
