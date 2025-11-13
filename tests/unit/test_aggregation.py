"""
Aggregation Tests (Tests 8-11)

Verify that the sequential merge algorithm produces correct aggregated results.

Test File: tests/unit/test_aggregation.py
Markers: @pytest.mark.unit, @pytest.mark.thread_safety
"""

import threading
import time

import pytest


@pytest.mark.unit
@pytest.mark.thread_safety
def test_sequential_merge_correctness(profiler):
    """
    Test 8: Sequential Merge Correctness

    Purpose: Verify that the sequential merge algorithm correctly aggregates
    statistics from multiple threads.

    Expected Behavior:
    - hit_count: 10 + 20 + 30 = 60
    - total_time_ns: (10×1ms) + (20×2ms) + (30×3ms) = 140ms
    - min_time_ns: min(1ms, 2ms, 3ms) = 1ms
    - max_time_ns: max(1ms, 2ms, 3ms) = 3ms
    """

    @profiler.track(0, "test_function")
    def test_function(sleep_ms, iterations):
        for _ in range(iterations):
            time.sleep(sleep_ms / 1000.0)

    # Thread 1: 10 calls, 1ms each
    thread1 = threading.Thread(target=test_function, args=(1, 10))
    # Thread 2: 20 calls, 2ms each
    thread2 = threading.Thread(target=test_function, args=(2, 20))
    # Thread 3: 30 calls, 3ms each
    thread3 = threading.Thread(target=test_function, args=(3, 30))

    thread1.start()
    thread2.start()
    thread3.start()
    thread1.join()
    thread2.join()
    thread3.join()

    # Get aggregated results
    results = profiler.get_results()
    block = results.tracks[0].blocks[0]

    # Validate aggregation
    assert block.hit_count == 60
    assert block.total_time_ns == pytest.approx(140_000_000, rel=0.1)
    assert block.min_time_ns <= 1_100_000  # ~1ms with tolerance
    assert block.max_time_ns >= 2_900_000  # ~3ms with tolerance


@pytest.mark.unit
@pytest.mark.thread_safety
def test_multi_thread_aggregation_different_blocks(profiler):
    """
    Test 9: Multi-Thread Aggregation with Different Blocks

    Purpose: Verify that aggregation correctly handles threads profiling
    different blocks.

    Expected Behavior:
    - Block A: hit_count = 15 (10 from T1 + 5 from T3)
    - Block B: hit_count = 20 (20 from T2)
    - Block C: hit_count = 5 (5 from T3)
    """

    @profiler.track(0, "block_a")
    def block_a():
        return "A"

    @profiler.track(0, "block_b")
    def block_b():
        return "B"

    @profiler.track(0, "block_c")
    def block_c():
        return "C"

    # Thread 1: profiles block A (10 calls)
    def thread1_target():
        for _ in range(10):
            block_a()

    # Thread 2: profiles block B (20 calls)
    def thread2_target():
        for _ in range(20):
            block_b()

    # Thread 3: profiles blocks A and C (5 calls each)
    def thread3_target():
        for _ in range(5):
            block_a()
            block_c()

    thread1 = threading.Thread(target=thread1_target)
    thread2 = threading.Thread(target=thread2_target)
    thread3 = threading.Thread(target=thread3_target)

    thread1.start()
    thread2.start()
    thread3.start()
    thread1.join()
    thread2.join()
    thread3.join()

    # Get aggregated results
    results = profiler.get_results()

    # Find blocks by name
    blocks = {block.name: block for block in results.tracks[0].blocks}

    assert blocks["block_a"].hit_count == 15  # 10 from T1 + 5 from T3
    assert blocks["block_b"].hit_count == 20  # 20 from T2
    assert blocks["block_c"].hit_count == 5  # 5 from T3


@pytest.mark.unit
@pytest.mark.thread_safety
def test_empty_thread_handling(profiler):
    """
    Test 10: Empty Thread Handling

    Purpose: Verify that aggregation correctly handles threads with no
    profiling data.

    Expected Behavior:
    - Aggregation skips empty thread data
    - Results only include data from Thread 1 and Thread 3
    - hit_count = 30
    """

    @profiler.track(0, "test_function")
    def test_function(iterations):
        for _ in range(iterations):
            pass

    # Thread 1: executes profiled function (10 calls)
    thread1 = threading.Thread(target=test_function, args=(10,))

    # Thread 2: starts but doesn't execute profiled function (empty data)
    def empty_thread_target():
        pass  # No profiled function calls

    thread2 = threading.Thread(target=empty_thread_target)

    # Thread 3: executes profiled function (20 calls)
    thread3 = threading.Thread(target=test_function, args=(20,))

    thread1.start()
    thread2.start()
    thread3.start()
    thread1.join()
    thread2.join()
    thread3.join()

    # Get aggregated results
    results = profiler.get_results()

    # Validate aggregation (empty thread should be skipped)
    assert results.tracks[0].blocks[0].hit_count == 30


@pytest.mark.unit
@pytest.mark.thread_safety
def test_aggregation_preserves_metadata(profiler):
    """
    Test 11: Aggregation Preserves Metadata

    Purpose: Verify that aggregation preserves block metadata (name, file, line).

    Expected Behavior:
    - Block name matches original
    - File path matches original
    - Line number matches original
    """

    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Execute in 3 threads
    threads = []
    for _ in range(3):
        thread = threading.Thread(target=test_function)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Get aggregated results
    results = profiler.get_results()
    block = results.tracks[0].blocks[0]

    # Validate metadata preservation
    assert block.name == "test_function"
    assert "test_aggregation.py" in block.file
    assert block.line > 0

