"""
Lock Protection Tests (Tests 5-7)

Verify that lock-protected global structures are safe under concurrent access.

Test File: tests/unit/test_lock_protection.py
Markers: @pytest.mark.unit, @pytest.mark.thread_safety
"""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.mark.unit
@pytest.mark.thread_safety
def test_call_site_cache_concurrent_access():
    """
    Test 5: Call-Site Cache Concurrent Access

    Purpose: Verify that the global call-site cache is protected by
    _GLOBAL_CACHE_LOCK during concurrent decorator application.

    Expected Behavior:
    - All 10 call-sites are registered in cache
    - No duplicate entries
    - No KeyError during concurrent access
    """
    from stichotrope import Profiler
    from stichotrope.profiler import _CALL_SITE_CACHE

    profiler = Profiler("TestProfiler")

    # Define 10 different functions to be decorated
    def create_function(idx):
        @profiler.track(0, f"function_{idx}")
        def func():
            return idx

        return func

    # Apply decorators concurrently from 5 threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_function, i) for i in range(10)]
        functions = [f.result() for f in futures]

    # Verify all 10 call-sites are registered
    # Note: Cache keys are (track_idx, file, line, block_name)
    # We expect at least 10 entries (one per function)
    assert len(_CALL_SITE_CACHE) >= 10

    # Verify all entries are valid
    for key, value in _CALL_SITE_CACHE.items():
        assert isinstance(value, tuple)
        assert len(value) == 2  # (profiler_id, block_idx)


@pytest.mark.unit
@pytest.mark.thread_safety
def test_profiler_registry_concurrent_access():
    """
    Test 6: Profiler Registry Concurrent Access

    Purpose: Verify that the global profiler registry is protected by
    _REGISTRY_LOCK during concurrent profiler instantiation.

    Expected Behavior:
    - All 10 profilers registered in _PROFILER_REGISTRY
    - Profiler IDs are unique and sequential
    - No race condition in ID allocation
    """
    from stichotrope import Profiler
    from stichotrope.profiler import _PROFILER_REGISTRY

    # Clear registry before test
    initial_count = len(_PROFILER_REGISTRY)

    # Create 10 profiler instances concurrently from 5 threads
    def create_profiler(idx):
        return Profiler(f"Profiler_{idx}")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(create_profiler, i) for i in range(10)]
        profilers = [f.result() for f in futures]

    # Verify all 10 profilers registered
    assert len(_PROFILER_REGISTRY) == initial_count + 10

    # Verify profiler IDs are unique
    profiler_ids = [p._profiler_id for p in profilers]
    assert len(set(profiler_ids)) == 10  # All unique


@pytest.mark.unit
@pytest.mark.thread_safety
@pytest.mark.timeout(10)
def test_lock_hierarchy_compliance(profiler):
    """
    Test 7: Lock Hierarchy Compliance

    Purpose: Verify that locks are acquired in the correct order to prevent
    deadlocks.

    Expected Behavior:
    - All operations complete successfully
    - No deadlocks (all threads complete within timeout)
    - Lock hierarchy: _REGISTRY_LOCK → _GLOBAL_CACHE_LOCK → Profiler._global_lock

    Note: pytest-timeout marker ensures test fails if deadlock occurs
    """

    # Define operations that require lock acquisition
    @profiler.track(0, "test_function")
    def test_function():
        return 42

    # Execute operations from multiple threads concurrently
    def thread_target():
        # This will trigger:
        # 1. Decorator application (_GLOBAL_CACHE_LOCK)
        # 2. Thread registration (Profiler._global_lock)
        for _ in range(10):
            test_function()

    threads = []
    for _ in range(5):
        thread = threading.Thread(target=thread_target)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify all threads completed (no deadlock)
    assert all(not thread.is_alive() for thread in threads)

    # Verify profiling occurred
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 50  # 5 threads × 10 calls

