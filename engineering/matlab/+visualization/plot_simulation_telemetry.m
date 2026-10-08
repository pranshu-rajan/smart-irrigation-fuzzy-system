function fig = plot_simulation_telemetry(results)
% PLOT_SIMULATION_TELEMETRY Plots 24-hour closed-loop simulation telemetry
%
% Renders multi-panel timeseries:
%   Panel 1: Weather Diurnal Trajectories (T, RH, Solar, Rain)
%   Panel 2: Soil Moisture Closed-Loop Tracking by Zone vs Targets
%   Panel 3: Subsystem Diagnostics (Soil Stress, Weather Stress, Water Demand)
%   Panel 4: Allocated Irrigation vs Unmet Requests

if nargin < 1 || isempty(results)
    results = simulation.run_multizone_sim('Normal', 24, 1);
end

t_hr = results.time_hr;
num_zones = size(results.soil_moisture, 2);
colors = {'#1f77b4', '#ff7f0e', '#2ca02c'}; % Tomato, Wheat, Maize

fig = figure('Name', sprintf('Irrigation Simulation Telemetry (%s)', results.scenario), ...
             'Position', [50 50 1300 900], 'Color', 'w');

% Panel 1: Environmental Forcing
subplot(4, 1, 1);
yyaxis left;
plot(t_hr, results.weather.temperature, 'r-', 'LineWidth', 1.5); hold on;
plot(t_hr, results.weather.humidity, 'b--', 'LineWidth', 1.2);
ylabel('Temp (°C) / RH (%)');
ylim([0 100]);
yyaxis right;
plot(t_hr, results.weather.solar_radiation, 'k-', 'LineWidth', 1.2);
ylabel('Solar Rad (W/m²)');
title(sprintf('Scenario: %s - Environmental Atmospheric Forcing', results.scenario), 'FontWeight', 'bold');
grid on; xlim([0 24]);
legend({'Temperature (°C)', 'Relative Humidity (%)', 'Solar Radiation (W/m²)'}, 'Location', 'northwest', 'NumColumns', 3);

% Panel 2: Soil Moisture Tracking
subplot(4, 1, 2);
hold on;
for z = 1:num_zones
    target_val = results.zone_metrics(z).target_sm;
    plot(t_hr, results.soil_moisture(:, z), 'Color', colors{z}, 'LineWidth', 2.0, ...
         'DisplayName', sprintf('Zone %d: %s (%s)', z, results.zone_metrics(z).crop, results.zone_metrics(z).soil));
    yline(target_val, ':', 'Color', colors{z}, 'LineWidth', 1.5, ...
          'DisplayName', sprintf('Zone %d Target (%.1f%%)', z, target_val));
end
ylabel('Soil Moisture (%)');
title('Closed-Loop Soil Moisture Regulation vs Target Setpoints', 'FontWeight', 'bold');
grid on; xlim([0 24]); ylim([20 85]);
legend('Location', 'southeast', 'NumColumns', 3);

% Panel 3: Controller Diagnostic Indices
subplot(4, 1, 3);
plot(t_hr, results.weather_stress, 'm-', 'LineWidth', 1.5, 'DisplayName', 'Atmospheric Weather Stress'); hold on;
for z = 1:num_zones
    plot(t_hr, results.soil_stress(:, z), 'Color', colors{z}, 'LineWidth', 1.5, ...
         'DisplayName', sprintf('Zone %d Soil Stress', z));
end
ylabel('Stress Index (%)');
title('Fuzzy Inference Diagnostic Indicators (Weather & Soil Moisture Stress)', 'FontWeight', 'bold');
grid on; xlim([0 24]); ylim([0 100]);
legend('Location', 'northeast', 'NumColumns', 4);

% Panel 4: Water Allocation and Deliveries
subplot(4, 1, 4);
hold on;
for z = 1:num_zones
    plot(t_hr, results.allocated_vol_l(:, z), 'Color', colors{z}, 'LineWidth', 1.8, ...
         'DisplayName', sprintf('Zone %d Allocated (L/min)', z));
end
xlabel('Simulation Time (Hours)');
ylabel('Water Flow (L/min)');
title('Actuator Water Delivery Under Constrained Shared Reservoir Allocation', 'FontWeight', 'bold');
grid on; xlim([0 24]);
legend('Location', 'northeast', 'NumColumns', 3);
end
