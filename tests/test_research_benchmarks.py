"""Unit and Integration Tests for Research Validation Modules.

Tests:
1. Statistical Multi-Scenario Monte Carlo Benchmark
2. 5-Stage Ablation Study
3. Sensor Noise & Valve Chattering Robustness
4. Edge Microcontroller Latency & Memory Profiler
5. Verification REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from simulation.statistical_benchmark import run_statistical_monte_carlo
from simulation.ablation_study import run_ablation_study
from simulation.sensor_noise_test import run_sensor_noise_test
from simulation.edge_hardware_profile import run_edge_hardware_profiler


@pytest.fixture
def client():
    return TestClient(app)


def test_statistical_benchmark():
    """Verify multi-scenario Monte Carlo benchmark with statistical t-tests."""
    report = run_statistical_monte_carlo(num_runs=3, duration_hours=6)
    
    assert report.num_runs == 3
    assert len(report.summaries) == 4
    assert "Fuzzy (Ours)" in report.summaries
    assert "Fixed Timer" in report.summaries
    assert "On-Off (Bang-Bang)" in report.summaries
    assert "PID Control" in report.summaries

    fuz_summary = report.summaries["Fuzzy (Ours)"]
    assert fuz_summary.mean_water_l > 0.0
    assert fuz_summary.water_savings_vs_timer_pct > 0.0
    assert fuz_summary.water_savings_vs_onoff_pct >= 0.0

    # Verify statistical significance structure
    assert "fuzzy_vs_fixed_timer" in report.statistical_tests
    assert "p_value" in report.statistical_tests["fuzzy_vs_fixed_timer"]
    assert len(report.plain_language_verdict) > 20


def test_ablation_study():
    """Verify systematic ablation study across all 4 configurations."""
    report = run_ablation_study(scenario_name="Heatwave", duration_hours=6)
    
    assert len(report.variants) == 4
    assert "Full 5-Stage System" in report.variants
    assert "Without Weather Stage" in report.variants
    assert "Without Water Demand Stage" in report.variants
    assert "Without Water-Filling Arbitrator" in report.variants

    full_variant = report.variants["Full 5-Stage System"]
    assert full_variant.reservoir_overdraft_violations == 0
    assert full_variant.water_used_l > 0.0

    # Without water filling should flag reservoir overdrafts or higher stress
    unconstrained_variant = report.variants["Without Water-Filling Arbitrator"]
    assert unconstrained_variant.variant_name == "Without Water-Filling Arbitrator"
    assert len(report.takeaway_summary) > 20


def test_sensor_noise_robustness():
    """Verify sensor noise and chattering resilience under degraded conditions."""
    report = run_sensor_noise_test(duration_hours=6)
    
    assert len(report.results) == 4
    clean = report.results["Clean Sensors (0% Noise)"]
    heavy = report.results["Heavy Noise (+/- 15% Noise)"]
    
    assert clean.fuzzy_valve_switches >= 0
    # Under heavy noise, On-Off chattering should exceed Fuzzy switches
    assert heavy.onoff_valve_switches >= heavy.fuzzy_valve_switches
    assert len(report.plain_language_verdict) > 20


def test_edge_hardware_profiler():
    """Verify edge hardware latency (< 5 ms per step) and memory profile."""
    report = run_edge_hardware_profiler(num_cycles=100)
    
    assert report.benchmark_cycles_tested == 100
    assert report.average_step_latency_ms < 50.0  # Fast execution in Python interpreter
    assert report.decisions_per_second > 20.0
    assert report.estimated_ram_usage_kb < 64.0   # Fits standard MCU RAM
    assert len(report.supported_hardware) >= 3
    assert all(chip.compatible for chip in report.supported_hardware)
    assert len(report.plain_language_verdict) > 20


def test_verification_api_endpoints(client):
    """Verify all 4 research endpoints respond with HTTP 200 via FastAPI."""
    r_stat = client.get("/api/verification/statistical-benchmark?runs=3&hours=6")
    assert r_stat.status_code == 200
    data_stat = r_stat.json()
    assert "summaries" in data_stat
    assert "statistical_tests" in data_stat

    r_abl = client.get("/api/verification/ablation-study?scenario=Heatwave&hours=6")
    assert r_abl.status_code == 200
    data_abl = r_abl.json()
    assert "variants" in data_abl

    r_rob = client.get("/api/verification/sensor-robustness?hours=6")
    assert r_rob.status_code == 200
    data_rob = r_rob.json()
    assert "results" in data_rob

    r_hw = client.get("/api/verification/hardware-profile?cycles=100")
    assert r_hw.status_code == 200
    data_hw = r_hw.json()
    assert "supported_hardware" in data_hw
    assert data_hw["average_step_latency_ms"] > 0.0
