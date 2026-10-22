'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';

type ThemeMode = 'dark' | 'light';

interface ThemeContextType {
  theme: ThemeMode;
  toggleTheme: () => void;
  setTheme: (theme: ThemeMode) => void;
  audioFeedback: boolean;
  toggleAudioFeedback: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<ThemeMode>('dark');
  const [audioFeedback, setAudioFeedback] = useState<boolean>(true);
  const [mounted, setMounted] = useState<boolean>(false);

  useEffect(() => {
    // Check saved theme or default to 2026 dark cyber-agri cockpit
    const savedTheme = localStorage.getItem('agri_theme') as ThemeMode | null;
    const initialTheme = savedTheme === 'light' ? 'light' : 'dark';
    setThemeState(initialTheme);

    const savedAudio = localStorage.getItem('agri_audio_feedback');
    if (savedAudio !== null) {
      setAudioFeedback(savedAudio === 'true');
    }

    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.style.colorScheme = 'dark';
    } else {
      root.classList.remove('dark');
      root.style.colorScheme = 'light';
    }
    localStorage.setItem('agri_theme', theme);
  }, [theme, mounted]);

  const toggleTheme = () => {
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const setTheme = (mode: ThemeMode) => {
    setThemeState(mode);
  };

  const toggleAudioFeedback = () => {
    setAudioFeedback((prev) => {
      const next = !prev;
      localStorage.setItem('agri_audio_feedback', String(next));
      return next;
    });
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
        setTheme,
        audioFeedback,
        toggleAudioFeedback,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
