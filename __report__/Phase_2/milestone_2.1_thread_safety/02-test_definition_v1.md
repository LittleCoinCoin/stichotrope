# Thread-Safe Test Suite Definition

**Task**: 2.1.2 – Design Thread-Safe Test Suite  
**Issue**: [#19](https://github.com/LittleCoinCoin/stichotrope/issues/19)  
**Milestone**: 2.1 Thread-Safe Architecture Redesign  
**Version Target**: v0.2.0  
**Report Version**: v1 (refined)  
**Date**: 2025-11-07  
**Status**: Awaiting stakeholder review  
**Dependencies**: Task 2.1.1 (Architecture Design) - ✅ APPROVED

---

## Changes from v0

### Improvements Based on Stakeholder Feedback

**1. Replaced Wobble with pytest**
- ✅ Removed all Wobble-specific content (framework, decorators, CLI examples)
- ✅ Added pytest-specific guidance (markers, fixtures, execution patterns)
- ✅ Updated all decorator examples to use pytest markers
- ✅ Updated CI/CD examples to use pytest commands

**2. Added Dependency Recommendations**
- ✅ Identified additional dev dependencies needed for thread-safety tests
- ✅ Recommended pytest-timeout (deadlock detection)
- ✅ Recommended psutil (memory usage measurement)

**3. Fixed Test Development Workflow Section**
- ✅ Renamed to "Initial Test Implementation Workflow" (clarifies one-time vs ongoing)
- ✅ Added note about expected test failures before implementation
- ✅ Clarified that tests run regularly (not just during Task 2.1.3)
- ✅ Replaced "Phase" with "Step" (avoid hierarchy confusion)

**4. Updated Test Execution Examples**
- ✅ All examples now use pytest commands
- ✅ Added pytest marker-based filtering examples
- ✅ Updated CI/CD pipeline examples

### Rationale

- **pytest standard**: Stichotrope uses pytest (already in dev dependencies), not Wobble
- **Dependency clarity**: Explicit about what's needed for thread-safety testing
- **Workflow clarity**: Distinguish initial implementation from ongoing test execution
- **Terminology consistency**: "Step" vs "Phase" avoids confusion with milestone phases

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Test Strategy](#test-strategy)
3. [Test Categories](#test-categories)
   - [A. Thread-Local Storage Tests](#a-thread-local-storage-tests)
   - [B. Lock Protection Tests](#b-lock-protection-tests)
   - [C. Aggregation Tests](#c-aggregation-tests)
   - [D. Multi-Threaded Integration Tests](#d-multi-threaded-integration-tests)
   - [E. Stress Tests](#e-stress-tests)
   - [F. Performance Tests](#f-performance-tests)
4. [Test Infrastructure](#test-infrastructure)
5. [Test File Organization](#test-file-organization)
6. [Development Dependencies](#development-dependencies)
7. [Success Criteria Mapping](#success-criteria-mapping)
8. [Implementation Guidance](#implementation-guidance)
9. [Conclusion](#conclusion)

---

## Executive Summary

This document defines a comprehensive test suite for validating the thread-safe architecture redesign of Stichotrope v1.0.0 (Milestone 2.1).

**Test Strategy**: Multi-layered validation covering unit tests, integration tests, stress tests, and performance tests to ensure thread-safety correctness and performance targets.

**Test Categories**:
1. **Thread-Local Storage Tests** (4 unit tests) - Verify thread isolation and data independence
2. **Lock Protection Tests** (3 unit tests) - Verify lock-protected global structures
3. **Aggregation Tests** (4 unit tests) - Verify sequential merge algorithm correctness
4. **Multi-Threaded Integration Tests** (6 integration tests) - Verify concurrent profiling scenarios
5. **Stress Tests** (4 integration tests) - Verify behavior under high load
6. **Performance Tests** (3 performance tests) - Verify overhead and performance targets

**Total Test Count**: 24 tests

**Coverage Areas**:
- Thread-local storage isolation (zero contention in hot path)
- Lock-protected global structures (call-site cache, profiler registry, thread data registry)
- Aggregation algorithm correctness (sequential merge)
- Multi-threaded profiling scenarios (thread pools, concurrent operations)
- Stress scenarios (high thread count, high measurement frequency)
- Performance targets (≤1% overhead increase, <10ms aggregation)

**Testing Framework**: pytest (standard Python testing framework)

**Test Categorization**: pytest markers for test selection and filtering

---

## Test Strategy

### Testing Approach

Based on the approved architecture design (Task 2.1.1), the test strategy focuses on:

1. **Thread-Safety Validation**: Verify that concurrent access to profiler data structures is safe
2. **Correctness Validation**: Verify that aggregation produces correct results
3. **Performance Validation**: Verify that thread-safety overhead meets targets (≤1% increase)
4. **Stress Validation**: Verify behavior under high load (100+ threads, 100K+ measurements)

### Testing Principles

**What to Test** (our implementation):
- ✅ Thread-local storage initialization pattern (hasattr check + registration)
- ✅ Aggregation algorithm (sequential merge logic)
- ✅ Lock usage patterns (correct acquisition order, no deadlocks)
- ✅ Data isolation (threads don't interfere with each other)
- ✅ API behavior under multi-threading

**What NOT to Test** (trust standard library):
- ❌ `threading.local()` behavior (trust Python stdlib)
- ❌ `threading.RLock()` behavior (trust Python stdlib)
- ❌ `threading.get_ident()` behavior (trust Python stdlib)
- ❌ Dict operations thread-safety (trust Python GIL)

### Test Priorities

**Priority 1 (Critical)**: Thread-local storage, lock protection, aggregation correctness
**Priority 2 (High)**: Multi-threaded integration, concurrent operations
**Priority 3 (Medium)**: Stress tests, edge cases
**Priority 4 (Low)**: Performance tests (informational, not blocking)

### Success Criteria

Tests must verify:
1. **Correctness**: No race conditions, no data corruption, correct aggregation
2. **Safety**: No deadlocks, no AttributeError, no KeyError
3. **Performance**: Hot path overhead ≤1% increase vs prototype
4. **Scalability**: Handles 100+ threads without degradation

---

## Test Categories

### A. Thread-Local Storage Tests

**Purpose**: Verify that each thread maintains independent profiling data with zero contention in the hot path.

**Test File**: `tests/unit/test_thread_local_storage.py`

**Markers**: `@pytest.mark.unit`, `@pytest.mark.thread_safety`

#### Test 1: Thread-Local Storage Isolation

**Test Name**: `test_thread_local_storage_isolation`

**Purpose**: Verify that each thread maintains independent profiling data without cross-thread interference.

**Setup**:
- Create profiler instance
- Define simple profiled function

**Test Steps**:
1. Execute profiled function in Thread 1 (10 calls, sleep 1ms each)
2. Execute profiled function in Thread 2 (20 calls, sleep 2ms each)
3. Wait for both threads to complete
4. Get aggregated results from profiler

**Expected Behavior**:
- Thread 1 records 10 hits with ~1ms average time
- Thread 2 records 20 hits with ~2ms average time
- Aggregated results: hit_count=30, correct min/max/total
- No cross-thread interference (Thread 1 data unchanged by Thread 2)

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 30
assert results.tracks[0].blocks[0].min_time_ns >= 1_000_000  # ~1ms
assert results.tracks[0].blocks[0].max_time_ns >= 2_000_000  # ~2ms
```

---

#### Test 2: Thread Registration in Global Registry

**Test Name**: `test_thread_registration_in_global_registry`

**Purpose**: Verify that threads are correctly registered in the profiler's global thread data registry.

**Setup**:
- Create profiler instance
- Define profiled function

**Test Steps**:
1. Execute profiled function in 3 different threads
2. Access profiler's `_all_thread_data` registry (via internal API)
3. Verify thread count and thread IDs

**Expected Behavior**:
- Registry contains exactly 3 thread entries
- Each thread ID is unique
- Each thread has independent data structures

**Validation**:
```python
assert len(profiler._all_thread_data) == 3
thread_ids = list(profiler._all_thread_data.keys())
assert len(set(thread_ids)) == 3  # All unique
```

---

#### Test 3: Thread-Local Initialization Pattern

**Test Name**: `test_thread_local_initialization_pattern`

**Purpose**: Verify that thread-local storage is correctly initialized on first access using the hasattr pattern.

**Setup**:
- Create profiler instance
- Define profiled function

**Test Steps**:
1. Execute profiled function in new thread
2. Verify thread-local attributes are initialized
3. Verify no AttributeError is raised

**Expected Behavior**:
- First access initializes thread-local storage
- Subsequent accesses use existing storage
- No AttributeError on first access

**Validation**:
```python
# This test verifies the pattern works correctly
# by executing profiled code in a new thread
# and checking that no exceptions are raised
```

---

#### Test 4: Thread-Local Measurement Recording

**Test Name**: `test_thread_local_measurement_recording`

**Purpose**: Verify that measurement recording operates on thread-local data without locks.

**Setup**:
- Create profiler instance
- Define profiled function with known execution time

**Test Steps**:
1. Execute profiled function in Thread 1 (record start time)
2. Simultaneously execute in Thread 2 (record start time)
3. Verify both threads record measurements independently
4. Verify no blocking or contention

**Expected Behavior**:
- Both threads record measurements concurrently
- No blocking (execution time ≈ single-thread time)
- Measurements are accurate

**Validation**:
```python
# Verify concurrent execution (no blocking)
assert total_execution_time < 2 * single_thread_time
# Verify both threads recorded data
assert len(profiler._all_thread_data) == 2
```

---

### B. Lock Protection Tests

**Purpose**: Verify that lock-protected global structures are safe under concurrent access.

**Test File**: `tests/unit/test_lock_protection.py`

**Markers**: `@pytest.mark.unit`, `@pytest.mark.thread_safety`

#### Test 5: Call-Site Cache Concurrent Access

**Test Name**: `test_call_site_cache_concurrent_access`

**Purpose**: Verify that the global call-site cache is protected by `_GLOBAL_CACHE_LOCK` during concurrent decorator application.

**Setup**:
- Create profiler instance
- Define 10 different functions to be decorated

**Test Steps**:
1. Apply decorators to all 10 functions concurrently from 5 threads
2. Verify call-site cache is populated correctly
3. Verify no KeyError or race conditions

**Expected Behavior**:
- All 10 call-sites are registered in cache
- No duplicate entries
- No KeyError during concurrent access

**Validation**:
```python
assert len(_CALL_SITE_CACHE) == 10
# Verify all entries are valid
for key, value in _CALL_SITE_CACHE.items():
    assert isinstance(value, tuple)
    assert len(value) == 2  # (profiler_id, block_idx)
```

---

#### Test 6: Profiler Registry Concurrent Access

**Test Name**: `test_profiler_registry_concurrent_access`

**Purpose**: Verify that the global profiler registry is protected by `_REGISTRY_LOCK` during concurrent profiler instantiation.

**Setup**:
- No pre-existing profilers

**Test Steps**:
1. Create 10 profiler instances concurrently from 5 threads
2. Verify all profilers are registered
3. Verify profiler IDs are unique and sequential

**Expected Behavior**:
- All 10 profilers registered in `_PROFILER_REGISTRY`
- Profiler IDs are unique (0-9)
- No race condition in ID allocation

**Validation**:
```python
assert len(_PROFILER_REGISTRY) == 10
profiler_ids = list(_PROFILER_REGISTRY.keys())
assert profiler_ids == list(range(10))  # Sequential IDs
```

---

#### Test 7: Lock Hierarchy Compliance

**Test Name**: `test_lock_hierarchy_compliance`

**Purpose**: Verify that locks are acquired in the correct order to prevent deadlocks.

**Markers**: `@pytest.mark.unit`, `@pytest.mark.thread_safety`, `@pytest.mark.timeout(10)`

**Setup**:
- Create profiler instance
- Define scenario requiring multiple locks

**Test Steps**:
1. Execute operations requiring lock acquisition in correct order
2. Execute operations from multiple threads concurrently
3. Verify no deadlocks occur (pytest-timeout will fail test if deadlock)

**Expected Behavior**:
- All operations complete successfully
- No deadlocks (all threads complete within timeout)
- Lock hierarchy: _REGISTRY_LOCK → _GLOBAL_CACHE_LOCK → Profiler._global_lock

**Validation**:
```python
# pytest-timeout marker ensures test fails if deadlock occurs
# All threads should complete successfully
assert all(thread.is_alive() == False for thread in threads)
```

---

### C. Aggregation Tests

**Purpose**: Verify that the sequential merge algorithm produces correct aggregated results.

**Test File**: `tests/unit/test_aggregation.py`

**Markers**: `@pytest.mark.unit`, `@pytest.mark.thread_safety`

#### Test 8: Sequential Merge Correctness

**Test Name**: `test_sequential_merge_correctness`

**Purpose**: Verify that the sequential merge algorithm correctly aggregates statistics from multiple threads.

**Setup**:
- Create profiler instance
- Define profiled function with controlled execution time

**Test Steps**:
1. Execute profiled function in Thread 1: 10 calls, 1ms each
2. Execute profiled function in Thread 2: 20 calls, 2ms each
3. Execute profiled function in Thread 3: 30 calls, 3ms each
4. Get aggregated results

**Expected Behavior**:
- hit_count: 10 + 20 + 30 = 60
- total_time_ns: (10×1ms) + (20×2ms) + (30×3ms) = 140ms
- min_time_ns: min(1ms, 2ms, 3ms) = 1ms
- max_time_ns: max(1ms, 2ms, 3ms) = 3ms

**Validation**:
```python
block = results.tracks[0].blocks[0]
assert block.hit_count == 60
assert block.total_time_ns == pytest.approx(140_000_000, rel=0.1)
assert block.min_time_ns <= 1_100_000  # ~1ms with tolerance
assert block.max_time_ns >= 2_900_000  # ~3ms with tolerance
```

---

#### Test 9: Multi-Thread Aggregation with Different Blocks

**Test Name**: `test_multi_thread_aggregation_different_blocks`

**Purpose**: Verify that aggregation correctly handles threads profiling different blocks.

**Setup**:
- Create profiler instance
- Define 3 different profiled functions (blocks A, B, C)

**Test Steps**:
1. Thread 1 profiles block A (10 calls)
2. Thread 2 profiles block B (20 calls)
3. Thread 3 profiles blocks A and C (5 calls each)
4. Get aggregated results

**Expected Behavior**:
- Block A: hit_count = 15 (10 from T1 + 5 from T3)
- Block B: hit_count = 20 (20 from T2)
- Block C: hit_count = 5 (5 from T3)

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 15  # Block A
assert results.tracks[0].blocks[1].hit_count == 20  # Block B
assert results.tracks[0].blocks[2].hit_count == 5   # Block C
```

---

#### Test 10: Empty Thread Handling

**Test Name**: `test_empty_thread_handling`

**Purpose**: Verify that aggregation correctly handles threads with no profiling data.

**Setup**:
- Create profiler instance
- Define profiled function

**Test Steps**:
1. Thread 1 executes profiled function (10 calls)
2. Thread 2 starts but doesn't execute profiled function (empty data)
3. Thread 3 executes profiled function (20 calls)
4. Get aggregated results

**Expected Behavior**:
- Aggregation skips empty thread data
- Results only include data from Thread 1 and Thread 3
- hit_count = 30

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 30
assert len(profiler._all_thread_data) == 3  # All threads registered
```

---

#### Test 11: Aggregation Preserves Metadata

**Test Name**: `test_aggregation_preserves_metadata`

**Purpose**: Verify that aggregation preserves block metadata (name, file, line).

**Setup**:
- Create profiler instance
- Define profiled function with known metadata

**Test Steps**:
1. Execute profiled function in 3 threads
2. Get aggregated results
3. Verify metadata is preserved

**Expected Behavior**:
- Block name matches original
- File path matches original
- Line number matches original

**Validation**:
```python
block = results.tracks[0].blocks[0]
assert block.name == "test_function"
assert "test_file.py" in block.file
assert block.line > 0
```

---

### D. Multi-Threaded Integration Tests

**Purpose**: Verify that profiler works correctly in realistic multi-threaded scenarios.

**Test File**: `tests/integration/test_multithreaded_profiling.py`

**Markers**: `@pytest.mark.integration`, `@pytest.mark.thread_safety`

#### Test 12: ThreadPoolExecutor Profiling

**Test Name**: `test_thread_pool_executor_profiling`

**Purpose**: Verify that profiler works correctly with `concurrent.futures.ThreadPoolExecutor`.

**Setup**:
- Create profiler instance
- Define profiled function
- Create ThreadPoolExecutor with 10 workers

**Test Steps**:
1. Submit 100 tasks to thread pool
2. Wait for all tasks to complete
3. Get aggregated results

**Expected Behavior**:
- All 100 tasks are profiled
- Results show hit_count = 100
- No exceptions or errors

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 100
assert len(profiler._all_thread_data) <= 10  # Max 10 worker threads
```

---

#### Test 13: Concurrent get_results() Calls

**Test Name**: `test_concurrent_get_results_calls`

**Purpose**: Verify that multiple threads can call `get_results()` concurrently without race conditions.

**Setup**:
- Create profiler instance
- Execute profiled function in background threads

**Test Steps**:
1. Start 5 threads continuously executing profiled function
2. Start 3 threads continuously calling `get_results()`
3. Run for 2 seconds
4. Verify no exceptions or race conditions

**Expected Behavior**:
- All `get_results()` calls succeed
- No AttributeError, KeyError, or race conditions
- Results are consistent (monotonically increasing hit_count)

**Validation**:
```python
# Verify all get_results() calls succeeded
assert all(result is not None for result in results_list)
# Verify no exceptions
assert len(exceptions) == 0
```

---

#### Test 14: Thread Lifecycle During Profiling

**Test Name**: `test_thread_lifecycle_during_profiling`

**Purpose**: Verify that profiler handles thread creation and destruction during active profiling.

**Setup**:
- Create profiler instance
- Define profiled function

**Test Steps**:
1. Start 10 threads, each executes profiled function 10 times
2. Threads complete and terminate
3. Start 10 new threads, each executes profiled function 20 times
4. Get aggregated results

**Expected Behavior**:
- Results include data from all 20 threads (10 old + 10 new)
- Total hit_count = (10×10) + (10×20) = 300
- Thread data persists after thread termination

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 300
assert len(profiler._all_thread_data) == 20
```

---

#### Test 15: Nested Profiling Across Threads

**Test Name**: `test_nested_profiling_across_threads`

**Purpose**: Verify that nested profiling works correctly when calls span multiple threads.

**Setup**:
- Create profiler instance
- Define nested profiled functions (outer calls inner)

**Test Steps**:
1. Thread 1 calls outer function (which profiles inner function)
2. Thread 2 calls inner function directly
3. Get aggregated results

**Expected Behavior**:
- Outer function profiled only in Thread 1
- Inner function profiled in both threads
- Aggregation correctly merges inner function data

**Validation**:
```python
outer_block = results.tracks[0].blocks[0]
inner_block = results.tracks[0].blocks[1]
assert outer_block.hit_count == 1  # Only Thread 1
assert inner_block.hit_count == 2  # Both threads
```

---

#### Test 16: Concurrent Track Enable/Disable

**Test Name**: `test_concurrent_track_enable_disable`

**Purpose**: Verify that track enable/disable operations are thread-safe.

**Setup**:
- Create profiler instance
- Define profiled function on track 0

**Test Steps**:
1. Start 5 threads continuously executing profiled function
2. Main thread toggles track enable/disable every 100ms
3. Run for 1 second
4. Verify no exceptions

**Expected Behavior**:
- No exceptions or race conditions
- Some measurements recorded (when track enabled)
- Some measurements skipped (when track disabled)

**Validation**:
```python
# Verify profiling occurred (track was enabled at some point)
assert results.tracks[0].blocks[0].hit_count > 0
# Verify no exceptions
assert len(exceptions) == 0
```

---

#### Test 17: Rapid Thread Creation/Destruction

**Test Name**: `test_rapid_thread_creation_destruction`

**Purpose**: Verify that profiler handles rapid thread creation and destruction without memory leaks or errors.

**Setup**:
- Create profiler instance
- Define profiled function

**Test Steps**:
1. Create and destroy 100 threads rapidly (each executes profiled function once)
2. Get aggregated results
3. Verify thread data registry size

**Expected Behavior**:
- All 100 threads profiled successfully
- Thread data persists in registry (not cleaned up automatically)
- No memory errors or exceptions

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 100
assert len(profiler._all_thread_data) == 100
```

---

### E. Stress Tests

**Purpose**: Verify that profiler maintains correctness and stability under high load.

**Test File**: `tests/integration/test_stress.py`

**Markers**: `@pytest.mark.integration`, `@pytest.mark.stress`, `@pytest.mark.slow`

#### Test 18: High Thread Count (100 Threads)

**Test Name**: `test_high_thread_count_100_threads`

**Purpose**: Verify that profiler handles 100 concurrent threads without degradation.

**Setup**:
- Create profiler instance
- Define profiled function
- Create ThreadPoolExecutor with 100 workers

**Test Steps**:
1. Submit 1000 tasks to thread pool (100 threads, 10 tasks each)
2. Wait for all tasks to complete
3. Get aggregated results
4. Verify correctness and performance

**Expected Behavior**:
- All 1000 tasks profiled successfully
- Aggregation completes in <10ms (target from architecture)
- No exceptions or errors

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 1000
assert aggregation_time_ms < 10.0
assert len(profiler._all_thread_data) <= 100
```

---

#### Test 19: High Measurement Frequency (100K Measurements)

**Test Name**: `test_high_measurement_frequency_100k_measurements`

**Purpose**: Verify that profiler handles high measurement frequency without performance degradation.

**Setup**:
- Create profiler instance
- Define fast profiled function (< 1μs execution time)

**Test Steps**:
1. Execute profiled function 100,000 times in single thread
2. Measure total execution time
3. Calculate overhead percentage

**Expected Behavior**:
- All 100,000 measurements recorded
- Overhead ≤1% vs unprofiled execution
- No memory errors

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 100_000
overhead_pct = (profiled_time - unprofiled_time) / unprofiled_time * 100
assert overhead_pct <= 1.0
```

---

#### Test 20: Combined Stress (Many Threads + Many Measurements)

**Test Name**: `test_combined_stress_many_threads_many_measurements`

**Purpose**: Verify that profiler handles combined stress of many threads and many measurements.

**Setup**:
- Create profiler instance
- Define profiled function
- Create ThreadPoolExecutor with 50 workers

**Test Steps**:
1. Submit 50,000 tasks to thread pool (50 threads, 1000 tasks each)
2. Wait for all tasks to complete
3. Get aggregated results
4. Measure aggregation time

**Expected Behavior**:
- All 50,000 measurements recorded
- Aggregation completes in <10ms
- No exceptions or memory errors

**Validation**:
```python
assert results.tracks[0].blocks[0].hit_count == 50_000
assert aggregation_time_ms < 10.0
```

---

#### Test 21: Long-Running Profiling Session

**Test Name**: `test_long_running_profiling_session`

**Purpose**: Verify that profiler maintains stability during long-running profiling sessions.

**Setup**:
- Create profiler instance
- Define profiled function
- Create ThreadPoolExecutor with 10 workers

**Test Steps**:
1. Run profiling for 10 seconds with continuous task submission
2. Periodically call `get_results()` (every 1 second)
3. Verify no memory leaks or degradation

**Expected Behavior**:
- Profiling continues without errors
- Memory usage remains stable (no leaks)
- Aggregation time remains consistent

**Validation**:
```python
# Verify memory usage is stable
assert max_memory_mb - min_memory_mb < 50  # <50MB growth
# Verify aggregation time is consistent
assert max(aggregation_times) < 2 * min(aggregation_times)
```

---

### F. Performance Tests

**Purpose**: Verify that thread-safety implementation meets performance targets.

**Test File**: `tests/performance/test_thread_safety_overhead.py`

**Markers**: `@pytest.mark.performance`, `@pytest.mark.slow`

**Note**: Performance tests are informational and should not block CI/CD pipelines.

#### Test 22: Hot Path Overhead Measurement

**Test Name**: `test_hot_path_overhead_measurement`

**Purpose**: Measure hot path overhead and verify it meets the ≤1% target.

**Setup**:
- Create profiler instance
- Define fast profiled function (< 1μs execution time)
- Baseline: measure unprofiled execution time

**Test Steps**:
1. Execute unprofiled function 100,000 times (baseline)
2. Execute profiled function 100,000 times (with thread-safety)
3. Calculate overhead percentage
4. Compare to prototype v0.5.0 overhead

**Expected Behavior**:
- Overhead ≤1% increase vs prototype (currently 0.02-0.23%)
- Target: 0.02-0.25% overhead for ≥1ms blocks

**Validation**:
```python
overhead_pct = (profiled_time - baseline_time) / baseline_time * 100
assert overhead_pct <= 1.0, f"Overhead {overhead_pct:.2f}% exceeds 1% target"
# Log for performance tracking
print(f"Hot path overhead: {overhead_pct:.4f}%")
```

---

#### Test 23: Aggregation Performance Measurement

**Test Name**: `test_aggregation_performance_measurement`

**Purpose**: Measure aggregation performance and verify it meets the <10ms target for 100 threads.

**Setup**:
- Create profiler instance
- Define profiled function
- Execute profiling in 100 threads

**Test Steps**:
1. Execute profiled function in 100 threads (100 measurements each)
2. Measure `get_results()` execution time
3. Verify aggregation time <10ms

**Expected Behavior**:
- Aggregation completes in <10ms for 100 threads
- Time scales linearly with thread count (O(T × K × B))

**Validation**:
```python
assert aggregation_time_ms < 10.0, f"Aggregation {aggregation_time_ms:.2f}ms exceeds 10ms target"
# Log for performance tracking
print(f"Aggregation time (100 threads): {aggregation_time_ms:.2f}ms")
```

---

#### Test 24: Memory Usage Measurement

**Test Name**: `test_memory_usage_measurement`

**Purpose**: Measure memory usage and verify it scales as O(threads × blocks).

**Markers**: `@pytest.mark.performance`, `@pytest.mark.slow`

**Setup**:
- Create profiler instance
- Define profiled function

**Test Steps**:
1. Measure baseline memory usage
2. Execute profiling in 50 threads (100 blocks each)
3. Measure memory usage after profiling
4. Calculate memory per thread

**Expected Behavior**:
- Memory usage: O(threads × blocks)
- Typical: 50 threads × 100 blocks × 100 bytes ≈ 500 KB
- Acceptable: <10 MB for 100 threads

**Validation**:
```python
memory_increase_mb = (after_memory - baseline_memory) / 1024 / 1024
assert memory_increase_mb < 10.0, f"Memory usage {memory_increase_mb:.2f}MB exceeds 10MB"
# Log for performance tracking
print(f"Memory usage (50 threads, 100 blocks): {memory_increase_mb:.2f}MB")
```

---

## Test Infrastructure

### Test Fixtures

**Purpose**: Provide reusable test infrastructure for consistent test setup and teardown.

**Location**: `tests/conftest.py` (pytest fixtures)

#### Fixture 1: Basic Profiler Fixture

**Name**: `profiler`

**Purpose**: Provide fresh profiler instance for each test.

**Implementation**:
```python
import pytest
from stichotrope import Profiler

@pytest.fixture
def profiler():
    """Provide fresh profiler instance."""
    p = Profiler("TestProfiler")
    yield p
    # Cleanup: clear profiler data
    p.clear()
```

---

#### Fixture 2: Thread Pool Fixture

**Name**: `thread_pool`

**Purpose**: Provide ThreadPoolExecutor with configurable worker count.

**Implementation**:
```python
from concurrent.futures import ThreadPoolExecutor

@pytest.fixture
def thread_pool():
    """Provide ThreadPoolExecutor with 10 workers."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        yield executor
    # Automatic cleanup via context manager
```

---

#### Fixture 3: Profiled Function Fixtures

**Name**: `simple_function`, `cpu_bound_function`, `io_bound_function`

**Purpose**: Provide profiled functions with known execution characteristics.

**Implementation**:
```python
import time

@pytest.fixture
def simple_function(profiler):
    """Simple profiled function with minimal overhead."""
    @profiler.track(0, "simple")
    def func():
        return 42
    return func

@pytest.fixture
def cpu_bound_function(profiler):
    """CPU-bound profiled function (1ms execution)."""
    @profiler.track(0, "cpu_bound")
    def func():
        # Busy loop for ~1ms
        end = time.perf_counter() + 0.001
        while time.perf_counter() < end:
            pass
        return 42
    return func

@pytest.fixture
def io_bound_function(profiler):
    """I/O-bound profiled function (sleep-based)."""
    @profiler.track(0, "io_bound")
    def func(sleep_ms=1):
        time.sleep(sleep_ms / 1000.0)
        return 42
    return func
```

---

#### Fixture 4: Thread Barrier Fixture

**Name**: `thread_barrier`

**Purpose**: Synchronize thread start for concurrent testing.

**Implementation**:
```python
import threading

@pytest.fixture
def thread_barrier():
    """Provide threading.Barrier for synchronized thread start."""
    def create_barrier(num_threads):
        return threading.Barrier(num_threads)
    return create_barrier
```

---

### Test Data Requirements

**Purpose**: Define data variations for comprehensive test coverage.

#### Thread Count Variations

| Variation | Thread Count | Use Case |
|-----------|--------------|----------|
| Single | 1 | Baseline (no concurrency) |
| Minimal | 2 | Minimal concurrency |
| Moderate | 10 | Typical concurrency |
| High | 100 | Stress testing |

#### Measurement Count Variations

| Variation | Measurement Count | Use Case |
|-----------|-------------------|----------|
| Minimal | 10 | Basic functionality |
| Moderate | 100 | Typical usage |
| High | 1,000 | Heavy usage |
| Stress | 100,000 | Stress testing |

#### Timing Variations

| Variation | Execution Time | Use Case |
|-----------|----------------|----------|
| Fast | < 1μs | Overhead measurement |
| Medium | 1-100μs | Typical functions |
| Slow | > 100μs | I/O-bound functions |

---

### Validation Helpers

**Purpose**: Provide reusable validation logic for test assertions.

**Location**: `tests/test_utils.py` or inline in test files

#### Helper 1: Aggregation Validator

**Name**: `validate_aggregation`

**Purpose**: Verify aggregation correctness for multiple threads.

**Implementation**:
```python
def validate_aggregation(results, expected_hit_count, expected_min_ns, expected_max_ns):
    """
    Validate aggregation results.

    Args:
        results: ProfilerResults object
        expected_hit_count: Expected total hit count
        expected_min_ns: Expected minimum time (with tolerance)
        expected_max_ns: Expected maximum time (with tolerance)
    """
    block = results.tracks[0].blocks[0]
    assert block.hit_count == expected_hit_count
    assert block.min_time_ns <= expected_min_ns * 1.1  # 10% tolerance
    assert block.max_time_ns >= expected_max_ns * 0.9  # 10% tolerance
```

---

#### Helper 2: Thread Safety Validator

**Name**: `validate_thread_safety`

**Purpose**: Verify no thread-safety violations occurred.

**Implementation**:
```python
def validate_thread_safety(exception_list):
    """
    Validate that no thread-safety exceptions occurred.

    Args:
        exception_list: List of exceptions caught during concurrent execution
    """
    # Filter for thread-safety related exceptions
    thread_errors = [
        e for e in exception_list
        if isinstance(e, (AttributeError, KeyError, RuntimeError))
    ]
    assert len(thread_errors) == 0, f"Thread-safety violations: {thread_errors}"
```

---

#### Helper 3: Performance Validator

**Name**: `validate_performance`

**Purpose**: Verify performance meets targets.

**Implementation**:
```python
def validate_performance(profiled_time, baseline_time, max_overhead_pct=1.0):
    """
    Validate performance overhead.

    Args:
        profiled_time: Execution time with profiling (seconds)
        baseline_time: Execution time without profiling (seconds)
        max_overhead_pct: Maximum acceptable overhead percentage
    """
    overhead_pct = (profiled_time - baseline_time) / baseline_time * 100
    assert overhead_pct <= max_overhead_pct, \
        f"Overhead {overhead_pct:.2f}% exceeds {max_overhead_pct}% target"
    return overhead_pct
```

---

## Test File Organization

### Directory Structure

Following pytest conventions, tests are organized hierarchically:

```
tests/
├── __init__.py
├── conftest.py                          # Shared fixtures
├── test_utils.py                        # Validation helpers
├── unit/
│   ├── __init__.py
│   ├── test_thread_local_storage.py    # Tests 1-4
│   ├── test_lock_protection.py         # Tests 5-7
│   └── test_aggregation.py             # Tests 8-11
├── integration/
│   ├── __init__.py
│   ├── test_multithreaded_profiling.py # Tests 12-17
│   └── test_stress.py                  # Tests 18-21
└── performance/
    ├── __init__.py
    └── test_thread_safety_overhead.py  # Tests 22-24
```

### File Naming Conventions

**Standard**: `test_<component>.py` (pytest convention)

**Examples**:
- `test_thread_local_storage.py` - Thread-local storage tests
- `test_lock_protection.py` - Lock protection tests
- `test_aggregation.py` - Aggregation algorithm tests

### pytest Marker Usage

**Marker Registration** (`pytest.ini` or `pyproject.toml`):
```toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "performance: Performance tests",
    "thread_safety: Thread-safety specific tests",
    "stress: Stress tests (high load)",
    "slow: Slow-running tests",
]
```

**Marker Application Examples**:

```python
# Unit test
@pytest.mark.unit
@pytest.mark.thread_safety
def test_thread_local_storage_isolation():
    pass

# Integration test
@pytest.mark.integration
@pytest.mark.thread_safety
def test_thread_pool_executor_profiling():
    pass

# Stress test
@pytest.mark.integration
@pytest.mark.stress
@pytest.mark.slow
def test_high_thread_count_100_threads():
    pass

# Performance test
@pytest.mark.performance
@pytest.mark.slow
def test_hot_path_overhead_measurement():
    pass

# Deadlock detection test
@pytest.mark.unit
@pytest.mark.thread_safety
@pytest.mark.timeout(10)
def test_lock_hierarchy_compliance():
    pass
```

### pytest Execution Examples

**Run all tests**:
```bash
pytest tests/
```

**Run by marker**:
```bash
# Run only unit tests
pytest -m unit

# Run only thread-safety tests
pytest -m thread_safety

# Run integration tests (excluding slow tests)
pytest -m "integration and not slow"

# Run stress tests
pytest -m stress
```

**Run by file**:
```bash
# Run specific test file
pytest tests/unit/test_thread_local_storage.py

# Run specific test
pytest tests/unit/test_thread_local_storage.py::test_thread_local_storage_isolation
```

**Run with coverage**:
```bash
pytest --cov=stichotrope --cov-report=html tests/
```

---

## Development Dependencies

### Required Dependencies

The following dependencies are needed for thread-safety testing:

**Already in `pyproject.toml` (dev dependencies)**:
- `pytest>=7.0.0` ✅ - Core testing framework
- `pytest-cov>=4.0.0` ✅ - Coverage reporting

**Recommended additions to `pyproject.toml`**:

```toml
[project.optional-dependencies]
dev = [
    # ... existing dependencies ...
    "pytest-timeout>=2.1.0",  # Deadlock detection (Test 7)
    "psutil>=5.9.0",          # Memory usage measurement (Test 24)
]
```

### Dependency Rationale

**pytest-timeout**:
- **Purpose**: Detect deadlocks in lock hierarchy tests
- **Usage**: `@pytest.mark.timeout(10)` decorator
- **Critical for**: Test 7 (Lock Hierarchy Compliance)
- **Why needed**: Deadlocks cause tests to hang indefinitely; timeout ensures test fails

**psutil**:
- **Purpose**: Measure memory usage for performance tests
- **Usage**: `psutil.Process().memory_info().rss`
- **Critical for**: Test 24 (Memory Usage Measurement)
- **Why needed**: Standard library doesn't provide reliable cross-platform memory measurement

### Installation

After adding to `pyproject.toml`:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or install specific dependencies
pip install pytest-timeout psutil
```

---

## Success Criteria Mapping

This section maps the test suite to the success gates defined in Issue #19.

### Success Gate 1: Test Plan Includes Required Categories

**Requirement**: Test plan includes unit tests, integration tests, stress tests, race condition detection

**Mapping**:
- ✅ **Unit Tests**: Tests 1-11 (Thread-local storage, lock protection, aggregation)
- ✅ **Integration Tests**: Tests 12-17 (Multi-threaded profiling scenarios)
- ✅ **Stress Tests**: Tests 18-21 (High thread count, high measurement frequency)
- ✅ **Race Condition Detection**: Tests 5-7, 13 (Lock protection, concurrent operations)

**Status**: ✅ SATISFIED

---

### Success Gate 2: Test Scenarios Cover Required Cases

**Requirement**: Test scenarios cover single-threaded, multi-threaded, high contention, thread pool

**Mapping**:
- ✅ **Single-Threaded**: Test 19 (baseline for overhead measurement)
- ✅ **Multi-Threaded**: Tests 1-4, 8-11, 12-17 (all multi-threaded scenarios)
- ✅ **High Contention**: Tests 5-7, 13, 18, 20 (concurrent access, stress tests)
- ✅ **Thread Pool**: Tests 12, 18, 20 (ThreadPoolExecutor scenarios)

**Status**: ✅ SATISFIED

---

### Success Gate 3: Test Data and Fixtures Defined

**Requirement**: Test data and fixtures defined

**Mapping**:
- ✅ **Fixtures**: Basic profiler, thread pool, profiled functions, thread barrier
- ✅ **Test Data**: Thread count variations, measurement count variations, timing variations
- ✅ **Validation Helpers**: Aggregation validator, thread safety validator, performance validator

**Status**: ✅ SATISFIED

---

### Success Gate 4: Test Review Completed and Approved

**Requirement**: Test review completed and approved

**Status**: ⏳ PENDING (awaiting stakeholder review of this v1 report)

**Next Steps**:
1. Stakeholder reviews test definitions
2. Feedback incorporated into v2 (if needed)
3. Approval granted
4. Implementation proceeds (Task 2.1.3)

---

## Implementation Guidance

### Initial Test Implementation Workflow

**Purpose**: Guide for implementing tests during Task 2.1.3 (one-time implementation).

**Important Notes**:
- ⚠️ **Tests will fail before implementation**: These tests validate the thread-safe implementation. Running them before implementing the thread-safe code will result in failures. This is expected and normal.
- ✅ **Tests run regularly**: After initial implementation, these tests run in CI/CD and during development to prevent regressions.

**Recommended workflow for initial implementation**:

1. **Step 1: Setup Test Infrastructure**
   - Create test file structure
   - Implement fixtures in `conftest.py`
   - Implement validation helpers in `test_utils.py`
   - Add pytest markers to `pyproject.toml`
   - Install dependencies (`pytest-timeout`, `psutil`)

2. **Step 2: Implement Unit Tests**
   - Thread-local storage tests (Tests 1-4)
   - Lock protection tests (Tests 5-7)
   - Aggregation tests (Tests 8-11)
   - Run: `pytest -m unit`
   - **Expected**: All tests fail (implementation not done yet)

3. **Step 3: Implement Thread-Safe Code** (parallel with Step 4)
   - Follow architecture design (Task 2.1.1)
   - Implement thread-local storage
   - Implement lock protection
   - Implement aggregation algorithm

4. **Step 4: Implement Integration Tests**
   - Multi-threaded profiling tests (Tests 12-17)
   - Run: `pytest -m integration`
   - **Expected**: Tests start passing as implementation progresses

5. **Step 5: Implement Stress Tests**
   - Stress tests (Tests 18-21)
   - Run: `pytest -m stress`

6. **Step 6: Implement Performance Tests**
   - Performance tests (Tests 22-24)
   - Run: `pytest -m performance`

7. **Step 7: Full Test Suite Execution** (Task 2.1.4)
   - Run all tests: `pytest tests/`
   - Generate test execution report
   - Verify all success criteria met

---

### CI/CD Integration

**pytest Commands for CI/CD**:

```bash
# Run all unit tests
pytest -m unit --cov=stichotrope --cov-report=xml --cov-report=term

# Run integration tests (excluding slow tests)
pytest -m "integration and not slow" --cov=stichotrope --cov-append

# Run stress tests (optional, may be slow)
pytest -m stress --cov=stichotrope --cov-append || true

# Run performance tests (informational, non-blocking)
pytest -m performance || true
```

**CI/CD Pipeline Configuration** (GitHub Actions example):

```yaml
name: Thread-Safety Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run Unit Tests
        run: pytest -m unit --cov=stichotrope --cov-report=xml

      - name: Run Integration Tests
        run: pytest -m "integration and not slow" --cov=stichotrope --cov-append

      - name: Run Stress Tests (Non-Blocking)
        run: pytest -m stress || true
        continue-on-error: true

      - name: Run Performance Tests (Non-Blocking)
        run: pytest -m performance || true
        continue-on-error: true

      - name: Upload Coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

### Performance Baselines

**Purpose**: Establish performance baselines for regression detection.

**Baseline Measurements** (from prototype v0.5.0):
- Hot path overhead: 0.02-0.23% for ≥1ms blocks
- Aggregation time: ~0.5-1ms for 50 threads × 100 blocks

**Target Measurements** (v1.0.0 with thread-safety):
- Hot path overhead: ≤1% increase (target: 0.02-0.25%)
- Aggregation time: <10ms for 100 threads

**Baseline Tracking**:
1. Record baseline measurements from prototype v0.5.0
2. Run performance tests on v1.0.0 implementation
3. Compare results and verify targets met
4. Update baselines for future regression detection

**Performance Test Execution**:
```bash
# Run performance tests with detailed output
pytest -m performance -v -s
```

---

## Conclusion

### Summary

This test definition report provides a comprehensive test suite for validating the thread-safe architecture redesign of Stichotrope v1.0.0 (Milestone 2.1).

**Key Achievements**:
1. ✅ **24 tests defined** across 6 categories (unit, integration, stress, performance)
2. ✅ **All success gates addressed** (unit/integration/stress/race detection, scenarios, fixtures)
3. ✅ **Test infrastructure specified** (fixtures, test data, validation helpers)
4. ✅ **Implementation guidance provided** (execution order, CI/CD integration, baselines)
5. ✅ **pytest-based approach** (standard Python testing framework)
6. ✅ **Dependencies identified** (pytest-timeout, psutil)

**Test Coverage**:
- **Thread-Local Storage**: 4 tests verifying isolation and independence
- **Lock Protection**: 3 tests verifying concurrent access safety
- **Aggregation**: 4 tests verifying merge algorithm correctness
- **Multi-Threaded Integration**: 6 tests verifying realistic scenarios
- **Stress**: 4 tests verifying high-load behavior
- **Performance**: 3 tests verifying overhead and performance targets

**Testing Approach**:
- Focus on our implementation (not standard library behavior)
- Functional grouping (not arbitrary categories)
- Comprehensive yet focused (24 tests for critical thread-safety feature)
- pytest markers for flexible test selection

### Success Criteria Met

**Issue #19 Success Gates**:
- ✅ Test plan includes: unit tests, integration tests, stress tests, race condition detection
- ✅ Test scenarios cover: single-threaded, multi-threaded, high contention, thread pool
- ✅ Test data and fixtures defined
- ⏳ Test review completed and approved (awaiting stakeholder review)

**Reporting Standards**:
- ✅ Comprehensive test specifications with clear input/output expectations
- ✅ Test infrastructure and fixtures defined
- ✅ Implementation guidance provided
- ✅ pytest-based approach (standard for Stichotrope)

**Architecture Design Alignment**:
- ✅ Tests cover thread-local storage strategy
- ✅ Tests cover lock design and hierarchy
- ✅ Tests cover aggregation algorithm
- ✅ Tests cover hot path (no locks) and cold path (lock protection)
- ✅ Tests cover performance targets (≤1% overhead, <10ms aggregation)

### Improvements from v0

**1. pytest Integration**:
- Replaced Wobble with pytest throughout
- Added pytest marker examples and configuration
- Updated all execution examples to use pytest commands
- Added pytest-specific CI/CD pipeline examples

**2. Dependency Clarity**:
- Identified pytest-timeout for deadlock detection
- Identified psutil for memory measurement
- Provided clear rationale for each dependency

**3. Workflow Clarity**:
- Renamed "Test Development Workflow" to "Initial Test Implementation Workflow"
- Added note about expected test failures before implementation
- Clarified tests run regularly (not just during Task 2.1.3)
- Replaced "Phase" with "Step" to avoid hierarchy confusion

### Next Steps

**Phase 1 (Current)**:
1. ✅ Task 2.1.0: Architecture Evaluation - APPROVED
2. ✅ Task 2.1.1: Architecture Design v1 - APPROVED
3. ✅ Task 2.1.2: Test Definition v1 - COMPLETE (awaiting review)

**Phase 2 (After Approval)**:
4. Task 2.1.3: Implement Thread-Safe Profiler Core + Tests
5. Task 2.1.4: Execute Thread-Safe Test Suite + Validation Report

**Immediate Next Actions**:
1. Stakeholder review of test definitions (this report)
2. Feedback incorporation (v2 if needed)
3. Add dependencies to `pyproject.toml` (pytest-timeout, psutil)
4. Approval for implementation
5. Proceed to Task 2.1.3 (implementation)

### Future Considerations

**Test Suite Enhancements** (post-v1.0.0):
- Binary merge algorithm tests (when implemented in v1.1.0+)
- Post-GIL Python tests (Python 3.13+, PEP 703)
- API improvement tests (instance-level track enable/disable, per-thread results)
- Memory leak detection tests (long-running sessions)
- Thread count monitoring tests

**Performance Regression Detection**:
- Automated baseline tracking in CI/CD
- Performance trend analysis over time
- Alert on performance degradation >5%

**Test Maintenance**:
- Review test suite quarterly for relevance
- Update baselines after performance optimizations
- Add tests for bug fixes (regression prevention)

---

**Report Version**: v1 (refined based on stakeholder feedback)
**Date**: 2025-11-07
**Author**: Test Definition (Phase 1)
**Status**: Awaiting stakeholder review
**Next Action**: Stakeholder feedback and iteration to v2 if needed

---

## Appendix: Test Summary Table

| # | Test Name | Category | Markers | Purpose |
|---|-----------|----------|---------|---------|
| 1 | test_thread_local_storage_isolation | Unit | unit, thread_safety | Verify thread isolation |
| 2 | test_thread_registration_in_global_registry | Unit | unit, thread_safety | Verify thread registration |
| 3 | test_thread_local_initialization_pattern | Unit | unit, thread_safety | Verify initialization pattern |
| 4 | test_thread_local_measurement_recording | Unit | unit, thread_safety | Verify measurement recording |
| 5 | test_call_site_cache_concurrent_access | Unit | unit, thread_safety | Verify cache lock protection |
| 6 | test_profiler_registry_concurrent_access | Unit | unit, thread_safety | Verify registry lock protection |
| 7 | test_lock_hierarchy_compliance | Unit | unit, thread_safety, timeout | Verify lock hierarchy |
| 8 | test_sequential_merge_correctness | Unit | unit, thread_safety | Verify merge algorithm |
| 9 | test_multi_thread_aggregation_different_blocks | Unit | unit, thread_safety | Verify block merging |
| 10 | test_empty_thread_handling | Unit | unit, thread_safety | Verify empty thread handling |
| 11 | test_aggregation_preserves_metadata | Unit | unit, thread_safety | Verify metadata preservation |
| 12 | test_thread_pool_executor_profiling | Integration | integration, thread_safety | Verify thread pool profiling |
| 13 | test_concurrent_get_results_calls | Integration | integration, thread_safety | Verify concurrent get_results |
| 14 | test_thread_lifecycle_during_profiling | Integration | integration, thread_safety | Verify thread lifecycle |
| 15 | test_nested_profiling_across_threads | Integration | integration, thread_safety | Verify nested profiling |
| 16 | test_concurrent_track_enable_disable | Integration | integration, thread_safety | Verify concurrent enable/disable |
| 17 | test_rapid_thread_creation_destruction | Integration | integration, thread_safety | Verify rapid thread churn |
| 18 | test_high_thread_count_100_threads | Stress | integration, stress, slow | Verify 100 threads |
| 19 | test_high_measurement_frequency_100k_measurements | Stress | integration, stress, slow | Verify 100K measurements |
| 20 | test_combined_stress_many_threads_many_measurements | Stress | integration, stress, slow | Verify combined stress |
| 21 | test_long_running_profiling_session | Stress | integration, stress, slow | Verify long-running session |
| 22 | test_hot_path_overhead_measurement | Performance | performance, slow | Measure hot path overhead |
| 23 | test_aggregation_performance_measurement | Performance | performance, slow | Measure aggregation time |
| 24 | test_memory_usage_measurement | Performance | performance, slow | Measure memory usage |

**Total**: 24 tests (11 unit, 6 integration, 4 stress, 3 performance)

**Marker Summary**:
- `unit`: 11 tests
- `integration`: 10 tests (6 integration + 4 stress)
- `thread_safety`: 17 tests (all unit + all integration except stress)
- `stress`: 4 tests
- `slow`: 7 tests (4 stress + 3 performance)
- `performance`: 3 tests
- `timeout`: 1 test (deadlock detection)


