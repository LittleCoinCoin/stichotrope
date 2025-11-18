"""
Stress Tests (Tests 18-21)

Verify that profiler maintains correctness and stability under high load.

Test File: tests/integration/test_stress.py
Markers: @pytest.mark.integration, @pytest.mark.stress, @pytest.mark.slow
"""

import time
from concurrent.futures import ThreadPoolExecutor

import pytest

try:
    import psutil
except ImportError:
    psutil = None


@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.slow
def test_high_thread_count_100_threads(profiler):
    """
    Test 18: High Thread Count (100 Threads)

    Purpose: Verify that profiler handles 100 concurrent threads without
    degradation.

    Expected Behavior:
    - All 1000 tasks profiled successfully
    - Aggregation completes in <10ms (target from architecture)
    - No exceptions or errors
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Submit 1000 tasks to thread pool (100 threads, 10 tasks each)
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(test_function) for _ in range(1000)]
        results_list = [f.result() for f in futures]

    # Verify all tasks completed
    assert len(results_list) == 1000

    # Measure aggregation time
    start_time = time.perf_counter()
    results = profiler.get_results()
    aggregation_time_ms = (time.perf_counter() - start_time) * 1000

    # Validate results
    assert results.tracks[0].blocks[0].hit_count == 1000
    assert aggregation_time_ms < 10.0, (
        f"Aggregation time {aggregation_time_ms:.2f}ms exceeds 10ms target"
    )
    assert len(profiler._all_thread_data) <= 100


@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.slow
def test_high_measurement_frequency_100k_measurements(profiler):
    """
    Test 19: High Measurement Frequency (100K Measurements)

    Purpose: Verify that profiler handles high measurement frequency without
    performance degradation.

    Expected Behavior:
    - All 100,000 measurements recorded
    - Overhead ≤1% vs unprofiled execution
    - No memory errors
    """

    # Fast function (< 1μs execution time)
    def fast_function():
        return 42

    # Measure unprofiled execution time (baseline)
    start_time = time.perf_counter()
    for _ in range(100_000):
        fast_function()
    unprofiled_time = time.perf_counter() - start_time

    # Measure profiled execution time
    @profiler.track(0, "fast_function")
    def profiled_fast_function():
        return 42

    start_time = time.perf_counter()
    for _ in range(100_000):
        profiled_fast_function()
    profiled_time = time.perf_counter() - start_time

    # Get results
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 100_000

    # Calculate overhead
    overhead_pct = (profiled_time - unprofiled_time) / unprofiled_time * 100
    assert overhead_pct <= 1.0, (
        f"Overhead {overhead_pct:.2f}% exceeds 1% target"
    )


@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.slow
def test_combined_stress_many_threads_many_measurements(profiler):
    """
    Test 20: Combined Stress (Many Threads + Many Measurements)

    Purpose: Verify that profiler handles combined stress of many threads
    and many measurements.

    Expected Behavior:
    - All 50,000 measurements recorded
    - Aggregation completes in <10ms
    - No exceptions or memory errors
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Submit 50,000 tasks to thread pool (50 threads, 1000 tasks each)
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(test_function) for _ in range(50_000)]
        results_list = [f.result() for f in futures]

    # Verify all tasks completed
    assert len(results_list) == 50_000

    # Measure aggregation time
    start_time = time.perf_counter()
    results = profiler.get_results()
    aggregation_time_ms = (time.perf_counter() - start_time) * 1000

    # Validate results
    assert results.tracks[0].blocks[0].hit_count == 50_000
    assert aggregation_time_ms < 10.0, (
        f"Aggregation time {aggregation_time_ms:.2f}ms exceeds 10ms target"
    )


@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.slow
@pytest.mark.skipif(psutil is None, reason="psutil not installed")
def test_long_running_profiling_session(profiler):
    """
    Test 21: Long-Running Profiling Session

    Purpose: Verify that profiler maintains stability during long-running
    profiling sessions.

    Expected Behavior:
    - Profiling continues without errors
    - Memory usage remains stable (no leaks)
    - Aggregation time remains consistent
    """

    @profiler.track(0, "test_function")
    def test_function():
        time.sleep(0.001)  # 1ms
        return 42

    process = psutil.Process()
    memory_samples = []
    aggregation_times = []

    # Run profiling for 10 seconds with continuous task submission
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        while time.time() - start_time < 10:
            # Submit batch of tasks
            futures = [executor.submit(test_function) for _ in range(100)]
            for f in futures:
                f.result()

            # Periodically call get_results() and measure memory
            agg_start = time.perf_counter()
            profiler.get_results()
            agg_time = (time.perf_counter() - agg_start) * 1000
            aggregation_times.append(agg_time)

            # Sample memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_samples.append(memory_mb)

            time.sleep(1)  # 1 second between samples

    # Verify memory usage is stable (no leaks)
    min_memory_mb = min(memory_samples)
    max_memory_mb = max(memory_samples)
    assert max_memory_mb - min_memory_mb < 50, (
        f"Memory growth {max_memory_mb - min_memory_mb:.2f}MB exceeds 50MB"
    )

    # Verify aggregation time is consistent
    assert max(aggregation_times) < 2 * min(aggregation_times), (
        "Aggregation time degraded significantly"
    )

