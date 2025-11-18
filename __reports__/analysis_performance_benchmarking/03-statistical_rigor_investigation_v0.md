# Statistical Rigor Investigation & Implementation Plan

**Date**: 2025-11-16
**Version**: v1 (Revised with simplified scope)
**Author**: AI Agent
**Status**: Investigation Complete, Implementation Approved

---

## Executive Summary

Investigation confirms that current performance comparison lacks statistical rigor. Raw measurement data is captured but not persisted, and no hypothesis testing is performed. This report documents findings and proposes a streamlined solution focused on engineering-quality statistical validation.

**Scope**: Production software project requiring sound statistical validation for engineering decisions, not academic publication.

**Critical Findings**:
1. ✅ Raw data IS captured (30 measurements per test)
2. ❌ Raw data is NOT persisted to JSON files
3. ✅ Statistical infrastructure exists (CI calculation, outlier detection)
4. ❌ No hypothesis testing (t-tests, p-values)
5. ❌ Graphs lack error bars
6. 🐛 Context Method graph bug identified (method name mismatch)

---

## 1. Current Data Capture Analysis

### 1.1 Raw Data Capture

**File**: `tests/performance/test_overhead.py`

**Evidence** (Lines 77-89, 91-113):
```python
def measure_baseline(self, workload_func, iterations: int = 30) -> list[float]:
    """Returns list of execution times in seconds"""
    times = timeit.repeat(workload_func, repeat=iterations, number=1)
    return times  # ✅ Raw data captured as list of 30 measurements
```

**Conclusion**: ✅ Raw data IS captured during test execution

### 1.2 Data Persistence

**File**: `tests/performance/test_overhead.py` (Lines 174-200)

**Current JSON Structure**:
```json
{
  "scenario": "small",
  "multiplier": 10,
  "method": "decorator",
  "statistics": {
    "overhead_ns": 89743.33,
    "overhead_pct": 0.59,
    "baseline_mean_ms": 15.20,
    "profiled_mean_ms": 15.29,
    "baseline_ci": [15.16, 15.23],
    "profiled_ci": [15.22, 15.35]
  }
}
```

**Missing**: Raw measurement arrays (`baseline_times`, `profiled_times`)

**Conclusion**: ❌ Only aggregated statistics are persisted

### 1.3 Statistical Infrastructure

**File**: `tests/performance/statistics_utils.py`

**Existing Capabilities**:
- ✅ Confidence interval calculation (t-distribution for n<30, z-distribution for n≥30)
- ✅ Outlier detection (z-score method)
- ✅ Comprehensive statistics (mean, median, std_dev, min, max, CI)
- ❌ No hypothesis testing (t-tests, p-values)
- ❌ No effect size calculation (Cohen's d)
- ❌ No equivalence testing (TOST)

**Conclusion**: Good foundation, but missing hypothesis testing

---

## 2. Context Method Graph Bug

### 2.1 Root Cause

**File**: `scripts/compare_baselines.py` (Line 64)
```python
methods = ['decorator', 'context']  # ❌ Wrong name
```

**File**: `tests/performance/test_overhead.py` (Line 252)
```python
"method": "context_manager"  # ✅ Actual name in JSON
```

**File**: `__report__/perf/v0.2.0/overhead_context_small_x10.json` (Line 4)
```python
"method": "context_manager"  # ✅ Confirmed
```

### 2.2 Fix

Change line 64 in `scripts/compare_baselines.py`:
```python
methods = ['decorator', 'context_manager']  # ✅ Correct
```

**Impact**: This will make context manager data visible in graphs

---

## 3. Statistical Testing Requirements

### 3.1 Research Findings

**Best Practices for Engineering-Quality Performance Comparison**:

1. **Welch's t-test** (recommended over Student's t-test)
   - Does not assume equal variances
   - More robust for real-world data
   - Implementation: `scipy.stats.ttest_ind(a, b, equal_var=False)`

2. **Two-sided test** (default)
   - Tests if means are different in either direction
   - Null hypothesis: μ₁ = μ₂
   - Alternative hypothesis: μ₁ ≠ μ₂

3. **P-value interpretation**:
   - p < 0.05: Statistically significant difference
   - p ≥ 0.05: No statistically significant difference

4. **Error bars**: ±1 SD (standard deviation)
   - Shows variability in measurements
   - More intuitive for engineers than confidence intervals
   - Easier to interpret than statistical jargon

**Simplified Scope** (removed from original plan):
- ❌ TOST equivalence testing (academic, not needed for engineering decisions)
- ❌ Cohen's d effect size (statistical jargon, not user-facing)
- ❌ Extensive statistical reports (focus on concise, actionable insights)

### 3.2 Required Dependencies

Add to `pyproject.toml` (dev dependencies):
```toml
[project.optional-dependencies]
dev = [
    "scipy>=1.11.0",  # For Welch's t-test
    "matplotlib>=3.8.0",  # For visualizations (already installed)
    # ... existing deps
]
```

---

## 4. Implementation Plan

### 4.1 Phase 1: Infrastructure Improvements

**Goal**: Enhance benchmark infrastructure to capture raw data and perform statistical tests

**Tasks**:
1. ✅ Fix Context Method graph bug (5 min)
2. Update `test_overhead.py` to persist raw measurement data (30 min)
3. Add Welch's t-test to `statistics_utils.py` (20 min):
   - `perform_welch_ttest(group1, group2)` → (t_statistic, p_value)
4. Update graph generation to include ±1 SD error bars (30 min)
5. Add p-value annotations to comparison graphs (20 min)

**Total Effort**: ~1.75 hours

### 4.2 Phase 2: New Benchmarks

**Goal**: Create missing benchmarks for constant overhead and cProfile comparison

**Task 1: Constant Overhead Benchmark**

**Purpose**: Measure profiler's constant overhead per operation

**Implementation** (`benchmarks/constant_overhead.py`):
```python
def measure_constant_overhead(iterations=1000):
    """Measure profiler's constant overhead by profiling minimal function"""

    def minimal_function():
        """Minimal function that does almost nothing"""
        return 42

    # Measure baseline
    baseline_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        minimal_function()
        baseline_times.append(time.perf_counter() - start)

    # Measure with profiler
    profiler = Profiler("ConstantOverhead")

    @profiler.track(0, "minimal")
    def profiled_minimal():
        return 42

    profiled_times = []
    for _ in range(iterations):
        start = time.perf_counter()
        profiled_minimal()
        profiled_times.append(time.perf_counter() - start)

    # Calculate constant overhead
    overhead_times = [p - b for p, b in zip(profiled_times, baseline_times)]

    return {
        "raw_baseline_times": baseline_times,
        "raw_profiled_times": profiled_times,
        "raw_overhead_times": overhead_times,
        "mean_overhead_us": statistics.mean(overhead_times) * 1e6,
        "std_overhead_us": statistics.stdev(overhead_times) * 1e6,
        "ci_95": calculate_confidence_interval(overhead_times),
    }
```

**Output**: Raw data + statistics showing ~1.8 µs claim validation

**Task 2: cProfile Comparison Benchmark**

**Purpose**: Compare Stichotrope vs cProfile for equivalent workloads

**Implementation** (`benchmarks/cprofile_comparison.py`):
```python
def compare_with_cprofile(workload_func, iterations=30):
    """Compare Stichotrope vs cProfile timing accuracy"""

    # Measure baseline (no profiling)
    baseline_times = timeit.repeat(workload_func, repeat=iterations, number=1)

    # Measure with Stichotrope
    profiler = Profiler("Comparison")

    @profiler.track(0, "workload")
    def stichotrope_workload():
        return workload_func()

    stichotrope_times = timeit.repeat(stichotrope_workload, repeat=iterations, number=1)

    # Measure with cProfile
    def cprofile_workload():
        profiler = cProfile.Profile()
        profiler.enable()
        result = workload_func()
        profiler.disable()
        return result

    cprofile_times = timeit.repeat(cprofile_workload, repeat=iterations, number=1)

    # Statistical comparison
    stich_vs_baseline = perform_welch_ttest(stichotrope_times, baseline_times)
    cprof_vs_baseline = perform_welch_ttest(cprofile_times, baseline_times)
    stich_vs_cprof = perform_welch_ttest(stichotrope_times, cprofile_times)

    return {
        "raw_baseline_times": baseline_times,
        "raw_stichotrope_times": stichotrope_times,
        "raw_cprofile_times": cprofile_times,
        "statistics": {
            "baseline": calculate_statistics(baseline_times),
            "stichotrope": calculate_statistics(stichotrope_times),
            "cprofile": calculate_statistics(cprofile_times),
        },
        "statistical_tests": {
            "stichotrope_vs_baseline": stich_vs_baseline,
            "cprofile_vs_baseline": cprof_vs_baseline,
            "stichotrope_vs_cprofile": stich_vs_cprof,
        }
    }
```

**Output**: Statistical comparison showing timing equivalence or differences

**Effort**: ~3 hours total (1.5 hours each)

### 4.3 Phase 3: Measurement Regeneration

**Goal**: Regenerate all measurements with improved infrastructure

**Approach Evaluation**:

The user proposed a git workflow involving:
1. Branch `refactor/perf-benchmarks` for infrastructure
2. Checkout prototype at tag `v0.1.0`
3. Branch `perf/prototype-measures` from prototype
4. Cherry-pick measurements back

**Analysis**:
- ✅ Separates infrastructure from measurements
- ✅ Preserves prototype code state
- ⚠️ Cherry-pick may be complex if infrastructure changes significantly
- ⚠️ Copying scripts manually is error-prone

**Improved Workflow**:

```
1. Create infrastructure branch
   git checkout -b refactor/perf-benchmarks

2. Implement all infrastructure improvements
   - Update test_overhead.py (raw data persistence)
   - Update statistics_utils.py (hypothesis testing)
   - Update compare_baselines.py (error bars, p-values)
   - Create constant_overhead.py
   - Create cprofile_comparison.py
   - Commit all infrastructure changes

3. Generate v0.2.0 measurements (current thread-safe)
   pytest tests/performance/test_overhead.py --baseline-dir=__report__/perf/v0.2.0_raw -v
   python benchmarks/constant_overhead.py > __report__/perf/v0.2.0_raw/constant_overhead.json
   python benchmarks/cprofile_comparison.py > __report__/perf/v0.2.0_raw/cprofile_comparison.json
   git add __report__/perf/v0.2.0_raw/
   git commit -m "perf: Add v0.2.0 baseline measurements with raw data"

4. Generate prototype measurements
   # Save current HEAD
   CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

   # Checkout prototype code
   git checkout v0.1.0  # Tag: 5fe3a02f578a5b17bdfbab73e8b1b66a99e9c4c0

   # Create temporary branch
   git checkout -b temp/prototype-measurements

   # Cherry-pick ONLY the infrastructure commits (not measurements)
   git cherry-pick <infrastructure-commit-sha>

   # Run measurements
   pytest tests/performance/test_overhead.py --baseline-dir=__report__/perf/prototype_raw -v
   python benchmarks/constant_overhead.py > __report__/perf/prototype_raw/constant_overhead.json
   python benchmarks/cprofile_comparison.py > __report__/perf/prototype_raw/cprofile_comparison.json

   # Commit measurements
   git add __report__/perf/prototype_raw/
   git commit -m "perf: Add prototype baseline measurements with raw data"

   # Return to infrastructure branch
   git checkout $CURRENT_BRANCH

   # Cherry-pick measurement commit
   git cherry-pick temp/prototype-measurements

   # Clean up
   git branch -D temp/prototype-measurements

5. Generate statistical comparison
   python scripts/compare_baselines.py --prototype=__report__/perf/prototype_raw --threadsafe=__report__/perf/v0.2.0_raw
   git add __reports__/analysis_performance_benchmarking/
   git commit -m "docs: Add statistically rigorous performance comparison"
```

**Advantages**:
- ✅ Clean separation of concerns
- ✅ Reproducible workflow
- ✅ Preserves git history
- ✅ Easy to re-run if needed

**Effort**: ~2 hours (mostly waiting for tests)

### 4.4 Phase 4: Statistical Analysis & Reporting

**Goal**: Generate engineering-quality comparison with statistical validation

**Deliverables**:

1. **Updated Comparison Graphs** (`comparison_x10.png`, `comparison_x100.png`):
   - ±1 SD error bars on all data points
   - P-value annotations for key comparisons
   - Professional styling suitable for README
   - Clear legends and labels

2. **Concise Comparison Report** (`04-statistical_comparison_v0.md`):
   - Clear conclusions backed by statistical evidence
   - P-values for each scenario/multiplier combination
   - User-friendly interpretation (avoid statistical jargon)
   - Actionable insights for users

3. **Constant Overhead Report** (`05-constant_overhead_v0.md`):
   - Histogram showing overhead distribution
   - Validation of ~1.8 µs claim with statistical confidence
   - Concise summary suitable for README

4. **cProfile Comparison Report** (`06-cprofile_comparison_v0.md`):
   - Timing accuracy comparison with p-values
   - Performance overhead comparison
   - Concise recommendations

**Effort**: ~2 hours (simplified scope)

---

## 5. Success Criteria

### 5.1 Data Transparency

- [x] Raw measurement data captured (already done)
- [ ] Raw measurement data persisted in JSON files
- [ ] All measurements reproducible from raw data

### 5.2 Statistical Rigor

- [ ] Welch's t-test performed for all comparisons
- [ ] P-values computed and reported
- [ ] ±1 SD error bars on all graphs

### 5.3 Visualization Quality

- [ ] ±1 SD error bars on all graphs
- [ ] P-value annotations on key comparisons
- [ ] Context Method graph displays correctly
- [ ] Professional-quality figures suitable for README

### 5.4 New Benchmarks

- [ ] Constant overhead benchmark implemented
- [ ] Constant overhead ~1.8 µs claim validated
- [ ] cProfile comparison benchmark implemented
- [ ] Statistical comparison with cProfile completed

### 5.5 Documentation

- [ ] All claims backed by statistical evidence
- [ ] P-values reported with user-friendly interpretation
- [ ] Concise, engineering-focused reports (no statistical jargon)
- [ ] Actionable insights for users

---

## 6. Total Effort Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Infrastructure | Fix bug, update tests, add Welch's t-test, improve graphs | 1.75 hours |
| Phase 2: New Benchmarks | Constant overhead, cProfile comparison | 3 hours |
| Phase 3: Regeneration | Run all measurements for both versions | 2 hours |
| Phase 4: Analysis | Statistical comparison, reports, visualizations | 2 hours |
| **Total** | | **8.75 hours** |

**Note**: Streamlined scope focused on engineering-quality statistical validation. The work is systematic and builds on existing infrastructure.

---

## 7. Implementation Status

**Approved by User**: ✅ 2025-11-16

**Approved Decisions**:
- ✅ Git workflow approved (improved version)
- ✅ Statistical testing: Welch's t-test only (no TOST, no Cohen's d)
- ✅ Error bars: ±1 SD (standard deviation)
- ✅ Scope: Engineering-focused, not academic publication
- ✅ Dependencies: scipy>=1.11.0 approved

**Next Action**: Begin Phase 1 implementation

---

**Last Updated**: 2025-11-16 (v1 - Simplified scope approved)
