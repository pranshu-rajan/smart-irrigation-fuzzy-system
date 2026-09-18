import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import Sidebar from '@/components/Sidebar';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
});

export const metadata: Metadata = {
  title: 'Smart Multizone Fuzzy Irrigation Platform | HAFC Agricultural System',
  description:
    'Hierarchical Adaptive Fuzzy Control platform with FAO-56 Penman-Monteith ET0, dynamic soil-water mass balance, 3-zone water-filling allocation, offline PSO optimization, and 3D digital twin visualization.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-[#f8faf9] text-slate-900 font-sans selection:bg-emerald-500 selection:text-white antialiased">
        <Sidebar />
        
        {/* Main Content Area Offset for Left Sidebar */}
        <div className="flex flex-col min-h-screen lg:pl-64 transition-all duration-300">
          <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          <footer className="border-t border-slate-200/90 bg-white py-6 text-center text-xs text-slate-500 shadow-sm mt-auto">
            <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="font-medium text-slate-700">Smart Multizone Irrigation Platform</span>
                <span>&bull;</span>
                <span>Hierarchical Adaptive Fuzzy Control</span>
              </div>
              <div className="font-mono text-[11px] text-slate-600 bg-slate-50 px-2.5 py-1 rounded-md border border-slate-200">
                FAO-56 Penman-Monteith &bull; Bounded Water-Filling &bull; 3D Digital Twin
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
