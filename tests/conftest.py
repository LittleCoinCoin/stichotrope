"""
Pytest configuration and shared fixtures for Stichotrope tests.

This module provides common fixtures and configuration for all test modules.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture
def profiler_available():
    """
    Check if profiler implementation is available.

    Returns:
        bool: True if profiler can be imported, False otherwise
    """
    try:
        from stichotrope import Profiler

        return True
    except (ImportError, AttributeError):
        return False


@pytest.fixture
def get_profiler():
    """
    Factory fixture to create profiler instances.

    Returns:
        Callable: Function that creates a Profiler instance

    Raises:
        pytest.skip: If profiler implementation is not available
    """
    try:
        from stichotrope import Profiler
    except (ImportError, AttributeError):
        pytest.skip("Profiler implementation not available")

    def _create_profiler(name="TestProfiler"):
        return Profiler(name)

    return _create_profiler


@pytest.fixture
def sample_workload():
    """
    Provide a sample workload function for testing.

    Returns:
        Callable: A function that performs some work
    """

    def workload(duration_ms=1.0):
        """Simulate work by busy-waiting for specified duration."""
        import time

        time.sleep(duration_ms / 1000.0)

    return workload


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Provide a temporary directory for test outputs.

    Args:
        tmp_path: pytest's built-in temporary directory fixture

    Returns:
        Path: Path to temporary output directory
    """
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


# ============================================================================
# Thread-Safety Test Fixtures (Milestone 2.1)
# ============================================================================


@pytest.fixture
def profiler():
    """
    Provide fresh profiler instance for thread-safety tests.

    Yields:
        Profiler: Fresh profiler instance

    Note:
        Automatically clears profiler data after test completion.
    """
    try:
        from stichotrope import Profiler
    except (ImportError, AttributeError):
        pytest.skip("Profiler implementation not available")

    p = Profiler("TestProfiler")
    yield p
    # Cleanup: clear profiler data
    try:
        p.clear()
    except AttributeError:
        pass  # clear() method may not exist yet


@pytest.fixture
def thread_pool():
    """
    Provide ThreadPoolExecutor with 10 workers.

    Yields:
        ThreadPoolExecutor: Thread pool with 10 workers

    Note:
        Automatically shuts down thread pool after test completion.
    """
    with ThreadPoolExecutor(max_workers=10) as executor:
        yield executor
    # Automatic cleanup via context manager


@pytest.fixture
def simple_function(profiler):
    """
    Simple profiled function with minimal overhead.

    Args:
        profiler: Profiler fixture

    Returns:
        Callable: Profiled function that returns 42
    """

    @profiler.track(0, "simple")
    def func():
        return 42

    return func


@pytest.fixture
def cpu_bound_function(profiler):
    """
    CPU-bound profiled function (~1ms execution).

    Args:
        profiler: Profiler fixture

    Returns:
        Callable: Profiled function with ~1ms busy loop
    """

    @profiler.track(0, "cpu_bound")
    def func():
        # Busy loop for ~1ms
        end = time.perf_counter() + 0.001
        while time.perf_counter() < end:
            pass
        return 42

    return func


@pytest.fixture
def io_bound_function(profiler):
    """
    I/O-bound profiled function (sleep-based).

    Args:
        profiler: Profiler fixture

    Returns:
        Callable: Profiled function with configurable sleep duration
    """

    @profiler.track(0, "io_bound")
    def func(sleep_ms=1):
        time.sleep(sleep_ms / 1000.0)
        return 42

    return func


@pytest.fixture
def thread_barrier():
    """
    Provide threading.Barrier factory for synchronized thread start.

    Returns:
        Callable: Function that creates a Barrier for given number of threads
    """

    def create_barrier(num_threads):
        return threading.Barrier(num_threads)

    return create_barrier
