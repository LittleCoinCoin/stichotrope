## Competitive Benchmarking Suite

Compares Stichotrope against other Python profiling tools to establish competitive positioning.

## Profilers Compared

| Profiler | Type | Granularity | Installation |
|----------|------|-------------|--------------|
| **Stichotrope** | Instrumentation (explicit) | Block-level | `pip install stichotrope` |
| **cProfile** | Instrumentation (automatic) | Function-level | Built-in (stdlib) |
| **py-spy** | Sampling (external) | Function-level | `pip install py-spy` |
| **line_profiler** | Instrumentation (line-level) | Line-level | `pip install line_profiler` |
| **pyinstrument** | Statistical sampling | Function-level | `pip install pyinstrument` |

## Running Benchmarks

### Check Profiler Availability

```bash
pytest tests/performance/benchmarks/test_competitive.py::TestCompetitiveBenchmark::test_profiler_availability -v -s
```

### Run Overhead Comparison

```bash
pytest tests/performance/benchmarks/test_competitive.py::TestCompetitiveBenchmark::test_overhead_comparison -v -s
```

This will:
- Measure overhead for each available profiler
- Test with 1ms, 10ms, and 100ms workloads
- Export results to JSON
- Print comparison table

### View Feature Comparison

```bash
pytest tests/performance/benchmarks/test_competitive.py::TestCompetitiveBenchmark::test_feature_comparison -v -s
```

### View Use Case Recommendations

```bash
pytest tests/performance/benchmarks/test_competitive.py::TestCompetitiveBenchmark::test_use_case_recommendations -v -s
```

## Installing Competitors

To run full competitive benchmarks, install all profilers:

```bash
pip install line_profiler pyinstrument py-spy
```

Note: `cProfile` is built-in and always available.

## Benchmark Results

Results are exported to JSON format:

```json
{
  "workload_duration_ms": 10.0,
  "profilers": [
    {
      "profiler": "Stichotrope",
      "baseline_mean_ms": 10.234,
      "profiled_mean_ms": 10.756,
      "overhead_ns": 522000,
      "overhead_pct": 5.10,
      "iterations": 30
    },
    {
      "profiler": "cProfile",
      "baseline_mean_ms": 10.234,
      "profiled_mean_ms": 11.123,
      "overhead_ns": 889000,
      "overhead_pct": 8.68,
      "iterations": 30
    }
  ]
}
```

## Competitive Positioning

### Stichotrope Strengths

- **Block-level granularity**: Fills gap between function-level and line-level profiling
- **Multi-track organization**: Logical grouping of profiling data
- **Explicit instrumentation**: Decorators and context managers for precise control
- **Runtime enable/disable**: Zero overhead when disabled
- **CppProfiler compatibility**: Familiar API for C++ developers

### When to Use Stichotrope

1. **Block-level profiling needed**: More granular than cProfile, less overhead than line_profiler
2. **Multi-track organization**: Group related profiling data logically
3. **Production profiling**: Runtime enable/disable with zero overhead when disabled
4. **CppProfiler workflows**: Maintain consistency across C++ and Python codebases

### When to Use Competitors

- **cProfile**: Quick function-level profiling, no installation needed
- **py-spy**: Production profiling without code changes, sampling profiler
- **line_profiler**: Line-by-line profiling for debugging specific functions
- **pyinstrument**: Statistical profiling with call tree visualization

## Success Criteria

From roadmap (Task 1.1.2):

✓ Benchmark suite compares Stichotrope vs 4 competitors  
✓ Results exportable to JSON for tracking  
✓ Baseline competitive positioning documented  

## Example Output

```
================================================================================
Overhead Comparison - 10.0ms workload
================================================================================

Benchmarking Stichotrope...
  Baseline:  10.234 ms
  Profiled:  10.756 ms
  Overhead:  522000 ns (5.10%)

Benchmarking cProfile...
  Baseline:  10.234 ms
  Profiled:  11.123 ms
  Overhead:  889000 ns (8.68%)

================================================================================
SUMMARY
================================================================================

Profiler             Overhead (ns)   Overhead (%)    Status
--------------------------------------------------------------------------------
Stichotrope               522000 ns        5.10%     ✓ Good
cProfile                  889000 ns        8.68%     ✓ Good
pyinstrument             1234000 ns       12.05%     ⚠ High

================================================================================
```

