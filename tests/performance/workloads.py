"""
Standard workload functions for performance testing.

Provides consistent workload functions for benchmarking profiler overhead
across different scenarios and workload multipliers.
"""

import time
from typing import Any, Callable


def simulate_work(duration_ms: float) -> None:
    """
    Simulate work by sleeping for specified duration.

    Args:
        duration_ms: Duration in milliseconds
    """
    time.sleep(duration_ms / 1000.0)


def cpu_intensive_work(iterations: int = 1000) -> int:
    """
    Simulate CPU-intensive work with arithmetic operations.

    Args:
        iterations: Number of iterations

    Returns:
        Result of computation (to prevent optimization)
    """
    result = 0
    for i in range(iterations):
        result += i * i
        result = result % 1000000
    return result


def nested_function_calls(depth: int = 5) -> int:
    """
    Simulate nested function calls.

    Args:
        depth: Recursion depth

    Returns:
        Result of computation
    """
    if depth <= 0:
        return 1
    return depth + nested_function_calls(depth - 1)


def mixed_workload(duration_ms: float = 1.0, cpu_iterations: int = 100) -> tuple[None, int]:
    """
    Simulate mixed I/O and CPU workload.

    Args:
        duration_ms: Sleep duration in milliseconds
        cpu_iterations: Number of CPU iterations

    Returns:
        Tuple of (sleep_result, cpu_result)
    """
    simulate_work(duration_ms)
    cpu_result = cpu_intensive_work(cpu_iterations)
    return (None, cpu_result)


class WorkloadMultiplier:
    """
    Wrapper to run workloads with different multipliers (x1, x10, x100).

    This helps reduce measurement noise by averaging over multiple operations.
    """

    def __init__(self, workload_func: Callable, multiplier: int = 1):
        """
        Initialize workload multiplier.

        Args:
            workload_func: Function to execute
            multiplier: Number of times to execute (1, 10, or 100)
        """
        self.workload_func = workload_func
        self.multiplier = multiplier

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """
        Execute workload with multiplier.

        Returns:
            Result of last execution
        """
        result = None
        for _ in range(self.multiplier):
            result = self.workload_func(*args, **kwargs)
        return result


def create_workload_variants(
    base_workload: Callable, multipliers: list[int] = None
) -> dict[str, Callable]:
    """
    Create workload variants with different multipliers.

    Args:
        base_workload: Base workload function
        multipliers: List of multipliers to create (default: [1, 10, 100])

    Returns:
        Dictionary mapping multiplier name to workload function
    """
    if multipliers is None:
        multipliers = [1, 10, 100]
    variants = {}
    for mult in multipliers:
        name = f"x{mult}"
        variants[name] = WorkloadMultiplier(base_workload, mult)
    return variants


# Pre-defined workload scenarios
WORKLOAD_SCENARIOS = {
    "tiny": {
        "name": "Tiny blocks (0.1ms)",
        "duration_ms": 0.1,
        "description": "Very short blocks, high overhead expected",
    },
    "small": {
        "name": "Small blocks (1ms)",
        "duration_ms": 1.0,
        "description": "Small blocks, target ≤10% overhead",
    },
    "medium": {
        "name": "Medium blocks (10ms)",
        "duration_ms": 10.0,
        "description": "Medium blocks, low overhead expected",
    },
    "large": {
        "name": "Large blocks (100ms)",
        "duration_ms": 100.0,
        "description": "Large blocks, minimal overhead expected",
    },
}


def get_workload_scenario(scenario_name: str) -> dict:
    """
    Get workload scenario configuration.

    Args:
        scenario_name: Name of scenario (tiny, small, medium, large)

    Returns:
        Scenario configuration dictionary

    Raises:
        KeyError: If scenario name not found
    """
    return WORKLOAD_SCENARIOS[scenario_name]


def get_all_scenarios() -> list[str]:
    """
    Get list of all available workload scenarios.

    Returns:
        List of scenario names
    """
    return list(WORKLOAD_SCENARIOS.keys())
