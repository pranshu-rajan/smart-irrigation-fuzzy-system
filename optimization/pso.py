"""
Particle Swarm Optimization (PSO) Solver for Phase 14 Fuzzy Controller Tuning.

Implements standard continuous PSO in normalized coordinates [0, 1]^D:
    v_i(t+1) = w * v_i(t) + c1 * r1 * (pbest_i - x_i) + c2 * r2 * (gbest - x_i)
    x_i(t+1) = x_i(t) + v_i(t+1)

Includes:
- Bounded search space with velocity and position clamping.
- Personal best (pbest) and global best (gbest) tracking.
- Per-iteration convergence telemetry (best, mean, worst fitness).
- Deterministic PRNG seeding for reproducible optimization.
- Non-destructive evaluation using the ClosedLoopEvaluator.
"""

from typing import Callable, Dict, List, Optional, Tuple, Any
import time
import numpy as np
from pydantic import BaseModel, Field

from optimization.parameter_space import FuzzyParameterSpace
from optimization.evaluation import ClosedLoopEvaluator


class PSOConfig(BaseModel):
    """Hyperparameters and configuration for PSO solver."""
    swarm_size: int = Field(default=20, ge=2, le=100, description="Number of particles in swarm")
    max_iterations: int = Field(default=30, ge=1, le=200, description="Maximum optimization iterations")
    inertia_weight: float = Field(default=0.729, ge=0.1, le=1.2, description="Inertia weight w")
    cognitive_coeff: float = Field(default=1.494, ge=0.1, le=3.0, description="Cognitive acceleration c1")
    social_coeff: float = Field(default=1.494, ge=0.1, le=3.0, description="Social acceleration c2")
    max_velocity_ratio: float = Field(default=0.20, ge=0.01, le=1.0, description="Max velocity as fraction of domain")
    seed: int = Field(default=42, description="PRNG seed for deterministic reproducibility")
    verbose: bool = Field(default=True, description="Print iteration progress to stdout")


class Particle:
    """A single particle in the D-dimensional normalized parameter space [0, 1]^D."""

    def __init__(self, dim: int, max_velocity: float, rng: np.random.RandomState) -> None:
        self.dim = dim
        self.max_velocity = max_velocity

        # Initialize position uniformly in [0, 1]^D
        self.position: np.ndarray = rng.uniform(0.0, 1.0, size=dim)
        # Initialize velocity in [-v_max, v_max]^D
        self.velocity: np.ndarray = rng.uniform(-max_velocity, max_velocity, size=dim)

        # Personal best tracking
        self.pbest_position: np.ndarray = self.position.copy()
        self.pbest_fitness: float = float("inf")
        self.current_fitness: float = float("inf")

    def update_velocity(
        self,
        gbest_position: np.ndarray,
        w: float,
        c1: float,
        c2: float,
        rng: np.random.RandomState,
    ) -> None:
        """Update particle velocity with inertia, cognitive, and social components."""
        r1 = rng.uniform(0.0, 1.0, size=self.dim)
        r2 = rng.uniform(0.0, 1.0, size=self.dim)

        cognitive = c1 * r1 * (self.pbest_position - self.position)
        social = c2 * r2 * (gbest_position - self.position)

        self.velocity = w * self.velocity + cognitive + social
        # Velocity clamping to [-max_velocity, max_velocity]
        self.velocity = np.clip(self.velocity, -self.max_velocity, self.max_velocity)

    def update_position(self) -> None:
        """Update particle position with boundary reflection / clamping to [0, 1]^D."""
        self.position += self.velocity

        # Clamping position to [0, 1] with velocity dampening on boundary hit
        for d in range(self.dim):
            if self.position[d] < 0.0:
                self.position[d] = 0.0
                self.velocity[d] = -0.5 * self.velocity[d]
            elif self.position[d] > 1.0:
                self.position[d] = 1.0
                self.velocity[d] = -0.5 * self.velocity[d]


class PSOSolver:
    """
    Particle Swarm Optimization Solver coordinating swarm evolution over the
    fuzzy controller parameter search space.
    """

    def __init__(
        self,
        evaluator: ClosedLoopEvaluator,
        config: Optional[PSOConfig] = None,
    ) -> None:
        self.evaluator = evaluator
        self.param_space = evaluator.param_space
        self.config = config or PSOConfig()
        self.dim = self.param_space.dim
        self.max_velocity = float(self.config.max_velocity_ratio)

        self.rng = np.random.RandomState(self.config.seed)

        # Swarm initialization
        self.particles: List[Particle] = [
            Particle(self.dim, self.max_velocity, self.rng)
            for _ in range(self.config.swarm_size)
        ]

        # Seed particle 0 with the exact baseline configuration
        baseline_norm = self.param_space.get_baseline_normalized()
        self.particles[0].position = baseline_norm.copy()
        self.particles[0].velocity = np.zeros(self.dim)

        # Global best state
        self.gbest_position: np.ndarray = baseline_norm.copy()
        self.gbest_fitness: float = float("inf")

        # Telemetry records: List of Dict for convergence dataframe
        self.convergence_history: List[Dict[str, Any]] = []

    def optimize(
        self,
        callback: Optional[Callable[[int, float, float, float], None]] = None,
    ) -> Tuple[np.ndarray, float, List[Dict[str, Any]]]:
        """
        Execute the PSO optimization loop.

        Args:
            callback: Optional callback(iteration, best_fitness, mean_fitness, elapsed_sec)

        Returns:
            Tuple[np.ndarray, float, List[Dict[str, Any]]]:
                - Global best physical parameter vector (18-D)
                - Global best fitness value (scalar J)
                - Convergence history telemetry records
        """
        t_start = time.time()

        if self.config.verbose:
            print("=================================================================")
            print("PHASE 14: PARTICLE SWARM OPTIMIZATION (FUZZY CONTROLLER TUNING)")
            print("=================================================================")
            print(f"Swarm Size: {self.config.swarm_size} particles | Max Iterations: {self.config.max_iterations}")
            print(f"Search Dimension: {self.dim} parameters | PRNG Seed: {self.config.seed}")
            print("Evaluating initial swarm...")

        # 1. Initial swarm evaluation (Iteration 0)
        fitnesses = []
        for i, p in enumerate(self.particles):
            theta_phys = self.param_space.denormalize(p.position)
            eval_res = self.evaluator.evaluate_vector(theta_phys)
            fit = eval_res.composite_fitness
            p.current_fitness = fit
            fitnesses.append(fit)

            if fit < p.pbest_fitness:
                p.pbest_fitness = fit
                p.pbest_position = p.position.copy()

            if fit < self.gbest_fitness:
                self.gbest_fitness = fit
                self.gbest_position = p.position.copy()

        mean_fit = float(np.mean(fitnesses))
        best_fit = float(np.min(fitnesses))

        self.convergence_history.append({
            "iteration": 0,
            "best_fitness": best_fit,
            "mean_fitness": mean_fit,
            "global_best_fitness": self.gbest_fitness,
            "elapsed_seconds": round(time.time() - t_start, 2),
        })

        if self.config.verbose:
            print(f"Iter 00 | Best J: {best_fit:.5f} | Mean J: {mean_fit:.5f} | GBest J: {self.gbest_fitness:.5f} | Elapsed: {time.time() - t_start:.1f}s")

        if callback:
            callback(0, best_fit, mean_fit, time.time() - t_start)

        # 2. Main PSO Iteration Loop (1 to max_iterations)
        for it in range(1, self.config.max_iterations + 1):
            t_it_start = time.time()
            fitnesses = []

            for p in self.particles:
                # Update velocity and position
                p.update_velocity(
                    gbest_position=self.gbest_position,
                    w=self.config.inertia_weight,
                    c1=self.config.cognitive_coeff,
                    c2=self.config.social_coeff,
                    rng=self.rng,
                )
                p.update_position()

                # Evaluate new position
                theta_phys = self.param_space.denormalize(p.position)
                eval_res = self.evaluator.evaluate_vector(theta_phys)
                fit = eval_res.composite_fitness
                p.current_fitness = fit
                fitnesses.append(fit)

                # Update personal best
                if fit < p.pbest_fitness:
                    p.pbest_fitness = fit
                    p.pbest_position = p.position.copy()

                # Update global best
                if fit < self.gbest_fitness:
                    self.gbest_fitness = fit
                    self.gbest_position = p.position.copy()

            mean_fit = float(np.mean(fitnesses))
            best_fit = float(np.min(fitnesses))
            elapsed_tot = time.time() - t_start

            self.convergence_history.append({
                "iteration": it,
                "best_fitness": best_fit,
                "mean_fitness": mean_fit,
                "global_best_fitness": self.gbest_fitness,
                "elapsed_seconds": round(elapsed_tot, 2),
            })

            if self.config.verbose:
                print(f"Iter {it:02d} | Best J: {best_fit:.5f} | Mean J: {mean_fit:.5f} | GBest J: {self.gbest_fitness:.5f} | Step: {time.time() - t_it_start:.1f}s")

            if callback:
                callback(it, best_fit, mean_fit, elapsed_tot)

        total_time = time.time() - t_start
        gbest_physical = self.param_space.denormalize(self.gbest_position)
        repaired_physical = self.param_space.repair_and_validate(gbest_physical)

        if self.config.verbose:
            print("=================================================================")
            print(f"PSO Complete! Total Runtime: {total_time:.2f}s")
            print(f"Global Best Fitness: {self.gbest_fitness:.5f}")
            print("=================================================================")

        return repaired_physical, self.gbest_fitness, self.convergence_history
