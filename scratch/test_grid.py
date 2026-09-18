import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import time
from fuzzy_engine.soil_stress import SoilStressFIS

fis_soil = SoilStressFIS(resolution=501)

# Build 201x201 grid
rsm_grid = np.linspace(0.0, 1.0, 201)
err_grid = np.linspace(-45.0, 45.0, 201)
table = np.zeros((201, 201))

for i, r in enumerate(rsm_grid):
    for j, e in enumerate(err_grid):
        table[i, j] = fis_soil.evaluate(rsm=r, moisture_error=e)

print("Grid table computed.")

# Test 1000 random points
rng = np.random.RandomState(42)
test_rsm = rng.uniform(0.0, 1.0, 1000)
test_err = rng.uniform(-45.0, 45.0, 1000)

diffs = []
t0 = time.time()
for r, e in zip(test_rsm, test_err):
    val_true = fis_soil.evaluate(rsm=r, moisture_error=e)
    # Bilinear interpolation
    ir = (r - 0.0) / (1.0 / 200)
    ie = (e - (-45.0)) / (90.0 / 200)
    i0 = int(np.clip(np.floor(ir), 0, 199))
    j0 = int(np.clip(np.floor(ie), 0, 199))
    i1 = i0 + 1
    j1 = j0 + 1
    wr = ir - i0
    we = ie - j0
    interp = (1 - wr) * (1 - we) * table[i0, j0] + wr * (1 - we) * table[i1, j0] + (1 - wr) * we * table[i0, j1] + wr * we * table[i1, j1]
    diffs.append(abs(val_true - interp))

print(f"Max diff: {max(diffs):.4f}, Mean diff: {np.mean(diffs):.6f}")
