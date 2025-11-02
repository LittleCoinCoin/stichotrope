"""
Timing utilities for Stichotrope profiler.

Provides high-precision timing mechanisms for profiling code blocks.
"""

import time
from typing import Callable


# Primary timing function: nanosecond precision wall-clock time
get_time_ns: Callable[[], int] = time.perf_counter_ns

"""
Timing Mechanism Selection:

Primary: time.perf_counter_ns()
- Nanosecond precision
- Wall-clock time (includes I/O, sleep)
- Platform-independent
- Best for general-purpose profiling

Alternatives (documented for future consideration):

1. time.process_time_ns()
   - CPU time only (excludes I/O, sleep)
   - Useful for CPU-bound profiling
   - May miss important I/O bottlenecks

2. time.thread_time_ns()
   - Per-thread CPU time
   - Useful for multi-threaded profiling
   - More complex to integrate

Trade-offs:
- Wall-clock time (perf_counter_ns) captures total execution time including I/O
- CPU time (process_time_ns) excludes I/O, which may hide bottlenecks
- For coarse-grained profiling (≥1ms blocks), wall-clock time is more practical

Expected Overhead:
- ~100-200ns per perf_counter_ns() call
- Measured in benchmark suite (v0.4.0)
"""


def measure_timing_overhead(iterations: int = 10000) -> float:
    """
    Measure the overhead of the timing mechanism itself.

    Args:
        iterations: Number of timing calls to measure

    Returns:
        Average overhead per timing call in nanoseconds
    """
    start = get_time_ns()
    for _ in range(iterations):
        get_time_ns()
    end = get_time_ns()

    total_time = end - start
    # Subtract the two timing calls (start and end)
    overhead_per_call = (total_time - 2 * 100) / iterations  # Approximate
    return overhead_per_call

