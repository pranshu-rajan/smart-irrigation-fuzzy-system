"""Dynamic meteorological time-series generation engine.

Produces deterministic or stochastic physical weather trajectories across 24-hour,
7-day, or 30-day durations for the 6 agricultural simulation scenarios.
"""

from pathlib import Path
from typing import Optional, Union, List, Dict, Any, Tuple
import pandas as pd
import numpy as np

from config.schemas import SimulationScenario, WeatherParameters
from simulation.scenarios import ScenarioManager, ScenarioParameters


class WeatherEngine:
    """Generates continuous meteorological inputs across simulation timelines."""

    # Baseline calibration derived from Phase 2 empirical EDA
    T_MIN_BASE = 18.00        # °C
    T_MAX_BASE = 34.20        # °C
    T_MEAN_BASE = 25.75       # °C
    T_AMP_BASE = (T_MAX_BASE - T_MIN_BASE) / 2.0  # 8.10 °C

    SOLAR_PEAK_BASE = 915.20  # W/m2
    SUNRISE_HOUR = 5.50       # 05:30
    SUNSET_HOUR = 19.50       # 19:30

    RH_MAX_BASE = 87.50       # % (at pre-dawn min temp)
    RH_MIN_BASE = 42.50       # % (at afternoon max temp)
    RH_MEAN_BASE = 64.44      # %
    # Coupling coefficient: change in RH per °C change in T
    BETA_H = (RH_MAX_BASE - RH_MIN_BASE) / (T_MAX_BASE - T_MIN_BASE)  # ~2.78 %/°C

    WIND_MEAN_BASE = 2.38     # m/s
    WIND_AMP_BASE = 0.90      # m/s

    def __init__(
        self,
        scenario: SimulationScenario = SimulationScenario.NORMAL,
        seed: Optional[int] = None,
    ) -> None:
        """Initialize weather engine with target scenario and optional PRNG seed.

        Args:
            scenario: Preset environmental scenario enum.
            seed: Optional integer seed for deterministic reproducibility.
        """
        self.scenario = scenario
        self.seed = seed
        self.params: ScenarioParameters = ScenarioManager.get_scenario_parameters(scenario)

    def _generate_rainfall_series(
        self,
        total_steps: int,
        timestep_minutes: int,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Generate event-based precipitation trajectory in mm per timestep."""
        rainfall = np.zeros(total_steps, dtype=np.float64)
        if self.params.rain_probability <= 0.0:
            return rainfall

        duration_days = (total_steps * timestep_minutes) / (24 * 60)
        num_days = int(np.ceil(duration_days))

        for day in range(num_days):
            day_start_idx = int((day * 24 * 60) / timestep_minutes)
            day_end_idx = min(total_steps, int(((day + 1) * 24 * 60) / timestep_minutes))

            # Decide if rain occurs on this day
            if rng.uniform(0.0, 1.0) <= self.params.rain_probability:
                # Decide number of events in the day (1 to 3 events)
                num_events = rng.integers(1, 4) if self.scenario == SimulationScenario.RAINY else 1
                for _ in range(num_events):
                    event_duration_min = int(
                        rng.uniform(
                            self.params.rain_duration_min_minutes,
                            self.params.rain_duration_max_minutes,
                        )
                    )
                    event_duration_steps = max(1, event_duration_min // timestep_minutes)

                    # Event start time (prefer daytime afternoon for convection or random)
                    max_start = max(0, (day_end_idx - day_start_idx) - event_duration_steps)
                    if max_start == 0:
                        continue
                    event_start_offset = int(rng.integers(0, max_start))
                    start_idx = day_start_idx + event_start_offset
                    end_idx = min(day_end_idx, start_idx + event_duration_steps)

                    # Intensity (mm per timestep)
                    base_intensity = rng.uniform(
                        self.params.rain_intensity_min_mm_min,
                        self.params.rain_intensity_max_mm_min,
                    ) * timestep_minutes

                    # Triangular/sinusoidal event intensity envelope
                    event_len = end_idx - start_idx
                    if event_len > 0:
                        envelope = np.sin(np.linspace(0, np.pi, event_len))
                        noise = rng.normal(1.0, 0.15, event_len)
                        noise = np.clip(noise, 0.5, 1.5)
                        event_rain = base_intensity * envelope * noise
                        rainfall[start_idx:end_idx] += event_rain

        return np.clip(rainfall, 0.0, 50.0)

    def generate_timeline(
        self,
        duration_hours: int = 24,
        timestep_minutes: int = 1,
        start_time: str = "2026-06-01 00:00:00",
        seed: Optional[int] = None,
    ) -> pd.DataFrame:
        """Synthesize continuous, physics-consistent meteorological trajectory.

        Args:
            duration_hours: Total length of simulation in hours (24, 168 for 7-day, 720 for 30-day).
            timestep_minutes: Resolution in minutes (default 1).
            start_time: ISO-8601 initial timestamp.
            seed: Optional seed override.

        Returns:
            pd.DataFrame: Validated time-series with columns:
                [timestamp, temperature, humidity, solar_radiation, wind_speed,
                 rainfall, scenario, water_availability_factor]
        """
        active_seed = seed if seed is not None else self.seed
        rng = np.random.default_rng(active_seed)

        total_steps = (duration_hours * 60) // timestep_minutes
        timestamps = pd.date_range(
            start=pd.to_datetime(start_time),
            periods=total_steps,
            freq=f"{timestep_minutes}min",
        )

        # Elapsed hours as continuous float
        step_minutes = np.arange(total_steps) * timestep_minutes
        step_hours = step_minutes / 60.0
        hour_of_day = step_hours % 24.0
        day_index = (step_hours // 24.0).astype(int)

        # Multi-day synoptic weather drift (synoptic front variance: +/- 1.5°C day-to-day)
        unique_days = int(np.ceil(duration_hours / 24.0))
        if unique_days > 1:
            # Generate random walk with mean reversion for multi-day synoptic drift
            synoptic_drift = np.zeros(unique_days)
            for d in range(1, unique_days):
                synoptic_drift[d] = 0.7 * synoptic_drift[d - 1] + rng.normal(0.0, 1.2)
            synoptic_drift = np.clip(synoptic_drift, -3.5, 3.5)
            step_synoptic_drift = synoptic_drift[day_index]
        else:
            step_synoptic_drift = np.zeros(total_steps)

        # -------------------------------------------------------------
        # 1. Temperature Model (°C)
        # -------------------------------------------------------------
        # Peak at ~13:45, Min at ~04:30
        # Phase shift: t_min=4.5h => (hour - 4.5)/24 * 2pi - pi/2
        t_phase = (2.0 * np.pi * (hour_of_day - 4.5) / 24.0) - (np.pi / 2.0)
        temp_cycle = np.sin(t_phase)

        # Slight asymmetry: daytime warming is steeper than nighttime cooling
        temp_pos = np.maximum(0.0, temp_cycle)
        temp_neg = np.maximum(0.0, -temp_cycle)
        temp_asym = (temp_pos ** 0.95) - (temp_neg ** 1.05)

        t_amp = self.T_AMP_BASE * self.params.temperature_range_multiplier
        t_mean = self.T_MEAN_BASE + self.params.temperature_offset_c
        t_noise = rng.normal(0.0, 0.15, total_steps)  # Bounded stochastic micro-fluctuation

        temperature = t_mean + (t_amp * temp_asym) + step_synoptic_drift + t_noise
        temperature = np.clip(temperature, -20.0, 60.0)

        # -------------------------------------------------------------
        # 2. Solar Radiation Model (W/m2)
        # -------------------------------------------------------------
        # Clear-sky solar arc between sunrise (05:30) and sunset (19:30)
        daylight_duration = self.SUNSET_HOUR - self.SUNRISE_HOUR  # 14 hours
        in_daylight = (hour_of_day >= self.SUNRISE_HOUR) & (hour_of_day <= self.SUNSET_HOUR)
        solar_fraction = np.zeros(total_steps, dtype=np.float64)

        daylight_hours = hour_of_day[in_daylight] - self.SUNRISE_HOUR
        solar_fraction[in_daylight] = np.sin(np.pi * (daylight_hours / daylight_duration))
        solar_fraction = np.maximum(0.0, solar_fraction)

        # Add slight cloudiness noise during daylight
        solar_noise = rng.normal(1.0, 0.03, total_steps)
        solar_noise = np.clip(solar_noise, 0.85, 1.15)

        solar_radiation = (
            self.SOLAR_PEAK_BASE
            * solar_fraction
            * self.params.solar_multiplier
            * solar_noise
        )
        # Strict physical enforcement: zero at night, non-negative
        solar_radiation = np.where(in_daylight, np.maximum(0.0, solar_radiation), 0.0)
        solar_radiation = np.clip(solar_radiation, 0.0, 1500.0)

        # -------------------------------------------------------------
        # 3. Relative Humidity Model (%)
        # -------------------------------------------------------------
        # Inverse psychrometric coupling with temperature
        t_deviation = temperature - t_mean
        rh_baseline = self.RH_MEAN_BASE + self.params.humidity_offset_pct
        rh_noise = rng.normal(0.0, 0.6, total_steps)

        humidity = rh_baseline - (self.BETA_H * t_deviation) + rh_noise
        # Under rainy / cloudy conditions, elevate humidity further during precipitation
        humidity = np.clip(humidity, 0.0, 100.0)

        # -------------------------------------------------------------
        # 4. Wind Speed Model (m/s)
        # -------------------------------------------------------------
        # Peak convective afternoon sea-breeze (~14:00), minimum late night (~02:00)
        wind_phase = 2.0 * np.pi * (hour_of_day - 8.0) / 24.0
        wind_cycle = np.sin(wind_phase)
        wind_noise = rng.normal(0.0, 0.20, total_steps)

        wind_speed = (
            (self.WIND_MEAN_BASE + (self.WIND_AMP_BASE * wind_cycle) + wind_noise)
            * self.params.wind_multiplier
        )
        wind_speed = np.maximum(0.2, wind_speed)  # Non-negative, minimum air draft
        wind_speed = np.clip(wind_speed, 0.0, 50.0)

        # -------------------------------------------------------------
        # 5. Event-Based Rainfall (mm/step)
        # -------------------------------------------------------------
        rainfall = self._generate_rainfall_series(total_steps, timestep_minutes, rng)

        # When raining, bump relative humidity toward saturation (90-98%) and suppress solar
        is_raining = rainfall > 0.0
        if np.any(is_raining):
            humidity[is_raining] = np.maximum(humidity[is_raining], rng.uniform(88.0, 97.0, np.sum(is_raining)))
            humidity = np.clip(humidity, 0.0, 100.0)
            solar_radiation[is_raining] *= rng.uniform(0.15, 0.35, np.sum(is_raining))

        # Assemble canonical output DataFrame
        df = pd.DataFrame({
            "timestamp": timestamps,
            "temperature": np.round(temperature, 2),
            "humidity": np.round(humidity, 2),
            "solar_radiation": np.round(solar_radiation, 2),
            "wind_speed": np.round(wind_speed, 2),
            "rainfall": np.round(rainfall, 3),
            "scenario": self.scenario.value,
            "water_availability_factor": self.params.water_availability_factor,
        })

        return df
