import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from optimization.evaluation import ClosedLoopEvaluator
from optimization.parameter_space import FuzzyParameterSpace

evaluator = ClosedLoopEvaluator()
p_space = evaluator.param_space
thetas = [p_space.baseline_values for _ in range(4)]

# Sequential
t0 = time.time()
res_seq = [evaluator.evaluate_vector(th) for th in thetas]
t_seq = time.time() - t0
print(f"Sequential 4 evals: {t_seq:.2f}s ({t_seq/4:.2f}s per eval)")

# ThreadPoolExecutor (max_workers=4)
t1 = time.time()
with ThreadPoolExecutor(max_workers=4) as ex:
    res_thread = list(ex.map(evaluator.evaluate_vector, thetas))
t_thread = time.time() - t1
print(f"ThreadPool 4 evals: {t_thread:.2f}s ({t_thread/4:.2f}s per eval)")
