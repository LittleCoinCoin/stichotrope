"""
Validation helpers for thread-safety tests.

This module provides reusable validation logic for test assertions
in the thread-safety test suite (Milestone 2.1).
"""


def validate_aggregation(results, expected_hit_count, expected_min_ns, expected_max_ns):
    """
    Validate aggregation results.

    Args:
        results: ProfilerResults object
        expected_hit_count: Expected total hit count
        expected_min_ns: Expected minimum time (with tolerance)
        expected_max_ns: Expected maximum time (with tolerance)

    Raises:
        AssertionError: If validation fails
    """
    block = results.tracks[0].blocks[0]
    assert block.hit_count == expected_hit_count, (
        f"Expected hit_count={expected_hit_count}, got {block.hit_count}"
    )
    assert block.min_time_ns <= expected_min_ns * 1.1, (
        f"Expected min_time_ns<={expected_min_ns * 1.1}, got {block.min_time_ns}"
    )
    assert block.max_time_ns >= expected_max_ns * 0.9, (
        f"Expected max_time_ns>={expected_max_ns * 0.9}, got {block.max_time_ns}"
    )


def validate_thread_safety(exception_list):
    """
    Validate that no thread-safety exceptions occurred.

    Args:
        exception_list: List of exceptions caught during concurrent execution

    Raises:
        AssertionError: If thread-safety violations detected
    """
    # Filter for thread-safety related exceptions
    thread_errors = [
        e
        for e in exception_list
        if isinstance(e, (AttributeError, KeyError, RuntimeError))
    ]
    assert len(thread_errors) == 0, f"Thread-safety violations: {thread_errors}"


def validate_performance(profiled_time, baseline_time, max_overhead_pct=1.0):
    """
    Validate performance overhead.

    Args:
        profiled_time: Execution time with profiling (seconds)
        baseline_time: Execution time without profiling (seconds)
        max_overhead_pct: Maximum acceptable overhead percentage

    Returns:
        float: Actual overhead percentage

    Raises:
        AssertionError: If overhead exceeds target
    """
    overhead_pct = (profiled_time - baseline_time) / baseline_time * 100
    assert overhead_pct <= max_overhead_pct, (
        f"Overhead {overhead_pct:.2f}% exceeds {max_overhead_pct}% target"
    )
    return overhead_pct

