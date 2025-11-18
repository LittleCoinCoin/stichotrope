"""
Constant Overhead Benchmark

Measures the profiler's constant overhead per operation by profiling a minimal function.
Validates the ~1.8 µs constant overhead claim.
"""

import json
import sys
import time
import statistics
from pathlib import Path
from stichotrope import Profiler


def minimal_function():
    """Minimal function that does almost nothing."""
    return 42


def measure_constant_overhead(iterations: int = 1000):
    """
    Measure profiler's constant overhead by profiling minimal function.
    
    Args:
        iterations: Number of measurements to take
        
    Returns:
        Dictionary containing raw data and statistics
    """
    print(f"Measuring constant overhead with {iterations} iterations...")
    
    # Measure baseline (unprofiled)
    baseline_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        minimal_function()
        end = time.perf_counter()
        baseline_times.append(end - start)
    
    # Measure with profiler
    profiler = Profiler("ConstantOverhead")
    
    @profiler.track(0, "minimal")
    def profiled_minimal():
        return 42
    
    profiled_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        profiled_minimal()
        end = time.perf_counter()
        profiled_times.append(end - start)
    
    # Calculate overhead (profiled - baseline)
    overhead_times = [p - b for p, b in zip(profiled_times, baseline_times)]
    
    # Calculate statistics
    baseline_mean = statistics.mean(baseline_times)
    baseline_std = statistics.stdev(baseline_times)
    
    profiled_mean = statistics.mean(profiled_times)
    profiled_std = statistics.stdev(profiled_times)
    
    overhead_mean = statistics.mean(overhead_times)
    overhead_std = statistics.stdev(overhead_times)
    overhead_min = min(overhead_times)
    overhead_max = max(overhead_times)
    
    # Convert to microseconds for readability
    overhead_mean_us = overhead_mean * 1e6
    overhead_std_us = overhead_std * 1e6
    overhead_min_us = overhead_min * 1e6
    overhead_max_us = overhead_max * 1e6
    
    # Calculate 95% confidence interval (using t-distribution approximation)
    # For large n, t ≈ 1.96
    import math
    n = len(overhead_times)
    t_value = 2.0 if n < 30 else 1.96
    margin_of_error = t_value * (overhead_std / math.sqrt(n))
    ci_lower = (overhead_mean - margin_of_error) * 1e6
    ci_upper = (overhead_mean + margin_of_error) * 1e6
    
    results = {
        "iterations": iterations,
        "raw_data": {
            "baseline_times_us": [t * 1e6 for t in baseline_times],
            "profiled_times_us": [t * 1e6 for t in profiled_times],
            "overhead_times_us": [t * 1e6 for t in overhead_times],
        },
        "statistics": {
            "baseline_mean_us": baseline_mean * 1e6,
            "baseline_std_us": baseline_std * 1e6,
            "profiled_mean_us": profiled_mean * 1e6,
            "profiled_std_us": profiled_std * 1e6,
            "overhead_mean_us": overhead_mean_us,
            "overhead_std_us": overhead_std_us,
            "overhead_min_us": overhead_min_us,
            "overhead_max_us": overhead_max_us,
            "overhead_ci_95": [ci_lower, ci_upper],
        }
    }
    
    return results


def print_results(results):
    """Print constant overhead results."""
    stats = results["statistics"]
    
    print("\n" + "="*80)
    print("CONSTANT OVERHEAD MEASUREMENT")
    print("="*80)
    print(f"\nIterations: {results['iterations']}")
    
    print(f"\nBaseline (Unprofiled):")
    print(f"  Mean:    {stats['baseline_mean_us']:.3f} µs")
    print(f"  Std Dev: {stats['baseline_std_us']:.3f} µs")
    
    print(f"\nProfiled:")
    print(f"  Mean:    {stats['profiled_mean_us']:.3f} µs")
    print(f"  Std Dev: {stats['profiled_std_us']:.3f} µs")
    
    print(f"\nConstant Overhead:")
    print(f"  Mean:    {stats['overhead_mean_us']:.3f} µs")
    print(f"  Std Dev: {stats['overhead_std_us']:.3f} µs")
    print(f"  Min:     {stats['overhead_min_us']:.3f} µs")
    print(f"  Max:     {stats['overhead_max_us']:.3f} µs")
    print(f"  95% CI:  [{stats['overhead_ci_95'][0]:.3f}, {stats['overhead_ci_95'][1]:.3f}] µs")
    
    # Validation against ~1.8 µs claim
    print(f"\nValidation:")
    claimed_overhead = 1.8
    measured_overhead = stats['overhead_mean_us']
    ci_lower, ci_upper = stats['overhead_ci_95']
    
    if ci_lower <= claimed_overhead <= ci_upper:
        print(f"  ✓ Claimed overhead (~{claimed_overhead} µs) is within 95% CI")
    else:
        print(f"  ⚠ Claimed overhead (~{claimed_overhead} µs) is outside 95% CI")
    
    print(f"  Measured: {measured_overhead:.3f} µs (claimed: ~{claimed_overhead} µs)")
    print("="*80 + "\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Measure profiler's constant overhead")
    parser.add_argument("--iterations", type=int, default=1000, help="Number of measurements")
    parser.add_argument("--output", type=Path, help="Output JSON file path")
    args = parser.parse_args()
    
    results = measure_constant_overhead(iterations=args.iterations)
    print_results(results)
    
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to: {args.output}\n")

