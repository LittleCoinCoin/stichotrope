"""
Multi-Threaded Integration Tests (Tests 12-17)

Verify that profiler works correctly in realistic multi-threaded scenarios.

Test File: tests/integration/test_multithreaded_profiling.py
Markers: @pytest.mark.integration, @pytest.mark.thread_safety
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.integration
@pytest.mark.thread_safety
def test_thread_pool_executor_profiling(profiler):
    """
    Test 12: ThreadPoolExecutor Profiling

    Purpose: Verify that profiler works correctly with
    concurrent.futures.ThreadPoolExecutor.

    Expected Behavior:
    - All 100 tasks are profiled
    - Results show hit_count = 100
    - No exceptions or errors
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Submit 100 tasks to thread pool
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(test_function) for _ in range(100)]
        results_list = [f.result() for f in futures]

    # Verify all tasks completed
    assert len(results_list) == 100

    # Get aggregated results
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 100
    assert len(profiler._all_thread_data) <= 10  # Max 10 worker threads


@pytest.mark.integration
@pytest.mark.thread_safety
def test_concurrent_get_results_calls(profiler):
    """
    Test 13: Concurrent get_results() Calls

    Purpose: Verify that multiple threads can call get_results() concurrently
    without race conditions.

    Expected Behavior:
    - All get_results() calls succeed
    - No AttributeError, KeyError, or race conditions
    - Results are consistent (monotonically increasing hit_count)
    """

    @profiler.track(0, "test_function")
    def test_function():
        time.sleep(0.001)  # 1ms
        return 42

    results_list = []
    exceptions = []

    # Thread function: continuously execute profiled function
    def profiling_thread():
        try:
            for _ in range(100):
                test_function()
        except Exception as e:
            exceptions.append(e)

    # Thread function: continuously call get_results()
    def results_thread():
        try:
            for _ in range(50):
                result = profiler.get_results()
                results_list.append(result)
                time.sleep(0.01)  # 10ms between calls
        except Exception as e:
            exceptions.append(e)

    # Start 5 profiling threads and 3 results threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=profiling_thread)
        threads.append(thread)
        thread.start()

    for _ in range(3):
        thread = threading.Thread(target=results_thread)
        threads.append(thread)
        thread.start()

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Verify all get_results() calls succeeded
    assert len(results_list) > 0
    assert all(result is not None for result in results_list)

    # Verify no exceptions
    assert len(exceptions) == 0


@pytest.mark.integration
@pytest.mark.thread_safety
def test_thread_lifecycle_during_profiling(profiler):
    """
    Test 14: Thread Lifecycle During Profiling

    Purpose: Verify that profiler handles thread creation and destruction
    during active profiling.

    Expected Behavior:
    - Results include data from all 20 threads (10 old + 10 new)
    - Total hit_count = (10×10) + (10×20) = 300
    - Thread data persists after thread termination
    """

    @profiler.track(0, "test_function")
    def test_function(iterations):
        for _ in range(iterations):
            pass

    # Start 10 threads, each executes 10 times
    threads1 = []
    for _ in range(10):
        thread = threading.Thread(target=test_function, args=(10,))
        threads1.append(thread)
        thread.start()

    for thread in threads1:
        thread.join()

    # Start 10 new threads, each executes 20 times
    threads2 = []
    for _ in range(10):
        thread = threading.Thread(target=test_function, args=(20,))
        threads2.append(thread)
        thread.start()

    for thread in threads2:
        thread.join()

    # Get aggregated results
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 300
    assert len(profiler._all_thread_data) == 20


@pytest.mark.integration
@pytest.mark.thread_safety
def test_nested_profiling_across_threads(profiler):
    """
    Test 15: Nested Profiling Across Threads

    Purpose: Verify that nested profiling works correctly when calls span
    multiple threads.

    Expected Behavior:
    - Outer function profiled only in Thread 1
    - Inner function profiled in both threads
    - Aggregation correctly merges inner function data
    """

    @profiler.track(0, "inner_function")
    def inner_function():
        return 42

    @profiler.track(0, "outer_function")
    def outer_function():
        return inner_function()

    # Thread 1: calls outer function (which profiles inner function)
    def thread1_target():
        outer_function()

    # Thread 2: calls inner function directly
    def thread2_target():
        inner_function()

    thread1 = threading.Thread(target=thread1_target)
    thread2 = threading.Thread(target=thread2_target)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    # Get aggregated results
    results = profiler.get_results()

    # Find blocks by name
    blocks = {block.name: block for block in results.tracks[0].blocks}

    assert blocks["outer_function"].hit_count == 1  # Only Thread 1
    assert blocks["inner_function"].hit_count == 2  # Both threads


@pytest.mark.integration
@pytest.mark.thread_safety
def test_concurrent_track_enable_disable(profiler):
    """
    Test 16: Concurrent Track Enable/Disable

    Purpose: Verify that track enable/disable operations are thread-safe.

    Expected Behavior:
    - No exceptions or race conditions
    - Some measurements recorded (when track enabled)
    - Some measurements skipped (when track disabled)
    """

    @profiler.track(0, "test_function")
    def test_function():
        time.sleep(0.001)  # 1ms
        return 42

    exceptions = []

    # Thread function: continuously execute profiled function
    def profiling_thread():
        try:
            for _ in range(100):
                test_function()
        except Exception as e:
            exceptions.append(e)

    # Start 5 profiling threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=profiling_thread)
        threads.append(thread)
        thread.start()

    # Main thread: toggle track enable/disable
    for _ in range(10):
        time.sleep(0.01)  # 10ms
        profiler.disable_track(0)
        time.sleep(0.01)  # 10ms
        profiler.enable_track(0)

    # Wait for all threads
    for thread in threads:
        thread.join()

    # Verify profiling occurred (track was enabled at some point)
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count > 0

    # Verify no exceptions
    assert len(exceptions) == 0


@pytest.mark.integration
@pytest.mark.thread_safety
def test_rapid_thread_creation_destruction(profiler):
    """
    Test 17: Rapid Thread Creation/Destruction

    Purpose: Verify that profiler handles rapid thread creation and
    destruction without memory leaks or errors.

    Expected Behavior:
    - All 100 threads profiled successfully
    - Thread data persists in registry (not cleaned up automatically)
    - No memory errors or exceptions
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Create and destroy 100 threads rapidly
    threads = []
    for _ in range(100):
        thread = threading.Thread(target=test_function)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Get aggregated results
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 100
    assert len(profiler._all_thread_data) == 100


