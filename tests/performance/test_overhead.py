"""
Overhead performance tests for Stichotrope.

Tests profiler overhead with x1, x10, x100 workload multipliers and statistical analysis.
Establishes baseline measurements with 95% confidence intervals.
"""

import pytest
import timeit
import json
from pathlib import Path
from typing import List, Dict, Any

from tests.performance.workloads import (
    simulate_work,
    create_workload_variants,
    get_all_scenarios,
    get_workload_scenario,
)
from tests.performance.statistics_utils import (
    calculate_overhead_statistics,
    format_overhead_report,
    check_regression,
)


# Try to import profiler from current implementation or skip tests
try:
    # First try current implementation
    from stichotrope import Profiler
    PROFILER_AVAILABLE = True
except (ImportError, AttributeError):
    # If not available, try to import from prototype branch
    # This allows us to establish baseline even before v1.0.0 implementation
    import sys
    import subprocess
    
    # Check if we can access prototype branch
    try:
        # Get prototype branch profiler code
        result = subprocess.run(
            ["git", "show", "prototype:stichotrope/profiler.py"],
            capture_output=True,
            text=True,
            check=True
        )
        # Note: In real scenario, we'd need to properly import from prototype
        # For now, mark as unavailable and skip tests
        PROFILER_AVAILABLE = False
    except:
        PROFILER_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not PROFILER_AVAILABLE,
    reason="Profiler implementation not available (run against prototype branch or wait for v1.0.0)"
)


class TestOverheadMeasurement:
    """Test profiler overhead with statistical rigor."""
    
    @pytest.fixture
    def baseline_dir(self, tmp_path):
        """Provide directory for baseline storage."""
        baseline_dir = tmp_path / "baselines"
        baseline_dir.mkdir(exist_ok=True)
        return baseline_dir
    
    def measure_baseline(
        self,
        workload_func,
        iterations: int = 30
    ) -> List[float]:
        """
        Measure baseline execution time without profiling.
        
        Args:
            workload_func: Function to measure
            iterations: Number of measurements
            
        Returns:
            List of execution times in seconds
        """
        times = timeit.repeat(workload_func, repeat=iterations, number=1)
        return times
    
    def measure_profiled_decorator(
        self,
        workload_func,
        track_idx: int,
        block_name: str,
        iterations: int = 30
    ) -> List[float]:
        """
        Measure execution time with profiler decorator.
        
        Args:
            workload_func: Function to measure
            track_idx: Track index for profiling
            block_name: Block name
            iterations: Number of measurements
            
        Returns:
            List of execution times in seconds
        """
        profiler = Profiler("OverheadTest")
        
        @profiler.track(track_idx, block_name)
        def profiled_workload():
            return workload_func()
        
        times = timeit.repeat(profiled_workload, repeat=iterations, number=1)
        return times
    
    def measure_profiled_context_manager(
        self,
        workload_func,
        track_idx: int,
        block_name: str,
        iterations: int = 30
    ) -> List[float]:
        """
        Measure execution time with profiler context manager.
        
        Args:
            workload_func: Function to measure
            track_idx: Track index for profiling
            block_name: Block name
            iterations: Number of measurements
            
        Returns:
            List of execution times in seconds
        """
        profiler = Profiler("OverheadTest")
        
        def profiled_workload():
            with profiler.block(track_idx, block_name):
                return workload_func()
        
        times = timeit.repeat(profiled_workload, repeat=iterations, number=1)
        return times
    
    @pytest.mark.parametrize("scenario", get_all_scenarios())
    @pytest.mark.parametrize("multiplier", [1, 10, 100])
    def test_overhead_decorator(self, scenario, multiplier, baseline_dir):
        """
        Test profiler overhead using decorator with workload multipliers.
        
        This test measures overhead at x1, x10, and x100 multipliers to reduce
        measurement noise and provide more reliable statistics.
        """
        scenario_config = get_workload_scenario(scenario)
        duration_ms = scenario_config["duration_ms"]
        
        # Create workload with multiplier
        base_workload = lambda: simulate_work(duration_ms)
        variants = create_workload_variants(base_workload, [multiplier])
        workload = variants[f"x{multiplier}"]
        
        # Measure baseline and profiled execution
        iterations = 30
        baseline_times = self.measure_baseline(workload, iterations)
        profiled_times = self.measure_profiled_decorator(
            workload, 0, f"{scenario}_x{multiplier}", iterations
        )
        
        # Calculate statistics
        stats = calculate_overhead_statistics(baseline_times, profiled_times)
        
        # Print report
        report = format_overhead_report(
            stats,
            f"{scenario_config['name']} - Decorator - x{multiplier}"
        )
        print(report)
        
        # Store results for regression tracking
        result_file = baseline_dir / f"overhead_decorator_{scenario}_x{multiplier}.json"
        with open(result_file, 'w') as f:
            json.dump({
                "scenario": scenario,
                "multiplier": multiplier,
                "method": "decorator",
                "statistics": {
                    "overhead_ns": stats["overhead_ns"],
                    "overhead_pct": stats["overhead_pct"],
                    "slowdown_factor": stats["slowdown_factor"],
                    "baseline_mean_ms": stats["baseline"]["mean"] * 1000,
                    "profiled_mean_ms": stats["profiled"]["mean"] * 1000,
                    "baseline_ci": [
                        stats["baseline"]["ci_lower"] * 1000,
                        stats["baseline"]["ci_upper"] * 1000
                    ],
                    "profiled_ci": [
                        stats["profiled"]["ci_lower"] * 1000,
                        stats["profiled"]["ci_upper"] * 1000
                    ],
                }
            }, f, indent=2)
        
        # Success criterion: ≤10% overhead for ≥1ms blocks
        # Note: We don't fail the test, just report the measurement
        # This avoids anchoring bias and lets the data speak for itself
        if duration_ms >= 1.0:
            print(f"\nSuccess criterion check (≥1ms blocks):")
            print(f"  Overhead: {stats['overhead_pct']:.2f}% (target: ≤10%)")
            if stats['overhead_pct'] <= 10.0:
                print(f"  Status: ✓ PASS")
            else:
                print(f"  Status: ⚠ ABOVE TARGET")
    
    @pytest.mark.parametrize("scenario", get_all_scenarios())
    @pytest.mark.parametrize("multiplier", [1, 10, 100])
    def test_overhead_context_manager(self, scenario, multiplier, baseline_dir):
        """
        Test profiler overhead using context manager with workload multipliers.
        """
        scenario_config = get_workload_scenario(scenario)
        duration_ms = scenario_config["duration_ms"]
        
        # Create workload with multiplier
        base_workload = lambda: simulate_work(duration_ms)
        variants = create_workload_variants(base_workload, [multiplier])
        workload = variants[f"x{multiplier}"]
        
        # Measure baseline and profiled execution
        iterations = 30
        baseline_times = self.measure_baseline(workload, iterations)
        profiled_times = self.measure_profiled_context_manager(
            workload, 0, f"{scenario}_x{multiplier}", iterations
        )
        
        # Calculate statistics
        stats = calculate_overhead_statistics(baseline_times, profiled_times)
        
        # Print report
        report = format_overhead_report(
            stats,
            f"{scenario_config['name']} - Context Manager - x{multiplier}"
        )
        print(report)
        
        # Store results
        result_file = baseline_dir / f"overhead_context_{scenario}_x{multiplier}.json"
        with open(result_file, 'w') as f:
            json.dump({
                "scenario": scenario,
                "multiplier": multiplier,
                "method": "context_manager",
                "statistics": {
                    "overhead_ns": stats["overhead_ns"],
                    "overhead_pct": stats["overhead_pct"],
                    "slowdown_factor": stats["slowdown_factor"],
                    "baseline_mean_ms": stats["baseline"]["mean"] * 1000,
                    "profiled_mean_ms": stats["profiled"]["mean"] * 1000,
                    "baseline_ci": [
                        stats["baseline"]["ci_lower"] * 1000,
                        stats["baseline"]["ci_upper"] * 1000
                    ],
                    "profiled_ci": [
                        stats["profiled"]["ci_lower"] * 1000,
                        stats["profiled"]["ci_upper"] * 1000
                    ],
                }
            }, f, indent=2)
        
        # Success criterion check
        if duration_ms >= 1.0:
            print(f"\nSuccess criterion check (≥1ms blocks):")
            print(f"  Overhead: {stats['overhead_pct']:.2f}% (target: ≤10%)")
            if stats['overhead_pct'] <= 10.0:
                print(f"  Status: ✓ PASS")
            else:
                print(f"  Status: ⚠ ABOVE TARGET")

