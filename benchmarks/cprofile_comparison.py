"""
cProfile Comparison Benchmark

Compares Stichotrope overhead with cProfile for function-level profiling.
Tests SECONDARY success criterion: Competitive with cProfile.
"""

import json
import sys
import time
import timeit
import statistics
import cProfile
import pstats
from io import StringIO
from pathlib import Path
from stichotrope import Profiler

from benchmarks.statistics_utils import perform_welch_ttest


def simulate_work(duration_ms: float):
    """Simulate work by sleeping for specified duration."""
    time.sleep(duration_ms / 1000.0)


def create_workload_functions(duration_ms: float):
    """Create a set of functions to profile."""
    def func_a():
        simulate_work(duration_ms)

    def func_b():
        simulate_work(duration_ms)

    def func_c():
        simulate_work(duration_ms)

    def main():
        func_a()
        func_b()
        func_c()

    return main, func_a, func_b, func_c


def benchmark_unprofiled(duration_ms: float, iterations: int = 50):
    """Benchmark unprofiled execution."""
    main, _, _, _ = create_workload_functions(duration_ms)

    times = timeit.repeat(main, repeat=iterations, number=1)
    return times


def benchmark_stichotrope(duration_ms: float, iterations: int = 50):
    """Benchmark Stichotrope profiled execution."""
    profiler = Profiler("ComparisonTest")

    @profiler.track(0, "func_a")
    def func_a():
        simulate_work(duration_ms)

    @profiler.track(0, "func_b")
    def func_b():
        simulate_work(duration_ms)

    @profiler.track(0, "func_c")
    def func_c():
        simulate_work(duration_ms)

    @profiler.track(0, "main")
    def main():
        func_a()
        func_b()
        func_c()

    times = timeit.repeat(main, repeat=iterations, number=1)
    return times


def benchmark_cprofile(duration_ms: float, iterations: int = 50):
    """Benchmark cProfile profiled execution."""
    main, _, _, _ = create_workload_functions(duration_ms)

    times = []
    for _ in range(iterations):
        profiler = cProfile.Profile()
        start = time.perf_counter()
        profiler.runcall(main)
        end = time.perf_counter()
        times.append(end - start)

    return times


def calculate_stats(times):
    """Calculate timing statistics."""
    return {
        "mean": statistics.mean(times),
        "std": statistics.stdev(times),
        "min": min(times),
        "max": max(times),
    }


def print_comparison(duration_ms, unprofiled_stats, stichotrope_stats, cprofile_stats):
    """Print comparison results."""
    print(f"\n{'='*80}")
    print(f"Workload Duration: {duration_ms} ms per function (3 functions total)")
    print(f"{'='*80}")

    # Calculate overhead
    stich_overhead_pct = (stichotrope_stats["mean"] - unprofiled_stats["mean"]) / unprofiled_stats["mean"] * 100
    cprof_overhead_pct = (cprofile_stats["mean"] - unprofiled_stats["mean"]) / unprofiled_stats["mean"] * 100

    stich_slowdown = stichotrope_stats["mean"] / unprofiled_stats["mean"]
    cprof_slowdown = cprofile_stats["mean"] / unprofiled_stats["mean"]

    print(f"\n{'Unprofiled (Baseline):':<30}")
    print(f"  {'Mean:':<20} {unprofiled_stats['mean']*1000:.3f} ms")
    print(f"  {'Std Dev:':<20} {unprofiled_stats['std']*1000:.3f} ms")

    print(f"\n{'Stichotrope:':<30}")
    print(f"  {'Mean:':<20} {stichotrope_stats['mean']*1000:.3f} ms")
    print(f"  {'Overhead:':<20} {stich_overhead_pct:.2f}%")
    print(f"  {'Slowdown:':<20} {stich_slowdown:.2f}x")

    print(f"\n{'cProfile:':<30}")
    print(f"  {'Mean:':<20} {cprofile_stats['mean']*1000:.3f} ms")
    print(f"  {'Overhead:':<20} {cprof_overhead_pct:.2f}%")
    print(f"  {'Slowdown:':<20} {cprof_slowdown:.2f}x")

    # Comparison
    print(f"\n{'Comparison:':<30}")
    if stich_overhead_pct < cprof_overhead_pct:
        improvement = cprof_overhead_pct - stich_overhead_pct
        print(f"  ✓ Stichotrope is {improvement:.2f}% faster than cProfile")
    elif stich_overhead_pct > cprof_overhead_pct:
        degradation = stich_overhead_pct - cprof_overhead_pct
        print(f"  ⚠ Stichotrope is {degradation:.2f}% slower than cProfile")
    else:
        print(f"  = Stichotrope and cProfile have similar overhead")


def run_comparison(output_file: Path = None):
    """Run complete cProfile comparison with statistical testing."""
    print("="*80)
    print("STICHOTROPE vs cProfile COMPARISON")
    print("="*80)
    print("\nComparing function-level profiling overhead...")
    print("Iterations: 50 per workload")
    print("\nSECONDARY SUCCESS CRITERION: Competitive with cProfile")

    # Test different workload durations
    durations = [1.0, 10.0, 100.0]  # milliseconds
    iterations = 50

    results = []

    for duration_ms in durations:
        print(f"\nBenchmarking {duration_ms} ms per function...")

        # Baseline (unprofiled)
        unprofiled_times = benchmark_unprofiled(duration_ms, iterations)
        unprofiled_stats = calculate_stats(unprofiled_times)

        # Stichotrope
        stichotrope_times = benchmark_stichotrope(duration_ms, iterations)
        stichotrope_stats = calculate_stats(stichotrope_times)

        # cProfile
        cprofile_times = benchmark_cprofile(duration_ms, iterations)
        cprofile_stats = calculate_stats(cprofile_times)

        # Statistical testing
        stich_vs_baseline = perform_welch_ttest(stichotrope_times, unprofiled_times)
        cprof_vs_baseline = perform_welch_ttest(cprofile_times, unprofiled_times)
        stich_vs_cprof = perform_welch_ttest(stichotrope_times, cprofile_times)

        # Print comparison
        print_comparison(duration_ms, unprofiled_stats, stichotrope_stats, cprofile_stats)

        results.append({
            "duration_ms": duration_ms,
            "raw_data": {
                "unprofiled_times_ms": [t * 1000 for t in unprofiled_times],
                "stichotrope_times_ms": [t * 1000 for t in stichotrope_times],
                "cprofile_times_ms": [t * 1000 for t in cprofile_times],
            },
            "statistics": {
                "unprofiled": unprofiled_stats,
                "stichotrope": stichotrope_stats,
                "cprofile": cprofile_stats,
            },
            "statistical_tests": {
                "stichotrope_vs_baseline": stich_vs_baseline,
                "cprofile_vs_baseline": cprof_vs_baseline,
                "stichotrope_vs_cprofile": stich_vs_cprof,
            }
        })

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\n{'Duration':<12} {'Stichotrope':<20} {'cProfile':<20} {'Winner':<15} {'p-value':<12}")
    print("-"*80)

    for result in results:
        duration = result["duration_ms"]
        stich_overhead = (result["statistics"]["stichotrope"]["mean"] - result["statistics"]["unprofiled"]["mean"]) / result["statistics"]["unprofiled"]["mean"] * 100
        cprof_overhead = (result["statistics"]["cprofile"]["mean"] - result["statistics"]["unprofiled"]["mean"]) / result["statistics"]["unprofiled"]["mean"] * 100
        p_value = result["statistical_tests"]["stichotrope_vs_cprofile"]["p_value"]

        if stich_overhead < cprof_overhead:
            winner = "Stichotrope"
        elif stich_overhead > cprof_overhead:
            winner = "cProfile"
        else:
            winner = "Tie"

        print(f"{duration:<12.1f} {stich_overhead:>10.2f}%        {cprof_overhead:>10.2f}%        {winner:<15} p={p_value:.4f}")

    print(f"\n{'='*80}")

    # Overall assessment
    stich_wins = sum(1 for r in results if (r["statistics"]["stichotrope"]["mean"] - r["statistics"]["unprofiled"]["mean"]) < (r["statistics"]["cprofile"]["mean"] - r["statistics"]["unprofiled"]["mean"]))
    cprof_wins = sum(1 for r in results if (r["statistics"]["cprofile"]["mean"] - r["statistics"]["unprofiled"]["mean"]) < (r["statistics"]["stichotrope"]["mean"] - r["statistics"]["unprofiled"]["mean"]))

    print("\nOVERALL ASSESSMENT:")
    if stich_wins > cprof_wins:
        print(f"  ✓ Stichotrope is competitive: Faster than cProfile in {stich_wins}/{len(results)} tests")
    elif stich_wins == cprof_wins:
        print(f"  ✓ Stichotrope is competitive: Similar performance to cProfile")
    else:
        print(f"  ⚠ Stichotrope is slower: cProfile wins {cprof_wins}/{len(results)} tests")

    print(f"{'='*80}\n")

    # Save results to JSON if output file specified
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✅ Results saved to: {output_file}\n")

    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare Stichotrope vs cProfile performance")
    parser.add_argument("--output", type=Path, help="Output JSON file path")
    args = parser.parse_args()

    results = run_comparison(output_file=args.output)

