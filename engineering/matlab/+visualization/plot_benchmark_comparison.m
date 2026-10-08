function fig = plot_benchmark_comparison(comparison)
% PLOT_BENCHMARK_COMPARISON Renders Controller Performance Comparison Figure
%
% Panels:
%   1. Zone 1 (Tomato) Soil Moisture Closed-Loop Tracking (Fuzzy vs PID vs On-Off)
%   2. Actuator Irrigation Valve Opening Command (%) Over 24 Hours
%   3. Total Water Consumption (Liters) Bar Chart with Savings Highlighted
%   4. Actuator Chattering & Switching Frequency Comparison

if nargin < 1 || isempty(comparison)
    comparison = simulation.run_benchmark_comparison('Normal', 24, 60);
end

t_hr = comparison.time_hr;
fig = figure('Name', sprintf('Benchmark Controller Comparison (%s)', comparison.scenario), ...
             'Position', [80 80 1350 850], 'Color', 'w');

% Colors
c_fuzzy = [0.12 0.53 0.90]; % Blue
c_pid   = [0.93 0.49 0.19]; % Orange
c_onoff = [0.85 0.20 0.20]; % Red
c_target= [0.20 0.70 0.20]; % Green

% Panel 1: Soil Moisture Tracking (Zone 1 - Tomato)
subplot(2, 2, 1);
plot(t_hr, comparison.fuzzy.sm(:, 1), '-', 'Color', c_fuzzy, 'LineWidth', 2.2, 'DisplayName', 'Fuzzy Control (Our System)'); hold on;
plot(t_hr, comparison.pid.sm(:, 1), '--', 'Color', c_pid, 'LineWidth', 1.8, 'DisplayName', 'Classical PID Control');
plot(t_hr, comparison.onoff.sm(:, 1), '-.', 'Color', c_onoff, 'LineWidth', 1.6, 'DisplayName', 'On-Off (Bang-Bang)');
yline(comparison.zones(1).target_moisture, ':', 'Color', c_target, 'LineWidth', 2.0, ...
      'DisplayName', sprintf('Target (%.1f%%)', comparison.zones(1).target_moisture));
title('Zone 1 (Tomato): Soil Moisture Regulation vs Target', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Time (Hours)'); ylabel('Soil Moisture (%)');
grid on; xlim([0 max(t_hr)]); ylim([40 75]);
legend('Location', 'southeast', 'FontSize', 9);

% Panel 2: Valve Command Comparison (Zone 1)
subplot(2, 2, 2);
plot(t_hr, comparison.fuzzy.cmd(:, 1), '-', 'Color', c_fuzzy, 'LineWidth', 2.0, 'DisplayName', 'Fuzzy (Smooth Modulation)'); hold on;
plot(t_hr, comparison.pid.cmd(:, 1), '--', 'Color', c_pid, 'LineWidth', 1.6, 'DisplayName', 'PID (Continuous)');
plot(t_hr, comparison.onoff.cmd(:, 1), '-.', 'Color', c_onoff, 'LineWidth', 1.6, 'DisplayName', 'On-Off (Bang-Bang Pulses)');
title('Actuator Control Action: Valve Command (%)', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Time (Hours)'); ylabel('Valve Opening (%)');
grid on; xlim([0 max(t_hr)]); ylim([0 105]);
legend('Location', 'northeast', 'FontSize', 9);

% Panel 3: Total Water Consumption Bar Chart
subplot(2, 2, 3);
water_vals = [comparison.fuzzy.total_water_l, comparison.pid.total_water_l, comparison.onoff.total_water_l];
b = bar(categorical({'Fuzzy Logic', 'PID Controller', 'On-Off Bang-Bang'}), water_vals, 0.55);
b.FaceColor = 'flat';
b.CData(1, :) = c_fuzzy;
b.CData(2, :) = c_pid;
b.CData(3, :) = c_onoff;
ylabel('Total Water Consumed (Liters)');
title(sprintf('Water Usage Efficiency (Fuzzy saves %.1f%% vs On-Off)', comparison.savings_vs_onoff_pct), ...
      'FontSize', 12, 'FontWeight', 'bold');
grid on;

% Label values on top of bars
for i = 1:3
    text(i, water_vals(i) + max(water_vals)*0.03, sprintf('%.0f L', water_vals(i)), ...
        'HorizontalAlignment', 'center', 'FontWeight', 'bold', 'FontSize', 10);
end
ylim([0 max(water_vals) * 1.18]);

% Panel 4: Actuator Stress & Chattering (Switching Count)
subplot(2, 2, 4);
switch_vals = [comparison.fuzzy.switches, comparison.pid.switches, comparison.onoff.switches];
b2 = bar(categorical({'Fuzzy Logic', 'PID Controller', 'On-Off Bang-Bang'}), switch_vals, 0.55);
b2.FaceColor = 'flat';
b2.CData(1, :) = c_fuzzy;
b2.CData(2, :) = c_pid;
b2.CData(3, :) = c_onoff;
ylabel('Valve Switching Events (Count)');
title('Actuator Wear & Valve Chattering Frequency', 'FontSize', 12, 'FontWeight', 'bold');
grid on;
for i = 1:3
    text(i, switch_vals(i) + max(switch_vals)*0.03, sprintf('%d', switch_vals(i)), ...
        'HorizontalAlignment', 'center', 'FontWeight', 'bold', 'FontSize', 10);
end
ylim([0 max(max(switch_vals) * 1.25, 5)]);

sgtitle(sprintf('End-to-End Benchmark Evaluation: Fuzzy vs On-Off vs PID (%s Scenario)', comparison.scenario), ...
        'FontSize', 14, 'FontWeight', 'bold');
end
