'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, SimulationSummaryResponse } from '@/lib/api';
import { Lock, MessageSquare, Globe, ExternalLink, Brain, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import FormattedAIResponse from '@/components/FormattedAIResponse';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  source?: string;
  model_name?: string;
  reasoning?: string;
  web_sources?: Array<{ title: string; url: string; content: string }>;
  grounded_context?: any;
}

function AIChatContent() {
  const searchParams = useSearchParams();
  const initialSimId = searchParams.get('sim_id');

  const [simulations, setSimulations] = useState<SimulationSummaryResponse[]>([]);
  const [selectedSimId, setSelectedSimId] = useState<string>(initialSimId || '');
  const [selectedZone, setSelectedZone] = useState<number | undefined>(undefined);
  const [useWebSearch, setUseWebSearch] = useState<boolean>(true);
  const [locationContext, setLocationContext] = useState<string>('National (India / ICAR)');
  const [expandedReasoningIdx, setExpandedReasoningIdx] = useState<number | null>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your Senior Agronomic & Control Systems AI Specialist powered by **Groq OpenAI GPT-OSS-120B** and **Tavily Live Web Search**.\n\nI can explain live 5-stage fuzzy inference decisions, ICAR/IMD regional agromet advisories, telemetry trends, and bounded water allocation across Indian districts. How may I assist your engineering audit today?',
      source: 'groq',
      model_name: 'openai/gpt-oss-120b',
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
        use_web_search: useWebSearch,
        location: locationContext || undefined,
      });

      const assistantMsg: Message = {
        role: 'assistant',
        content: res.response,
        source: res.source,
        model_name: res.model_name || 'openai/gpt-oss-120b',
        reasoning: res.reasoning,
        web_sources: res.web_sources,
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
    'What are the latest ICAR irrigation recommendations for wheat in Punjab vertisols/alluvials?',
    'Why did Zone 1 request more water than Zone 3 during peak midday hours?',
    'Explain how the Water Allocation FIS prioritizes Tomato over Maize under 40% scarcity.',
    'Explain the mathematical proof that the water-balance residual closes to 0.00 mm.',
    'How do the 18 PSO parameters reduce tracking error while preventing valve chatter?',
  ];

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200">
            <Brain className="h-3.5 w-3.5 text-emerald-600" />
            Groq: openai/gpt-oss-120b
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="inline-flex items-center gap-1 rounded-md bg-sky-50 px-2 py-0.5 text-xs font-semibold text-sky-800 border border-sky-200">
            <Globe className="h-3 w-3 text-sky-600" />
            Tavily Web Search Live
          </span>
          <span className="text-xs text-slate-400">•</span>
          <span className="text-xs text-slate-500 font-medium">120B Reasoning & ICAR Agromet Copilot</span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Grounded AI Advisory & ICAR Intelligence Hub
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Domain-specific technical advisor grounded in simulation telemetry and live web agricultural bulletins. Strictly interpretive — never overrides online physical actuators.
        </p>
      </div>

      {/* Strict Decoupling Banner */}
      <div className="rounded-2xl border border-emerald-200 bg-emerald-50/50 p-4 text-xs text-emerald-950 shadow-2xs">
        <div className="flex items-center gap-1.5 font-bold text-emerald-900 mb-1">
          <Lock className="h-3.5 w-3.5 text-emerald-700" />
          <span>Safety Notice & Operational Decoupling:</span>
        </div>
        This AI system functions strictly as a diagnostic, analytical, and agronomic advisory copilot. All valve commands and water balance dispatches are governed exclusively by deterministic Mamdani FIS and bounded water-filling conservation math.
      </div>

      {/* Main Chat Interface */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Grounding Context Selector (Left) */}
        <div className="rounded-2xl border border-slate-200/90 bg-white p-5 shadow-xs space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-emerald-800">
            Intelligence Grounding
          </h2>

          <div className="space-y-3 text-xs">
            {/* Live Web Search Toggle */}
            <div className="p-2.5 rounded-xl border border-sky-200 bg-sky-50/50 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe className="h-4 w-4 text-sky-600" />
                <div>
                  <span className="font-semibold text-slate-900 block text-[11px]">Tavily Web Search</span>
                  <span className="text-[10px] text-slate-500">Live ICAR / IMD Agromet</span>
                </div>
              </div>
              <input
                type="checkbox"
                checked={useWebSearch}
                onChange={(e) => setUseWebSearch(e.target.checked)}
                className="h-4 w-4 rounded accent-sky-600 cursor-pointer"
              />
            </div>

            <div>
              <label htmlFor="ai-location-select" className="text-slate-700 font-semibold block mb-1">
                Regional Agromet Context
              </label>
              <select
                id="ai-location-select"
                value={locationContext}
                onChange={(e) => setLocationContext(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-medium text-[11px] focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
              >
                <option value="National (India / ICAR)">National (India / ICAR Overall)</option>
                <option value="Punjab (Trans-Gangetic / PAU Ludhiana)">Punjab (PAU Ludhiana • Alluvial)</option>
                <option value="Maharashtra (Western Plateau / Pune)">Maharashtra (Pune • Black Vertisol)</option>
                <option value="Uttar Pradesh (Middle Gangetic / Varanasi)">Uttar Pradesh (Varanasi • Alluvial Loam)</option>
                <option value="Karnataka (Southern Dry Zone / Mandya)">Karnataka (Mandya • Red Sandy Loam)</option>
                <option value="Rajasthan (Arid Zone / Jaipur)">Rajasthan (Jaipur • Desert Aridisol)</option>
                <option value="Andhra Pradesh (East Coast / Guntur)">Andhra Pradesh (Guntur • Coastal Deltaic)</option>
              </select>
            </div>

            <div>
              <label htmlFor="ai-sim-select" className="text-slate-700 font-semibold block mb-1">Telemetry Grounding</label>
              <select
                id="ai-sim-select"
                value={selectedSimId}
                onChange={(e) => setSelectedSimId(e.target.value)}
                aria-label="Grounding simulation run telemetry context"
                className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-mono text-[11px] focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
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
              <label htmlFor="ai-zone-select" className="text-slate-700 font-semibold block mb-1">Zone Scope</label>
              <select
                id="ai-zone-select"
                value={selectedZone !== undefined ? selectedZone : ''}
                onChange={(e) => setSelectedZone(e.target.value ? Number(e.target.value) : undefined)}
                aria-label="Zone telemetry scope"
                className="w-full rounded-lg border border-slate-300 bg-slate-50/70 px-3 py-2 text-slate-900 font-medium text-[11px] focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
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
                aria-label={`Inquire: ${pq}`}
                className="w-full text-left rounded-xl bg-slate-50/90 hover:bg-emerald-50/80 p-2.5 text-[11px] text-slate-700 hover:text-emerald-900 border border-slate-200/70 transition-colors cursor-pointer flex items-start gap-2 focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:outline-none"
              >
                <MessageSquare className="h-3.5 w-3.5 mt-0.5 shrink-0 text-emerald-600" />
                <span>{pq}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages Container (Right) */}
        <div className="lg:col-span-3 flex flex-col rounded-2xl border border-slate-200/90 bg-white shadow-xs h-[550px] sm:h-[650px]">
          {/* Scrollable Conversation */}
          <div className="flex-1 overflow-y-auto p-3 sm:p-6 space-y-4">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-2xl rounded-2xl p-3.5 sm:p-4 text-xs leading-relaxed ${
                    m.role === 'user'
                      ? 'bg-emerald-600 text-white rounded-br-none shadow-xs'
                      : 'bg-slate-50/90 text-slate-800 border border-slate-200/90 rounded-bl-none shadow-2xs'
                  }`}
                >
                  {m.role === 'user' ? (
                    <p className="whitespace-pre-line font-medium text-white">{m.content}</p>
                  ) : (
                    <div>
                      <FormattedAIResponse content={m.content} />

                      {/* Expandable Reasoning Trace */}
                      {m.reasoning && (
                        <div className="mt-3 pt-2 border-t border-slate-200">
                          <button
                            onClick={() => setExpandedReasoningIdx(expandedReasoningIdx === idx ? null : idx)}
                            className="flex items-center gap-1.5 text-[11px] font-semibold text-purple-700 hover:text-purple-900 transition cursor-pointer"
                          >
                            <Brain className="h-3.5 w-3.5 text-purple-600" />
                            <span>120B Reasoning Chain-of-Thought</span>
                            {expandedReasoningIdx === idx ? (
                              <ChevronUp className="h-3.5 w-3.5" />
                            ) : (
                              <ChevronDown className="h-3.5 w-3.5" />
                            )}
                          </button>
                          {expandedReasoningIdx === idx && (
                            <div className="mt-2 p-3 rounded-xl bg-purple-50/60 border border-purple-200 text-[10px] font-mono text-purple-950 whitespace-pre-wrap leading-relaxed max-h-48 overflow-y-auto">
                              {m.reasoning}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Web Search Sources */}
                      {m.web_sources && m.web_sources.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-slate-200">
                          <span className="text-[10px] font-bold text-sky-800 flex items-center gap-1 mb-1.5">
                            <Globe className="h-3 w-3 text-sky-600" />
                            Verified Live Web Sources (Tavily):
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {m.web_sources.map((src, sIdx) => (
                              <a
                                key={sIdx}
                                href={src.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-white border border-sky-200 text-[10px] text-sky-700 hover:bg-sky-50 transition"
                              >
                                <span className="truncate max-w-[200px]">{src.title}</span>
                                <ExternalLink className="h-2.5 w-2.5 flex-shrink-0" />
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      {m.grounded_context && (
                        <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] text-slate-500 font-mono">
                          <span>Grounding: </span>
                          <span className="text-emerald-700 font-bold">
                            {m.grounded_context.sim_id ? 'Simulation Attached' : 'RAG Knowledge Index'}
                            {m.grounded_context.web_results_count ? ` • ${m.grounded_context.web_results_count} live web sources` : ''}
                          </span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <span className="mt-1 text-[10px] text-slate-400 font-mono flex items-center gap-1">
                  {m.role === 'user' ? 'Operator' : (
                    <>
                      <span>{m.model_name || 'openai/gpt-oss-120b'}</span>
                      <span>•</span>
                      <span>{m.source === 'groq' ? 'Groq High-Speed Cloud' : 'Rule-Based Fallback'}</span>
                    </>
                  )}
                </span>
              </div>
            ))}

            {isLoading && (
              <div className="flex items-center gap-2 text-xs text-slate-500 italic p-2 rounded-xl bg-slate-50">
                <div className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
                <span>
                  Querying {useWebSearch ? 'Tavily web search & ' : ''}Groq openai/gpt-oss-120b reasoning model...
                </span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input Bar */}
          <div className="border-t border-slate-100 p-3 sm:p-4 bg-white rounded-b-2xl flex flex-col sm:flex-row gap-2.5 sm:gap-3">
            <input
              id="ai-prompt-input"
              aria-label="Ask Groq AI advisory prompt"
              type="text"
              placeholder={
                useWebSearch
                  ? "Ask about live ICAR practices, monsoon alerts, soil stress, or fuzzy allocation..."
                  : "Ask about fuzzy rules, moisture balance, scarcity allocation, or PSO tuning..."
              }
              value={inputPrompt}
              onChange={(e) => setInputPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50/70 px-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 shadow-2xs"
            />
            <button
              id="ai-send-btn"
              aria-label="Send advisory inquiry"
              onClick={() => handleSendMessage()}
              disabled={isLoading || !inputPrompt.trim()}
              className="w-full sm:w-auto rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 transition-all shadow-md shadow-emerald-600/15 cursor-pointer text-center"
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
    <Suspense fallback={<div className="p-8 text-xs text-slate-500">Loading AI Advisory Workspace...</div>}>
      <AIChatContent />
    </Suspense>
  );
}
