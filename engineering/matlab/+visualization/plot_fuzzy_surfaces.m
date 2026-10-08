function fig = plot_fuzzy_surfaces()
% PLOT_FUZZY_SURFACES Generates 3D Control Surface Plots for all 5 FIS systems
%
% Renders 3D nonlinear control manifold surfaces using Fuzzy Logic Toolbox gensurf

fis1 = fuzzy_builder.build_soil_stress_fis();
fis3 = fuzzy_builder.build_water_demand_fis();
fis4 = fuzzy_builder.build_main_irrigation_fis();
fis5 = fuzzy_builder.build_water_allocation_fis();

fig = figure('Name', 'FIS 3D Control Manifolds', 'Position', [100 100 1200 800], 'Color', 'w');

% 1. Soil Stress Surface (RSM vs Moisture Error -> Soil Stress)
subplot(2, 2, 1);
gensurf(fis1, [1 2], 1);
title('FIS 1: Soil Stress Manifold', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Relative Soil Moisture (RSM)');
ylabel('Moisture Tracking Error (%)');
zlabel('Soil Stress (%)');
colormap(gca, parula);
grid on; view([-45 35]);

% 2. Water Demand Surface (ETc vs Deficit -> Water Demand)
subplot(2, 2, 2);
gensurf(fis3, [1 2], 1);
title('FIS 3: Water Demand Manifold', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Crop ETc (mm/day)');
ylabel('Crop Water Deficit (mm/day)');
zlabel('Water Demand (%)');
colormap(gca, viridis_or_jet());
grid on; view([-45 35]);

% 3. Main Irrigation Surface (Soil Stress vs Error -> Command)
subplot(2, 2, 3);
gensurf(fis4, [1 4], 1);
title('FIS 4: Main Irrigation Supervisory Manifold', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Soil Stress (%)');
ylabel('Moisture Error (%)');
zlabel('Irrigation Command (%)');
colormap(gca, parula);
grid on; view([-45 35]);

% 4. Water Allocation Surface (Available Water vs Zone Demand -> Allocation)
subplot(2, 2, 4);
gensurf(fis5, [1 2], 1);
title('FIS 5: Supervisory Water Allocation Manifold', 'FontSize', 12, 'FontWeight', 'bold');
xlabel('Available Water (%)');
ylabel('Zone Demand (%)');
zlabel('Allocated Ratio (%)');
colormap(gca, turbo);
grid on; view([-45 35]);
end

function cmap = viridis_or_jet()
    if exist('turbo', 'builtin')
        cmap = turbo;
    else
        cmap = jet;
    end
end
