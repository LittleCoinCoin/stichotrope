# Performance Baselines

This directory stores baseline performance measurements for regression detection.

## Structure

Baseline files are named: `overhead_{method}_{scenario}_x{multiplier}.json`

Where:
- `method`: `decorator` or `context_manager`
- `scenario`: `tiny`, `small`, `medium`, or `large`
- `multiplier`: `1`, `10`, or `100`

## Usage

1. **Establish baseline**: Run `pytest tests/performance/test_overhead.py` to create baseline measurements
2. **Check regression**: Run `pytest tests/performance/test_regression.py` to compare against baseline
3. **Update baseline**: Delete old baselines and re-run overhead tests to establish new baseline

## Baseline Format

```json
{
  "scenario": "small",
  "multiplier": 10,
  "method": "decorator",
  "statistics": {
    "overhead_ns": 12345.67,
    "overhead_pct": 5.23,
    "slowdown_factor": 1.05,
    "baseline_mean_ms": 10.0,
    "profiled_mean_ms": 10.52,
    "baseline_ci": [9.8, 10.2],
    "profiled_ci": [10.3, 10.7]
  }
}
```

## Regression Threshold

Performance regression is detected when overhead increases by >1% compared to baseline.

## Version Tracking

Baselines should be updated when:
- Major profiler changes are made
- New version is released (v0.1.0, v0.2.0, etc.)
- Baseline measurements become outdated

Store version-specific baselines in subdirectories:
- `baselines/v0.1.0/` - Prototype baseline
- `baselines/v0.2.0/` - Thread-safe implementation baseline
- `baselines/v1.0.0/` - Production release baseline

