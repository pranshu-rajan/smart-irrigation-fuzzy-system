import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { SidebarProvider } from '@/context/SidebarContext';
import { AuthProvider } from '@/context/AuthContext';
import AppLayoutClient from '@/components/AppLayoutClient';

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
        <AuthProvider>
          <SidebarProvider>
            <AppLayoutClient>{children}</AppLayoutClient>
          </SidebarProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
