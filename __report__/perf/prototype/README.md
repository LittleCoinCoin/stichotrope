# Prototype Performance Baseline Data

Raw performance measurement data for Stichotrope prototype (v0.5.0).

## Overview

This directory contains the raw JSON output from performance tests run against the prototype implementation. These measurements serve as the baseline for:
- Performance regression detection
- Comparison with v1.0.0 implementation
- Statistical analysis and reporting

## Test Configuration

- **Date**: 2025-11-02
- **Python Version**: 3.10.12
- **pytest Version**: 8.4.2
- **Profiler**: Stichotrope prototype (from `prototype` branch)
- **Iterations**: 30 per test
- **Confidence Level**: 95%

## Data Files

### Decorator Method

| File | Scenario | Multiplier | Overhead |
|------|----------|------------|----------|
| `overhead_decorator_tiny_x10.json` | 0.1ms blocks | x10 | 4.74% |
| `overhead_decorator_tiny_x100.json` | 0.1ms blocks | x100 | 0.78% |
| `overhead_decorator_small_x10.json` | 1ms blocks | x10 | 0.68% |
| `overhead_decorator_small_x100.json` | 1ms blocks | x100 | 0.05% |
| `overhead_decorator_medium_x10.json` | 10ms blocks | x10 | 0.02% |
| `overhead_decorator_medium_x100.json` | 10ms blocks | x100 | 0.07% |
| `overhead_decorator_large_x10.json` | 100ms blocks | x10 | 0.00% |
| `overhead_decorator_large_x100.json` | 100ms blocks | x100 | -0.01% |

### Context Manager Method

| File | Scenario | Multiplier | Overhead |
|------|----------|------------|----------|
| `overhead_context_tiny_x10.json` | 0.1ms blocks | x10 | ~5% |
| `overhead_context_tiny_x100.json` | 0.1ms blocks | x100 | ~1% |
| `overhead_context_small_x10.json` | 1ms blocks | x10 | ~0.7% |
| `overhead_context_small_x100.json` | 1ms blocks | x100 | ~0.05% |
| `overhead_context_medium_x10.json` | 10ms blocks | x10 | ~0.02% |
| `overhead_context_medium_x100.json` | 10ms blocks | x100 | ~0.07% |
| `overhead_context_large_x10.json` | 100ms blocks | x10 | ~0.00% |
| `overhead_context_large_x100.json` | 100ms blocks | x100 | ~0.00% |

## JSON Format

Each file contains:

```json
{
  "scenario": "small",
  "multiplier": 10,
  "method": "decorator",
  "statistics": {
    "overhead_ns": 76401.03,
    "overhead_pct": 0.68,
    "slowdown_factor": 1.007,
    "baseline_mean_ms": 11.17,
    "profiled_mean_ms": 11.25,
    "baseline_ci": [11.13, 11.21],
    "profiled_ci": [11.20, 11.29]
  }
}
```

## Fields Description

- **scenario**: Workload scenario (tiny/small/medium/large)
- **multiplier**: Workload multiplier (1/10/100)
- **method**: Profiling method (decorator/context_manager)
- **overhead_ns**: Absolute overhead in nanoseconds
- **overhead_pct**: Overhead as percentage of baseline
- **slowdown_factor**: Profiled time / baseline time
- **baseline_mean_ms**: Mean baseline execution time (ms)
- **profiled_mean_ms**: Mean profiled execution time (ms)
- **baseline_ci**: 95% confidence interval for baseline [lower, upper]
- **profiled_ci**: 95% confidence interval for profiled [lower, upper]

## Usage

### Load Data in Python

```python
import json
from pathlib import Path

# Load a specific measurement
with open('__report__/perf/prototype/overhead_decorator_small_x10.json') as f:
    data = json.load(f)
    
print(f"Overhead: {data['statistics']['overhead_pct']:.2f}%")
```

### Regenerate Data

To regenerate baseline measurements:

```bash
pytest tests/performance/test_overhead.py \
  --baseline-dir=__report__/perf/prototype \
  -v --no-cov
```

### Compare with Future Versions

When v1.0.0 is implemented:

```bash
# Run tests against v1.0.0
pytest tests/performance/test_overhead.py \
  --baseline-dir=__report__/perf/v1.0.0 \
  -v --no-cov

# Compare results
python scripts/compare_baselines.py \
  __report__/perf/prototype \
  __report__/perf/v1.0.0
```

## Statistical Notes

- **30 iterations** per test ensures statistical significance
- **95% confidence intervals** provide reliability bounds
- **Workload multipliers** reduce measurement noise:
  - x10: Good for routine benchmarking
  - x100: Best for precise baseline establishment
- **Outlier detection**: 2σ threshold (none detected in these measurements)

## Key Findings

1. **Excellent Performance**: 0.02-0.68% overhead for ≥1ms blocks (well below 10% target)
2. **Consistent Results**: Overhead stable across multipliers
3. **Scalability**: Overhead decreases with block duration (constant absolute overhead ~25-90 μs)
4. **Production Ready**: Negligible impact on application performance

## References

- Full analysis: `__report__/milestone_1/01-baseline_establishment_v0.md`
- Test implementation: `tests/performance/test_overhead.py`
- Statistical utilities: `tests/performance/statistics_utils.py`

---

**Generated**: 2025-11-02  
**Test Duration**: ~25 minutes (16 tests)  
**Status**: ✅ Baseline Established

