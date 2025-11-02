"""
Pytest configuration and shared fixtures for Stichotrope tests.

This module provides common fixtures and configuration for all test modules.
"""


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
