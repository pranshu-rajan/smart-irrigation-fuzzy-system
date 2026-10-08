classdef WeatherEngine < handle
% WEATHERENGINE Generates dynamic meteorological trajectories matching Python engine
%
% Implements diurnal curves for:
%   Temperature (T), Relative Humidity (RH), Solar Radiation (Rs),
%   Wind Speed (u2), Precipitation (P)

    properties
        scenario_name
        params
        seed
    end

    properties (Constant)
        T_MIN_BASE = 18.00;
        T_MAX_BASE = 34.20;
        T_MEAN_BASE = 25.75;
        T_AMP_BASE = (34.20 - 18.00) / 2.0; % 8.10 °C

        SOLAR_PEAK_BASE = 915.20; % W/m²
        SUNRISE_HOUR = 5.50;      % 05:30
        SUNSET_HOUR = 19.50;      % 19:30

        RH_MAX_BASE = 87.50;
        RH_MIN_BASE = 42.50;
        RH_MEAN_BASE = 64.44;
        BETA_H = (87.50 - 42.50) / (34.20 - 18.00); % 2.78 %/°C

        WIND_MEAN_BASE = 2.38;
        WIND_AMP_BASE = 0.90;
    end

    methods
        function obj = WeatherEngine(scenario_name, seed)
            if nargin < 1 || isempty(scenario_name)
                scenario_name = 'Normal';
            end
            if nargin < 2
                seed = 42;
            end
            obj.scenario_name = scenario_name;
            obj.params = weather.get_scenario_definition(scenario_name);
            obj.seed = seed;
        end

        function timeline = generate_timeline(obj, duration_hours, dt_minutes)
            if nargin < 2 || isempty(duration_hours)
                duration_hours = 24;
            end
            if nargin < 3 || isempty(dt_minutes)
                dt_minutes = 1;
            end

            total_steps = floor((duration_hours * 60) / dt_minutes);
            step_minutes = (0:total_steps-1)' * dt_minutes;
            step_hours = step_minutes / 60.0;
            hour_of_day = mod(step_hours, 24.0);

            % Set deterministic PRNG
            if ~isempty(obj.seed)
                rng(obj.seed, 'twister');
            end

            % 1. Temperature model
            t_phase = (2.0 * pi * (hour_of_day - 4.5) / 24.0) - (pi / 2.0);
            temp_cycle = sin(t_phase);
            temp_pos = max(0.0, temp_cycle);
            temp_neg = max(0.0, -temp_cycle);
            temp_asym = (temp_pos.^0.95) - (temp_neg.^1.05);

            t_amp = obj.T_AMP_BASE * obj.params.temp_range_mult;
            t_mean = obj.T_MEAN_BASE + obj.params.temp_offset_c;
            t_noise = randn(total_steps, 1) * 0.15;
            temperature = t_mean + (t_amp .* temp_asym) + t_noise;
            temperature = max(-20.0, min(60.0, temperature));

            % 2. Solar radiation model
            daylight_duration = obj.SUNSET_HOUR - obj.SUNRISE_HOUR;
            in_daylight = (hour_of_day >= obj.SUNRISE_HOUR) & (hour_of_day <= obj.SUNSET_HOUR);
            solar_fraction = zeros(total_steps, 1);
            daylight_hours = hour_of_day(in_daylight) - obj.SUNRISE_HOUR;
            solar_fraction(in_daylight) = max(0.0, sin(pi * (daylight_hours / daylight_duration)));

            solar_noise = max(0.85, min(1.15, 1.0 + randn(total_steps, 1) * 0.03));
            solar_radiation = obj.SOLAR_PEAK_BASE * solar_fraction * obj.params.solar_multiplier .* solar_noise;
            solar_radiation(~in_daylight) = 0.0;
            solar_radiation = max(0.0, min(1500.0, solar_radiation));

            % 3. Relative humidity model
            t_dev = temperature - t_mean;
            rh_base = obj.RH_MEAN_BASE + obj.params.humidity_offset_pct;
            rh_noise = randn(total_steps, 1) * 0.60;
            humidity = rh_base - (obj.BETA_H * t_dev) + rh_noise;
            humidity = max(0.0, min(100.0, humidity));

            % 4. Wind speed model
            wind_phase = 2.0 * pi * (hour_of_day - 8.0) / 24.0;
            wind_cycle = sin(wind_phase);
            wind_noise = randn(total_steps, 1) * 0.20;
            wind_speed = (obj.WIND_MEAN_BASE + (obj.WIND_AMP_BASE * wind_cycle) + wind_noise) * obj.params.wind_multiplier;
            wind_speed = max(0.2, min(50.0, wind_speed));

            % 5. Rainfall model
            rainfall = zeros(total_steps, 1);
            if obj.params.rain_probability > 0
                if rand() <= obj.params.rain_probability
                    % Generate event in daytime
                    event_dur_min = obj.params.rain_dur_min + rand() * (obj.params.rain_dur_max - obj.params.rain_dur_min);
                    event_steps = max(1, floor(event_dur_min / dt_minutes));
                    start_step = floor(total_steps * 0.35); % Afternoon shower
                    end_step = min(total_steps, start_step + event_steps);
                    len_ev = end_step - start_step;
                    if len_ev > 0
                        env = sin(linspace(0, pi, len_ev))';
                        intensity = (obj.params.rain_intensity_min + rand() * (obj.params.rain_intensity_max - obj.params.rain_intensity_min)) * dt_minutes;
                        rainfall(start_step:end_step-1) = intensity * env;
                    end
                end
            end

            % Cloud & humidity adjustments when raining
            is_rain = rainfall > 0;
            if any(is_rain)
                humidity(is_rain) = max(humidity(is_rain), 92.0);
                solar_radiation(is_rain) = solar_radiation(is_rain) * 0.25;
            end

            % Pack results into timetable or struct
            timeline.minutes = step_minutes;
            timeline.hours = step_hours;
            timeline.temperature = round(temperature, 2);
            timeline.humidity = round(humidity, 2);
            timeline.solar_radiation = round(solar_radiation, 2);
            timeline.wind_speed = round(wind_speed, 2);
            timeline.rainfall = round(rainfall, 3);
            timeline.scenario = obj.scenario_name;
            timeline.water_availability_factor = obj.params.water_avail_factor;
            timeline.total_steps = total_steps;
        end
    end
end
