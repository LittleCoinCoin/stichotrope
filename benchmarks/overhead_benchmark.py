"""
Overhead Benchmark for Stichotrope

Measures profiler overhead for different workload durations.
Tests PRIMARY success criterion: ≤10% overhead for ≥1ms blocks.
"""

import time
import timeit
import statistics
from stichotrope import Profiler


def simulate_work(duration_ms: float):
    """Simulate work by sleeping for specified duration."""
    time.sleep(duration_ms / 1000.0)


def benchmark_unprofiled(duration_ms: float, iterations: int = 100):
    """Benchmark unprofiled execution."""
    def workload():
        simulate_work(duration_ms)

    times = timeit.repeat(workload, repeat=iterations, number=1)
    return times


def benchmark_profiled_decorator(duration_ms: float, iterations: int = 100):
    """Benchmark profiled execution using decorator."""
    profiler = Profiler("OverheadTest")

    @profiler.track(0, f"work_{duration_ms}ms")
    def workload():
        simulate_work(duration_ms)

    times = timeit.repeat(workload, repeat=iterations, number=1)
    return times


def benchmark_profiled_context_manager(duration_ms: float, iterations: int = 100):
    """Benchmark profiled execution using context manager."""
    profiler = Profiler("OverheadTest")

    def workload():
        with profiler.block(0, f"work_{duration_ms}ms"):
            simulate_work(duration_ms)

    times = timeit.repeat(workload, repeat=iterations, number=1)
    return times


def calculate_overhead(baseline_times, profiled_times):
    """Calculate overhead statistics."""
    baseline_mean = statistics.mean(baseline_times)
    profiled_mean = statistics.mean(profiled_times)

    overhead_ns = (profiled_mean - baseline_mean) * 1e9
    overhead_pct = (profiled_mean - baseline_mean) / baseline_mean * 100
    slowdown_factor = profiled_mean / baseline_mean

    return {
        "baseline_mean_s": baseline_mean,
        "profiled_mean_s": profiled_mean,
        "overhead_ns": overhead_ns,
        "overhead_pct": overhead_pct,
        "slowdown_factor": slowdown_factor,
        "baseline_std": statistics.stdev(baseline_times),
        "profiled_std": statistics.stdev(profiled_times),
    }


def print_results(duration_ms, decorator_stats, context_stats):
    """Print benchmark results."""
    print(f"\n{'='*80}")
    print(f"Workload Duration: {duration_ms} ms")
    print(f"{'='*80}")

    print(f"\n{'Decorator Overhead:':<30}")
    print(f"  {'Baseline mean:':<25} {decorator_stats['baseline_mean_s']*1000:.3f} ms")
    print(f"  {'Profiled mean:':<25} {decorator_stats['profiled_mean_s']*1000:.3f} ms")
    print(f"  {'Overhead:':<25} {decorator_stats['overhead_ns']:.0f} ns")
    print(f"  {'Overhead %:':<25} {decorator_stats['overhead_pct']:.2f}%")
    print(f"  {'Slowdown factor:':<25} {decorator_stats['slowdown_factor']:.2f}x")

    print(f"\n{'Context Manager Overhead:':<30}")
    print(f"  {'Baseline mean:':<25} {context_stats['baseline_mean_s']*1000:.3f} ms")
    print(f"  {'Profiled mean:':<25} {context_stats['profiled_mean_s']*1000:.3f} ms")
    print(f"  {'Overhead:':<25} {context_stats['overhead_ns']:.0f} ns")
    print(f"  {'Overhead %:':<25} {context_stats['overhead_pct']:.2f}%")
    print(f"  {'Slowdown factor:':<25} {context_stats['slowdown_factor']:.2f}x")

    # Success criterion check
    decorator_pass = decorator_stats['overhead_pct'] <= 10.0 if duration_ms >= 1.0 else True
    context_pass = context_stats['overhead_pct'] <= 10.0 if duration_ms >= 1.0 else True

    if duration_ms >= 1.0:
        print(f"\n{'SUCCESS CRITERION (≥1ms blocks):':<30}")
        print(f"  {'Decorator:':<25} {'✓ PASS' if decorator_pass else '✗ FAIL'} ({decorator_stats['overhead_pct']:.2f}% ≤ 10%)")
        print(f"  {'Context Manager:':<25} {'✓ PASS' if context_pass else '✗ FAIL'} ({context_stats['overhead_pct']:.2f}% ≤ 10%)")


def run_benchmark():
    """Run complete overhead benchmark."""
    print("="*80)
    print("STICHOTROPE OVERHEAD BENCHMARK")
    print("="*80)
    print("\nMeasuring profiler overhead for different workload durations...")
    print("Iterations: 100 per workload")
    print("\nPRIMARY SUCCESS CRITERION: ≤10% overhead for ≥1ms blocks")

    # Test different workload durations
    durations = [0.1, 1.0, 10.0, 100.0]  # milliseconds
    iterations = 100

    results = []

    for duration_ms in durations:
        print(f"\nBenchmarking {duration_ms} ms workload...")

        # Baseline (unprofiled)
        baseline_times = benchmark_unprofiled(duration_ms, iterations)

        # Profiled (decorator)
        decorator_times = benchmark_profiled_decorator(duration_ms, iterations)

        # Profiled (context manager)
        context_times = benchmark_profiled_context_manager(duration_ms, iterations)

        # Calculate overhead
        decorator_stats = calculate_overhead(baseline_times, decorator_times)
        context_stats = calculate_overhead(baseline_times, context_times)

        # Print results
        print_results(duration_ms, decorator_stats, context_stats)

        results.append({
            "duration_ms": duration_ms,
            "decorator": decorator_stats,
            "context": context_stats,
        })

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"\n{'Duration':<12} {'Decorator Overhead':<25} {'Context Manager Overhead':<25} {'Status':<10}")
    print("-"*80)

    for result in results:
        duration = result["duration_ms"]
        dec_pct = result["decorator"]["overhead_pct"]
        ctx_pct = result["context"]["overhead_pct"]

        # Check success criterion for ≥1ms blocks
        if duration >= 1.0:
            status = "✓ PASS" if (dec_pct <= 10.0 and ctx_pct <= 10.0) else "✗ FAIL"
        else:
            status = "N/A"

        print(f"{duration:<12.1f} {dec_pct:>10.2f}%             {ctx_pct:>10.2f}%             {status:<10}")

    print(f"\n{'='*80}")

    # Overall assessment
    coarse_grained_results = [r for r in results if r["duration_ms"] >= 1.0]
    all_pass = all(
        r["decorator"]["overhead_pct"] <= 10.0 and r["context"]["overhead_pct"] <= 10.0
        for r in coarse_grained_results
    )

    print("\nOVERALL ASSESSMENT:")
    if all_pass:
        print("  ✓ PRIMARY SUCCESS CRITERION MET: ≤10% overhead for all ≥1ms blocks")
    else:
        print("  ✗ PRIMARY SUCCESS CRITERION NOT MET: Some ≥1ms blocks exceed 10% overhead")

    print(f"{'='*80}\n")

    return results


if __name__ == "__main__":
    results = run_benchmark()

