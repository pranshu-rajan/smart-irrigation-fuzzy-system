function fis = build_water_demand_fis()
% BUILD_WATER_DEMAND_FIS Constructs FIS 3: Crop Water Demand Fuzzy Inference System
%
% Inputs:
%   1. etc: Crop Evapotranspiration [0.0, 15.0] mm/day
%   2. crop_water_deficit: Crop Water Deficit [0.0, 15.0] mm/day
%   3. effective_rainfall: Effective Rainfall [0.0, 50.0] mm
%
% Output:
%   1. water_demand: Normalized Water Demand [0.0, 100.0] %

fis = mamfis('Name', 'water_demand', ...
             'AndMethod', 'min', ...
             'OrMethod', 'max', ...
             'ImplicationMethod', 'min', ...
             'AggregationMethod', 'max', ...
             'DefuzzificationMethod', 'centroid');

% Input 1: etc [0, 15]
fis = addInput(fis, [0 15], 'Name', 'etc');
fis = addMF(fis, 'etc', 'trapmf', [0.0 0.0 1.0 2.5],       'Name', 'Very_Low');
fis = addMF(fis, 'etc', 'trimf',  [1.5 3.5 5.5],           'Name', 'Low');
fis = addMF(fis, 'etc', 'trimf',  [4.5 7.0 9.5],           'Name', 'Moderate');
fis = addMF(fis, 'etc', 'trimf',  [8.5 10.5 12.5],         'Name', 'High');
fis = addMF(fis, 'etc', 'trapmf', [11.5 13.0 15.0 15.0],   'Name', 'Very_High');

% Input 2: crop_water_deficit [0, 15]
fis = addInput(fis, [0 15], 'Name', 'crop_water_deficit');
fis = addMF(fis, 'crop_water_deficit', 'trapmf', [0.0 0.0 0.5 2.0],       'Name', 'None');
fis = addMF(fis, 'crop_water_deficit', 'trimf',  [0.8 2.5 5.0],           'Name', 'Low');
fis = addMF(fis, 'crop_water_deficit', 'trimf',  [3.5 6.5 9.5],           'Name', 'Moderate');
fis = addMF(fis, 'crop_water_deficit', 'trimf',  [8.0 10.5 12.5],         'Name', 'High');
fis = addMF(fis, 'crop_water_deficit', 'trapmf', [11.0 13.0 15.0 15.0],   'Name', 'Very_High');

% Input 3: effective_rainfall [0, 50]
fis = addInput(fis, [0 50], 'Name', 'effective_rainfall');
fis = addMF(fis, 'effective_rainfall', 'trapmf', [0.0 0.0 0.3 1.8],       'Name', 'None');
fis = addMF(fis, 'effective_rainfall', 'trimf',  [0.6 2.5 6.0],           'Name', 'Low');
fis = addMF(fis, 'effective_rainfall', 'trimf',  [4.0 9.0 16.0],          'Name', 'Moderate');
fis = addMF(fis, 'effective_rainfall', 'trimf',  [12.0 20.0 32.0],        'Name', 'High');
fis = addMF(fis, 'effective_rainfall', 'trapmf', [24.0 34.0 50.0 50.0],   'Name', 'Very_High');

% Output: water_demand [0, 100]
fis = addOutput(fis, [0 100], 'Name', 'water_demand');
fis = addMF(fis, 'water_demand', 'trapmf', [0.0 0.0 10.0 25.0],      'Name', 'Very_Low');
fis = addMF(fis, 'water_demand', 'trimf',  [15.0 30.0 45.0],         'Name', 'Low');
fis = addMF(fis, 'water_demand', 'trimf',  [35.0 50.0 65.0],         'Name', 'Moderate');
fis = addMF(fis, 'water_demand', 'trimf',  [55.0 70.0 85.0],         'Name', 'High');
fis = addMF(fis, 'water_demand', 'trapmf', [75.0 90.0 100.0 100.0],  'Name', 'Very_High');

% Rules matrix [ETc, Deficit, Rain, Demand, Weight, Conn]
rules = [];

% Layer 1: Heavy / Torrential Rain (Rain in {High(4), Very High(5)})
rules = [rules;
    0 1 5 1 1 1; % vhigh rain, none def -> very_low
    0 2 5 1 1 1; % vhigh rain, low/mod def -> very_low
    0 3 5 1 1 1;
    0 4 5 2 1 1; % vhigh rain, high def -> low
    0 5 5 3 1 1; % vhigh rain, vhigh def -> moderate
    0 1 4 1 1 1; % high rain, none def -> very_low
    0 2 4 2 1 1; % high rain, low def -> low
    0 3 4 2 1 1; % high rain, mod def -> low
    0 4 4 3 1 1; % high rain, high def -> moderate
    0 5 4 4 1 1; % high rain, vhigh def -> high
];

% Layer 2: Moderate Rain Regime (Rain = Moderate(3))
rules = [rules;
    0 1 3 1 1 1; % mod rain, none def -> very_low
    0 2 3 2 1 1; % mod rain, low def -> low
    0 3 3 3 1 1; % mod rain, mod def -> moderate
    0 4 3 4 1 1; % mod rain, high def -> high
    0 5 3 5 1 1; % mod rain, vhigh def -> very_high
];

% Layer 3: Dry Baseline Kernel (Rain in {None(1), Low(2)})
% 5x5 product across ETc (1..5) and Deficit (1..5)
% ETc: 1=VLow, 2=Low, 3=Mod, 4=High, 5=VHigh
% Def: 1=None, 2=Low, 3=Mod, 4=High, 5=VHigh
grid_demand = [
    1 2 3 4 5;  % ETc Very Low -> Demand [VLow, Low, Mod, High, VHigh]
    1 2 3 4 5;  % ETc Low      -> Demand [VLow, Low, Mod, High, VHigh]
    2 3 3 4 5;  % ETc Moderate -> Demand [Low, Mod, Mod, High, VHigh]
    3 3 4 4 5;  % ETc High     -> Demand [Mod, Mod, High, High, VHigh]
    3 4 4 5 5;  % ETc VeryHigh -> Demand [Mod, High, High, VHigh, VHigh]
];

for e = 1:5
    for d = 1:5
        out = grid_demand(e, d);
        for r = [1 2]
            rules = [rules; e d r out 1 1];
        end
    end
end

fis = addRule(fis, rules);
end
