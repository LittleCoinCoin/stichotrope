# Thread-Safe Test Suite Definition

**Task**: 2.1.2 – Design Thread-Safe Test Suite  
**Issue**: [#19](https://github.com/LittleCoinCoin/stichotrope/issues/19)  
**Milestone**: 2.1 Thread-Safe Architecture Redesign  
**Version Target**: v0.2.0  
**Report Version**: v0 (initial)  
**Date**: 2025-11-07  
**Status**: Awaiting stakeholder review  
**Dependencies**: Task 2.1.1 (Architecture Design) - ✅ APPROVED

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
6. [Success Criteria Mapping](#success-criteria-mapping)
7. [Implementation Guidance](#implementation-guidance)
8. [Conclusion](#conclusion)

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

**Testing Framework**: Wobble (organizational standard)

**Test Categorization**: Three-tier system (unit/integration/performance) with appropriate decorators

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

**Decorator**: `@regression_test`

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

**Decorator**: `@regression_test`

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

**Setup**:
- Create profiler instance
- Define scenario requiring multiple locks

**Test Steps**:
1. Execute operations requiring lock acquisition in correct order
2. Execute operations from multiple threads concurrently
3. Verify no deadlocks occur (use timeout)

**Expected Behavior**:
- All operations complete successfully
- No deadlocks (all threads complete within timeout)
- Lock hierarchy: _REGISTRY_LOCK → _GLOBAL_CACHE_LOCK → Profiler._global_lock

**Validation**:
```python
# Use threading.Timer to detect deadlocks
timeout = 5.0  # seconds
all_threads_completed = wait_for_threads(threads, timeout)
assert all_threads_completed, "Deadlock detected"
```

---

### C. Aggregation Tests

**Purpose**: Verify that the sequential merge algorithm produces correct aggregated results.

**Test File**: `tests/unit/test_aggregation.py`

**Decorator**: `@regression_test`

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

**Decorator**: `@integration_test(scope="component")`

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

**Decorator**: `@integration_test(scope="component")` + `@slow_test`

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
- Overhead ≤1% vs unprofilied execution
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

**Decorator**: `@slow_test` (performance tests are informational, not blocking)

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

**Location**: `tests/conftest.py` (pytest fixtures) or test file `setUp()` methods

#### Fixture 1: Basic Profiler Fixture

**Name**: `profiler`

**Purpose**: Provide fresh profiler instance for each test.

**Implementation**:
```python
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

Following Wobble testing standards, tests are organized hierarchically:

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

**Standard**: `test_<component>.py` (industry-standard naming)

**Examples**:
- `test_thread_local_storage.py` - Thread-local storage tests
- `test_lock_protection.py` - Lock protection tests
- `test_aggregation.py` - Aggregation algorithm tests

### Decorator Usage

**Unit Tests (Regression)**:
```python
@regression_test
def test_thread_local_storage_isolation():
    pass
```

**Integration Tests**:
```python
@integration_test(scope="component")
def test_thread_pool_executor_profiling():
    pass
```

**Stress Tests**:
```python
@integration_test(scope="component")
@slow_test
def test_high_thread_count_100_threads():
    pass
```

**Performance Tests**:
```python
@slow_test
def test_hot_path_overhead_measurement():
    pass
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

**Status**: ⏳ PENDING (awaiting stakeholder review of this v0 report)

**Next Steps**:
1. Stakeholder reviews test definitions
2. Feedback incorporated into v1 (if needed)
3. Approval granted
4. Implementation proceeds (Task 2.1.3)

---

## Implementation Guidance

### Test Execution Order

**Recommended execution order for development**:

1. **Phase 1: Unit Tests** (fast, foundational)
   - Thread-local storage tests (Tests 1-4)
   - Lock protection tests (Tests 5-7)
   - Aggregation tests (Tests 8-11)

2. **Phase 2: Integration Tests** (moderate speed)
   - Multi-threaded profiling tests (Tests 12-17)

3. **Phase 3: Stress Tests** (slow, comprehensive)
   - Stress tests (Tests 18-21)

4. **Phase 4: Performance Tests** (informational)
   - Performance tests (Tests 22-24)

**Rationale**: Fast tests first for rapid feedback, slow tests last for comprehensive validation.

---

### CI/CD Integration

**Wobble Commands for CI/CD**:

```bash
# Run all regression tests (unit tests)
wobble --category regression --log-file ci_unit_results.json --log-verbosity 3

# Run integration tests (excluding slow tests)
wobble --category integration --log-file ci_integration_results.json --log-verbosity 3

# Run performance tests (informational, non-blocking)
wobble --category performance --log-file ci_performance_results.json --log-verbosity 3 || true
```

**CI/CD Pipeline Configuration**:

```yaml
# GitHub Actions example
- name: Run Unit Tests
  run: wobble --category regression --log-file unit_results.json

- name: Run Integration Tests
  run: wobble --category integration --log-file integration_results.json

- name: Run Performance Tests (Non-Blocking)
  run: wobble --category performance --log-file performance_results.json || true
  continue-on-error: true

- name: Archive Test Results
  uses: actions/upload-artifact@v3
  with:
    name: test-results
    path: |
      unit_results.json
      integration_results.json
      performance_results.json
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
wobble --pattern "test_thread_safety_overhead.py" --log-file performance_baseline_v1.txt --log-verbosity 3
```

---

### Test Development Workflow

**Recommended workflow for implementing tests**:

1. **Setup Test Infrastructure** (Task 2.1.3 - Phase 1)
   - Create test file structure
   - Implement fixtures in `conftest.py`
   - Implement validation helpers in `test_utils.py`

2. **Implement Unit Tests** (Task 2.1.3 - Phase 2)
   - Thread-local storage tests (Tests 1-4)
   - Lock protection tests (Tests 5-7)
   - Aggregation tests (Tests 8-11)
   - Run: `wobble --category regression`

3. **Implement Integration Tests** (Task 2.1.3 - Phase 3)
   - Multi-threaded profiling tests (Tests 12-17)
   - Run: `wobble --category integration`

4. **Implement Stress Tests** (Task 2.1.3 - Phase 4)
   - Stress tests (Tests 18-21)
   - Run: `wobble --category integration --pattern "test_stress.py"`

5. **Implement Performance Tests** (Task 2.1.3 - Phase 5)
   - Performance tests (Tests 22-24)
   - Run: `wobble --pattern "test_thread_safety_overhead.py"`

6. **Full Test Suite Execution** (Task 2.1.4)
   - Run all tests: `wobble --log-file test_execution_v0.txt --log-verbosity 3`
   - Generate test execution report
   - Verify all success criteria met

---

## Conclusion

### Summary

This test definition report provides a comprehensive test suite for validating the thread-safe architecture redesign of Stichotrope v1.0.0 (Milestone 2.1).

**Key Achievements**:
1. ✅ **24 tests defined** across 6 categories (unit, integration, stress, performance)
2. ✅ **All success gates addressed** (unit/integration/stress/race detection, scenarios, fixtures)
3. ✅ **Test infrastructure specified** (fixtures, test data, validation helpers)
4. ✅ **Implementation guidance provided** (execution order, CI/CD integration, baselines)

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
- Aligned with organizational testing standards (Wobble, three-tier categorization)

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
- ✅ Aligned with organizational testing standards

**Architecture Design Alignment**:
- ✅ Tests cover thread-local storage strategy
- ✅ Tests cover lock design and hierarchy
- ✅ Tests cover aggregation algorithm
- ✅ Tests cover hot path (no locks) and cold path (lock protection)
- ✅ Tests cover performance targets (≤1% overhead, <10ms aggregation)

### Next Steps

**Phase 1 (Current)**:
1. ✅ Task 2.1.0: Architecture Evaluation - APPROVED
2. ✅ Task 2.1.1: Architecture Design v1 - APPROVED
3. ✅ Task 2.1.2: Test Definition v0 - COMPLETE (awaiting review)

**Phase 2 (After Approval)**:
4. Task 2.1.3: Implement Thread-Safe Profiler Core + Tests
5. Task 2.1.4: Execute Thread-Safe Test Suite + Validation Report

**Immediate Next Actions**:
1. Stakeholder review of test definitions (this report)
2. Feedback incorporation (v1 if needed)
3. Approval for implementation
4. Proceed to Task 2.1.3 (implementation)

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

**Report Version**: v0 (initial)
**Date**: 2025-11-07
**Author**: Test Definition (Phase 1)
**Status**: Awaiting stakeholder review
**Next Action**: Stakeholder feedback and iteration to v1 if needed

---

## Appendix: Test Summary Table

| # | Test Name | Category | Decorator | Purpose |
|---|-----------|----------|-----------|---------|
| 1 | test_thread_local_storage_isolation | Unit | @regression_test | Verify thread isolation |
| 2 | test_thread_registration_in_global_registry | Unit | @regression_test | Verify thread registration |
| 3 | test_thread_local_initialization_pattern | Unit | @regression_test | Verify initialization pattern |
| 4 | test_thread_local_measurement_recording | Unit | @regression_test | Verify measurement recording |
| 5 | test_call_site_cache_concurrent_access | Unit | @regression_test | Verify cache lock protection |
| 6 | test_profiler_registry_concurrent_access | Unit | @regression_test | Verify registry lock protection |
| 7 | test_lock_hierarchy_compliance | Unit | @regression_test | Verify lock hierarchy |
| 8 | test_sequential_merge_correctness | Unit | @regression_test | Verify merge algorithm |
| 9 | test_multi_thread_aggregation_different_blocks | Unit | @regression_test | Verify block merging |
| 10 | test_empty_thread_handling | Unit | @regression_test | Verify empty thread handling |
| 11 | test_aggregation_preserves_metadata | Unit | @regression_test | Verify metadata preservation |
| 12 | test_thread_pool_executor_profiling | Integration | @integration_test | Verify thread pool profiling |
| 13 | test_concurrent_get_results_calls | Integration | @integration_test | Verify concurrent get_results |
| 14 | test_thread_lifecycle_during_profiling | Integration | @integration_test | Verify thread lifecycle |
| 15 | test_nested_profiling_across_threads | Integration | @integration_test | Verify nested profiling |
| 16 | test_concurrent_track_enable_disable | Integration | @integration_test | Verify concurrent enable/disable |
| 17 | test_rapid_thread_creation_destruction | Integration | @integration_test | Verify rapid thread churn |
| 18 | test_high_thread_count_100_threads | Stress | @integration_test @slow_test | Verify 100 threads |
| 19 | test_high_measurement_frequency_100k_measurements | Stress | @integration_test @slow_test | Verify 100K measurements |
| 20 | test_combined_stress_many_threads_many_measurements | Stress | @integration_test @slow_test | Verify combined stress |
| 21 | test_long_running_profiling_session | Stress | @integration_test @slow_test | Verify long-running session |
| 22 | test_hot_path_overhead_measurement | Performance | @slow_test | Measure hot path overhead |
| 23 | test_aggregation_performance_measurement | Performance | @slow_test | Measure aggregation time |
| 24 | test_memory_usage_measurement | Performance | @slow_test | Measure memory usage |

**Total**: 24 tests (11 unit, 6 integration, 4 stress, 3 performance)


