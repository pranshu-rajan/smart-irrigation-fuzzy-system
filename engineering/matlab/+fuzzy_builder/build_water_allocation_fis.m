function fis = build_water_allocation_fis()
% BUILD_WATER_ALLOCATION_FIS Constructs FIS 5: Supervisory Water Allocation FIS
%
% Inputs:
%   1. available_water: Available Shared Reservoir Storage [0.0, 100.0] %
%   2. zone_demand: Zone Requested Irrigation Demand [0.0, 100.0] %
%   3. zone_stress: Zone Crop Physiological Stress [0.0, 100.0] %
%   4. zone_priority: Economic & Agronomic Priority Weight [0.0, 100.0] %
%
% Output:
%   1. zone_allocation: Raw Allocation Factor [0.0, 100.0] %

fis = mamfis('Name', 'water_allocation', ...
             'AndMethod', 'min', ...
             'OrMethod', 'max', ...
             'ImplicationMethod', 'min', ...
             'AggregationMethod', 'max', ...
             'DefuzzificationMethod', 'centroid');

% Input 1: available_water [0, 100]
fis = addInput(fis, [0 100], 'Name', 'available_water');
fis = addMF(fis, 'available_water', 'trapmf', [0.0 0.0 10.0 25.0],      'Name', 'Very_Low');
fis = addMF(fis, 'available_water', 'trimf',  [15.0 30.0 45.0],         'Name', 'Low');
fis = addMF(fis, 'available_water', 'trimf',  [35.0 50.0 65.0],         'Name', 'Moderate');
fis = addMF(fis, 'available_water', 'trimf',  [55.0 70.0 85.0],         'Name', 'High');
fis = addMF(fis, 'available_water', 'trapmf', [75.0 90.0 100.0 100.0],  'Name', 'Very_High');

% Input 2: zone_demand [0, 100]
fis = addInput(fis, [0 100], 'Name', 'zone_demand');
fis = addMF(fis, 'zone_demand', 'trapmf', [0.0 0.0 10.0 25.0],      'Name', 'Very_Low');
fis = addMF(fis, 'zone_demand', 'trimf',  [15.0 30.0 45.0],         'Name', 'Low');
fis = addMF(fis, 'zone_demand', 'trimf',  [35.0 50.0 65.0],         'Name', 'Moderate');
fis = addMF(fis, 'zone_demand', 'trimf',  [55.0 70.0 85.0],         'Name', 'High');
fis = addMF(fis, 'zone_demand', 'trapmf', [75.0 90.0 100.0 100.0],  'Name', 'Very_High');

% Input 3: zone_stress [0, 100]
fis = addInput(fis, [0 100], 'Name', 'zone_stress');
fis = addMF(fis, 'zone_stress', 'trapmf', [0.0 0.0 15.0 35.0],       'Name', 'Low');
fis = addMF(fis, 'zone_stress', 'trimf',  [25.0 45.0 65.0],          'Name', 'Moderate');
fis = addMF(fis, 'zone_stress', 'trimf',  [55.0 75.0 85.0],          'Name', 'High');
fis = addMF(fis, 'zone_stress', 'trapmf', [75.0 85.0 100.0 100.0],   'Name', 'Very_High');

% Input 4: zone_priority [0, 100]
fis = addInput(fis, [0 100], 'Name', 'zone_priority');
fis = addMF(fis, 'zone_priority', 'trapmf', [0.0 0.0 15.0 35.0],       'Name', 'Low');
fis = addMF(fis, 'zone_priority', 'trimf',  [25.0 45.0 65.0],          'Name', 'Medium');
fis = addMF(fis, 'zone_priority', 'trimf',  [55.0 75.0 85.0],          'Name', 'High');
fis = addMF(fis, 'zone_priority', 'trapmf', [75.0 85.0 100.0 100.0],   'Name', 'Critical');

% Output: zone_allocation [0, 100]
fis = addOutput(fis, [0 100], 'Name', 'zone_allocation');
fis = addMF(fis, 'zone_allocation', 'trapmf', [0.0 0.0 5.0 15.0],      'Name', 'None');
fis = addMF(fis, 'zone_allocation', 'trimf',  [10.0 25.0 40.0],        'Name', 'Low');
fis = addMF(fis, 'zone_allocation', 'trimf',  [30.0 50.0 70.0],        'Name', 'Moderate');
fis = addMF(fis, 'zone_allocation', 'trimf',  [60.0 75.0 90.0],        'Name', 'High');
fis = addMF(fis, 'zone_allocation', 'trapmf', [80.0 90.0 100.0 100.0], 'Name', 'Maximum');

% Rules matrix [AvailableWater, ZoneDemand, ZoneStress, ZonePriority, ZoneAlloc, Weight, Conn]
rules = [];

% Layer 1: Severe Scarcity & Zero-Demand Safety
% R1: demand very_low(1) -> None(1)
rules = [rules; 0 1 0 0 1 1 1];
% R2: water very_low(1), priority low/med(1,2) -> None(1)
rules = [rules; 1 0 0 1 1 1 1; 1 0 0 2 1 1 1];
% R3: water very_low(1), stress low/mod(1,2) -> None(1)
rules = [rules; 1 0 1 0 1 1 1; 1 0 2 0 1 1 1];
% R4: water very_low(1), stress high/vhigh(3,4), priority high/critical(3,4) -> Low(2)
for s = [3 4]
    for p = [3 4]
        rules = [rules; 1 0 s p 2 1 1];
    end
end
% R5: water very_low(1), demand high/vhigh(4,5), priority low(1) -> None(1)
rules = [rules; 1 4 0 1 1 1 1; 1 5 0 1 1 1 1];

% Layer 2: Abundant Supply Satisfaction
% R6: water high/vhigh(4,5), demand low(2) -> Max(5)
rules = [rules; 4 2 0 0 5 1 1; 5 2 0 0 5 1 1];
% R7: water high/vhigh(4,5), demand mod(3) -> Max(5)
rules = [rules; 4 3 0 0 5 1 1; 5 3 0 0 5 1 1];
% R8: water high/vhigh(4,5), demand high(4) -> Max(5)
rules = [rules; 4 4 0 0 5 1 1; 5 4 0 0 5 1 1];
% R9: water high/vhigh(4,5), demand vhigh(5) -> Max(5)
rules = [rules; 4 5 0 0 5 1 1; 5 5 0 0 5 1 1];
% R10: water vhigh(5), priority high/critical(3,4) -> Max(5)
rules = [rules; 5 0 0 3 5 1 1; 5 0 0 4 5 1 1];
% R11: water high(4), demand mod/high/vhigh(3,4,5), stress high/vhigh(3,4) -> Max(5)
for d = [3 4 5]
    for s = [3 4]
        rules = [rules; 4 d s 0 5 1 1];
    end
end

% Layer 3: Moderate Supply Balancing (Water = Moderate(3))
rules = [rules;
    3 2 0 0 2 1 1; % R12: demand low -> Low(2)
    3 3 1 0 3 1 1; % R13: demand mod, stress low/mod -> Mod(3)
    3 3 2 0 3 1 1;
    3 3 3 0 4 1 1; % R14: demand mod, stress high/vhigh -> High(4)
    3 3 4 0 4 1 1;
];
% R15: water mod(3), demand high/vhigh(4,5), priority high/critical(3,4) -> High(4)
for d = [4 5]
    for p = [3 4]
        rules = [rules; 3 d 0 p 4 1 1];
    end
end
% R16: water mod(3), demand high/vhigh(4,5), priority low(1) -> Mod(3)
rules = [rules; 3 4 0 1 3 1 1; 3 5 0 1 3 1 1];
% R17: water mod(3), demand high/vhigh(4,5), stress vhigh(4), priority high/critical(3,4) -> Max(5)
for d = [4 5]
    for p = [3 4]
        rules = [rules; 3 d 4 p 5 1 1];
    end
end
% R18: water mod(3), demand high(4), stress low/mod(1,2), priority low/med(1,2) -> Low(2)
for s = [1 2]
    for p = [1 2]
        rules = [rules; 3 4 s p 2 1 1];
    end
end

% Layer 4: Low Supply & Drought Rationing (Water = Low(2))
% R19: water low(2), demand low/mod(2,3), priority low(1) -> None(1)
rules = [rules; 2 2 0 1 1 1 1; 2 3 0 1 1 1 1];
% R20: water low(2), demand low/mod(2,3), priority med/high(2,3) -> Low(2)
for d = [2 3]
    for p = [2 3]
        rules = [rules; 2 d 0 p 2 1 1];
    end
end
% R21: water low(2), demand high/vhigh(4,5), priority low(1) -> None(1)
rules = [rules; 2 4 0 1 1 1 1; 2 5 0 1 1 1 1];
% R22: water low(2), demand high/vhigh(4,5), priority med(2) -> Low(2)
rules = [rules; 2 4 0 2 2 1 1; 2 5 0 2 2 1 1];
% R23: water low(2), demand high/vhigh(4,5), priority high/critical(3,4), stress low/mod(1,2) -> Mod(3)
for d = [4 5]
    for p = [3 4]
        for s = [1 2]
            rules = [rules; 2 d s p 3 1 1];
        end
    end
end
% R24: water low(2), demand high/vhigh(4,5), priority high/critical(3,4), stress high/vhigh(3,4) -> High(4)
for d = [4 5]
    for p = [3 4]
        for s = [3 4]
            rules = [rules; 2 d s p 4 1 1];
        end
    end
end
% R25: water low(2), stress low(1) -> None(1)
rules = [rules; 2 0 1 0 1 1 1];
% R26: water low(2), stress vhigh(4), priority critical(4) -> High(4)
rules = [rules; 2 0 4 4 4 1 1];

% Layer 5: Priority & Stress Cross-Modulation
% R27: priority critical(4), stress high/vhigh(3,4), water mod/high/vhigh(3,4,5) -> Max(5)
for s = [3 4]
    for w = [3 4 5]
        rules = [rules; w 0 s 4 5 1 1];
    end
end
% R28: priority low(1), water vlow/low(1,2) -> None(1)
rules = [rules; 1 0 0 1 1 1 1; 2 0 0 1 1 1 1];
% R29: demand vhigh(5), stress low(1), water low/mod(2,3) -> Low(2)
rules = [rules; 2 5 1 0 2 1 1; 3 5 1 0 2 1 1];
% R30: demand mod/high(3,4), stress high/vhigh(3,4), water high/vhigh(4,5) -> Max(5)
for d = [3 4]
    for s = [3 4]
        for w = [4 5]
            rules = [rules; w d s 0 5 1 1];
        end
    end
end
% R31: water vhigh(5), priority high/critical(3,4), demand mod/high/vhigh(3,4,5) -> Max(5)
for p = [3 4]
    for d = [3 4 5]
        rules = [rules; 5 d 0 p 5 1 1];
    end
end
% R32: stress vhigh(4), demand high/vhigh(4,5), priority high/critical(3,4), water low/mod(2,3) -> High(4)
for d = [4 5]
    for p = [3 4]
        for w = [2 3]
            rules = [rules; w d 4 p 4 1 1];
        end
    end
end

fis = addRule(fis, rules);
end
