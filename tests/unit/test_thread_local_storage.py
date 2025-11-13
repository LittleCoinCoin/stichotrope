"""
Thread-Local Storage Tests (Tests 1-4)

Verify that each thread maintains independent profiling data with zero contention
in the hot path.

Test File: tests/unit/test_thread_local_storage.py
Markers: @pytest.mark.unit, @pytest.mark.thread_safety
"""

import threading
import time

import pytest


@pytest.mark.unit
@pytest.mark.thread_safety
def test_thread_local_storage_isolation(profiler):
    """
    Test 1: Thread-Local Storage Isolation

    Purpose: Verify that each thread maintains independent profiling data
    without cross-thread interference.

    Expected Behavior:
    - Thread 1 records 10 hits with ~1ms average time
    - Thread 2 records 20 hits with ~2ms average time
    - Aggregated results: hit_count=30, correct min/max/total
    - No cross-thread interference
    """

    @profiler.track(0, "test_function")
    def test_function(sleep_ms, iterations):
        for _ in range(iterations):
            time.sleep(sleep_ms / 1000.0)

    # Execute in Thread 1: 10 calls, 1ms each
    thread1 = threading.Thread(target=test_function, args=(1, 10))
    # Execute in Thread 2: 20 calls, 2ms each
    thread2 = threading.Thread(target=test_function, args=(2, 20))

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    # Get aggregated results
    results = profiler.get_results()

    # Validate aggregation
    assert results.tracks[0].blocks[0].hit_count == 30
    assert results.tracks[0].blocks[0].min_time_ns >= 1_000_000  # ~1ms
    assert results.tracks[0].blocks[0].max_time_ns >= 2_000_000  # ~2ms


@pytest.mark.unit
@pytest.mark.thread_safety
def test_thread_registration_in_global_registry(profiler):
    """
    Test 2: Thread Registration in Global Registry

    Purpose: Verify that threads are correctly registered in the profiler's
    global thread data registry.

    Expected Behavior:
    - Registry contains exactly 3 thread entries
    - Each thread ID is unique
    - Each thread has independent data structures
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Execute in 3 different threads
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=test_function)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Access profiler's _all_thread_data registry
    assert len(profiler._all_thread_data) == 3
    thread_ids = list(profiler._all_thread_data.keys())
    assert len(set(thread_ids)) == 3  # All unique


@pytest.mark.unit
@pytest.mark.thread_safety
def test_thread_local_initialization_pattern(profiler):
    """
    Test 3: Thread-Local Initialization Pattern

    Purpose: Verify that thread-local storage is correctly initialized on
    first access using the hasattr pattern.

    Expected Behavior:
    - First access initializes thread-local storage
    - Subsequent accesses use existing storage
    - No AttributeError on first access
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Execute in new thread - should not raise AttributeError
    exception_raised = False

    def thread_target():
        nonlocal exception_raised
        try:
            test_function()
        except AttributeError:
            exception_raised = True

    thread = threading.Thread(target=thread_target)
    thread.start()
    thread.join()

    assert not exception_raised, "AttributeError raised on first access"


@pytest.mark.unit
@pytest.mark.thread_safety
def test_thread_local_measurement_recording(profiler):
    """
    Test 4: Thread-Local Measurement Recording

    Purpose: Verify that measurement recording operates on thread-local data
    without locks.

    Expected Behavior:
    - Both threads record measurements concurrently
    - No blocking (execution time ≈ single-thread time)
    - Measurements are accurate
    """

    @profiler.track(0, "test_function")
    def test_function():
        time.sleep(0.01)  # 10ms
        return 42

    # Measure concurrent execution time
    start_time = time.perf_counter()

    thread1 = threading.Thread(target=test_function)
    thread2 = threading.Thread(target=test_function)

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    total_execution_time = time.perf_counter() - start_time

    # Verify concurrent execution (no blocking)
    # If threads blocked each other, time would be ~20ms
    # With concurrent execution, time should be ~10ms
    assert total_execution_time < 0.015, (
        f"Execution time {total_execution_time:.3f}s suggests blocking"
    )

    # Verify both threads recorded data
    assert len(profiler._all_thread_data) == 2

