# Performance Characteristics

Stichotrope is designed for low-overhead profiling of function and block execution times. This guide covers performance expectations and when Stichotrope is most effective.

## Performance Guarantee

**≤1% overhead for functions ≥1ms** - This guarantee is verified through systematic benchmarking against multiple versions (v0.1.0, v0.2.0) and comparisons with cProfile.

### Verified Overhead

Profiler overhead measured across realistic workloads:

| Workload Size | Measured Overhead | Status |
|---|---|---|
| 0.1ms (tiny) | 0.63-0.66% | ✅ Within tolerance |
| 1.0ms (small) | -0.21-0.37% | ✅ Effectively zero |
| 10.0ms (medium) | Negligible (< 0.1%) | ✅ Well below threshold |
| 100.0ms (large) | 0.02-0.05% | ✅ Minimal |

**Typical range for realistic applications**: 0.02-0.66% overhead

## Benchmarking Methodology

Performance claims are validated through:

1. **Systematic measurement**: Executions measured across multiple workload scenarios (tiny, small, medium, large) with varying multipliers (x1, x10, x100)
2. **Statistical testing**: Welch's t-test with p < 0.05 significance threshold and ±1 SD confidence intervals
3. **Multiple baselines**: Comparison against v0.1.0 prototype and cProfile for context
4. **Thread-safe implementation**: Performance verified in both single-threaded and multi-threaded scenarios

For detailed technical reports on benchmark design and analysis, see the [benchmark reports](https://github.com/LittleCoinCoin/stichotrope/tree/main/__reports__/analysis_performance_benchmarking).

## When to Use Stichotrope

### Best For

- **Functions with ≥1ms execution time**: Stichotrope overhead is negligible relative to execution time
- **Production profiling**: Can be enabled/disabled at runtime with zero overhead when disabled
- **Block-level analysis**: Need to profile specific code sections within functions
- **Multi-threaded applications**: Built-in thread-safety with minimal lock contention

### Consider Alternatives For

- **Microsecond-level profiling**: Use cProfile or sys.settrace for sub-millisecond functions
- **Line-level profiling**: Use py-spy or line_profiler for per-line analysis
- **Statistical sampling**: Use py-spy for low-overhead statistical profiling of large codebases

## Zero Overhead When Disabled

When profiling is disabled globally (`set_global_enabled(False)`), decorators return identity functions with no profiling overhead. This makes Stichotrope suitable for production use with conditional profiling:

```python
from stichotrope import Profiler, set_global_enabled
import os

# Enable profiling only in development/debug mode
profiler = Profiler("MyApp")
set_global_enabled(os.getenv("DEBUG_PROFILING", "false").lower() == "true")

@profiler.track(0, "expensive_operation")
def expensive_operation():
    # Zero overhead in production when DEBUG_PROFILING is false
    pass
```

## Developer Benchmarks

The project includes comprehensive benchmarking infrastructure for verifying performance claims and comparing implementations:

```
benchmarks/
├── README.md                 # How to run benchmarks
├── constant_overhead.py      # Measure per-call overhead
├── overhead_benchmark.py     # Workload-based overhead measurement
├── cprofile_comparison.py    # Compare with cProfile
├── realistic_workload.py     # Real-world scenario profiling
└── data/
    └── v0.2.0/              # Benchmark results for v0.2.0
```

To reproduce benchmarks and verify performance characteristics, see [Benchmarks README](../../benchmarks/README.md).

## Performance Tips

1. **Profile blocks ≥1ms**: Best performance/overhead trade-off
2. **Use decorators for whole functions**: More efficient than context managers for function-level profiling
3. **Organize with tracks**: Use multiple tracks to organize profiling logically without performance impact
4. **Enable/disable at runtime**: Use `set_global_enabled()` to reduce profiling overhead when not needed

## See Also

- [API Reference - Profiler](../api/profiler.md) - Complete API documentation
- [Getting Started](./GettingStarted.md) - Installation and basic usage
- [Developer Architecture](../devs/architecture.md) - Internal design details (thread-safety, locking strategy)
