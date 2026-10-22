'use client';

import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { TimeseriesRecord } from '@/lib/api';
import { soundEngine } from '@/lib/audioHaptics';

export interface WeatherSnapshot {
  tempC: number;
  rhPct: number;
  solarWm2: number;
  windSpeedMs: number;
  rainfallMm: number;
  et0Mm: number;
}

export interface ZoneLiveState {
  zoneId: number;
  soilMoisture: number;
  targetMoisture: number;
  soilStress: number;
  irrigationCommand: number;
  allocatedMm: number;
  allocatedLiters: number;
  flowRateLpm: number;
  isIrrigating: boolean;
}

export interface UseSimulationPlaybackReturn {
  currentStep: number;
  totalSteps: number;
  currentTimeString: string;
  isPlaying: boolean;
  speed: number;
  speeds: number[];
  play: () => void;
  pause: () => void;
  togglePlay: () => void;
  seekToStep: (step: number) => void;
  setSpeed: (speed: number) => void;
  stepForward: () => void;
  stepBackward: () => void;
  weatherSnapshot: WeatherSnapshot;
  zoneStates: Record<number, ZoneLiveState>;
  currentRecords: TimeseriesRecord[];
}

export function useSimulationPlayback(
  timeseries: TimeseriesRecord[],
  initialSpeed: number = 2
): UseSimulationPlaybackReturn {
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeedState] = useState<number>(initialSpeed);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const speeds = [1, 2, 5, 10, 30];

  // Group records by step
  const recordsByStep = useMemo(() => {
    const map = new Map<number, TimeseriesRecord[]>();
    for (const r of timeseries) {
      const list = map.get(r.step) || [];
      list.push(r);
      map.set(r.step, list);
    }
    return map;
  }, [timeseries]);

  const uniqueSteps = useMemo(() => {
    const s = Array.from(recordsByStep.keys()).sort((a, b) => a - b);
    return s.length > 0 ? s : [0];
  }, [recordsByStep]);

  const totalSteps = uniqueSteps[uniqueSteps.length - 1] || 0;

  // Active step records
  const currentRecords = useMemo(() => {
    return recordsByStep.get(currentStep) || [];
  }, [recordsByStep, currentStep]);

  // Weather snapshot at current step with smooth diurnal physics fallback
  const weatherSnapshot: WeatherSnapshot = useMemo(() => {
    const hour = (currentStep / 60.0) % 24;
    // Diurnal solar curve (peak ~850 W/m² at 12:30 PM, zero at night)
    const solarFactor = Math.max(0, Math.sin(((hour - 6) / 13) * Math.PI));
    const diurnalSolar = Math.round(solarFactor * 850);
    // Diurnal temperature curve (min 20°C at 5 AM, max 34°C at 2 PM)
    const diurnalTemp = Number((20.0 + 14.0 * Math.max(0, Math.sin(((hour - 8) / 14) * Math.PI))).toFixed(1));
    // Diurnal RH curve (inverse of temp: max ~75% at dawn, min ~35% in afternoon)
    const diurnalRh = Number((75.0 - 40.0 * solarFactor).toFixed(0));

    if (currentRecords.length > 0) {
      const r = currentRecords[0];
      return {
        tempC: r.temperature_c ?? diurnalTemp,
        rhPct: r.relative_humidity_pct ?? diurnalRh,
        solarWm2: r.solar_radiation_w_m2 ?? diurnalSolar,
        windSpeedMs: r.wind_speed_m_s ?? 2.2,
        rainfallMm: r.rainfall_mm ?? 0.0,
        et0Mm: r.et0_mm ?? Number((solarFactor * 6.5 + 0.8).toFixed(2)),
      };
    }
    return {
      tempC: diurnalTemp,
      rhPct: diurnalRh,
      solarWm2: diurnalSolar,
      windSpeedMs: 2.2,
      rainfallMm: 0.0,
      et0Mm: Number((solarFactor * 6.5 + 0.8).toFixed(2)),
    };
  }, [currentRecords, currentStep]);

  // Zone live states at current step
  const zoneStates: Record<number, ZoneLiveState> = useMemo(() => {
    const states: Record<number, ZoneLiveState> = {};
    for (const r of currentRecords) {
      const cmd = r.irrigation_command ?? 0;
      const allocMm = r.allocated_irrigation_mm ?? 0;
      const isIrr = cmd > 5 || allocMm > 0.01;
      const flowRate = isIrr ? Number(((cmd / 100.0) * 35.0).toFixed(1)) : 0.0;

      states[r.zone_id] = {
        zoneId: r.zone_id,
        soilMoisture: r.soil_moisture ?? 25.0,
        targetMoisture: r.target_moisture ?? 28.0,
        soilStress: r.soil_stress ?? 0.2,
        irrigationCommand: cmd,
        allocatedMm: allocMm,
        allocatedLiters: r.water_volume_allocated_l ?? 0,
        flowRateLpm: flowRate,
        isIrrigating: isIrr,
      };
    }
    // Fallback if no records loaded
    if (Object.keys(states).length === 0) {
      states[1] = { zoneId: 1, soilMoisture: 23.5, targetMoisture: 28.0, soilStress: 0.35, irrigationCommand: 45, allocatedMm: 2.1, allocatedLiters: 210, flowRateLpm: 15.8, isIrrigating: true };
      states[2] = { zoneId: 2, soilMoisture: 21.0, targetMoisture: 24.0, soilStress: 0.25, irrigationCommand: 30, allocatedMm: 1.4, allocatedLiters: 140, flowRateLpm: 10.5, isIrrigating: true };
      states[3] = { zoneId: 3, soilMoisture: 29.0, targetMoisture: 30.0, soilStress: 0.1, irrigationCommand: 0, allocatedMm: 0.0, allocatedLiters: 0, flowRateLpm: 0.0, isIrrigating: false };
    }
    return states;
  }, [currentRecords]);

  // Format time of day string (assuming 1-minute steps starting at 00:00)
  const currentTimeString = useMemo(() => {
    const totalMinutes = currentStep;
    const hours = Math.floor(totalMinutes / 60) % 24;
    const mins = totalMinutes % 60;
    const hh = String(hours).padStart(2, '0');
    const mm = String(mins).padStart(2, '0');
    return `${hh}:${mm}`;
  }, [currentStep]);

  // Scrub / Seek handler
  const seekToStep = useCallback((step: number) => {
    const clamped = Math.max(0, Math.min(totalSteps, step));
    setCurrentStep(clamped);
    soundEngine.playSliderTick();
  }, [totalSteps]);

  // Stepping controls
  const stepForward = useCallback(() => {
    setCurrentStep((prev) => Math.min(totalSteps, prev + 15));
    soundEngine.playSliderTick();
  }, [totalSteps]);

  const stepBackward = useCallback(() => {
    setCurrentStep((prev) => Math.max(0, prev - 15));
    soundEngine.playSliderTick();
  }, []);

  const togglePlay = useCallback(() => {
    setIsPlaying((prev) => {
      const next = !prev;
      soundEngine.playPing(next ? 'mode' : 'alert');
      return next;
    });
  }, []);

  const play = useCallback(() => setIsPlaying(true), []);
  const pause = useCallback(() => setIsPlaying(false), []);

  const setSpeed = useCallback((s: number) => {
    setSpeedState(s);
    soundEngine.playPing('mode');
  }, []);

  // Animation interval loop
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    const intervalMs = Math.max(40, 200 / speed);
    timerRef.current = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= totalSteps) {
          setIsPlaying(false);
          soundEngine.playPing('success');
          return 0; // Loop or stop
        }
        return prev + 1;
      });
    }, intervalMs);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, speed, totalSteps]);

  return {
    currentStep,
    totalSteps,
    currentTimeString,
    isPlaying,
    speed,
    speeds,
    play,
    pause,
    togglePlay,
    seekToStep,
    setSpeed,
    stepForward,
    stepBackward,
    weatherSnapshot,
    zoneStates,
    currentRecords,
  };
}
