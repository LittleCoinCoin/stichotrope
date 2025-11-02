"""
Pytest configuration for performance tests.

Provides fixtures and configuration specific to performance benchmarking.
"""

import pytest
from pathlib import Path


def pytest_addoption(parser):
    """Add custom command-line options for performance tests."""
    parser.addoption(
        "--baseline-dir",
        action="store",
        default=None,
        help="Directory to store permanent baseline results (default: use tmp_path)"
    )


@pytest.fixture(scope="session")
def performance_baseline_dir():
    """
    Provide the baseline directory for performance measurements.
    
    Returns:
        Path: Path to baselines directory
    """
    baseline_dir = Path(__file__).parent / "baselines"
    baseline_dir.mkdir(exist_ok=True)
    return baseline_dir


@pytest.fixture
def benchmark_iterations():
    """
    Provide default number of iterations for benchmarks.
    
    Returns:
        int: Number of iterations (30 for statistical significance)
    """
    return 30


@pytest.fixture
def regression_threshold():
    """
    Provide regression detection threshold.
    
    Returns:
        float: Threshold in percentage points (1.0 = 1%)
    """
    return 1.0


def pytest_configure(config):
    """Configure pytest with custom markers for performance tests."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: marks tests as benchmarks"
    )
    config.addinivalue_line(
        "markers",
        "regression: marks tests as regression detection tests"
    )

