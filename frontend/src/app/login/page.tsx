'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Sprout, Zap } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('operator@irrigation.platform');
  const [password, setPassword] = useState('••••••••••••');
  const [loading, setLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      router.push('/dashboard');
    }, 600);
  };

  const handleDemoAccess = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      router.push('/dashboard');
    }, 300);
  };

  return (
    <div className="flex min-h-[75vh] items-center justify-center">
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-slate-200/90 bg-white p-8 shadow-sm">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
            <Sprout className="h-6 w-6 text-emerald-600" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-sans">
            {isSignUp ? 'Create Operator Account' : 'Operator Authentication'}
          </h1>
          <p className="text-xs text-slate-500">
            Smart Multizone Fuzzy Irrigation Platform Access
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-700 mb-1.5 font-semibold">Operator Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 shadow-2xs"
              required
            />
          </div>

          <div>
            <label className="block text-slate-700 mb-1.5 font-semibold">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 shadow-2xs"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 py-3 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 transition-all shadow-md shadow-emerald-600/15 cursor-pointer"
          >
            {loading ? 'Authenticating...' : isSignUp ? 'Sign Up' : 'Sign In as Operator'}
          </button>
        </form>

        <div className="relative flex items-center justify-center">
          <div className="w-full border-t border-slate-200" />
          <span className="bg-white px-3 text-[11px] text-slate-400 font-mono uppercase">Or</span>
        </div>

        <button
          onClick={handleDemoAccess}
          disabled={loading}
          className="w-full rounded-xl border border-slate-200 bg-slate-50/80 py-2.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 hover:border-emerald-300 transition-colors cursor-pointer shadow-2xs inline-flex items-center justify-center gap-1.5"
        >
          <Zap className="h-3.5 w-3.5 text-amber-600" />
          <span>Instant Demo Operator Access</span>
        </button>

        <div className="text-center text-xs text-slate-500">
          {isSignUp ? (
            <span>
              Already have credentials?{' '}
              <button
                onClick={() => setIsSignUp(false)}
                className="text-emerald-700 hover:underline font-semibold"
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Need platform access?{' '}
              <button
                onClick={() => setIsSignUp(true)}
                className="text-emerald-700 hover:underline font-semibold"
              >
                Request Authorization
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
