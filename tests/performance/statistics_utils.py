"""
Statistical analysis utilities for performance testing.

Provides functions for calculating confidence intervals, detecting outliers,
and performing statistical analysis on benchmark results.
"""

import math
import statistics
from typing import Any, Optional


def calculate_confidence_interval(
    data: list[float], confidence: float = 0.95
) -> tuple[float, float]:
    """
    Calculate confidence interval for a dataset.

    Uses t-distribution for small samples (n < 30) and normal distribution
    for larger samples.

    Args:
        data: List of measurements
        confidence: Confidence level (default: 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if len(data) < 2:
        return (0.0, 0.0)

    mean = statistics.mean(data)
    std_dev = statistics.stdev(data)
    n = len(data)

    # For small samples, use t-distribution approximation
    # For n < 30, use conservative t-value of 2.0 (roughly t_0.975 for df=20)
    # For n >= 30, use z-value of 1.96 for 95% CI
    if n < 30:
        t_value = 2.0  # Conservative estimate
    else:
        t_value = 1.96  # z-value for 95% CI

    margin_of_error = t_value * (std_dev / math.sqrt(n))

    return (mean - margin_of_error, mean + margin_of_error)


def detect_outliers(data: list[float], threshold: float = 2.0) -> list[int]:
    """
    Detect outliers using standard deviation method.

    Args:
        data: List of measurements
        threshold: Number of standard deviations for outlier detection (default: 2.0)

    Returns:
        List of indices of outliers
    """
    if len(data) < 3:
        return []

    mean = statistics.mean(data)
    std_dev = statistics.stdev(data)

    outliers = []
    for i, value in enumerate(data):
        z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
        if z_score > threshold:
            outliers.append(i)

    return outliers


def calculate_statistics(data: list[float]) -> dict[str, Any]:
    """
    Calculate comprehensive statistics for a dataset.

    Args:
        data: List of measurements

    Returns:
        Dictionary containing statistical measures
    """
    if not data:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "std_dev": 0.0,
            "min": 0.0,
            "max": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "outliers": [],
        }

    ci_lower, ci_upper = calculate_confidence_interval(data)
    outliers = detect_outliers(data)

    return {
        "count": len(data),
        "mean": statistics.mean(data),
        "median": statistics.median(data),
        "std_dev": statistics.stdev(data) if len(data) > 1 else 0.0,
        "min": min(data),
        "max": max(data),
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "outliers": outliers,
    }


def calculate_overhead_statistics(
    baseline_times: list[float], profiled_times: list[float]
) -> dict[str, Any]:
    """
    Calculate overhead statistics comparing profiled vs baseline execution.

    Args:
        baseline_times: List of baseline execution times (seconds)
        profiled_times: List of profiled execution times (seconds)

    Returns:
        Dictionary containing overhead statistics
    """
    baseline_stats = calculate_statistics(baseline_times)
    profiled_stats = calculate_statistics(profiled_times)

    # Calculate overhead metrics
    baseline_mean = baseline_stats["mean"]
    profiled_mean = profiled_stats["mean"]

    overhead_ns = (profiled_mean - baseline_mean) * 1e9
    overhead_pct = (
        ((profiled_mean - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0.0
    )
    slowdown_factor = (profiled_mean / baseline_mean) if baseline_mean > 0 else 1.0

    return {
        "baseline": baseline_stats,
        "profiled": profiled_stats,
        "overhead_ns": overhead_ns,
        "overhead_pct": overhead_pct,
        "slowdown_factor": slowdown_factor,
    }


def format_statistics_report(stats: dict[str, Any], name: str = "Benchmark") -> str:
    """
    Format statistics into a human-readable report.

    Args:
        stats: Statistics dictionary from calculate_statistics()
        name: Name of the benchmark

    Returns:
        Formatted string report
    """
    lines = [
        f"\n{name} Statistics:",
        f"  Count:      {stats['count']}",
        f"  Mean:       {stats['mean']:.6f}",
        f"  Median:     {stats['median']:.6f}",
        f"  Std Dev:    {stats['std_dev']:.6f}",
        f"  Min:        {stats['min']:.6f}",
        f"  Max:        {stats['max']:.6f}",
        f"  95% CI:     [{stats['ci_lower']:.6f}, {stats['ci_upper']:.6f}]",
    ]

    if stats["outliers"]:
        lines.append(f"  Outliers:   {len(stats['outliers'])} detected")

    return "\n".join(lines)


def format_overhead_report(overhead_stats: dict[str, Any], workload_name: str = "Workload") -> str:
    """
    Format overhead statistics into a human-readable report.

    Args:
        overhead_stats: Overhead statistics from calculate_overhead_statistics()
        workload_name: Name of the workload

    Returns:
        Formatted string report
    """
    baseline = overhead_stats["baseline"]
    profiled = overhead_stats["profiled"]

    lines = [
        f"\n{'='*80}",
        f"{workload_name}",
        f"{'='*80}",
        "",
        "Baseline (Unprofiled):",
        f"  Mean:       {baseline['mean']*1000:.3f} ms",
        f"  95% CI:     [{baseline['ci_lower']*1000:.3f}, {baseline['ci_upper']*1000:.3f}] ms",
        f"  Std Dev:    {baseline['std_dev']*1000:.3f} ms",
        "",
        "Profiled:",
        f"  Mean:       {profiled['mean']*1000:.3f} ms",
        f"  95% CI:     [{profiled['ci_lower']*1000:.3f}, {profiled['ci_upper']*1000:.3f}] ms",
        f"  Std Dev:    {profiled['std_dev']*1000:.3f} ms",
        "",
        "Overhead:",
        f"  Absolute:   {overhead_stats['overhead_ns']:.0f} ns",
        f"  Percentage: {overhead_stats['overhead_pct']:.2f}%",
        f"  Slowdown:   {overhead_stats['slowdown_factor']:.2f}x",
    ]

    return "\n".join(lines)


def check_regression(
    current_overhead_pct: float, baseline_overhead_pct: Optional[float], threshold_pct: float = 1.0
) -> tuple[bool, str]:
    """
    Check if current overhead represents a regression from baseline.

    Args:
        current_overhead_pct: Current overhead percentage
        baseline_overhead_pct: Baseline overhead percentage (None if no baseline)
        threshold_pct: Regression threshold in percentage points (default: 1.0)

    Returns:
        Tuple of (is_regression, message)
    """
    if baseline_overhead_pct is None:
        return (False, "No baseline available for comparison")

    delta = current_overhead_pct - baseline_overhead_pct

    if delta > threshold_pct:
        return (
            True,
            f"REGRESSION: Overhead increased by {delta:.2f}% (threshold: {threshold_pct}%)",
        )
    else:
        return (False, f"OK: Overhead change {delta:+.2f}% (threshold: {threshold_pct}%)")
