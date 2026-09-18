'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Sprout, Zap, AlertCircle, CheckCircle2, X, Lock, Mail, User, ShieldCheck } from 'lucide-react';

export default function LoginModal() {
  const { isAuthModalOpen, closeAuthModal, login, signUp, demoAccess, isAuthenticated, user } = useAuth();

  const [isSignUp, setIsSignUp] = useState(false);
  const [name, setName] = useState('Field Operator');
  const [email, setEmail] = useState('operator@fuzzy-irrigation.local');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // If already authenticated or modal state is closed, do not render
  if (!isAuthModalOpen || isAuthenticated) {
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes('@') || !cleanEmail.includes('.')) {
      setErrorMessage('Please provide a valid operator email address.');
      return;
    }

    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters in length.');
      return;
    }

    setLoading(true);

    try {
      if (isSignUp) {
        const res = await signUp(cleanEmail, password, name);
        if (res.success) {
          setSuccessMessage('Account registered in Supabase! Welcome to the irrigation platform.');
        } else {
          setErrorMessage(res.error || 'Registration failed.');
        }
      } else {
        const res = await login(cleanEmail, password);
        if (res.success) {
          setSuccessMessage('Authentication verified! Loading supervisory platform...');
        } else {
          setErrorMessage(res.error || 'Invalid credentials.');
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Error connecting to authentication service.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoAccess = () => {
    setLoading(true);
    setErrorMessage(null);
    demoAccess();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in duration-200 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="login-modal-title"
    >
      <div className="relative w-full max-w-md max-h-[92vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 sm:p-8 shadow-2xl space-y-5 sm:space-y-6 animate-in zoom-in-95 duration-200">
        {/* Close / Dismiss Button */}
        <button
          onClick={closeAuthModal}
          className="absolute top-3.5 right-3.5 sm:top-4 sm:right-4 rounded-xl p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition-colors cursor-pointer"
          title="Dismiss dialog"
          aria-label="Close dialog"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
            <Sprout className="h-6 w-6 text-emerald-600" />
          </div>
          <h2 id="login-modal-title" className="text-xl font-bold tracking-tight text-slate-900 font-sans">
            {isSignUp ? 'Create Operator Account' : 'Operator Authentication'}
          </h2>
          <p className="text-xs text-slate-500">
            Smart Multizone Fuzzy Irrigation Platform &bull; Supabase Auth
          </p>
        </div>

        {/* Error Feedback Banner */}
        {errorMessage && (
          <div
            role="alert"
            className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-900 flex items-start gap-2 shadow-2xs animate-in fade-in"
          >
            <AlertCircle className="h-4 w-4 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1 leading-relaxed">
              <span className="font-semibold">Authentication Error: </span>
              {errorMessage}
            </div>
          </div>
        )}

        {/* Success Feedback Banner */}
        {successMessage && (
          <div
            role="status"
            className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-900 flex items-start gap-2 shadow-2xs animate-in fade-in"
          >
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0 mt-0.5" />
            <div className="flex-1 font-medium leading-relaxed">
              {successMessage}
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          {isSignUp && (
            <div>
              <label htmlFor="modal-operator-name" className="block text-slate-700 mb-1 font-semibold">
                Operator Full Name
              </label>
              <div className="relative">
                <input
                  id="modal-operator-name"
                  type="text"
                  placeholder="e.g. Elena Rostova"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 shadow-2xs"
                  required
                />
              </div>
            </div>
          )}

          <div>
            <label htmlFor="modal-operator-email" className="block text-slate-700 mb-1 font-semibold">
              Operator Email
            </label>
            <input
              id="modal-operator-email"
              type="email"
              placeholder="operator@farm-system.io"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 shadow-2xs"
              required
            />
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label htmlFor="modal-operator-password" className="block text-slate-700 font-semibold">
                Password
              </label>
              {isSignUp && (
                <span className="text-[10px] text-slate-400 font-mono">Min 6 characters</span>
              )}
            </div>
            <input
              id="modal-operator-password"
              type="password"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50/70 px-3.5 py-2.5 text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-emerald-500 focus-visible:ring-2 focus-visible:ring-emerald-500 shadow-2xs"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-emerald-600 py-3 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 transition-all shadow-md shadow-emerald-600/15 cursor-pointer mt-1"
          >
            {loading ? (
              <span className="inline-flex items-center gap-2">
                <span className="h-3 w-3 rounded-full border-2 border-white border-t-transparent animate-spin" />
                <span>Validating with Supabase...</span>
              </span>
            ) : isSignUp ? (
              'Create Account in Supabase'
            ) : (
              'Sign In with Supabase'
            )}
          </button>
        </form>

        <div className="relative flex items-center justify-center">
          <div className="w-full border-t border-slate-200" />
          <span className="bg-white px-3 text-[11px] text-slate-400 font-mono uppercase">Or</span>
        </div>

        {/* Instant Demo Access Button */}
        <button
          onClick={handleDemoAccess}
          disabled={loading}
          className="w-full rounded-xl border border-slate-200 bg-slate-50/80 py-2.5 text-xs font-semibold text-slate-800 hover:bg-slate-100 hover:border-emerald-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 transition-colors cursor-pointer shadow-2xs inline-flex items-center justify-center gap-1.5"
        >
          <Zap className="h-3.5 w-3.5 text-amber-600" />
          <span>Instant Demo Operator Access</span>
        </button>

        {/* Modal Footer Controls */}
        <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
          {isSignUp ? (
            <button
              type="button"
              onClick={() => {
                setIsSignUp(false);
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className="text-emerald-700 hover:underline font-semibold cursor-pointer"
            >
              &larr; Switch to Sign In
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                setIsSignUp(true);
                setErrorMessage(null);
                setSuccessMessage(null);
              }}
              className="text-emerald-700 hover:underline font-semibold cursor-pointer"
            >
              Need account? Sign Up
            </button>
          )}

          <button
            type="button"
            onClick={closeAuthModal}
            className="text-slate-400 hover:text-slate-700 text-[11px] hover:underline cursor-pointer"
          >
            Continue as Guest &rarr;
          </button>
        </div>
      </div>
    </div>
  );
}
