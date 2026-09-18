import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import Navbar from '@/components/Navbar';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'Smart Multizone Fuzzy Irrigation Platform | HAFC Engineering System',
  description:
    'Hierarchical Adaptive Fuzzy Control platform with FAO-56 Penman-Monteith ET0, dynamic soil-water mass balance, 3-zone water-filling allocation, offline PSO optimization, and Groq LLM agronomic advisor.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500 selection:text-slate-950 flex flex-col">
        <Navbar />
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>
        <footer className="border-t border-slate-900 bg-slate-950/80 py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
            <div>
              Smart Multizone Irrigation &bull; Hierarchical Adaptive Fuzzy Control &bull; Research & Production Platform
            </div>
            <div className="font-mono text-[11px] text-slate-400">
              FAO-56 Dual Kc &bull; Water-Filling Layer C &bull; Groq LLaMA-3.3-70B RAG
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
