function p = get_scenario_definition(scenario_name)
% GET_SCENARIO_DEFINITION Returns parameter modifiers for target weather scenario
%
% Supported Scenarios:
%   'Normal', 'Hot & Dry', 'Rainy', 'Cloudy', 'Heatwave', 'Water Scarcity'

switch lower(strrep(scenario_name, ' ', ''))
    case {'normal', 'normalsupply'}
        p.name = 'Normal';
        p.temp_offset_c = 0.0;
        p.temp_range_mult = 1.0;
        p.humidity_offset_pct = 0.0;
        p.solar_multiplier = 1.0;
        p.wind_multiplier = 1.0;
        p.rain_probability = 0.0;
        p.rain_intensity_min = 0.0;
        p.rain_intensity_max = 0.0;
        p.rain_dur_min = 0;
        p.rain_dur_max = 0;
        p.water_avail_factor = 1.0;

    case {'hot&dry', 'hotanddry', 'hot_and_dry'}
        p.name = 'Hot & Dry';
        p.temp_offset_c = 5.0;
        p.temp_range_mult = 1.15;
        p.humidity_offset_pct = -20.0;
        p.solar_multiplier = 1.05;
        p.wind_multiplier = 1.30;
        p.rain_probability = 0.0;
        p.rain_intensity_min = 0.0;
        p.rain_intensity_max = 0.0;
        p.rain_dur_min = 0;
        p.rain_dur_max = 0;
        p.water_avail_factor = 1.0;

    case 'rainy'
        p.name = 'Rainy';
        p.temp_offset_c = -4.0;
        p.temp_range_mult = 0.60;
        p.humidity_offset_pct = 18.0;
        p.solar_multiplier = 0.35;
        p.wind_multiplier = 1.10;
        p.rain_probability = 1.0;
        p.rain_intensity_min = 0.05;
        p.rain_intensity_max = 0.45;
        p.rain_dur_min = 45;
        p.rain_dur_max = 150;
        p.water_avail_factor = 1.0;

    case 'cloudy'
        p.name = 'Cloudy';
        p.temp_offset_c = -2.5;
        p.temp_range_mult = 0.70;
        p.humidity_offset_pct = 10.0;
        p.solar_multiplier = 0.40;
        p.wind_multiplier = 0.90;
        p.rain_probability = 0.20;
        p.rain_intensity_min = 0.02;
        p.rain_intensity_max = 0.10;
        p.rain_dur_min = 20;
        p.rain_dur_max = 60;
        p.water_avail_factor = 1.0;

    case 'heatwave'
        p.name = 'Heatwave';
        p.temp_offset_c = 8.0;
        p.temp_range_mult = 1.25;
        p.humidity_offset_pct = -25.0;
        p.solar_multiplier = 1.10;
        p.wind_multiplier = 1.40;
        p.rain_probability = 0.0;
        p.rain_intensity_min = 0.0;
        p.rain_intensity_max = 0.0;
        p.rain_dur_min = 0;
        p.rain_dur_max = 0;
        p.water_avail_factor = 1.0;

    case {'waterscarcity', 'water_scarcity', 'scarcity'}
        p.name = 'Water Scarcity';
        p.temp_offset_c = 1.5;
        p.temp_range_mult = 1.05;
        p.humidity_offset_pct = -5.0;
        p.solar_multiplier = 1.0;
        p.wind_multiplier = 1.05;
        p.rain_probability = 0.0;
        p.rain_intensity_min = 0.0;
        p.rain_intensity_max = 0.0;
        p.rain_dur_min = 0;
        p.rain_dur_max = 0;
        p.water_avail_factor = 0.30; % Acute 70% restriction

    otherwise
        error('Unknown scenario: %s. Supported: Normal, Hot & Dry, Rainy, Cloudy, Heatwave, Water Scarcity', scenario_name);
end
end
