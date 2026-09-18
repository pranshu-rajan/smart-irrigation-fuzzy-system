import Link from 'next/link';
import DigitalTwin3D from '@/components/DigitalTwin3D';
import { 
  Activity, 
  Cpu, 
  Sliders, 
  Layers, 
  TrendingUp, 
  Bot, 
  FileText, 
  GitFork,
  ArrowRight,
  ShieldCheck,
  Droplets,
  Sprout
} from 'lucide-react';

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
      tag: 'Live Monitoring',
      icon: Activity,
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    {
      title: 'Simulation Studio',
      description: 'Run 24-hour closed-loop multizone simulations under 6 environmental scenarios with high-frequency time-series telemetry.',
      href: '/simulation',
      tag: 'Closed Loop',
      icon: Cpu,
      color: 'bg-teal-50 text-teal-700 border-teal-200',
    },
    {
      title: 'Fuzzy Logic Diagnostics',
      description: 'Inspect membership functions, rule bases, and live defuzzification sandboxes for all 5 Mamdani FIS engines.',
      href: '/fuzzy',
      tag: '5 FIS Engines',
      icon: Sliders,
      color: 'bg-amber-50 text-amber-700 border-amber-200',
    },
    {
      title: 'Supervisory Water Allocation',
      description: 'Two-layer allocation engine combining Mamdani Scarcity FIS with deterministic bounded priority-weighted water-filling.',
      href: '/allocation',
      tag: 'Hierarchical',
      icon: Layers,
      color: 'bg-sky-50 text-sky-700 border-sky-200',
    },
    {
      title: 'Offline PSO Parameter Tuning',
      description: 'Offline Particle Swarm Optimization tuning 18 membership function parameters with convergence tracking.',
      href: '/optimization',
      tag: 'PSO Tuning',
      icon: TrendingUp,
      color: 'bg-purple-50 text-purple-700 border-purple-200',
    },
    {
      title: 'Scenario Comparison Matrix',
      description: 'Benchmark all 6 environmental scenarios side-by-side: ET0, ETc, stress indices, volume requested vs allocated, and MAE.',
      href: '/scenarios',
      tag: 'Benchmarking',
      icon: GitFork,
      color: 'bg-rose-50 text-rose-700 border-rose-200',
    },
    {
      title: 'Grounded AI Advisory',
      description: 'Technical assistant powered by Groq LLM grounded in real-time simulation telemetry. Strictly advisory and explanatory.',
      href: '/ai',
      tag: 'Advisory AI',
      icon: Bot,
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    {
      title: 'Audit PDF Reports & CSV',
      description: 'Generate publication-grade engineering PDF audit reports with ReportLab and export high-frequency CSV telemetry.',
      href: '/reports',
      tag: 'Reporting',
      icon: FileText,
      color: 'bg-slate-100 text-slate-700 border-slate-200',
    },
  ];

  return (
    <div className="space-y-12 pb-16">
      {/* Light Agricultural Hero Section */}
      <section className="relative overflow-hidden rounded-3xl border border-emerald-100 bg-gradient-to-br from-white via-emerald-50/30 to-teal-50/40 p-8 md:p-12 shadow-sm">
        <div className="relative z-10 max-w-4xl space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-white/90 px-3.5 py-1 text-xs font-semibold text-emerald-700 shadow-2xs">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>AGRICULTURAL CONTROL ENGINEERING PLATFORM &bull; HAFC v2.4</span>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl font-sans leading-tight">
            Smart Multizone Irrigation & Water Resource Management
          </h1>

          <p className="text-base text-slate-600 sm:text-lg font-normal leading-relaxed max-w-3xl">
            Hierarchical Adaptive Fuzzy Control platform combining physics-based FAO-56 Penman-Monteith ET0, dynamic root-zone soil water balance, 5 modular Mamdani fuzzy inference systems, supervisory bounded water allocation, and offline PSO optimization.
          </p>

          <div className="flex flex-wrap gap-3 pt-2">
            <Link
              href="/dashboard"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-sm shadow-emerald-600/25 hover:bg-emerald-700 transition-all hover:shadow-md"
            >
              <span>Open Live Dashboard</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/simulation"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 hover:border-emerald-300 transition-all shadow-2xs"
            >
              <Cpu className="h-4 w-4 text-emerald-600" />
              <span>Launch Simulation Studio</span>
            </Link>
            <Link
              href="/architecture"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-medium text-slate-600 hover:text-emerald-700 hover:border-emerald-200 transition-all"
            >
              <span>System Architecture</span>
              <ArrowRight className="h-4 w-4 text-slate-400" />
            </Link>
          </div>
        </div>
      </section>

      {/* Interactive 3D Digital Twin Farm Section */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
              <Sprout className="h-5 w-5 text-emerald-600" />
              Interactive 3D Multizone Digital Twin
            </h2>
            <p className="text-xs text-slate-500">
              WebGL interactive field rendering root-zone soil strata, crop canopies, and real-time sprinkler spray dynamics
            </p>
          </div>
          <span className="text-xs font-mono font-medium text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
            Rotate &bull; Pan &bull; Inspect
          </span>
        </div>

        <DigitalTwin3D />
      </section>

      {/* Metrics Banner */}
      <section className="grid grid-cols-2 gap-3.5 sm:grid-cols-3 lg:grid-cols-6">
        {stats.map((st, idx) => (
          <div
            key={idx}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-2xs hover:shadow-sm hover:border-emerald-200 transition-all"
          >
            <div className="text-[11px] font-medium text-slate-500">{st.label}</div>
            <div className="mt-1 text-xl font-bold text-slate-900 tracking-tight">{st.value}</div>
            <div className="mt-1 text-[11px] text-emerald-700 font-mono font-medium">{st.detail}</div>
          </div>
        ))}
      </section>

      {/* Feature Modules Grid */}
      <section className="space-y-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900">Platform Subsystems</h2>
          <p className="text-sm text-slate-500">Direct access to core simulation, control, diagnostic, and optimization interfaces.</p>
        </div>

        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-4">
          {modules.map((m, i) => {
            const Icon = m.icon;
            return (
              <Link
                key={i}
                href={m.href}
                className="group relative flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 transition-all duration-200 hover:-translate-y-1 hover:border-emerald-300 hover:shadow-md"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className={`inline-block rounded-lg border px-2.5 py-1 text-xs font-semibold ${m.color}`}>
                      {m.tag}
                    </span>
                    <Icon className="h-4 w-4 text-slate-400 group-hover:text-emerald-600 transition-colors" />
                  </div>
                  <h3 className="mt-4 text-base font-bold text-slate-900 group-hover:text-emerald-700 transition-colors">
                    {m.title}
                  </h3>
                  <p className="mt-2 text-xs text-slate-600 leading-relaxed">
                    {m.description}
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-emerald-600 group-hover:text-emerald-700">
                  <span>Open Interface</span>
                  <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
