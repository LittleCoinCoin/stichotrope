# Performance Benchmarking Suite

This directory contains all performance benchmarking infrastructure for Stichotrope.

## Directory Structure

```
benchmarks/
├── data/                           # Performance measurement data
│   ├── prototype/                  # v0.1.0 prototype baseline measurements
│   └── v0.2.0/                     # v0.2.0 thread-safe baseline measurements
├── overhead_measurement.py         # Main overhead measurement script
├── constant_overhead.py            # Constant overhead benchmark
├── cprofile_comparison.py          # cProfile comparison benchmark
├── workloads.py                    # Workload simulation utilities
├── statistics_utils.py             # Statistical analysis utilities
└── compare_baselines.py            # Baseline comparison and visualization

```

## Quick Start

### 1. Measure Overhead (Current Implementation)

```bash
# Measure overhead for v0.2.0 thread-safe implementation
pytest benchmarks/overhead_measurement.py \
  --baseline-dir=benchmarks/data/v0.2.0 \
  -v
```

### 2. Measure Constant Overhead

```bash
python benchmarks/constant_overhead.py \
  --iterations=1000 \
  --output=benchmarks/data/v0.2.0/constant_overhead.json
```

### 3. Compare with cProfile

```bash
python benchmarks/cprofile_comparison.py \
  --output=benchmarks/data/v0.2.0/cprofile_comparison.json
```

### 4. Generate Comparison Report

```bash
python benchmarks/compare_baselines.py
```

This generates:
- `__reports__/analysis_performance_benchmarking/comparison_x10.png`
- `__reports__/analysis_performance_benchmarking/comparison_x100.png`
- `__reports__/analysis_performance_benchmarking/02-prototype_comparison_v1.md`

## Performance Targets

### PRIMARY Success Criterion
**≤1% overhead for functions ≥1ms execution time**

### SECONDARY Success Criterion
**Competitive with cProfile for function-level profiling**

## Measurement Methodology

- **30 iterations** per measurement using `timeit.repeat()`
- **Welch's t-test** for statistical significance (p < 0.05)
- **±1 SD error bars** on all graphs
- **Raw data persistence** for transparency and reproducibility
- **Workload multipliers**: x1, x10, x100 to reduce measurement noise
- **Workload scenarios**: tiny (0.1ms), small (1ms), medium (10ms), large (100ms)

## Data Format

All measurement files are JSON with the following structure:

```json
{
  "scenario": "medium",
  "multiplier": 100,
  "method": "decorator",
  "raw_data": {
    "baseline_times_ms": [1050.83, 1051.42, ...],
    "profiled_times_ms": [1050.73, 1049.97, ...]
  },
  "statistics": {
    "overhead_ns": -99468.69,
    "overhead_pct": -0.0095,
    "baseline_mean_ms": 1050.831,
    "profiled_mean_ms": 1050.731,
    "baseline_std_ms": 1.234,
    "profiled_std_ms": 1.456,
    "baseline_ci": [1050.12, 1051.54],
    "profiled_ci": [1049.98, 1051.48]
  }
}
```

## Regression Testing

Performance regression tests are in `tests/performance/test_regression.py` and run as part of the test suite:

```bash
pytest tests/performance/test_regression.py -v
```

These tests compare current performance against stored baselines and **fail** if overhead increases by >1%.

## Contributing

When adding new benchmarks:
1. Follow the existing data format
2. Use `statistics_utils.py` for statistical analysis
3. Save raw measurement data for reproducibility
4. Update this README with new benchmark descriptions
5. Commit data files to track performance over time