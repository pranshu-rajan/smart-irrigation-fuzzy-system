function fis = build_weather_stress_fis()
% BUILD_WEATHER_STRESS_FIS Constructs FIS 2: Weather Stress Fuzzy Inference System
%
% Inputs:
%   1. temperature: Ambient Temperature [10.0, 50.0] °C
%   2. humidity: Relative Humidity [0.0, 100.0] %
%   3. solar_radiation: Solar Radiation [0.0, 1200.0] W/m²
%   4. wind_speed: Wind Speed at 2m [0.0, 15.0] m/s
%   5. rainfall: Precipitation [0.0, 50.0] mm/step
%
% Output:
%   1. weather_stress: Atmospheric Weather Stress [0.0, 100.0] %

fis = mamfis('Name', 'weather_stress', ...
             'AndMethod', 'min', ...
             'OrMethod', 'max', ...
             'ImplicationMethod', 'min', ...
             'AggregationMethod', 'max', ...
             'DefuzzificationMethod', 'centroid');

% Input 1: temperature [10, 50]
fis = addInput(fis, [10 50], 'Name', 'temperature');
fis = addMF(fis, 'temperature', 'trapmf', [10.0 10.0 18.0 24.0], 'Name', 'Low');
fis = addMF(fis, 'temperature', 'trimf',  [20.0 28.0 34.0],      'Name', 'Moderate');
fis = addMF(fis, 'temperature', 'trimf',  [30.0 38.0 44.0],      'Name', 'High');
fis = addMF(fis, 'temperature', 'trapmf', [40.0 45.0 50.0 50.0], 'Name', 'Very_High');

% Input 2: humidity [0, 100]
fis = addInput(fis, [0 100], 'Name', 'humidity');
fis = addMF(fis, 'humidity', 'trapmf', [0.0 0.0 15.0 30.0],     'Name', 'Very_Low');
fis = addMF(fis, 'humidity', 'trimf',  [20.0 35.0 50.0],         'Name', 'Low');
fis = addMF(fis, 'humidity', 'trimf',  [40.0 55.0 70.0],         'Name', 'Moderate');
fis = addMF(fis, 'humidity', 'trimf',  [60.0 75.0 85.0],         'Name', 'High');
fis = addMF(fis, 'humidity', 'trapmf', [75.0 90.0 100.0 100.0], 'Name', 'Very_High');

% Input 3: solar_radiation [0, 1200]
fis = addInput(fis, [0 1200], 'Name', 'solar_radiation');
fis = addMF(fis, 'solar_radiation', 'trapmf', [0.0 0.0 150.0 350.0],       'Name', 'Low');
fis = addMF(fis, 'solar_radiation', 'trimf',  [250.0 500.0 750.0],         'Name', 'Moderate');
fis = addMF(fis, 'solar_radiation', 'trimf',  [650.0 850.0 1000.0],        'Name', 'High');
fis = addMF(fis, 'solar_radiation', 'trapmf', [900.0 1050.0 1200.0 1200.0], 'Name', 'Very_High');

% Input 4: wind_speed [0, 15]
fis = addInput(fis, [0 15], 'Name', 'wind_speed');
fis = addMF(fis, 'wind_speed', 'trapmf', [0.0 0.0 1.0 2.5],        'Name', 'Calm');
fis = addMF(fis, 'wind_speed', 'trimf',  [1.5 3.5 5.5],            'Name', 'Low');
fis = addMF(fis, 'wind_speed', 'trimf',  [4.5 7.0 9.5],            'Name', 'Moderate');
fis = addMF(fis, 'wind_speed', 'trimf',  [8.0 10.5 12.5],          'Name', 'High');
fis = addMF(fis, 'wind_speed', 'trapmf', [11.0 13.0 15.0 15.0],    'Name', 'Very_High');

% Input 5: rainfall [0, 50]
fis = addInput(fis, [0 50], 'Name', 'rainfall');
fis = addMF(fis, 'rainfall', 'trapmf', [0.0 0.0 0.2 1.5],       'Name', 'None');
fis = addMF(fis, 'rainfall', 'trimf',  [0.4 2.0 4.5],           'Name', 'Light');
fis = addMF(fis, 'rainfall', 'trimf',  [3.0 7.0 14.0],          'Name', 'Moderate');
fis = addMF(fis, 'rainfall', 'trimf',  [10.0 18.0 28.0],        'Name', 'Heavy');
fis = addMF(fis, 'rainfall', 'trapmf', [22.0 32.0 50.0 50.0],   'Name', 'Very_Heavy');

% Output: weather_stress [0, 100]
fis = addOutput(fis, [0 100], 'Name', 'weather_stress');
fis = addMF(fis, 'weather_stress', 'trapmf', [0.0 0.0 15.0 35.0],       'Name', 'Low');
fis = addMF(fis, 'weather_stress', 'trimf',  [25.0 45.0 65.0],          'Name', 'Moderate');
fis = addMF(fis, 'weather_stress', 'trimf',  [55.0 75.0 85.0],          'Name', 'High');
fis = addMF(fis, 'weather_stress', 'trapmf', [75.0 85.0 100.0 100.0],   'Name', 'Very_High');

% Rules format: [Temp, Humidity, Solar, Wind, Rain, Out, Weight, Conn]
rules = [];

% Layer 1: Precipitation suppression
rules = [rules;
    0 0 0 0 4 1 1 1; % Heavy rain -> Low
    0 0 0 0 5 1 1 1; % Very Heavy rain -> Low
    0 3 0 0 3 1 1 1; % Mod rain, mod/high/vhigh hum -> Low
    0 4 0 0 3 1 1 1;
    0 5 0 0 3 1 1 1;
    0 1 0 0 3 2 1 1; % Mod rain, vlow/low hum -> Moderate
    0 2 0 0 3 2 1 1;
    0 4 0 0 2 1 1 1; % Light rain, high/vhigh hum -> Low
    0 5 0 0 2 1 1 1;
    2 3 0 0 2 2 1 1; % Light rain, mod temp, mod hum -> Moderate
    3 1 0 0 2 3 1 1; % Light rain, high/vhigh temp, vlow/low hum -> High
    3 2 0 0 2 3 1 1;
    4 1 0 0 2 3 1 1;
    4 2 0 0 2 3 1 1;
];

% Layer 2: VPD Baseline Kernel (Rain in {None(1), Light(2)})
vpd = [
    4 1 4; 4 2 4; 4 3 3; 4 4 2; 4 5 1; % Very High Temp
    3 1 4; 3 2 3; 3 3 2; 3 4 1; 3 5 1; % High Temp
    2 1 3; 2 2 2; 2 3 2; 2 4 1; 2 5 1; % Mod Temp
    1 1 2; 1 2 1; 1 3 1; 1 4 1; 1 5 1; % Low Temp
];
for i = 1:size(vpd, 1)
    t = vpd(i, 1);
    h = vpd(i, 2);
    out = vpd(i, 3);
    rules = [rules; t h 0 0 1 out 1 1; t h 0 0 2 out 1 1];
end

% Layer 3: Radiative Solar Forcing Modulation (Rain = None(1))
% Rule 27: solar vhigh(4), hum vlow/low(1,2) -> High(3)
rules = [rules;
    0 1 4 0 1 3 1 1;
    0 2 4 0 1 3 1 1;
];
% Rule 28: solar vhigh(4), temp high/vhigh(3,4), hum vlow/low/mod(1,2,3) -> Very High(4)
for t = [3 4]
    for h = [1 2 3]
        rules = [rules; t h 4 0 1 4 1 1];
    end
end
% Rule 29: solar high(3), temp high/vhigh(3,4), hum vlow/low(1,2) -> High(3)
for t = [3 4]
    for h = [1 2]
        rules = [rules; t h 3 0 1 3 1 1];
    end
end

% Layer 4: Advective Wind Modulation (Rain = None(1))
% Rule 30: wind vhigh(5), hum vlow/low(1,2), temp high/vhigh(3,4) -> Very High(4)
for t = [3 4]
    for h = [1 2]
        rules = [rules; t h 0 5 1 4 1 1];
    end
end
% Rule 31: wind high/vhigh(4,5), hum vlow/low(1,2) -> High(3)
for w = [4 5]
    for h = [1 2]
        rules = [rules; 0 h 0 w 1 3 1 1];
    end
end
% Rule 32: wind high(4), temp high/vhigh(3,4), solar high/vhigh(3,4) -> Very High(4)
for t = [3 4]
    for s = [3 4]
        rules = [rules; t 0 s 4 1 4 1 1];
    end
end

% Layer 5: Nocturnal / Calm Baselines
% Rule 33: solar low(1), wind calm/low(1,2), temp low/mod(1,2) -> Low(1)
for t = [1 2]
    for w = [1 2]
        rules = [rules; t 0 1 w 0 1 1 1];
    end
end
% Rule 34: humidity vhigh(5) -> Low(1)
rules = [rules; 0 5 0 0 0 1 1 1];

fis = addRule(fis, rules);
end
