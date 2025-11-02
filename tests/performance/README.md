# Performance Test Suite

Comprehensive performance testing framework for Stichotrope with statistical rigor and regression detection.

## Overview

This test suite measures profiler overhead with:
- **Workload multipliers** (x1, x10, x100) to reduce measurement noise
- **Statistical analysis** with 95% confidence intervals
- **Regression detection** with >1% degradation alerts
- **Unbiased measurement** (no hardcoded expected values)

## Structure

```
tests/performance/
├── README.md                    # This file
├── conftest.py                  # Pytest configuration and fixtures
├── workloads.py                 # Standard workload functions
├── statistics_utils.py          # Statistical analysis utilities
├── test_overhead.py             # Overhead measurement tests
├── test_regression.py           # Regression detection tests
└── baselines/                   # Stored baseline measurements
    ├── README.md
    └── *.json                   # Baseline result files
```

## Running Tests

### Establish Baseline

Run overhead tests to create baseline measurements:

```bash
pytest tests/performance/test_overhead.py -v
```

This will:
- Measure overhead for 4 scenarios (tiny, small, medium, large)
- Test 3 multipliers (x1, x10, x100) for each scenario
- Test both decorator and context manager methods
- Store results in `baselines/` directory
- Print detailed statistics with 95% CI

### Check for Regressions

Compare current performance against baseline:

```bash
pytest tests/performance/test_regression.py -v
```

This will:
- Load baseline measurements
- Compare against current performance
- Alert if overhead increased by >1%

### Run All Performance Tests

```bash
pytest tests/performance/ -v
```

## Workload Scenarios

| Scenario | Duration | Description | Success Criterion |
|----------|----------|-------------|-------------------|
| tiny     | 0.1 ms   | Very short blocks | High overhead expected |
| small    | 1 ms     | Small blocks | ≤10% overhead target |
| medium   | 10 ms    | Medium blocks | Low overhead expected |
| large    | 100 ms   | Large blocks | Minimal overhead expected |

## Workload Multipliers

To reduce measurement noise, each scenario is tested with multiple multipliers:

- **x1**: Single operation (baseline measurement)
- **x10**: 10 operations (better averaging, reduces noise)
- **x100**: 100 operations (best averaging, most reliable)

Higher multipliers provide more reliable statistics by averaging over more operations.

## Statistical Analysis

Each measurement includes:

- **Mean**: Average execution time
- **Median**: Middle value (robust to outliers)
- **Std Dev**: Standard deviation (variability)
- **Min/Max**: Range of measurements
- **95% CI**: Confidence interval (mean ± margin of error)
- **Outliers**: Detected using 2σ threshold

## Regression Detection

Performance regression is detected when:

```
current_overhead_pct - baseline_overhead_pct > 1.0%
```

Example:
- Baseline overhead: 5.0%
- Current overhead: 6.5%
- Delta: +1.5% → **REGRESSION DETECTED**

## Success Criteria

From roadmap (Task 1.1.1):

✓ Performance test suite runs successfully at x1, x10, and x100 workload multipliers  
✓ Baseline measurements documented with confidence intervals (95% CI)  
✓ Statistical analysis includes: mean, median, std dev, min, max across multiple runs  
✓ Performance regression detection working (alerts on >1% degradation)  
✓ No explicit reference to prototype's 0.51% overhead (avoid anchoring bias)  

## Example Output

```
================================================================================
Small blocks (1ms) - Decorator - x10
================================================================================

Baseline (Unprofiled):
  Mean:       10.234 ms
  95% CI:     [10.123, 10.345] ms
  Std Dev:    0.112 ms

Profiled:
  Mean:       10.756 ms
  95% CI:     [10.634, 10.878] ms
  Std Dev:    0.123 ms

Overhead:
  Absolute:   522000 ns
  Percentage: 5.10%
  Slowdown:   1.05x

Success criterion check (≥1ms blocks):
  Overhead: 5.10% (target: ≤10%)
  Status: ✓ PASS
```

## Integration with CI/CD

These tests can be integrated into CI/CD pipeline:

1. **On every PR**: Run regression tests to catch performance degradation
2. **On release**: Establish new baseline for version tracking
3. **Nightly**: Run full overhead suite for comprehensive monitoring

## Baseline Versioning

Store version-specific baselines:

```
baselines/
├── v0.1.0/  # Prototype baseline
├── v0.2.0/  # Thread-safe implementation
└── v1.0.0/  # Production release
```

## Notes

- Tests skip gracefully if profiler implementation not available
- Designed to work with both prototype and v1.0.0 implementation
- Results exportable to JSON for tracking over time
- No hardcoded expected values (unbiased measurement)

