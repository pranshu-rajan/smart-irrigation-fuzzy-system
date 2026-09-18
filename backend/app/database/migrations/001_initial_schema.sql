-- PostgreSQL / Supabase Schema for Smart Multizone Irrigation Platform
-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Profiles Table
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 2. Agricultural Zones Table
CREATE TABLE IF NOT EXISTS public.zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    zone_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    crop TEXT NOT NULL,
    soil TEXT NOT NULL,
    area_m2 NUMERIC(10, 2) NOT NULL,
    field_capacity NUMERIC(6, 2) NOT NULL,
    wilting_point NUMERIC(6, 2) NOT NULL,
    saturation NUMERIC(6, 2) DEFAULT 85.0 NOT NULL,
    initial_moisture NUMERIC(6, 2) NOT NULL,
    target_moisture NUMERIC(6, 2) NOT NULL,
    root_zone_depth NUMERIC(5, 2) NOT NULL,
    kc NUMERIC(4, 2) NOT NULL,
    priority NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    CONSTRAINT unique_user_zone_id UNIQUE (user_id, zone_id)
);

-- 3. Simulation Runs Table
CREATE TABLE IF NOT EXISTS public.simulation_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    scenario TEXT NOT NULL,
    duration_hours INTEGER DEFAULT 24 NOT NULL,
    timestep_minutes INTEGER DEFAULT 1 NOT NULL,
    status TEXT DEFAULT 'completed' NOT NULL,
    controller_type TEXT DEFAULT 'fuzzy' NOT NULL,
    supply_scenario TEXT DEFAULT 'Normal Supply' NOT NULL,
    config_snapshot JSONB DEFAULT '{}'::jsonb NOT NULL,
    summary_metrics JSONB DEFAULT '{}'::jsonb NOT NULL,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 4. Simulation Results (Time-Series) Table
CREATE TABLE IF NOT EXISTS public.simulation_results (
    id BIGSERIAL PRIMARY KEY,
    simulation_id UUID NOT NULL REFERENCES public.simulation_runs(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    step INTEGER NOT NULL,
    timestamp TEXT NOT NULL,
    zone_id INTEGER NOT NULL,
    soil_moisture NUMERIC(6, 2) NOT NULL,
    target_moisture NUMERIC(6, 2) NOT NULL,
    moisture_error NUMERIC(6, 2) NOT NULL,
    rsm NUMERIC(6, 4) NOT NULL,
    soil_stress NUMERIC(6, 2) NOT NULL,
    weather_stress NUMERIC(6, 2) NOT NULL,
    water_demand NUMERIC(6, 2) NOT NULL,
    irrigation_command NUMERIC(6, 2) NOT NULL,
    raw_request_mm NUMERIC(8, 4) NOT NULL,
    raw_allocation_pct NUMERIC(6, 2) NOT NULL,
    final_allocation_mm NUMERIC(8, 4) NOT NULL,
    unmet_demand_mm NUMERIC(8, 4) NOT NULL,
    water_volume_requested_l NUMERIC(10, 3) NOT NULL,
    water_volume_allocated_l NUMERIC(10, 3) NOT NULL,
    water_volume_unmet_l NUMERIC(10, 3) NOT NULL,
    et0_mm NUMERIC(8, 5) NOT NULL,
    etc_mm NUMERIC(8, 5) NOT NULL,
    rainfall_mm NUMERIC(8, 4) NOT NULL,
    effective_rainfall_mm NUMERIC(8, 4) NOT NULL,
    water_balance_residual NUMERIC(12, 8) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 5. Optimization Runs Table (PSO Tuning)
CREATE TABLE IF NOT EXISTS public.optimization_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'completed' NOT NULL,
    seed INTEGER DEFAULT 42 NOT NULL,
    swarm_size INTEGER DEFAULT 20 NOT NULL,
    max_iterations INTEGER DEFAULT 30 NOT NULL,
    objective_weights JSONB DEFAULT '{}'::jsonb NOT NULL,
    baseline_fitness NUMERIC(10, 6) DEFAULT 0.0 NOT NULL,
    optimized_fitness NUMERIC(10, 6) DEFAULT 0.0 NOT NULL,
    convergence_history JSONB DEFAULT '[]'::jsonb NOT NULL,
    optimized_parameters JSONB DEFAULT '{}'::jsonb NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    completed_at TIMESTAMPTZ
);

-- 6. Reports Table
CREATE TABLE IF NOT EXISTS public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    simulation_id UUID REFERENCES public.simulation_runs(id) ON DELETE SET NULL,
    optimization_id UUID REFERENCES public.optimization_runs(id) ON DELETE SET NULL,
    report_type TEXT DEFAULT 'simulation_pdf' NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 7. AI Conversations & Messages
CREATE TABLE IF NOT EXISTS public.ai_conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.ai_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES public.ai_conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    grounded_context JSONB,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_zones_user_id ON public.zones(user_id);
CREATE INDEX IF NOT EXISTS idx_sim_runs_user_id ON public.simulation_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_sim_results_sim_id ON public.simulation_results(simulation_id);
CREATE INDEX IF NOT EXISTS idx_sim_results_step ON public.simulation_results(simulation_id, step);
CREATE INDEX IF NOT EXISTS idx_sim_results_zone_id ON public.simulation_results(simulation_id, zone_id);
CREATE INDEX IF NOT EXISTS idx_opt_runs_user_id ON public.optimization_runs(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_messages_conv_id ON public.ai_messages(conversation_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.simulation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.optimization_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users only access their own records
CREATE POLICY "Users can view own profile" ON public.profiles FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users can view own zones" ON public.zones FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own simulation_runs" ON public.simulation_runs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own simulation_results" ON public.simulation_results FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own optimization_runs" ON public.optimization_runs FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own reports" ON public.reports FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own ai_conversations" ON public.ai_conversations FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own ai_messages" ON public.ai_messages FOR ALL USING (
    EXISTS (SELECT 1 FROM public.ai_conversations WHERE id = ai_messages.conversation_id AND user_id = auth.uid())
);
