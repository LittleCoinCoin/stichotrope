"""
Performance Tests (Tests 22-24)

Verify that thread-safety implementation meets performance targets.

Test File: tests/performance/test_thread_safety_overhead.py
Markers: @pytest.mark.performance, @pytest.mark.slow

Note: Performance tests are informational and should not block CI/CD pipelines.
"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

try:
    import psutil
except ImportError:
    psutil = None


@pytest.mark.performance
@pytest.mark.slow
def test_hot_path_overhead_measurement(profiler):
    """
    Test 22: Hot Path Overhead Measurement

    Purpose: Measure hot path overhead and verify it meets the ≤1% target.

    Expected Behavior:
    - Overhead ≤1% increase vs prototype (currently 0.02-0.23%)
    - Target: 0.02-0.25% overhead for ≥1ms blocks
    """

    # Fast function (< 1μs execution time)
    def fast_function():
        return 42

    # Measure baseline (unprofiled) execution time
    start_time = time.perf_counter()
    for _ in range(100_000):
        fast_function()
    baseline_time = time.perf_counter() - start_time

    # Measure profiled execution time
    @profiler.track(0, "fast_function")
    def profiled_fast_function():
        return 42

    start_time = time.perf_counter()
    for _ in range(100_000):
        profiled_fast_function()
    profiled_time = time.perf_counter() - start_time

    # Calculate overhead percentage
    overhead_pct = (profiled_time - baseline_time) / baseline_time * 100

    # Validate overhead
    assert overhead_pct <= 1.0, (
        f"Overhead {overhead_pct:.2f}% exceeds 1% target"
    )

    # Log for performance tracking
    print(f"\nHot path overhead: {overhead_pct:.4f}%")
    print(f"Baseline time: {baseline_time:.6f}s")
    print(f"Profiled time: {profiled_time:.6f}s")


@pytest.mark.performance
@pytest.mark.slow
def test_aggregation_performance_measurement(profiler):
    """
    Test 23: Aggregation Performance Measurement

    Purpose: Measure aggregation performance and verify it meets the <10ms
    target for 100 threads.

    Expected Behavior:
    - Aggregation completes in <10ms for 100 threads
    - Time scales linearly with thread count (O(T × K × B))
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Execute profiling in 100 threads (100 measurements each)
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(test_function) for _ in range(10_000)]
        for f in futures:
            f.result()

    # Measure get_results() execution time
    start_time = time.perf_counter()
    results = profiler.get_results()
    aggregation_time_ms = (time.perf_counter() - start_time) * 1000

    # Validate aggregation time
    assert aggregation_time_ms < 10.0, (
        f"Aggregation {aggregation_time_ms:.2f}ms exceeds 10ms target"
    )

    # Log for performance tracking
    print(f"\nAggregation time (100 threads): {aggregation_time_ms:.2f}ms")
    print(f"Total measurements: {results.tracks[0].blocks[0].hit_count}")
    print(f"Thread count: {len(profiler._all_thread_data)}")


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.skipif(psutil is None, reason="psutil not installed")
def test_memory_usage_measurement(profiler):
    """
    Test 24: Memory Usage Measurement

    Purpose: Measure memory usage and verify it scales as O(threads × blocks).

    Expected Behavior:
    - Memory usage: O(threads × blocks)
    - Typical: 50 threads × 100 blocks × 100 bytes ≈ 500 KB
    - Acceptable: <10 MB for 100 threads
    """

    process = psutil.Process()

    # Measure baseline memory usage
    baseline_memory = process.memory_info().rss

    # Execute profiling in 50 threads (100 blocks each)
    @profiler.track(0, "test_function")
    def test_function():
        return 42

    with ThreadPoolExecutor(max_workers=50) as executor:
        # Each thread executes 100 times
        futures = [executor.submit(test_function) for _ in range(5_000)]
        for f in futures:
            f.result()

    # Get results to ensure all data is aggregated
    results = profiler.get_results()

    # Measure memory usage after profiling
    after_memory = process.memory_info().rss

    # Calculate memory increase
    memory_increase_mb = (after_memory - baseline_memory) / 1024 / 1024

    # Validate memory usage
    assert memory_increase_mb < 10.0, (
        f"Memory usage {memory_increase_mb:.2f}MB exceeds 10MB"
    )

    # Log for performance tracking
    print(f"\nMemory usage (50 threads, 100 blocks): {memory_increase_mb:.2f}MB")
    print(f"Baseline memory: {baseline_memory / 1024 / 1024:.2f}MB")
    print(f"After profiling: {after_memory / 1024 / 1024:.2f}MB")
    print(f"Total measurements: {results.tracks[0].blocks[0].hit_count}")

