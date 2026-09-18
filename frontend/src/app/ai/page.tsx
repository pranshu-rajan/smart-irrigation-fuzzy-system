'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, SimulationSummaryResponse } from '@/lib/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  grounded_context?: any;
}

function AIChatContent() {
  const searchParams = useSearchParams();
  const initialSimId = searchParams.get('sim_id');


  const [simulations, setSimulations] = useState<SimulationSummaryResponse[]>([]);
  const [selectedSimId, setSelectedSimId] = useState<string>(initialSimId || '');
  const [selectedZone, setSelectedZone] = useState<number | undefined>(undefined);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your Technical Irrigation Advisory AI. I can explain fuzzy inference decisions, telemetry trends, bounded water allocation dynamics, and offline PSO calibration. How can I assist your engineering audit today?',
      source: 'groq',
    },
  ]);
  const [inputPrompt, setInputPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchSims = async () => {
      try {
        const list = await api.listSimulations(10);
        setSimulations(list);
        if (!selectedSimId && list.length > 0) {
          setSelectedSimId(list[0].id);
        }
      } catch (err) {
        console.error('Failed to load simulations for AI grounding:', err);
      }
    };
    fetchSims();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (customPrompt?: string) => {
    const text = customPrompt || inputPrompt;
    if (!text.trim() || isLoading) return;

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    if (!customPrompt) setInputPrompt('');
    setIsLoading(true);

    try {
      const res = await api.chatAI({
        prompt: text,
        simulation_id: selectedSimId || undefined,
        zone_id: selectedZone,
      });

      const assistantMsg: Message = {
        role: 'assistant',
        content: res.response,
        source: res.source,
        grounded_context: res.grounded_context_summary,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Error contacting advisory service: ${err.message}`,
          source: 'error',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const presetQueries = [
    'Why did Zone 1 request more water than Zone 3 during peak midday hours?',
    'Explain how the Water Allocation FIS prioritizes Tomato over Maize under 40% scarcity.',
    'Explain the mathematical proof that the water-balance residual closes to 0.00 mm.',
    'How do the 18 PSO parameters reduce tracking error while preventing valve chatter?',
  ];

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200/80">
            Grounded LLM Advisory
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-500 font-medium">Groq LLaMA 3.3 Reasoning Copilot</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Grounded AI Advisory & RAG Assistant
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Domain-specific technical advisor grounded in real-time simulation telemetry. Strictly explanatory — never acts as an online actuator controller.
        </p>
      </div>

      {/* Strict Decoupling Banner */}
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4 text-xs text-emerald-950 shadow-2xs">
        <strong className="text-emerald-900 block mb-1">🔒 Safety Notice & Operational Boundary:</strong>
        This AI system functions strictly as a diagnostic and analytical advisory copilot. All valve commands and water dispatches are governed exclusively by deterministic Mamdani FIS and bounded water-filling math.
      </div>

      {/* Main Chat Interface */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Grounding Context Selector (Left) */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-800">
            Telemetry Grounding
          </h2>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-700 font-semibold block mb-1">Grounding Simulation Run</label>
              <select
                value={selectedSimId}
                onChange={(e) => setSelectedSimId(e.target.value)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                <option value="">No simulation attached</option>
                {simulations.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.scenario} ({s.id.substring(0, 8)}...)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-slate-700 font-semibold block mb-1">Zone Scope</label>
              <select
                value={selectedZone !== undefined ? selectedZone : ''}
                onChange={(e) => setSelectedZone(e.target.value ? Number(e.target.value) : undefined)}
                className="w-full rounded-lg border border-slate-200 bg-slate-50/70 px-3 py-2 text-slate-900 font-medium focus:bg-white focus:border-emerald-500 focus:outline-none"
              >
                <option value="">All Zones (Multizone)</option>
                <option value="1">Zone 1 (Tomato / Loam)</option>
                <option value="2">Zone 2 (Potato / Sandy Loam)</option>
                <option value="3">Zone 3 (Maize / Clay Loam)</option>
              </select>
            </div>
          </div>

          {/* Preset Prompts */}
          <div className="pt-3 border-t border-slate-100 space-y-2">
            <span className="text-[11px] font-bold text-slate-700 block">Suggested Inquiries:</span>
            {presetQueries.map((pq, idx) => (
              <button
                key={idx}
                onClick={() => handleSendMessage(pq)}
                className="w-full text-left rounded-xl bg-slate-50/90 hover:bg-emerald-50/80 p-2.5 text-[11px] text-slate-700 hover:text-emerald-900 border border-slate-200/70 transition-colors cursor-pointer"
              >
                💬 {pq}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages Container (Right) */}
        <div className="lg:col-span-3 flex flex-col rounded-2xl border border-slate-200/90 bg-white shadow-xs h-[600px]">
          {/* Scrollable Conversation */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-emerald-600 text-white rounded-br-none shadow-xs'
                      : 'bg-slate-50 text-slate-800 border border-slate-200/90 rounded-bl-none shadow-2xs'
                  }`}
                >
                  <p className="whitespace-pre-line">{m.content}</p>

                  {m.grounded_context && (
                    <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] text-slate-500 font-mono">
                      <span>Telemetry Attached: </span>
                      <span className="text-emerald-700 font-bold">
                        {m.grounded_context.scenario || 'Simulation'} • {m.grounded_context.timesteps || 1440} timesteps
                      </span>
                    </div>
                  )}
                </div>

                <span className="mt-1 text-[10px] text-slate-400 font-mono">
                  {m.role === 'user' ? 'Operator' : `Advisory (${m.source || 'Groq'})`}
                </span>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500 italic">
                <div className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
                Querying Groq reasoning model with grounded telemetry...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="border-t border-slate-100 p-4 bg-white rounded-b-2xl flex gap-3">
            <input
              type="text"
              placeholder="Ask about fuzzy rules, moisture balance, scarcity allocation, or PSO tuning..."
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 shadow-2xs"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputPrompt.trim()}
              className="rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-600/15 cursor-pointer"
            >
              Send Inquire
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AIChatPage() {
  return (
    <Suspense fallback={<div className="p-8 text-xs text-slate-400 font-mono">Loading AI Advisory copilot...</div>}>
      <AIChatContent />
    </Suspense>
  );
}

