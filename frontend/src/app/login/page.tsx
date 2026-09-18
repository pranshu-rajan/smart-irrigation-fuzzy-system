'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

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
      <div className="w-full max-w-md space-y-8 rounded-2xl border border-slate-800 bg-slate-900/70 p-8 backdrop-blur shadow-2xl">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-2xl">
            🌱
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-sans">
            {isSignUp ? 'Create Operator Account' : 'Operator Authentication'}
          </h1>
          <p className="text-xs text-slate-400">
            Smart Multizone Fuzzy Irrigation Platform Access
          </p>
        </div>

        <form onSubmit={handleLogin} className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-400 mb-1 font-medium">Operator Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1 font-medium">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-emerald-500 py-2.5 text-xs font-bold text-slate-950 hover:bg-emerald-400 disabled:opacity-50 transition-colors shadow-lg shadow-emerald-500/20"
          >
            {loading ? 'Authenticating...' : isSignUp ? 'Sign Up' : 'Sign In as Operator'}
          </button>
        </form>

        <div className="relative flex items-center justify-center">
          <div className="w-full border-t border-slate-800" />
          <span className="bg-slate-900 px-3 text-[11px] text-slate-500 font-mono uppercase">Or</span>
        </div>

        <button
          onClick={handleDemoAccess}
          disabled={loading}
          className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2.5 text-xs font-semibold text-white hover:bg-slate-700 transition-colors"
        >
          ⚡ Instant Demo Operator Access
        </button>

        <div className="text-center text-xs text-slate-500">
          {isSignUp ? (
            <span>
              Already have credentials?{' '}
              <button
                onClick={() => setIsSignUp(false)}
                className="text-emerald-400 hover:underline font-medium"
              >
                Sign In
              </button>
            </span>
          ) : (
            <span>
              Need elevated permissions?{' '}
              <button
                onClick={() => setIsSignUp(true)}
                className="text-emerald-400 hover:underline font-medium"
              >
                Register
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
