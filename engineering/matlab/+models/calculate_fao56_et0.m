function et0 = calculate_fao56_et0(T, RH, Rs, u2, elevation_m)
% CALCULATE_FAO56_ET0 Reference Evapotranspiration by FAO-56 Penman-Monteith
%
% Inputs:
%   T: Mean air temperature at 2m [°C]
%   RH: Relative humidity [0, 100] %
%   Rs: Solar radiation [W/m²]
%   u2: Wind speed at 2m [m/s]
%   elevation_m: Elevation above sea level [m] (default: 53.0 m)
%
% Output:
%   et0: Reference evapotranspiration [mm/day] (hourly/sub-daily scaled)

if nargin < 5 || isempty(elevation_m)
    elevation_m = 53.0; % Baseline elevation
end

% 1. Atmospheric pressure P [kPa] (FAO-56 Eq. 7)
z = max(-100.0, elevation_m);
temp_term = (293.0 - 0.0065 * z) / 293.0;
if temp_term <= 0
    P = 101.3;
else
    P = 101.3 * (temp_term^5.26);
end

% 2. Psychrometric constant gamma [kPa/°C] (FAO-56 Eq. 8)
gamma = 0.665e-3 * P;

% 3. Saturation vapour pressure e_s [kPa] (FAO-56 Eq. 11)
es = 0.6108 * exp((17.27 * T) ./ (T + 237.3));

% 4. Actual vapour pressure e_a [kPa] (FAO-56 Eq. 17)
ea = es .* (max(0.0, min(100.0, RH)) / 100.0);

% 5. Slope of saturation vapour pressure curve Delta [kPa/°C] (FAO-56 Eq. 13)
Delta = (4098.0 * es) ./ ((T + 237.3).^2);

% 6. Net radiation Rn [MJ/(m²*h)] approximated from solar radiation Rs [W/m²]
% Convert W/m² to MJ/(m²*h): 1 W/m² = 0.0036 MJ/(m²*h)
Rs_MJ = Rs * 0.0036;
% Standard grass albedo alpha = 0.23, net solar Rns = (1 - 0.23) * Rs_MJ
Rns = 0.77 * Rs_MJ;
% Net longwave radiation estimation Rnl (sub-daily FAO-56 Eq. 39)
sigma = 2.043e-10; % Stefan-Boltzmann constant MJ/(K^4 * m^2 * h)
T_K = T + 273.16;
f_cloud = max(0.05, min(1.0, Rs / 1000.0)); % Cloudiness factor
Rnl = sigma * (T_K.^4) .* (0.34 - 0.14 * sqrt(max(0.0, ea))) .* (1.35 * f_cloud - 0.35);
Rn = Rns - Rnl;

% 7. Soil heat flux G [MJ/(m²*h)] (FAO-56 Eq. 45/46)
% G = 0.1 * Rn during daytime (Rn > 0), G = 0.5 * Rn at night
G = zeros(size(Rn));
day_idx = Rn > 0;
G(day_idx) = 0.1 * Rn(day_idx);
G(~day_idx) = 0.5 * Rn(~day_idx);

% 8. FAO-56 hourly Penman-Monteith equation (mm/hour)
u2_clamped = max(0.1, u2);
num = 0.408 * Delta .* (Rn - G) + gamma .* (37.0 ./ (T + 273.0)) .* u2_clamped .* (es - ea);
den = Delta + gamma .* (1.0 + 0.34 * u2_clamped);
et0_hr = max(0.0, num ./ den);

% Return standardized daily equivalent rate [mm/day]
et0 = et0_hr * 24.0;
end
