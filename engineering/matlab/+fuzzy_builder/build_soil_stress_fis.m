function fis = build_soil_stress_fis()
% BUILD_SOIL_STRESS_FIS Constructs FIS 1: Soil Stress Fuzzy Inference System
%
% Inputs:
%   1. rsm: Relative Soil Moisture [0.0, 1.0]
%   2. moisture_error: Moisture Tracking Error [-30.0, 30.0] %
%
% Output:
%   1. soil_stress: Crop Root-Zone Soil Stress [0.0, 100.0] %
%
% Rule Base: 25 rules (5x5 Cartesian product)

fis = mamfis('Name', 'soil_stress', ...
             'AndMethod', 'min', ...
             'OrMethod', 'max', ...
             'ImplicationMethod', 'min', ...
             'AggregationMethod', 'max', ...
             'DefuzzificationMethod', 'centroid');

% Input 1: rsm [0, 1]
fis = addInput(fis, [0 1], 'Name', 'rsm');
fis = addMF(fis, 'rsm', 'trapmf', [0.0 0.0 0.15 0.30], 'Name', 'Very_Dry');
fis = addMF(fis, 'rsm', 'trimf',  [0.20 0.35 0.50],      'Name', 'Dry');
fis = addMF(fis, 'rsm', 'trimf',  [0.40 0.55 0.70],      'Name', 'Adequate');
fis = addMF(fis, 'rsm', 'trimf',  [0.60 0.75 0.85],      'Name', 'Wet');
fis = addMF(fis, 'rsm', 'trapmf', [0.75 0.85 1.0 1.0],  'Name', 'Very_Wet');

% Input 2: moisture_error [-30, 30]
fis = addInput(fis, [-30 30], 'Name', 'moisture_error');
fis = addMF(fis, 'moisture_error', 'trapmf', [-30.0 -30.0 -20.0 -10.0], 'Name', 'Large_Negative');
fis = addMF(fis, 'moisture_error', 'trimf',  [-15.0 -7.5 0.0],          'Name', 'Negative');
fis = addMF(fis, 'moisture_error', 'trimf',  [-5.0 0.0 5.0],            'Name', 'Zero');
fis = addMF(fis, 'moisture_error', 'trimf',  [0.0 7.5 15.0],            'Name', 'Positive');
fis = addMF(fis, 'moisture_error', 'trapmf', [10.0 20.0 30.0 30.0],     'Name', 'Large_Positive');

% Output: soil_stress [0, 100]
fis = addOutput(fis, [0 100], 'Name', 'soil_stress');
fis = addMF(fis, 'soil_stress', 'trapmf', [0.0 0.0 15.0 35.0],       'Name', 'Low');
fis = addMF(fis, 'soil_stress', 'trimf',  [25.0 45.0 65.0],          'Name', 'Moderate');
fis = addMF(fis, 'soil_stress', 'trimf',  [55.0 75.0 85.0],          'Name', 'High');
fis = addMF(fis, 'soil_stress', 'trapmf', [75.0 85.0 100.0 100.0],   'Name', 'Very_High');

% Rules matrix [In1, In2, Out, Weight, Connection]
% In1 (rsm): 1=Very Dry, 2=Dry, 3=Adequate, 4=Wet, 5=Very Wet
% In2 (error): 1=Large Neg, 2=Neg, 3=Zero, 4=Pos, 5=Large Pos
% Out (stress): 1=Low, 2=Moderate, 3=High, 4=Very High
ruleList = [
    1 5 4 1 1;
    1 4 4 1 1;
    1 3 3 1 1;
    1 2 3 1 1;
    1 1 2 1 1;
    2 5 4 1 1;
    2 4 3 1 1;
    2 3 2 1 1;
    2 2 1 1 1;
    2 1 1 1 1;
    3 5 3 1 1;
    3 4 2 1 1;
    3 3 1 1 1;
    3 2 1 1 1;
    3 1 1 1 1;
    4 5 2 1 1;
    4 4 1 1 1;
    4 3 1 1 1;
    4 2 1 1 1;
    4 1 1 1 1;
    5 5 1 1 1;
    5 4 1 1 1;
    5 3 1 1 1;
    5 2 1 1 1;
    5 1 1 1 1
];

fis = addRule(fis, ruleList);
end
