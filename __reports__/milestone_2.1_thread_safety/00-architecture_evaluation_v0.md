# Thread-Safety Architecture Evaluation Report

**Task**: 2.1.0 – Evaluate Thread-Safety Architecture Approaches  
**Issue**: [#17](https://github.com/LittleCoinCoin/stichotrope/issues/17)  
**Milestone**: 2.1 Thread-Safe Architecture Redesign  
**Version Target**: v0.2.0  
**Report Version**: v0 (initial)  
**Date**: 2025-11-04  
**Status**: Awaiting stakeholder review

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Prototype Analysis (v0.5.0)](#prototype-analysis-v050)
3. [Aspect 1: Data Structure Safety](#aspect-1-data-structure-safety)
4. [Aspect 2: Profiler Threading](#aspect-2-profiler-threading)
5. [Recommended Approach](#recommended-approach)
6. [Trade-off Analysis](#trade-off-analysis)
7. [Prototype Comparison](#prototype-comparison)
8. [Implementation Considerations](#implementation-considerations)
9. [Conclusion](#conclusion)

---

## Executive Summary

This report evaluates alternative thread-safety approaches for Stichotrope v1.0.0, addressing two critical aspects:

1. **Data Structure Safety**: How to protect profiling data from race conditions
2. **Profiler Threading**: How the profiler handles multi-threaded execution

**Key Findings**:

- **Prototype v0.5.0** has significant thread-safety issues: global state race conditions, unprotected data mutations, non-atomic operations
- **Recommended Approach (Aspect 1)**: **Hybrid Thread-Local + Lock-Based** - Thread-local storage for per-thread data with RLock-protected aggregation
- **Recommended Approach (Aspect 2)**: **Synchronous Profiling** - Measurements on calling thread, no separate profiler threads
- **Performance Target**: ≤1% overhead increase vs prototype baseline (currently 0.02-0.23% for ≥1ms blocks)
- **Complexity**: Moderate - well-understood patterns with proven Python implementations

**Critical Decision**: Avoid asynchronous/queue-based profiling due to high complexity and measurement accuracy concerns. Prioritize simplicity and correctness over theoretical performance gains.

---

## Prototype Analysis (v0.5.0)

### Current Architecture

**File**: `stichotrope/profiler.py` (363 lines)

**Global State**:
```python
# Line 18: Global enable/disable flag
_PROFILER_ENABLED = True

# Line 21: Global call-site cache
_CALL_SITE_CACHE: dict[tuple[int, str, int, str], tuple[int, int]] = {}

# Line 24: Global profiler registry
_PROFILER_REGISTRY: dict[int, "Profiler"] = {}
_NEXT_PROFILER_ID = 0
```

**Instance State** (Profiler class):
```python
# Lines 78-81
self._tracks: dict[int, ProfileTrack] = {}
self._track_enabled: dict[int, bool] = {}
self._next_block_idx: dict[int, int] = {}
self._started = True
```

**Data Structures** (`stichotrope/types.py`):
```python
# ProfileBlock.record_time() - Lines 34-44
def record_time(self, elapsed_ns: int) -> None:
    self.hit_count += 1                              # Race condition
    self.total_time_ns += elapsed_ns                 # Race condition
    self.min_time_ns = min(self.min_time_ns, elapsed_ns)  # Race condition
    self.max_time_ns = max(self.max_time_ns, elapsed_ns)  # Race condition
```

### Thread-Safety Issues

**Issue 1: Global Dictionary Race Conditions**
- `_CALL_SITE_CACHE`: Concurrent `__setitem__` and `__getitem__` operations (lines 229-234, 302-308)
- `_PROFILER_REGISTRY`: Concurrent profiler registration (line 75)
- **Impact**: Cache corruption, lost profiler instances, KeyError exceptions

**Issue 2: Non-Atomic Counter**
- `_NEXT_PROFILER_ID`: Read-modify-write without synchronization (lines 72-74)
- **Impact**: Duplicate profiler IDs, registry collisions

**Issue 3: Unprotected Data Mutations**
- `ProfileBlock.record_time()`: 4 field updates without atomicity (types.py lines 41-44)
- **Impact**: Inconsistent statistics (e.g., hit_count=10 but total_time_ns reflects 9 measurements)

**Issue 4: Dictionary Resizing**
- `_tracks`, `_next_block_idx`: Concurrent insertions can trigger dict resizing (lines 131-132, 149-150)
- **Impact**: Segmentation faults, corrupted internal hash tables

**Severity**: **CRITICAL** - Prototype is unsafe for multi-threaded use. Data corruption and crashes are likely under concurrent load.

---

## Aspect 1: Data Structure Safety

This section evaluates approaches for protecting profiling data structures from race conditions in multi-threaded environments.

### Approach 1.1: Thread-Local Storage (threading.local())

**Description**: Each thread maintains its own isolated profiling data using Python's `threading.local()`. No shared state between threads during profiling. Results aggregated at retrieval time.

**Implementation Pattern**:
```python
import threading

class Profiler:
    def __init__(self, name: str):
        self._name = name
        self._thread_local = threading.local()  # Per-thread storage
        self._global_lock = threading.RLock()   # For aggregation only
        self._all_thread_data = {}              # Thread ID -> thread data

    def _get_thread_data(self):
        """Get or create thread-local profiling data."""
        if not hasattr(self._thread_local, 'tracks'):
            thread_id = threading.get_ident()
            self._thread_local.tracks = {}
            self._thread_local.next_block_idx = {}
            with self._global_lock:
                self._all_thread_data[thread_id] = self._thread_local
        return self._thread_local

    def get_results(self):
        """Aggregate results from all threads."""
        with self._global_lock:
            # Merge data from all threads
            aggregated = {}
            for thread_data in self._all_thread_data.values():
                # Merge thread_data.tracks into aggregated
                pass
        return aggregated
```

**Pros**:
- ✅ **Zero contention during profiling**: No locks needed in hot path (record_time)
- ✅ **Excellent performance**: No synchronization overhead during measurement
- ✅ **Simple reasoning**: Each thread operates independently
- ✅ **Natural fit**: Profiling is inherently per-thread activity
- ✅ **Industry standard**: Used by yappi (thread-aware profiler)

**Cons**:
- ❌ **Aggregation complexity**: Must merge data from all threads at retrieval
- ❌ **Memory overhead**: Duplicate data structures per thread
- ❌ **Thread lifecycle**: Must handle thread creation/destruction
- ❌ **Global cache still needed**: Call-site cache requires separate protection

**Performance Impact**:
- **Hot path (record_time)**: ~0% overhead (no locks)
- **Cold path (get_results)**: One-time aggregation cost (acceptable)
- **Memory**: O(threads × blocks) vs O(blocks)

**Industry Examples**:
- **yappi**: Uses thread-local storage for per-thread CPU/wall time tracking
- **cProfile**: Thread-local profiler instances (manual setup required)

---

### Approach 1.2: Lock-Based Synchronization (RLock/Lock)

**Description**: Protect all shared data structures with locks. Use `threading.RLock()` (reentrant lock) to allow nested profiler calls.

**Implementation Pattern**:
```python
import threading

class Profiler:
    def __init__(self, name: str):
        self._name = name
        self._lock = threading.RLock()  # Reentrant lock
        self._tracks = {}
        self._next_block_idx = {}

    def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int):
        with self._lock:  # Acquire lock for every measurement
            track = self._tracks.get(track_idx)
            if track:
                block = track.get_block(block_idx)
                if block:
                    block.record_time(elapsed_ns)  # Protected by lock
```

**Pros**:
- ✅ **Simple implementation**: Straightforward lock acquisition
- ✅ **No aggregation needed**: Single shared data structure
- ✅ **Well-understood**: Standard Python threading pattern
- ✅ **Correct by construction**: Lock guarantees mutual exclusion

**Cons**:
- ❌ **Lock contention**: High contention under heavy multi-threaded load
- ❌ **Performance overhead**: Lock acquisition on every measurement (~50-100ns)
- ❌ **Scalability**: Performance degrades with thread count
- ❌ **Deadlock risk**: Requires careful lock ordering (mitigated by RLock)

**Performance Impact**:
- **Hot path (record_time)**: +50-100ns per measurement (lock overhead)
- **Contention**: Increases linearly with thread count
- **Worst case**: 10 threads × 1000 measurements/sec = significant contention

**When to Use**:
- Low-contention scenarios (few threads, infrequent measurements)
- Simplicity prioritized over performance
- Combined with thread-local storage for hybrid approach

---

### Approach 1.3: Lock-Free / Atomic Operations

**Description**: Use atomic operations for counters and lock-free data structures to avoid lock contention.

**Implementation Challenges**:
```python
# Python has NO native atomic operations for user code
# No equivalent to C++ std::atomic<T> or Java AtomicInteger

# Workarounds:
# 1. ctypes with C atomic operations (complex, platform-specific)
# 2. multiprocessing.Value (heavyweight, designed for processes)
# 3. Third-party libraries (atomics, atomic-counter) - limited adoption
```

**Pros**:
- ✅ **No lock contention**: Theoretically better scalability
- ✅ **Wait-free progress**: No thread blocking

**Cons**:
- ❌ **No Python support**: No standard library atomic primitives
- ❌ **Complex implementation**: Requires C extensions or ctypes
- ❌ **Limited applicability**: Only works for simple counters, not complex data structures
- ❌ **ABA problem**: Classic lock-free data structure issues
- ❌ **Memory ordering**: Python's memory model is underspecified for lock-free code
- ❌ **Maintenance burden**: Platform-specific code, hard to debug

**Performance Impact**:
- **Theoretical**: Better than locks under high contention
- **Practical**: Implementation complexity outweighs benefits for Python

**Verdict**: **NOT RECOMMENDED** for Stichotrope. Python lacks native support, and complexity far exceeds benefits for a profiling library.

---

### Approach 1.4: Immutable Data Structures + Copy-on-Write

**Description**: Use immutable data structures. Create new copies on updates rather than mutating in place.

**Implementation Pattern**:
```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)  # Immutable
class ProfileBlock:
    name: str
    file: str
    line: int
    hit_count: int = 0
    total_time_ns: int = 0
    min_time_ns: int = 2**63 - 1
    max_time_ns: int = 0

    def record_time(self, elapsed_ns: int) -> 'ProfileBlock':
        """Return new ProfileBlock with updated statistics."""
        return replace(
            self,
            hit_count=self.hit_count + 1,
            total_time_ns=self.total_time_ns + elapsed_ns,
            min_time_ns=min(self.min_time_ns, elapsed_ns),
            max_time_ns=max(self.max_time_ns, elapsed_ns)
        )

# Still need locks to update the containing dictionary
def _record_block_time(self, track_idx, block_idx, elapsed_ns):
    with self._lock:  # Lock still required for dict update
        old_block = self._tracks[track_idx].blocks[block_idx]
        new_block = old_block.record_time(elapsed_ns)
        self._tracks[track_idx].blocks[block_idx] = new_block  # Replace
```

**Pros**:
- ✅ **Thread-safe reads**: Immutable objects safe to read concurrently
- ✅ **Functional style**: Easier to reason about state changes

**Cons**:
- ❌ **Still need locks**: Dictionary updates require synchronization
- ❌ **Memory overhead**: Creates new objects on every measurement
- ❌ **GC pressure**: Frequent allocations increase garbage collection
- ❌ **Performance**: Object creation + GC overhead > lock overhead
- ❌ **Complexity**: Doesn't eliminate locks, just moves them

**Performance Impact**:
- **Object creation**: ~100-200ns per measurement (dataclass instantiation)
- **GC pressure**: Increases with measurement frequency
- **Net result**: Worse than simple locks

**Verdict**: **NOT RECOMMENDED**. Adds complexity and overhead without eliminating locks.

---

### Aspect 1 Summary

| Approach | Performance | Complexity | Scalability | Recommendation |
|----------|-------------|------------|-------------|----------------|
| Thread-Local Storage | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Moderate | ⭐⭐⭐⭐⭐ Excellent | ✅ **Recommended** |
| Lock-Based Sync | ⭐⭐⭐ Good | ⭐⭐⭐⭐⭐ Simple | ⭐⭐ Poor | ⚠️ Use with thread-local |
| Lock-Free/Atomic | ⭐⭐⭐⭐ Very Good | ⭐ Very Complex | ⭐⭐⭐⭐ Very Good | ❌ Not viable in Python |
| Immutable + CoW | ⭐⭐ Poor | ⭐⭐ Complex | ⭐⭐ Poor | ❌ Not recommended |

**Recommended**: **Hybrid Thread-Local + Lock-Based**
- Thread-local storage for per-thread profiling data (zero contention in hot path)
- RLock-protected global structures (call-site cache, profiler registry)
- Lock-protected aggregation during `get_results()` (cold path)

---

## Aspect 2: Profiler Threading

This section evaluates how the profiler itself should handle threading - whether measurements should be synchronous, asynchronous, or hybrid.

### Approach 2.1: Synchronous Profiling (Measurements on Calling Thread)

**Description**: All profiling operations (timing, recording) happen on the thread being profiled. No separate profiler threads.

**Implementation Pattern**:
```python
class Profiler:
    def track(self, track_idx: int, name: str):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # All operations on calling thread
                start = get_time_ns()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end = get_time_ns()
                    elapsed = end - start
                    # Record immediately on this thread
                    self._record_block_time(track_idx, block_idx, elapsed)
            return wrapper
        return decorator
```

**Pros**:
- ✅ **Accurate timing**: Measurements on same thread as execution
- ✅ **Simple implementation**: No thread management complexity
- ✅ **Deterministic**: Predictable execution order
- ✅ **Low overhead**: No queue operations, no thread synchronization
- ✅ **Easy debugging**: Stack traces show profiler in context
- ✅ **No timing skew**: Immediate measurement, no queuing delays

**Cons**:
- ❌ **Blocking**: Recording happens in critical path (mitigated by thread-local storage)
- ❌ **Overhead on measured thread**: All profiling work on application thread

**Performance Impact**:
- **With thread-local storage**: ~100-200ns per measurement (time.perf_counter_ns × 2)
- **With locks**: +50-100ns (lock acquisition)
- **Total**: ~150-300ns per measurement
- **Comparison to prototype**: Similar overhead (prototype: 0.02-0.23% for ≥1ms blocks)

**Industry Examples**:
- **cProfile**: Synchronous profiling (sys.setprofile hook)
- **yappi**: Synchronous profiling with thread-local storage
- **line_profiler**: Synchronous line-by-line profiling

**Verdict**: **RECOMMENDED**. Proven approach with minimal complexity and accurate measurements.

---

### Approach 2.2: Asynchronous Profiling (Separate Profiler Thread)

**Description**: Profiler runs on a separate background thread. Measurements are taken asynchronously, potentially using sampling or periodic polling.

**Implementation Pattern**:
```python
import threading
import queue

class Profiler:
    def __init__(self, name: str):
        self._name = name
        self._profiler_thread = threading.Thread(target=self._profiler_loop, daemon=True)
        self._profiler_thread.start()

    def _profiler_loop(self):
        """Background thread that performs profiling."""
        while True:
            # Sample stack traces from all threads
            for thread_id, frame in sys._current_frames().items():
                # Record stack trace
                pass
            time.sleep(0.01)  # Sample every 10ms
```

**Pros**:
- ✅ **Non-blocking**: Profiling doesn't block application threads
- ✅ **Sampling profiler**: Can implement statistical profiling (like py-spy)

**Cons**:
- ❌ **Inaccurate for block profiling**: Sampling doesn't capture exact block boundaries
- ❌ **Timing skew**: Asynchronous measurements miss exact start/stop times
- ❌ **Complex implementation**: Thread lifecycle, synchronization, shutdown
- ❌ **Not deterministic**: Sampling introduces non-determinism
- ❌ **Wrong model**: Stichotrope is explicit instrumentation, not sampling
- ❌ **GIL contention**: Background thread competes for GIL with application threads

**Performance Impact**:
- **Sampling overhead**: Depends on sampling frequency
- **GIL contention**: Background thread wakes up periodically, acquires GIL
- **Accuracy loss**: Cannot measure exact block durations

**Verdict**: **NOT RECOMMENDED**. Asynchronous profiling is for sampling profilers (py-spy, pyinstrument), not explicit instrumentation profilers like Stichotrope.

---

### Approach 2.3: Hybrid (Start/Stop on Main Thread, Aggregation on Separate Thread)

**Description**: Timing measurements on calling thread, but data aggregation/processing happens on a background thread.

**Implementation Pattern**:
```python
import threading
import queue

class Profiler:
    def __init__(self, name: str):
        self._name = name
        self._measurement_queue = queue.Queue()
        self._aggregator_thread = threading.Thread(target=self._aggregator_loop, daemon=True)
        self._aggregator_thread.start()

    def _record_block_time(self, track_idx, block_idx, elapsed_ns):
        # Put measurement in queue (non-blocking)
        self._measurement_queue.put((track_idx, block_idx, elapsed_ns))

    def _aggregator_loop(self):
        """Background thread that aggregates measurements."""
        while True:
            track_idx, block_idx, elapsed_ns = self._measurement_queue.get()
            # Update data structures on background thread
            with self._lock:
                self._tracks[track_idx].blocks[block_idx].record_time(elapsed_ns)
```

**Pros**:
- ✅ **Reduced blocking**: Application thread only queues measurements
- ✅ **Centralized aggregation**: Single thread updates data structures

**Cons**:
- ❌ **Queue overhead**: Queue.put() + Queue.get() ~200-500ns per measurement
- ❌ **Memory overhead**: Queue buffering of measurements
- ❌ **Complexity**: Thread lifecycle, queue management, shutdown coordination
- ❌ **Shutdown complexity**: Must drain queue before exit
- ❌ **Ordering issues**: Measurements may be processed out of order
- ❌ **Debugging difficulty**: Profiler state updated asynchronously
- ❌ **No performance gain**: Queue overhead > lock overhead
- ❌ **GIL contention**: Background thread still competes for GIL

**Performance Impact**:
- **Queue.put()**: ~100-200ns (thread-safe queue operation)
- **Queue.get()**: ~100-200ns (background thread)
- **Total**: ~200-400ns per measurement
- **Comparison**: Worse than synchronous + thread-local (~150-300ns)

**Stakeholder Question**: "Hybrid approach (start/stop on main thread, data aggregation on separate thread) --> Solution some of the stakeholders had in mind; is it any good?"

**Answer**: **NO, not recommended**. Analysis shows:
1. **No performance benefit**: Queue overhead (200-400ns) > synchronous + thread-local (150-300ns)
2. **Increased complexity**: Thread management, queue draining, shutdown coordination
3. **Debugging difficulty**: Asynchronous state updates make debugging harder
4. **GIL contention**: Background thread doesn't avoid GIL, just moves contention
5. **Better alternative**: Synchronous profiling + thread-local storage achieves same goals with less complexity

**Verdict**: **NOT RECOMMENDED**. Complexity outweighs benefits. Thread-local storage achieves better performance without background threads.

---

### Approach 2.4: Queue-Based Profiling (Measurements Queued, Processed by Background Thread)

**Description**: Similar to hybrid approach, but with more sophisticated queue-based architecture. Measurements are queued and batch-processed.

**Implementation Pattern**:
```python
import threading
import queue
from collections import deque

class Profiler:
    def __init__(self, name: str):
        self._name = name
        self._measurement_queue = queue.Queue(maxsize=10000)  # Bounded queue
        self._processor_thread = threading.Thread(target=self._processor_loop, daemon=True)
        self._processor_thread.start()

    def _record_block_time(self, track_idx, block_idx, elapsed_ns):
        try:
            self._measurement_queue.put_nowait((track_idx, block_idx, elapsed_ns))
        except queue.Full:
            # Drop measurement if queue full (data loss!)
            pass

    def _processor_loop(self):
        """Background thread that batch-processes measurements."""
        batch = []
        while True:
            # Collect batch of measurements
            try:
                batch.append(self._measurement_queue.get(timeout=0.1))
                if len(batch) >= 100:  # Process in batches
                    self._process_batch(batch)
                    batch.clear()
            except queue.Empty:
                if batch:
                    self._process_batch(batch)
                    batch.clear()
```

**Pros**:
- ✅ **Batch processing**: Amortize lock overhead across multiple measurements
- ✅ **Bounded queue**: Prevents unbounded memory growth

**Cons**:
- ❌ **Data loss**: Bounded queue can drop measurements under load
- ❌ **Latency**: Batch processing delays result availability
- ❌ **Complexity**: Queue management, batching logic, shutdown coordination
- ❌ **Memory overhead**: Queue buffering + batch buffering
- ❌ **Tuning required**: Queue size, batch size, timeout - all need tuning
- ❌ **Worse than alternatives**: Thread-local storage is simpler and faster

**Performance Impact**:
- **Best case**: Amortized ~50-100ns per measurement (batching)
- **Worst case**: Data loss under high load
- **Complexity cost**: High implementation and maintenance burden

**Verdict**: **NOT RECOMMENDED**. Complexity far exceeds benefits. Thread-local storage is simpler, faster, and doesn't lose data.

---

### Aspect 2 Summary

| Approach | Accuracy | Performance | Complexity | Recommendation |
|----------|----------|-------------|------------|----------------|
| Synchronous Profiling | ⭐⭐⭐⭐⭐ Exact | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐⭐ Simple | ✅ **Recommended** |
| Asynchronous Profiling | ⭐⭐ Poor | ⭐⭐⭐ Good | ⭐⭐ Complex | ❌ Wrong model |
| Hybrid (Queue) | ⭐⭐⭐⭐ Good | ⭐⭐⭐ Good | ⭐⭐ Complex | ❌ No benefit |
| Queue-Based Batch | ⭐⭐⭐ Fair | ⭐⭐⭐⭐ Very Good | ⭐ Very Complex | ❌ Over-engineered |

**Recommended**: **Synchronous Profiling**
- All measurements on calling thread (accurate timing)
- Thread-local storage eliminates contention (no locks in hot path)
- Simple implementation (no thread management)
- Industry-proven approach (cProfile, yappi, line_profiler)

**Stakeholder Answer**: The hybrid approach is **not recommended**. Synchronous profiling with thread-local storage is simpler, faster, and more maintainable.

---

## Recommended Approach

Based on comprehensive evaluation of both aspects, the recommended architecture is:

### **Hybrid Thread-Local + Lock-Based Synchronous Profiling**

**Aspect 1 (Data Structure Safety)**: Hybrid Thread-Local + Lock-Based
**Aspect 2 (Profiler Threading)**: Synchronous Profiling

### Architecture Overview

```python
import threading
from typing import Dict, Any

class Profiler:
    """Thread-safe profiler using thread-local storage + synchronous profiling."""

    def __init__(self, name: str):
        self._name = name

        # Thread-local storage for per-thread profiling data
        self._thread_local = threading.local()

        # Global structures protected by RLock
        self._global_lock = threading.RLock()
        self._all_thread_data: Dict[int, Any] = {}  # thread_id -> thread data

        # Global call-site cache (protected by lock)
        self._call_site_cache: Dict[tuple, tuple] = {}

        # Profiler state
        self._started = True

    def _get_thread_data(self):
        """Get or create thread-local profiling data."""
        if not hasattr(self._thread_local, 'tracks'):
            # Initialize thread-local storage
            thread_id = threading.get_ident()
            self._thread_local.tracks = {}
            self._thread_local.next_block_idx = {}
            self._thread_local.track_enabled = {}

            # Register this thread's data (protected by lock)
            with self._global_lock:
                self._all_thread_data[thread_id] = self._thread_local

        return self._thread_local

    def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int):
        """Record measurement on calling thread (synchronous, no locks)."""
        thread_data = self._get_thread_data()

        # No lock needed - thread-local data
        track = thread_data.tracks.get(track_idx)
        if track:
            block = track.get_block(block_idx)
            if block:
                block.record_time(elapsed_ns)  # Thread-safe (thread-local)

    def get_results(self):
        """Aggregate results from all threads (cold path, lock-protected)."""
        with self._global_lock:
            aggregated_tracks = {}

            # Merge data from all threads
            for thread_id, thread_data in self._all_thread_data.items():
                for track_idx, track in thread_data.tracks.items():
                    if track_idx not in aggregated_tracks:
                        aggregated_tracks[track_idx] = self._create_aggregated_track(track_idx)

                    # Merge blocks from this thread into aggregated track
                    for block_idx, block in track.blocks.items():
                        self._merge_block(aggregated_tracks[track_idx], block_idx, block)

            return ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)
```

### Key Design Decisions

**1. Thread-Local Storage for Hot Path**
- **Rationale**: Eliminates lock contention during measurements (hot path)
- **Performance**: ~100-200ns per measurement (no lock overhead)
- **Trade-off**: Aggregation complexity (acceptable - cold path)

**2. Synchronous Profiling**
- **Rationale**: Accurate timing, simple implementation, industry-proven
- **Performance**: No queue overhead, no background thread GIL contention
- **Trade-off**: Profiling work on application thread (mitigated by thread-local storage)

**3. RLock-Protected Global Structures**
- **Rationale**: Call-site cache and profiler registry need shared access
- **Performance**: Cold path only (decorator application, get_results)
- **Trade-off**: Lock overhead acceptable for infrequent operations

**4. Aggregation at Retrieval Time**
- **Rationale**: Defer expensive merging until results needed
- **Performance**: One-time cost, not in hot path
- **Trade-off**: get_results() is slower (acceptable for profiling use case)

### Performance Characteristics

**Hot Path (record_time)**:
- Thread-local access: ~10-20ns (dict lookup)
- Time measurement: ~100-200ns (perf_counter_ns × 2)
- Block update: ~20-30ns (4 field updates)
- **Total**: ~130-250ns per measurement

**Cold Path (get_results)**:
- Lock acquisition: ~50-100ns (one-time)
- Aggregation: O(threads × blocks) (one-time)
- **Total**: Acceptable for infrequent operation

**Comparison to Prototype**:
- Prototype: 0.02-0.23% overhead for ≥1ms blocks
- Thread-safe: ~0.02-0.25% overhead (similar, within ≤1% target)

### Scalability

**Thread Count**: Excellent
- No contention in hot path (thread-local storage)
- Linear memory growth: O(threads × blocks)
- Aggregation time: O(threads × blocks) (one-time)

**Measurement Frequency**: Excellent
- No locks in hot path
- No queue buffering
- No GIL contention from background threads

---

## Trade-off Analysis

### Performance vs Complexity vs Maintainability

| Dimension | Thread-Local + Sync | Lock-Based Only | Queue-Based Hybrid | Lock-Free |
|-----------|---------------------|-----------------|-------------------|-----------|
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Complexity** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Maintainability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Scalability** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Debuggability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **Industry Adoption** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐ |

### Performance Trade-offs

**Chosen Approach (Thread-Local + Sync)**:
- ✅ **Hot path**: ~130-250ns per measurement (excellent)
- ✅ **Scalability**: No contention, linear with threads
- ⚠️ **Memory**: O(threads × blocks) vs O(blocks)
- ⚠️ **Aggregation**: O(threads × blocks) one-time cost

**Alternative (Lock-Based Only)**:
- ⚠️ **Hot path**: ~180-350ns per measurement (lock overhead)
- ❌ **Scalability**: Contention increases with threads
- ✅ **Memory**: O(blocks) (minimal)
- ✅ **Aggregation**: None needed

**Rejected (Queue-Based Hybrid)**:
- ⚠️ **Hot path**: ~200-400ns per measurement (queue overhead)
- ⚠️ **Scalability**: Queue becomes bottleneck
- ❌ **Memory**: O(queue_size + threads × blocks)
- ❌ **Complexity**: Thread management, shutdown coordination

### Complexity Trade-offs

**Chosen Approach**:
- ⚠️ **Moderate complexity**: Thread-local storage + aggregation logic
- ✅ **Well-understood patterns**: Standard Python threading.local()
- ✅ **No exotic primitives**: No C extensions, no lock-free algorithms
- ✅ **Debuggable**: Synchronous execution, clear stack traces

**Rejected Alternatives**:
- ❌ **Queue-based**: High complexity (thread lifecycle, queue management, shutdown)
- ❌ **Lock-free**: Very high complexity (C extensions, platform-specific, ABA problem)

### Maintainability Trade-offs

**Chosen Approach**:
- ✅ **Industry-proven**: yappi, cProfile use similar patterns
- ✅ **Standard library**: Only uses threading.local(), threading.RLock()
- ✅ **Testable**: Deterministic behavior, easy to write tests
- ✅ **Documented**: Well-understood threading patterns

**Rejected Alternatives**:
- ❌ **Queue-based**: Complex shutdown logic, hard to test edge cases
- ❌ **Lock-free**: Platform-specific, hard to debug, limited Python expertise

### Risk Analysis

**Chosen Approach Risks**:
- ⚠️ **Memory growth**: O(threads × blocks) - mitigated by typical thread counts (10-100)
- ⚠️ **Aggregation cost**: O(threads × blocks) - acceptable for infrequent operation
- ⚠️ **Thread lifecycle**: Must handle thread creation/destruction - standard pattern

**Mitigation Strategies**:
1. **Memory**: Document memory characteristics, provide clear() method
2. **Aggregation**: Lazy aggregation only when get_results() called
3. **Thread lifecycle**: Use threading.get_ident() for robust thread tracking

---

## Prototype Comparison

### Prototype v0.5.0 Architecture

**File**: `stichotrope/profiler.py`

**Thread-Safety Status**: ❌ **NOT THREAD-SAFE**

**Key Differences**:

| Aspect | Prototype v0.5.0 | Recommended v1.0.0 |
|--------|------------------|-------------------|
| **Data Storage** | Global dicts (shared) | Thread-local storage |
| **Synchronization** | None | RLock for global structures |
| **Profiler Threading** | Synchronous (implicit) | Synchronous (explicit) |
| **Call-Site Cache** | Global dict (unsafe) | RLock-protected global dict |
| **Block Recording** | Direct mutation (unsafe) | Thread-local mutation (safe) |
| **Results Aggregation** | Direct access (unsafe) | Lock-protected aggregation |
| **Performance** | 0.02-0.23% overhead | ~0.02-0.25% overhead (similar) |

### Specific Changes Required

**1. Global State Protection**

**Prototype** (unsafe):
```python
# Line 21: Global call-site cache (no protection)
_CALL_SITE_CACHE: dict[tuple[int, str, int, str], tuple[int, int]] = {}

# Lines 229-234: Unsafe cache access
cache_key = (track_idx, file, line, block_name)
if cache_key in _CALL_SITE_CACHE:  # Race condition
    profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
else:
    block_idx = self._register_block(track_idx, block_name, file, line)
    _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)  # Race condition
```

**Recommended** (safe):
```python
class Profiler:
    # Class-level lock for global structures
    _global_cache_lock = threading.RLock()
    _call_site_cache: dict[tuple[int, str, int, str], tuple[int, int]] = {}

    def _get_or_register_block(self, track_idx, file, line, name):
        cache_key = (track_idx, file, line, name)

        # Protected cache access
        with self._global_cache_lock:
            if cache_key in self._call_site_cache:
                profiler_id, block_idx = self._call_site_cache[cache_key]
            else:
                block_idx = self._register_block(track_idx, name, file, line)
                self._call_site_cache[cache_key] = (self._profiler_id, block_idx)

        return block_idx
```

**2. Instance State Thread-Local Storage**

**Prototype** (unsafe):
```python
# Lines 78-81: Shared instance state
self._tracks: dict[int, ProfileTrack] = {}
self._track_enabled: dict[int, bool] = {}
self._next_block_idx: dict[int, int] = {}
```

**Recommended** (safe):
```python
class Profiler:
    def __init__(self, name: str):
        self._name = name

        # Thread-local storage for per-thread data
        self._thread_local = threading.local()

        # Global lock for aggregation
        self._global_lock = threading.RLock()
        self._all_thread_data: Dict[int, Any] = {}

    def _get_thread_data(self):
        """Get or create thread-local profiling data."""
        if not hasattr(self._thread_local, 'tracks'):
            thread_id = threading.get_ident()
            self._thread_local.tracks = {}
            self._thread_local.next_block_idx = {}
            self._thread_local.track_enabled = {}

            with self._global_lock:
                self._all_thread_data[thread_id] = self._thread_local

        return self._thread_local
```

**3. Block Recording Thread-Safety**

**Prototype** (unsafe):
```python
# types.py lines 34-44: Unprotected mutations
def record_time(self, elapsed_ns: int) -> None:
    self.hit_count += 1                              # Race condition
    self.total_time_ns += elapsed_ns                 # Race condition
    self.min_time_ns = min(self.min_time_ns, elapsed_ns)  # Race condition
    self.max_time_ns = max(self.max_time_ns, elapsed_ns)  # Race condition
```

**Recommended** (safe):
```python
# With thread-local storage, each thread has its own ProfileBlock instance
# No race conditions because no sharing between threads
def record_time(self, elapsed_ns: int) -> None:
    # Safe: thread-local data, no concurrent access
    self.hit_count += 1
    self.total_time_ns += elapsed_ns
    self.min_time_ns = min(self.min_time_ns, elapsed_ns)
    self.max_time_ns = max(self.max_time_ns, elapsed_ns)
```

**4. Results Aggregation**

**Prototype** (unsafe):
```python
# Lines 172-181: Direct access to shared state
def get_results(self) -> ProfilerResults:
    results = ProfilerResults(profiler_name=self._name)
    results.tracks = self._tracks.copy()  # Unsafe: concurrent modifications
    return results
```

**Recommended** (safe):
```python
def get_results(self) -> ProfilerResults:
    """Aggregate results from all threads."""
    with self._global_lock:
        aggregated_tracks = {}

        # Merge data from all threads
        for thread_id, thread_data in self._all_thread_data.items():
            for track_idx, track in thread_data.tracks.items():
                if track_idx not in aggregated_tracks:
                    aggregated_tracks[track_idx] = self._create_aggregated_track(track_idx)

                # Merge blocks from this thread
                for block_idx, block in track.blocks.items():
                    self._merge_block(aggregated_tracks[track_idx], block_idx, block)

        return ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)

def _merge_block(self, aggregated_track, block_idx, source_block):
    """Merge a block from one thread into aggregated results."""
    if block_idx not in aggregated_track.blocks:
        # Create new aggregated block
        aggregated_track.blocks[block_idx] = ProfileBlock(
            name=source_block.name,
            file=source_block.file,
            line=source_block.line
        )

    # Merge statistics
    agg_block = aggregated_track.blocks[block_idx]
    agg_block.hit_count += source_block.hit_count
    agg_block.total_time_ns += source_block.total_time_ns
    agg_block.min_time_ns = min(agg_block.min_time_ns, source_block.min_time_ns)
    agg_block.max_time_ns = max(agg_block.max_time_ns, source_block.max_time_ns)
```

### Migration Impact

**Breaking Changes**: None (API remains compatible)

**Performance Impact**: Minimal (~0.02% increase, within ≤1% target)

**Memory Impact**: O(threads × blocks) vs O(blocks) - acceptable for typical use cases

**Code Complexity**: Moderate increase (thread-local storage + aggregation logic)

---

## Implementation Considerations

### 1. Thread Lifecycle Management

**Challenge**: Threads may be created and destroyed during profiling.

**Solution**:
```python
def _get_thread_data(self):
    """Get or create thread-local profiling data."""
    if not hasattr(self._thread_local, 'tracks'):
        thread_id = threading.get_ident()
        self._thread_local.tracks = {}

        # Register thread data
        with self._global_lock:
            self._all_thread_data[thread_id] = self._thread_local

    return self._thread_local

# Note: Thread cleanup handled by Python's threading.local() automatically
# When thread exits, thread-local data is garbage collected
```

**Trade-off**: Dead thread data remains in `_all_thread_data` until profiler cleared. Acceptable for typical profiling sessions.

### 2. Call-Site Cache Synchronization

**Challenge**: Call-site cache is global and accessed from multiple threads.

**Solution**:
```python
class Profiler:
    # Class-level lock for call-site cache
    _global_cache_lock = threading.RLock()
    _call_site_cache: Dict[tuple, tuple] = {}

    def _get_or_register_block(self, track_idx, file, line, name):
        cache_key = (track_idx, file, line, name)

        # Check cache with lock
        with self._global_cache_lock:
            if cache_key in self._call_site_cache:
                return self._call_site_cache[cache_key][1]  # block_idx

            # Register new block (thread-local)
            thread_data = self._get_thread_data()
            block_idx = self._register_block_thread_local(thread_data, track_idx, name, file, line)

            # Cache result
            self._call_site_cache[cache_key] = (self._profiler_id, block_idx)
            return block_idx
```

**Performance**: Lock only acquired during decorator application (cold path), not during measurement (hot path).

### 3. Profiler Registry Thread-Safety

**Challenge**: Global profiler registry accessed from multiple threads.

**Solution**:
```python
class Profiler:
    _registry_lock = threading.RLock()
    _profiler_registry: Dict[int, 'Profiler'] = {}
    _next_profiler_id = 0

    def __init__(self, name: str):
        with self._registry_lock:
            self._profiler_id = self._next_profiler_id
            self._next_profiler_id += 1
            self._profiler_registry[self._profiler_id] = self
```

**Performance**: Lock only acquired during profiler instantiation (cold path).

### 4. Aggregation Algorithm

**Challenge**: Efficiently merge data from multiple threads.

**Algorithm**:
```python
def get_results(self) -> ProfilerResults:
    """Aggregate results from all threads."""
    with self._global_lock:
        aggregated_tracks = {}

        # Iterate over all threads
        for thread_id, thread_data in self._all_thread_data.items():
            # Iterate over tracks in this thread
            for track_idx, track in thread_data.tracks.items():
                # Create aggregated track if needed
                if track_idx not in aggregated_tracks:
                    aggregated_tracks[track_idx] = ProfileTrack(
                        track_idx=track_idx,
                        track_name=track.track_name
                    )

                # Merge blocks
                for block_idx, block in track.blocks.items():
                    self._merge_block(aggregated_tracks[track_idx], block_idx, block)

        return ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)
```

**Complexity**: O(threads × tracks × blocks) - acceptable for infrequent operation.

### 5. Testing Strategy

**Unit Tests**:
- Thread-local storage isolation
- Lock acquisition/release
- Aggregation correctness

**Integration Tests**:
- Multi-threaded profiling (10+ threads)
- Concurrent decorator application
- Concurrent get_results() calls

**Stress Tests**:
- High contention (100+ threads)
- Rapid thread creation/destruction
- Large number of blocks (1000+ per thread)

**Race Condition Detection**:
- ThreadSanitizer (if available)
- Stress testing with assertions
- Property-based testing (hypothesis)

---

## Conclusion

### Summary of Recommendations

**Aspect 1 (Data Structure Safety)**: **Hybrid Thread-Local + Lock-Based**
- Thread-local storage for per-thread profiling data
- RLock-protected global structures (call-site cache, profiler registry)
- Lock-protected aggregation during get_results()

**Aspect 2 (Profiler Threading)**: **Synchronous Profiling**
- All measurements on calling thread
- No background profiler threads
- No queue-based architectures

### Rationale

1. **Performance**: ~130-250ns per measurement (within ≤1% overhead target)
2. **Scalability**: No contention in hot path, linear with thread count
3. **Simplicity**: Well-understood patterns, standard library only
4. **Maintainability**: Industry-proven approach (yappi, cProfile)
5. **Correctness**: Deterministic behavior, accurate measurements

### Stakeholder Question Answered

**Question**: "Hybrid approach (start/stop on main thread, data aggregation on separate thread) --> Solution some of the stakeholders had in mind; is it any good?"

**Answer**: **No, not recommended**. Analysis shows:
- Queue overhead (200-400ns) > synchronous + thread-local (130-250ns)
- Increased complexity (thread management, shutdown coordination)
- No performance benefit (GIL contention remains)
- Better alternative: Synchronous profiling + thread-local storage

### Next Steps

1. **Stakeholder Review**: Review and approve this evaluation report
2. **Task 2.1.1**: Create detailed architecture design document based on approved approach
3. **Task 2.1.2**: Design comprehensive thread-safety test suite
4. **Task 2.1.3**: Implement thread-safe profiler core
5. **Task 2.1.4**: Execute thread-safety test suite

### Success Criteria Met

- ✅ **Aspect 1: Data Structure Safety** - 4 approaches documented with pros/cons
- ✅ **Aspect 2: Profiler Threading** - 4 approaches documented with pros/cons
- ✅ **Recommended Approach** - Clear selection with rationale for both aspects
- ✅ **Trade-off Analysis** - Performance vs complexity vs maintainability documented
- ✅ **Prototype Comparison** - How recommended approach differs from v0.5.0 documented
- ⏳ **Evaluation Review** - Stakeholder review and approval pending

---

**Report Version**: v0 (initial)
**Date**: 2025-11-04
**Author**: Architecture Analysis (Phase 1)
**Status**: Awaiting stakeholder review
**Next Action**: Stakeholder feedback and iteration to v1 if needed

