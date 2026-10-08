function [best_theta, best_cost, optimized_fis] = pso_tune_main_fis(max_iterations, swarm_size)
% PSO_TUNE_MAIN_FIS Calibrates 18 Main Irrigation FIS parameters via Particle Swarm
%
% Usage:
%   [best_theta, best_cost, optimized_fis] = optimization.pso_tune_main_fis(20, 15);

if nargin < 1 || isempty(max_iterations)
    max_iterations = 25;
end
if nargin < 2 || isempty(swarm_size)
    swarm_size = 20;
end

[lb, ub, baseline] = optimization.pso_parameter_bounds();
dim = numel(lb);

fprintf('=================================================================\n');
fprintf('   OFFLINE PARTICLE SWARM OPTIMIZATION (MAIN IRRIGATION FIS)     \n');
fprintf('=================================================================\n');
fprintf('  Dimension: %d parameters\n', dim);
fprintf('  Swarm Size: %d particles\n', swarm_size);
fprintf('  Max Iterations: %d\n', max_iterations);

% Evaluate baseline performance
baseline_cost = optimization.pso_composite_fitness(baseline, 'Normal', 12);
fprintf('  Baseline Cost (Normal scenario): %.4f\n', baseline_cost);

% Configure particleswarm options
opts = optimoptions('particleswarm', ...
    'SwarmSize', swarm_size, ...
    'MaxIterations', max_iterations, ...
    'InitialSwarmMatrix', baseline', ...
    'Display', 'iter', ...
    'UseParallel', false);

% Cost function handle
cost_fn = @(x) optimization.pso_composite_fitness(x, 'Normal', 12);

fprintf('Starting swarm exploration...\n');
[x_opt, best_cost] = particleswarm(cost_fn, dim, lb, ub, opts);

best_theta = optimization.pso_repair_vector(x_opt);
improvement_pct = max(0.0, (baseline_cost - best_cost) / baseline_cost * 100.0);

fprintf('=================================================================\n');
fprintf('   OPTIMIZATION COMPLETE\n');
fprintf('   Baseline Cost:  %.4f\n', baseline_cost);
fprintf('   Optimized Cost: %.4f (Improvement: %.2f%%)\n', best_cost, improvement_pct);
fprintf('=================================================================\n');

% Build and export optimized FIS
optimized_fis = fuzzy_builder.build_main_irrigation_fis(best_theta);
output_path = fullfile(fileparts(mfilename('fullpath')), '..', 'fis_models', 'main_irrigation_optimized.fis');
writeFIS(optimized_fis, output_path);
fprintf('Optimized FIS saved to: %s\n', output_path);
end
