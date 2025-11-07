# Thread-Safe Architecture Design Document

**Task**: 2.1.1 – Design Thread-Safe Architecture Document  
**Issue**: [#18](https://github.com/LittleCoinCoin/stichotrope/issues/18)  
**Milestone**: 2.1 Thread-Safe Architecture Redesign  
**Version Target**: v0.2.0  
**Report Version**: v1 (refined)  
**Date**: 2025-11-04  
**Status**: Awaiting stakeholder review  
**Dependencies**: Task 2.1.0 (Architecture Evaluation) - ✅ APPROVED

---

## Changes from v0

### Improvements Based on Stakeholder Feedback

**1. Visual Clarity**
- ✅ Replaced ASCII diagrams with Mermaid diagrams (reusable in dev documentation)
- ✅ Added component relationship diagram
- ✅ Added sequence diagrams for hot/cold paths

**2. Reduced Code Verbosity**
- ✅ Converted detailed code to concise pseudo-code
- ✅ Kept only strategic code snippets (critical patterns)
- ✅ Reduced report length by ~40% (1818 → ~1100 lines)

**3. Enhanced Aggregation Analysis**
- ✅ Added binary merge algorithm analysis
- ✅ Compared sequential vs binary merge approaches
- ✅ Documented future optimization path (post-GIL Python)

**4. Streamlined Testing Section**
- ✅ Removed detailed test implementations (deferred to Task 2.1.2)
- ✅ Kept only high-level testing strategy

**5. API Design Clarification**
- ✅ Removed "backward compatibility required" constraint
- ✅ Evaluated API improvements (documented as future considerations)
- ✅ Maintained compatibility for v1.0.0 MVP (simplicity)

### Rationale

- **Mermaid diagrams**: Easier stakeholder review, reusable in MkDocs documentation
- **Pseudo-code focus**: Clearer architectural intent, less implementation detail
- **Binary merge analysis**: Addresses performance optimization question
- **Reduced testing**: Task 2.1.2 will provide comprehensive test design
- **API compatibility**: Safer for MVP, improvements deferred to v1.1.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Design Principles](#design-principles)
3. [Architecture Overview](#architecture-overview)
4. [Core Components Design](#core-components-design)
5. [Data Structures](#data-structures)
6. [Thread-Local Storage Strategy](#thread-local-storage-strategy)
7. [Lock Design](#lock-design)
8. [API Design](#api-design)
9. [Aggregation Algorithm](#aggregation-algorithm)
10. [Synchronization Patterns](#synchronization-patterns)
11. [Prototype Comparison](#prototype-comparison)
12. [Implementation Guidance](#implementation-guidance)
13. [Testing Strategy](#testing-strategy)
14. [Conclusion](#conclusion)

---

## Executive Summary

This document provides the detailed architectural design for Stichotrope v1.0.0's thread-safe profiler, based on the approved evaluation (Task 2.1.0).

**Design Approach**: **Hybrid Thread-Local + Lock-Based Synchronous Profiling**

**Key Design Decisions**:
1. **Thread-local storage** for per-thread profiling data (zero contention in hot path)
2. **RLock-protected global structures** (call-site cache, profiler registry)
3. **Synchronous profiling** (measurements on calling thread, no background threads)
4. **Sequential aggregation** (simple, GIL-friendly; binary merge deferred to post-GIL Python)
5. **Backward-compatible API** (no breaking changes for v1.0.0 MVP)

**Performance Target**: ≤1% overhead increase vs prototype (currently 0.02-0.23% for ≥1ms blocks)

**Complexity**: Moderate - uses standard library threading primitives only

---

## Design Principles

Based on the approved evaluation (Task 2.1.0), the design follows these principles:

### 1. Zero Contention in Hot Path
- **Principle**: No locks during measurement recording
- **Implementation**: Thread-local storage for all per-thread profiling data
- **Benefit**: Excellent scalability with thread count

### 2. Simplicity Over Optimization
- **Principle**: Use well-understood patterns, avoid exotic primitives
- **Implementation**: Standard library threading.local() and threading.RLock()
- **Benefit**: Maintainable, debuggable, testable

### 3. Correctness First
- **Principle**: Accurate measurements, deterministic behavior
- **Implementation**: Synchronous profiling (no sampling, no queues)
- **Benefit**: Reliable profiling data

### 4. Backward Compatibility
- **Principle**: No breaking API changes for v1.0.0 MVP
- **Implementation**: Same public interface as prototype v0.5.0
- **Benefit**: Smooth migration path
- **Note**: API improvements documented for v1.1.0

### 5. Lazy Aggregation
- **Principle**: Defer expensive operations to cold path
- **Implementation**: Aggregate thread data only in get_results()
- **Benefit**: Hot path remains fast

---

## Architecture Overview

### Component Architecture

```mermaid
graph TB
    subgraph "Application Threads"
        T1[Thread 1]
        T2[Thread 2]
        TN[Thread N]
    end

    subgraph "Profiler Instance"
        API[Public API Layer]

        subgraph "Thread-Local Storage"
            TL1[Thread 1 Data<br/>tracks, blocks, indices]
            TL2[Thread 2 Data<br/>tracks, blocks, indices]
            TLN[Thread N Data<br/>tracks, blocks, indices]
        end

        subgraph "Global State (RLock Protected)"
            LOCK[_global_lock: RLock]
            REGISTRY[_all_thread_data<br/>thread_id → thread_local]
        end
    end

    subgraph "Module-Level Global State"
        CACHE_LOCK[_GLOBAL_CACHE_LOCK]
        CACHE[_CALL_SITE_CACHE<br/>call-site → block_idx]
        REG_LOCK[_REGISTRY_LOCK]
        REG[_PROFILER_REGISTRY<br/>profiler_id → Profiler]
    end

    T1 -->|track/block| API
    T2 -->|track/block| API
    TN -->|track/block| API

    API -->|get_thread_data| TL1
    API -->|get_thread_data| TL2
    API -->|get_thread_data| TLN

    API -->|get_results| LOCK
    LOCK -->|aggregate| REGISTRY
    REGISTRY -->|read| TL1
    REGISTRY -->|read| TL2
    REGISTRY -->|read| TLN

    API -->|decorator| CACHE_LOCK
    CACHE_LOCK -->|protect| CACHE

    API -->|__init__| REG_LOCK
    REG_LOCK -->|protect| REG

    style TL1 fill:#90EE90
    style TL2 fill:#90EE90
    style TLN fill:#90EE90
    style LOCK fill:#FFB6C1
    style CACHE_LOCK fill:#FFB6C1
    style REG_LOCK fill:#FFB6C1
```

### Hot Path Data Flow (Measurement Recording)

```mermaid
sequenceDiagram
    participant App as Application Thread
    participant Wrapper as Decorator Wrapper
    participant TLS as Thread-Local Storage
    participant Block as ProfileBlock

    App->>Wrapper: Call profiled function
    Note over Wrapper: Check enable flags<br/>(no locks)
    Wrapper->>TLS: get_thread_data()
    TLS-->>Wrapper: thread_local data
    Note over Wrapper: Check track_enabled<br/>(thread-local, no lock)
    Wrapper->>Wrapper: start = get_time_ns()
    Wrapper->>App: Execute function
    App-->>Wrapper: Return result
    Wrapper->>Wrapper: end = get_time_ns()
    Wrapper->>TLS: Get track & block
    TLS-->>Wrapper: ProfileBlock
    Wrapper->>Block: record_time(elapsed)
    Note over Block: Update hit_count,<br/>total_time_ns, min, max<br/>(thread-local, no lock)
    Wrapper-->>App: Return result

    Note over Wrapper,Block: NO LOCKS IN HOT PATH<br/>~130-250ns overhead
```

### Cold Path Data Flow (Results Aggregation)

```mermaid
sequenceDiagram
    participant App as Application Thread
    participant Profiler as Profiler Instance
    participant Lock as _global_lock
    participant Registry as _all_thread_data
    participant TLS as Thread-Local Data

    App->>Profiler: get_results()
    Profiler->>Lock: Acquire lock
    Lock-->>Profiler: Lock acquired
    Profiler->>Registry: Iterate all threads
    loop For each thread
        Registry->>TLS: Get thread data
        TLS-->>Registry: tracks, blocks
        Registry->>Profiler: Merge into aggregated
        Note over Profiler: Merge blocks:<br/>sum hit_count, total_time<br/>min/max of min/max
    end
    Profiler->>Profiler: Create ProfilerResults
    Profiler->>Lock: Release lock
    Profiler-->>App: Return ProfilerResults

    Note over Profiler,Registry: LOCK-PROTECTED<br/>O(threads × blocks)<br/>Infrequent operation
```

### Lock Hierarchy

```mermaid
graph TD
    A[_REGISTRY_LOCK<br/>Module-level<br/>Profiler registration] -->|Lower priority| B[_GLOBAL_CACHE_LOCK<br/>Module-level<br/>Call-site cache]
    B -->|Lower priority| C[Profiler._global_lock<br/>Instance-level<br/>Thread data registry]

    style A fill:#FFE4E1
    style B fill:#FFE4E1
    style C fill:#FFE4E1

    Note1[Acquire in order 1→2→3<br/>to prevent deadlocks]

    A -.->|Rule| Note1
```

---

## Core Components Design

### 1. Profiler Class Structure

**Pseudo-code**:

```
CLASS Profiler:
    # Instance Attributes
    _profiler_id: int                    # Unique ID
    _name: str                           # Human-readable name
    _thread_local: threading.local       # Per-thread storage container
    _global_lock: RLock                  # Protects _all_thread_data
    _all_thread_data: Dict[int, Any]     # thread_id → thread-local data
    _started: bool                       # Instance enable/disable

    # Public API Methods (15 methods)
    FUNCTION __init__(name: str)
    FUNCTION start(), stop(), is_started()
    FUNCTION set_track_enabled(track_idx, enabled)
    FUNCTION is_track_enabled(track_idx) → bool
    FUNCTION set_track_name(track_idx, name)
    FUNCTION track(track_idx, name) → decorator
    FUNCTION block(track_idx, name) → context_manager
    FUNCTION get_results() → ProfilerResults
    FUNCTION clear()
    FUNCTION export_csv(filename), export_json(filename), print_results()

    # Internal Methods
    FUNCTION _get_thread_data() → thread_local_data
    FUNCTION _get_or_create_track(thread_data, track_idx) → ProfileTrack
    FUNCTION _register_block(thread_data, track_idx, name, file, line) → block_idx
    FUNCTION _record_block_time(track_idx, block_idx, elapsed_ns)
    FUNCTION _aggregate_results() → ProfilerResults
    FUNCTION _merge_block(aggregated_track, block_idx, source_block)
```

**Key Design Points**:
- Thread-local storage eliminates locks in hot path
- Global lock only for aggregation (cold path)
- All public methods thread-safe

### 2. Thread-Local Data Structure

**Pseudo-code**:

```
STRUCTURE ThreadLocalData (stored in threading.local()):
    tracks: Dict[int, ProfileTrack]      # track_idx → ProfileTrack
    next_block_idx: Dict[int, int]       # track_idx → next block index
    track_enabled: Dict[int, bool]       # track_idx → enabled flag
    thread_id: int                       # threading.get_ident()
    thread_name: str                     # threading.current_thread().name
```

**Initialization Pattern** (Critical):

```python
# CRITICAL: Check hasattr before accessing threading.local()
def _get_thread_data(self):
    if not hasattr(self._thread_local, 'tracks'):
        # First access from this thread - initialize
        self._thread_local.tracks = {}
        self._thread_local.next_block_idx = {}
        self._thread_local.track_enabled = {}
        self._thread_local.thread_id = threading.get_ident()
        self._thread_local.thread_name = threading.current_thread().name

        # Register in global registry (LOCK REQUIRED)
        with self._global_lock:
            self._all_thread_data[self._thread_local.thread_id] = self._thread_local

    return self._thread_local
```

**Why Critical**: Direct access to `threading.local()` attributes raises `AttributeError` on first access. Must use `hasattr()` check.

### 3. Module-Level Global State

**Pseudo-code**:

```
# Global enable/disable (read-only after init, no lock needed)
_PROFILER_ENABLED: bool = True

# Call-site cache (lock-protected)
_CALL_SITE_CACHE: Dict[tuple, tuple] = {}
_GLOBAL_CACHE_LOCK: RLock = RLock()

# Profiler registry (lock-protected)
_PROFILER_REGISTRY: Dict[int, Profiler] = {}
_NEXT_PROFILER_ID: int = 0
_REGISTRY_LOCK: RLock = RLock()

FUNCTION set_global_enabled(enabled: bool):
    _PROFILER_ENABLED = enabled

FUNCTION is_global_enabled() → bool:
    RETURN _PROFILER_ENABLED
```

---

## Data Structures

### ProfileBlock, ProfileTrack, ProfilerResults

**Design Decision**: No changes required from prototype v0.5.0.

**Rationale**: With thread-local storage, each thread has its own instances of these data structures. No concurrent access to the same instance means no race conditions.

**Structure Summary**:

```
DATACLASS ProfileBlock:
    name, file, line: str, str, int
    hit_count, total_time_ns: int, int
    min_time_ns, max_time_ns: int, int

    FUNCTION record_time(elapsed_ns):
        hit_count += 1
        total_time_ns += elapsed_ns
        min_time_ns = min(min_time_ns, elapsed_ns)
        max_time_ns = max(max_time_ns, elapsed_ns)

DATACLASS ProfileTrack:
    track_idx: int
    track_name: Optional[str]
    blocks: Dict[int, ProfileBlock]

    FUNCTION add_block(block_idx, name, file, line) → ProfileBlock
    FUNCTION get_block(block_idx) → Optional[ProfileBlock]

DATACLASS ProfilerResults:
    profiler_name: str
    tracks: Dict[int, ProfileTrack]
```

**Thread Safety**: Guaranteed by thread-local storage isolation.

---

## Thread-Local Storage Strategy

### Overview

Thread-local storage is the cornerstone of the thread-safe design. Each thread maintains isolated profiling data, eliminating contention in the hot path.

### Key Operations

**1. Thread-Local Initialization**

```
FUNCTION _get_thread_data() → thread_local_data:
    IF NOT hasattr(self._thread_local, 'tracks'):
        # First access from this thread
        thread_id = threading.get_ident()

        # Initialize thread-local storage
        self._thread_local.tracks = {}
        self._thread_local.next_block_idx = {}
        self._thread_local.track_enabled = {}
        self._thread_local.thread_id = thread_id

        # Register thread data (LOCK REQUIRED)
        LOCK self._global_lock:
            self._all_thread_data[thread_id] = self._thread_local

    RETURN self._thread_local
```

**2. Thread-Local Block Registration**

```
FUNCTION _register_block(thread_data, track_idx, name, file, line) → block_idx:
    track = _get_or_create_track(thread_data, track_idx)

    # Allocate block index (thread-local, no race condition)
    block_idx = thread_data.next_block_idx[track_idx]
    thread_data.next_block_idx[track_idx] += 1

    # Create block in thread-local track
    track.add_block(block_idx, name, file, line)

    RETURN block_idx
```

**3. Thread-Local Measurement Recording**

```
FUNCTION _record_block_time(track_idx, block_idx, elapsed_ns):
    thread_data = _get_thread_data()  # Thread-local access, NO LOCK

    track = thread_data.tracks.get(track_idx)
    IF track:
        block = track.get_block(block_idx)
        IF block:
            block.record_time(elapsed_ns)  # Thread-local mutation, NO LOCK
```

### Thread Lifecycle

**Thread Creation**: First call to `_get_thread_data()` initializes storage and registers thread.

**Thread Execution**: All profiling operations use thread-local data (no locks, no contention).

**Thread Termination**: Python's `threading.local()` automatically cleans up thread-local data. Thread data remains in `_all_thread_data` until `profiler.clear()` called.

**Memory**: O(threads × blocks). Typical: 50 threads × 100 blocks × 100 bytes = ~500 KB (acceptable).

---

## Lock Design

### Lock Hierarchy (Prevents Deadlocks)

**Rule**: Acquire locks in consistent order: `_REGISTRY_LOCK` → `_GLOBAL_CACHE_LOCK` → `Profiler._global_lock`

**Lock Purposes**:

| Lock | Scope | Protects | Frequency |
|------|-------|----------|-----------|
| `_REGISTRY_LOCK` | Module | Profiler registry, ID counter | Very low (profiler instantiation) |
| `_GLOBAL_CACHE_LOCK` | Module | Call-site cache | Low (decorator application) |
| `Profiler._global_lock` | Instance | Thread data registry | Low (thread registration, aggregation) |

### Lock Usage Patterns

**Pattern 1: Profiler Instantiation** (Cold Path)

```
FUNCTION __init__(name):
    LOCK _REGISTRY_LOCK:
        self._profiler_id = _NEXT_PROFILER_ID
        _NEXT_PROFILER_ID += 1
        _PROFILER_REGISTRY[self._profiler_id] = self

    # Initialize instance state (no lock needed)
    self._name = name
    self._thread_local = threading.local()
    self._global_lock = RLock()
    self._all_thread_data = {}
```

**Pattern 2: Call-Site Cache** (Cold Path)

```
FUNCTION track(track_idx, name) → decorator:
    FUNCTION decorator(func):
        cache_key = (track_idx, file, line, block_name)

        LOCK _GLOBAL_CACHE_LOCK:
            IF cache_key IN _CALL_SITE_CACHE:
                profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
            ELSE:
                # Register block (thread-local, no lock)
                thread_data = _get_thread_data()
                block_idx = _register_block(thread_data, track_idx, name, file, line)
                _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

        RETURN wrapper  # Hot path has NO LOCKS
```

**Pattern 3: Hot Path** (NO LOCKS)

```python
# CRITICAL: Hot path must have ZERO lock acquisitions
@functools.wraps(func)
def wrapper(*args, **kwargs):
    # All checks use thread-local or read-only data (NO LOCK)
    thread_data = self._get_thread_data()  # Thread-local

    if not thread_data.track_enabled.get(track_idx, True):  # Thread-local
        return func(*args, **kwargs)

    if not self._started:  # Read-only flag
        return func(*args, **kwargs)

    # Measurement (NO LOCK)
    start = get_time_ns()
    result = func(*args, **kwargs)
    end = get_time_ns()

    # Recording (NO LOCK - thread-local mutation)
    self._record_block_time(track_idx, block_idx, end - start)

    return result
```

**Why RLock**: Allows same thread to acquire lock multiple times (nested profiled calls). Prevents deadlock in recursive scenarios.

---

## API Design

### Public API Overview

All 15 public methods from prototype v0.5.0 are preserved with identical signatures for v1.0.0 MVP.

**API Improvements Considered**: Instance-level track enable/disable (affects all threads), per-thread results retrieval. **Decision**: Defer to v1.1.0 for simplicity.

### Key API Methods

**Profiler Lifecycle**:
```
__init__(name: str = "Profiler")
start(), stop(), is_started() → bool
clear()
```

**Track Management**:
```
set_track_enabled(track_idx: int, enabled: bool)
is_track_enabled(track_idx: int) → bool
set_track_name(track_idx: int, name: str)
```

**Profiling**:
```
track(track_idx: int, name: Optional[str] = None) → decorator
block(track_idx: int, name: str) → context_manager
```

**Results & Export**:
```
get_results() → ProfilerResults
export_csv(filename: str)
export_json(filename: str, indent: int = 2)
print_results()
```

### Critical Implementation: Decorator Hot Path

**Pseudo-code**:

```
FUNCTION track(track_idx, name) → decorator:
    # Cold path: Decorator application
    IF NOT _PROFILER_ENABLED:
        RETURN identity_decorator  # Zero overhead when disabled

    FUNCTION decorator(func):
        # Get call-site info and cache block_idx (LOCK REQUIRED)
        cache_key = (track_idx, file, line, block_name)
        block_idx = _get_or_register_block_cached(cache_key)

        FUNCTION wrapper(*args, **kwargs):
            # Hot path: Function execution (NO LOCKS)
            thread_data = _get_thread_data()

            IF NOT thread_data.track_enabled.get(track_idx, True):
                RETURN func(*args, **kwargs)

            IF NOT self._started:
                RETURN func(*args, **kwargs)

            # Profile function (NO LOCKS)
            start = get_time_ns()
            result = func(*args, **kwargs)
            end = get_time_ns()

            _record_block_time(track_idx, block_idx, end - start)
            RETURN result

        RETURN wrapper
    RETURN decorator
```

**Performance**: ~130-250ns per measurement (no lock overhead).

---

## Aggregation Algorithm

### Overview

The aggregation algorithm merges profiling data from all threads into a single `ProfilerResults` object. This is a cold-path operation (called infrequently).

### Sequential Aggregation (Recommended for v1.0.0)

**Algorithm**:

```
FUNCTION _aggregate_results() → ProfilerResults:
    LOCK self._global_lock:
        aggregated_tracks = {}

        # Sequential iteration over all threads
        FOR EACH thread_id, thread_data IN self._all_thread_data:
            FOR EACH track_idx, track IN thread_data.tracks:
                # Create aggregated track if needed
                IF track_idx NOT IN aggregated_tracks:
                    aggregated_tracks[track_idx] = NEW ProfileTrack(track_idx)

                # Merge blocks from this thread
                FOR EACH block_idx, block IN track.blocks:
                    _merge_block(aggregated_tracks[track_idx], block_idx, block)

        RETURN ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)

FUNCTION _merge_block(aggregated_track, block_idx, source_block):
    IF block_idx NOT IN aggregated_track.blocks:
        # First time seeing this block - create aggregated block
        aggregated_track.blocks[block_idx] = NEW ProfileBlock(
            name=source_block.name, file=source_block.file, line=source_block.line
        )

    agg_block = aggregated_track.blocks[block_idx]

    # Merge statistics
    agg_block.hit_count += source_block.hit_count
    agg_block.total_time_ns += source_block.total_time_ns
    agg_block.min_time_ns = min(agg_block.min_time_ns, source_block.min_time_ns)
    agg_block.max_time_ns = max(agg_block.max_time_ns, source_block.max_time_ns)
```

**Complexity**: O(T × K × B) where T=threads, K=tracks, B=blocks

**Performance**:
- Typical: 50 threads × 10 tracks × 100 blocks = 50,000 iterations
- ~10-20ns per iteration (dict operations)
- Total: ~0.5-1ms (acceptable for cold path)

### Binary Merge Alternative (Future Optimization)

**Algorithm**:

```
FUNCTION _aggregate_results_binary() → ProfilerResults:
    LOCK self._global_lock:
        thread_results = [thread_data FOR thread_data IN self._all_thread_data.values()]

        # Binary merge: divide and conquer
        WHILE len(thread_results) > 1:
            merged = []
            FOR i IN range(0, len(thread_results), 2):
                IF i + 1 < len(thread_results):
                    # Merge pair
                    merged.append(_merge_two_results(thread_results[i], thread_results[i+1]))
                ELSE:
                    # Odd one out
                    merged.append(thread_results[i])
            thread_results = merged

        RETURN thread_results[0]
```

**Complexity**: O(log(T) × K × B) if parallelized

### Sequential vs Binary Merge Comparison

| Aspect | Sequential | Binary Merge |
|--------|-----------|--------------|
| **Time Complexity** | O(T × K × B) | O(log(T) × K × B) if parallel |
| **Python GIL** | No parallelization | No parallelization (GIL prevents) |
| **Actual Performance** | ~0.5-1ms (T=50) | ~0.5-1ms (same, no parallel benefit) |
| **Code Complexity** | Simple (20 lines) | Complex (50+ lines) |
| **Maintainability** | High | Moderate |
| **Memory** | O(K × B) | O(K × B × log(T)) (intermediate results) |

**Analysis**:

```mermaid
graph LR
    A[Sequential Merge] -->|Python GIL| B[No Parallelization]
    C[Binary Merge] -->|Python GIL| B
    B -->|Result| D[Similar Performance]

    A -->|Complexity| E[Simple: 20 lines]
    C -->|Complexity| F[Complex: 50+ lines]

    E -->|Recommendation| G[Use Sequential for v1.0.0]
    F -->|Future| H[Binary for post-GIL Python]

    style G fill:#90EE90
    style H fill:#FFE4B5
```

**Decision for v1.0.0**: **Sequential aggregation**

**Rationale**:
1. **GIL limitation**: Python's GIL prevents true parallelization, so binary merge offers no performance benefit
2. **Simplicity**: Sequential is 20 lines vs 50+ for binary merge
3. **Maintainability**: Simpler code is easier to debug and maintain
4. **Performance**: Both are ~0.5-1ms for typical workloads (acceptable for cold path)
5. **Future path**: Binary merge can be added in v1.1.0+ for post-GIL Python (PEP 703)

**Future Consideration**: When Python removes GIL (PEP 703, Python 3.13+), binary merge with parallel execution could reduce aggregation time from O(T) to O(log(T)). Document this as optimization opportunity.

### Aggregation Example

**Scenario**: 3 threads profiling the same function

```
Thread 1: hit_count=100, total_time=1,000,000ns, min=5,000ns, max=20,000ns
Thread 2: hit_count=150, total_time=1,500,000ns, min=4,000ns, max=25,000ns
Thread 3: hit_count=200, total_time=2,000,000ns, min=6,000ns, max=18,000ns

Aggregated Result:
  hit_count: 450 (100 + 150 + 200)
  total_time: 4,500,000ns (sum)
  min: 4,000ns (min of all)
  max: 25,000ns (max of all)
  avg: 10,000ns (4,500,000 / 450)
```

---

## Synchronization Patterns

### Hot Path vs Cold Path

```mermaid
graph TB
    subgraph "Hot Path (High Frequency)"
        H1[Decorator wrapper execution]
        H2[Context manager entry/exit]
        H3[Time measurement]
        H4[Block time recording]
        H5[NO LOCKS<br/>Thread-local only]
    end

    subgraph "Cold Path (Low Frequency)"
        C1[Profiler instantiation]
        C2[Decorator application]
        C3[Thread registration]
        C4[Results aggregation]
        C5[Data clearing]
        C6[LOCK-PROTECTED<br/>RLock required]
    end

    H1 --> H2 --> H3 --> H4 --> H5
    C1 --> C2 --> C3 --> C4 --> C5 --> C6

    style H5 fill:#90EE90
    style C6 fill:#FFB6C1
```

### Lock Acquisition Summary

| Operation | Lock | Frequency | Performance Impact |
|-----------|------|-----------|-------------------|
| Measurement recording | **None** | High (hot path) | **Zero** |
| Decorator application | `_GLOBAL_CACHE_LOCK` | Low (once per call-site) | Negligible |
| Thread registration | `_global_lock` | Low (once per thread) | Negligible |
| Profiler instantiation | `_REGISTRY_LOCK` | Very low (once per profiler) | Negligible |
| Results aggregation | `_global_lock` | Very low (on-demand) | Acceptable (~1ms) |
| Data clearing | `_global_lock` | Very low (on-demand) | Negligible |

**Key Insight**: Hot path (99.9% of operations) has **zero lock overhead**.

---

## Prototype Comparison

### Key Differences

| Aspect | Prototype v0.5.0 | v1.0.0 Design |
|--------|------------------|---------------|
| **Data Storage** | Shared instance dicts | Thread-local storage |
| **ID Allocation** | Unprotected global counter | Lock-protected counter |
| **Call-Site Cache** | Unprotected global dict | Lock-protected global dict |
| **Block Recording** | Direct mutation (unsafe) | Thread-local mutation (safe) |
| **Results Retrieval** | Direct copy (unsafe) | Lock-protected aggregation |
| **Thread Safety** | ❌ None | ✅ Complete |
| **Performance** | 0.02-0.23% overhead | ~0.02-0.25% overhead (similar) |
| **Complexity** | Simple (363 lines) | Moderate (+~100 lines) |
| **API** | 15 public methods | 15 public methods (compatible) |

### Migration Impact

**Breaking Changes**: None - 100% API compatible

**Internal Changes**:
1. Add thread-local storage initialization
2. Add lock-protected global structures
3. Modify `_record_block_time` to use thread-local data
4. Implement aggregation algorithm in `get_results`
5. Add lock protection to `clear()`

**User Impact**: Zero - existing code works without modification

**Performance Impact**: Minimal (~0.02% increase, within ≤1% target)

---

## Implementation Guidance

### Phase 3 Implementation Checklist

**Step 1: Module-Level Changes**
- [ ] Add `_GLOBAL_CACHE_LOCK = threading.RLock()`
- [ ] Add `_REGISTRY_LOCK = threading.RLock()`
- [ ] Protect `_CALL_SITE_CACHE` access with `_GLOBAL_CACHE_LOCK`
- [ ] Protect `_PROFILER_REGISTRY` and `_NEXT_PROFILER_ID` with `_REGISTRY_LOCK`

**Step 2: Profiler.__init__ Changes**
- [ ] Add `self._thread_local = threading.local()`
- [ ] Add `self._global_lock = threading.RLock()`
- [ ] Add `self._all_thread_data: Dict[int, Any] = {}`
- [ ] Remove `self._tracks`, `self._track_enabled`, `self._next_block_idx`
- [ ] Protect profiler registration with `_REGISTRY_LOCK`

**Step 3: Thread-Local Storage**
- [ ] Implement `_get_thread_data()` method
- [ ] Implement thread registration in `_get_thread_data()`
- [ ] Update `_get_or_create_track()` to use thread-local data
- [ ] Update `_register_block()` to use thread-local data

**Step 4: API Method Updates**
- [ ] Update `set_track_enabled()`, `is_track_enabled()`, `set_track_name()` for thread-local
- [ ] Update `track()` decorator to use call-site cache with lock
- [ ] Update `block()` context manager to use call-site cache with lock
- [ ] Update `_record_block_time()` to use thread-local data

**Step 5: Aggregation**
- [ ] Implement `_aggregate_results()` method (sequential algorithm)
- [ ] Implement `_merge_block()` method
- [ ] Update `get_results()` to call `_aggregate_results()`

**Step 6: Clear Method**
- [ ] Update `clear()` to clear `_all_thread_data` with lock
- [ ] Update `clear()` to clear current thread's thread-local data

**Step 7: Testing**
- [ ] Run existing unit tests (should pass - API unchanged)
- [ ] Add thread-safety tests (Task 2.1.2 will define comprehensive suite)

### Critical Implementation Patterns

**Pattern 1: Thread-Local Initialization** (Critical for Correctness)

```python
# CORRECT: Check hasattr before accessing
if not hasattr(self._thread_local, 'tracks'):
    self._thread_local.tracks = {}
    # ... initialize other attributes ...

# INCORRECT: Direct access raises AttributeError
if self._thread_local.tracks is None:  # ❌ AttributeError on first access
    pass
```

**Pattern 2: Lock Ordering** (Prevents Deadlocks)

```python
# CORRECT: Acquire locks in consistent order
with _REGISTRY_LOCK:
    with _GLOBAL_CACHE_LOCK:
        with self._global_lock:
            pass

# INCORRECT: Inconsistent order (deadlock risk)
with self._global_lock:
    with _REGISTRY_LOCK:  # ❌ Deadlock possible
        pass
```

---

## Testing Strategy

### Overview

Comprehensive testing strategy will be defined in **Task 2.1.2 - Design Thread-Safe Test Suite**. This section provides high-level testing requirements.

### Test Categories

**1. Thread-Safety Unit Tests**
- Thread-local storage isolation (verify each thread has independent data)
- Aggregation correctness (verify merging produces correct results)
- Concurrent `get_results()` calls (verify lock protection)
- Lock ordering (verify no deadlocks)

**2. Multi-Threaded Integration Tests**
- Thread pool profiling (concurrent.futures.ThreadPoolExecutor)
- Nested profiling across threads
- Rapid thread creation/destruction

**3. Stress Tests**
- High thread count (100+ threads)
- High measurement frequency (1M+ measurements)
- Long-running profiling sessions

**4. Performance Tests**
- Hot path overhead measurement (target: ≤1% increase)
- Aggregation performance (target: <10ms for 100 threads)
- Memory usage (verify O(threads × blocks) scaling)

### Testing Tools

- **pytest**: Unit and integration tests
- **threading**: Multi-threaded test scenarios
- **concurrent.futures**: Thread pool testing
- **pytest-benchmark**: Performance regression testing

**Note**: Detailed test specifications, test cases, and test implementations will be provided in Task 2.1.2 report.

---

## Conclusion

### Design Summary

This architecture design provides a complete, implementation-ready specification for Stichotrope v1.0.0's thread-safe profiler.

**Key Design Elements**:
1. **Thread-local storage** for zero-contention hot path
2. **RLock-protected global structures** for safe shared state
3. **Synchronous profiling** for accurate measurements
4. **Sequential aggregation** for simplicity (binary merge deferred to post-GIL Python)
5. **Backward-compatible API** for smooth migration

**Performance Characteristics**:
- Hot path: ~130-250ns per measurement (no locks)
- Cold path: ~0.5-1ms aggregation (acceptable)
- Memory: O(threads × blocks) (acceptable for typical use)

**Complexity**:
- Moderate increase (~100 lines of code)
- Standard library primitives only
- Well-understood threading patterns

### Improvements from v0

1. **Visual clarity**: Mermaid diagrams for component architecture, data flow, lock hierarchy
2. **Reduced verbosity**: Pseudo-code focus with strategic code snippets
3. **Enhanced analysis**: Binary merge vs sequential aggregation comparison
4. **Streamlined testing**: High-level strategy only (details in Task 2.1.2)
5. **Better stakeholder review**: Clearer architectural intent, less implementation detail

### Success Criteria Met

- ✅ **Architecture document includes**: thread-local storage strategy, lock design, data structure choices
- ✅ **Design decisions documented with rationale**: Based on approved evaluation (Task 2.1.0)
- ✅ **Comparison to prototype (v0.5.0)**: Side-by-side comparison with migration guidance
- ✅ **Visual diagrams**: Mermaid diagrams for architecture, data flow, lock hierarchy
- ✅ **Aggregation analysis**: Sequential vs binary merge comparison
- ⏳ **Design review completed and approved**: Awaiting stakeholder review

### Next Steps

**Phase 1 (Current)**:
1. ✅ Task 2.1.0: Architecture Evaluation - APPROVED
2. ✅ Task 2.1.1: Architecture Design v1 - COMPLETE (awaiting review)
3. ⏳ Task 2.1.2: Design Thread-Safe Test Suite (next)

**Phase 2 (Future)**:
4. Task 2.1.3: Implement Thread-Safe Profiler Core
5. Task 2.1.4: Execute Thread-Safe Test Suite

**Implementation Readiness**: This design is sufficiently detailed for Phase 3 implementation. All architectural decisions are documented, all edge cases addressed, and all implementation patterns specified.

### Future Considerations (v1.1.0+)

**API Improvements**:
- Instance-level track enable/disable (affects all threads, not just current thread)
- Per-thread results retrieval (`get_results(thread_id=None)`)
- Thread-aware track naming

**Performance Optimizations**:
- Binary merge aggregation for post-GIL Python (PEP 703, Python 3.13+)
- Lock-free atomic operations when Python adds native support
- Parallel aggregation using multiprocessing for very large thread counts

**Monitoring**:
- Thread count tracking and warnings
- Memory usage monitoring
- Aggregation performance metrics

---

**Report Version**: v1 (refined based on stakeholder feedback)
**Date**: 2025-11-04
**Author**: Architecture Design (Phase 1)
**Status**: Awaiting stakeholder review
**Next Action**: Stakeholder feedback and iteration to v2 if needed

---

## Appendix: Mermaid Diagram Source

All Mermaid diagrams in this document can be extracted and used in MkDocs documentation. Diagrams are provided in standard Mermaid syntax for easy integration.

**Diagrams Included**:
1. Component Architecture (graph TB)
2. Hot Path Data Flow (sequenceDiagram)
3. Cold Path Data Flow (sequenceDiagram)
4. Lock Hierarchy (graph TD)
5. Sequential vs Binary Merge Analysis (graph LR)
6. Hot Path vs Cold Path (graph TB)

**Usage in MkDocs**:
```markdown
```mermaid
[Copy diagram code from report]
```
```

**Rendering**: Diagrams can be rendered in GitHub, MkDocs, and most modern Markdown viewers with Mermaid support.

