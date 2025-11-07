# Thread-Safe Architecture Design Document

**Task**: 2.1.1 – Design Thread-Safe Architecture Document  
**Issue**: [#18](https://github.com/LittleCoinCoin/stichotrope/issues/18)  
**Milestone**: 2.1 Thread-Safe Architecture Redesign  
**Version Target**: v0.2.0  
**Report Version**: v0 (initial)  
**Date**: 2025-11-04  
**Status**: Awaiting stakeholder review  
**Dependencies**: Task 2.1.0 (Architecture Evaluation) - ✅ APPROVED

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
13. [Testing Considerations](#testing-considerations)
14. [Conclusion](#conclusion)

---

## Executive Summary

This document provides the detailed architectural design for Stichotrope v1.0.0's thread-safe profiler, based on the approved evaluation (Task 2.1.0).

**Design Approach**: **Hybrid Thread-Local + Lock-Based Synchronous Profiling**

**Key Design Decisions**:
1. **Thread-local storage** for per-thread profiling data (zero contention in hot path)
2. **RLock-protected global structures** (call-site cache, profiler registry)
3. **Synchronous profiling** (measurements on calling thread, no background threads)
4. **Lazy aggregation** (merge thread data only when get_results() called)
5. **Backward-compatible API** (no breaking changes from prototype v0.5.0)

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
- **Principle**: No breaking API changes
- **Implementation**: Same public interface as prototype v0.5.0
- **Benefit**: Smooth migration path

### 5. Lazy Aggregation
- **Principle**: Defer expensive operations to cold path
- **Implementation**: Aggregate thread data only in get_results()
- **Benefit**: Hot path remains fast

---

## Architecture Overview

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Application Code                         │
│  (Multiple threads calling profiler.track() and profiler.block()) │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Profiler Instance                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Public API (thread-safe)                                 │  │
│  │  - track(track_idx, name) → decorator                     │  │
│  │  - block(track_idx, name) → context manager               │  │
│  │  - get_results() → ProfilerResults                        │  │
│  │  - start(), stop(), clear()                               │  │
│  │  - set_track_enabled(), set_track_name()                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Thread-Local Storage (per thread)                        │  │
│  │  - _thread_local.tracks: Dict[int, ProfileTrack]          │  │
│  │  - _thread_local.next_block_idx: Dict[int, int]           │  │
│  │  - _thread_local.track_enabled: Dict[int, bool]           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Global State (RLock-protected)                           │  │
│  │  - _global_lock: RLock                                    │  │
│  │  - _all_thread_data: Dict[int, ThreadLocal]               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Module-Level Global State                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  _PROFILER_ENABLED: bool (global enable/disable)          │  │
│  │  _CALL_SITE_CACHE: Dict (RLock-protected)                 │  │
│  │  _PROFILER_REGISTRY: Dict (RLock-protected)               │  │
│  │  _NEXT_PROFILER_ID: int (RLock-protected)                 │  │
│  │  _GLOBAL_CACHE_LOCK: RLock                                │  │
│  │  _REGISTRY_LOCK: RLock                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

**Hot Path (Measurement Recording)**:
```
Application Thread
  → profiler.track() decorator or profiler.block() context manager
  → _get_thread_data() [thread-local access, NO LOCK]
  → get_time_ns() [start]
  → Execute user code
  → get_time_ns() [end]
  → _record_block_time() [thread-local mutation, NO LOCK]
  → ProfileBlock.record_time() [thread-local, NO LOCK]
```

**Cold Path (Results Retrieval)**:
```
Application Thread
  → profiler.get_results()
  → Acquire _global_lock [LOCK]
  → Iterate over _all_thread_data
  → Merge blocks from all threads
  → Release _global_lock [UNLOCK]
  → Return ProfilerResults
```

---

## Core Components Design

### 1. Profiler Class

**File**: `stichotrope/profiler.py`

**Class Structure**:

```python
import threading
from typing import Dict, Any, Optional, Callable
from collections.abc import Generator
from contextlib import contextmanager

class Profiler:
    """
    Thread-safe profiler using thread-local storage + synchronous profiling.

    Thread Safety:
    - Hot path (measurement): Thread-local storage, no locks
    - Cold path (aggregation): RLock-protected global state
    - API methods: Thread-safe (appropriate locking)
    """

    # ========== Instance Attributes ==========

    # Profiler identity
    _profiler_id: int              # Unique profiler ID
    _name: str                     # Human-readable name

    # Thread-local storage (per-thread profiling data)
    _thread_local: threading.local  # Container for thread-local data

    # Global state (protected by _global_lock)
    _global_lock: threading.RLock   # Protects _all_thread_data
    _all_thread_data: Dict[int, Any]  # thread_id -> thread-local data

    # Profiler state
    _started: bool                  # Instance-level enable/disable

    # ========== Public API Methods ==========

    def __init__(self, name: str = "Profiler") -> None:
        """Initialize thread-safe profiler instance."""

    def start(self) -> None:
        """Start profiling (resume data collection)."""

    def stop(self) -> None:
        """Stop profiling (pause data collection)."""

    def is_started(self) -> bool:
        """Check if profiler is started."""

    def set_track_enabled(self, track_idx: int, enabled: bool) -> None:
        """Enable or disable a specific track (thread-safe)."""

    def is_track_enabled(self, track_idx: int) -> bool:
        """Check if a specific track is enabled (thread-safe)."""

    def set_track_name(self, track_idx: int, name: str) -> None:
        """Set a human-readable name for a track (thread-safe)."""

    def track(self, track_idx: int, name: Optional[str] = None) -> Callable:
        """Decorator for profiling functions (thread-safe)."""

    @contextmanager
    def block(self, track_idx: int, name: str) -> Generator[None, None, None]:
        """Context manager for profiling code blocks (thread-safe)."""

    def get_results(self) -> ProfilerResults:
        """Get aggregated profiling results from all threads (thread-safe)."""

    def clear(self) -> None:
        """Clear all profiling data from all threads (thread-safe)."""

    def export_csv(self, filename: str) -> None:
        """Export profiling results to CSV file."""

    def export_json(self, filename: str, indent: int = 2) -> None:
        """Export profiling results to JSON file."""

    def print_results(self) -> None:
        """Print profiling results to console."""

    # ========== Internal Methods ==========

    def _get_thread_data(self) -> Any:
        """Get or create thread-local profiling data (NO LOCK)."""

    def _get_or_create_track(self, thread_data: Any, track_idx: int) -> ProfileTrack:
        """Get or create a track in thread-local storage (NO LOCK)."""

    def _register_block(self, thread_data: Any, track_idx: int,
                       name: str, file: str, line: int) -> int:
        """Register a new profiling block in thread-local storage (NO LOCK)."""

    def _record_block_time(self, track_idx: int, block_idx: int,
                          elapsed_ns: int) -> None:
        """Record execution time for a block (NO LOCK - thread-local)."""

    def _aggregate_results(self) -> ProfilerResults:
        """Aggregate results from all threads (LOCK-PROTECTED)."""

    def _merge_block(self, aggregated_track: ProfileTrack,
                    block_idx: int, source_block: ProfileBlock) -> None:
        """Merge a block from one thread into aggregated results."""
```

### 2. Thread-Local Data Container

**Structure**:

```python
# Thread-local data structure (stored in threading.local())
class ThreadLocalData:
    """
    Container for per-thread profiling data.

    This is NOT a real class - it's the structure of attributes
    stored in threading.local() object.
    """

    # Per-thread profiling data
    tracks: Dict[int, ProfileTrack]      # track_idx -> ProfileTrack
    next_block_idx: Dict[int, int]       # track_idx -> next block index
    track_enabled: Dict[int, bool]       # track_idx -> enabled flag

    # Thread identity (for debugging)
    thread_id: int                       # threading.get_ident()
    thread_name: str                     # threading.current_thread().name
```

**Usage Pattern**:

```python
# In Profiler.__init__()
self._thread_local = threading.local()

# In Profiler._get_thread_data()
if not hasattr(self._thread_local, 'tracks'):
    # Initialize thread-local storage for this thread
    self._thread_local.tracks = {}
    self._thread_local.next_block_idx = {}
    self._thread_local.track_enabled = {}
    self._thread_local.thread_id = threading.get_ident()
    self._thread_local.thread_name = threading.current_thread().name

    # Register this thread's data in global registry
    with self._global_lock:
        self._all_thread_data[self._thread_local.thread_id] = self._thread_local

return self._thread_local
```

### 3. Module-Level Global State

**File**: `stichotrope/profiler.py` (module level)

**Structure**:

```python
# ========== Global Enable/Disable ==========
_PROFILER_ENABLED: bool = True  # Global enable/disable flag (no lock needed - read-only after init)

# ========== Call-Site Cache ==========
_CALL_SITE_CACHE: Dict[tuple[int, str, int, str], tuple[int, int]] = {}
# Key: (track_idx, file, line, name)
# Value: (profiler_id, block_idx)

_GLOBAL_CACHE_LOCK: threading.RLock = threading.RLock()  # Protects _CALL_SITE_CACHE

# ========== Profiler Registry ==========
_PROFILER_REGISTRY: Dict[int, Profiler] = {}  # profiler_id -> Profiler instance
_NEXT_PROFILER_ID: int = 0                    # Next profiler ID to assign

_REGISTRY_LOCK: threading.RLock = threading.RLock()  # Protects registry and ID counter

# ========== Module-Level Functions ==========

def set_global_enabled(enabled: bool) -> None:
    """Enable or disable profiling globally (thread-safe)."""
    global _PROFILER_ENABLED
    _PROFILER_ENABLED = enabled

def is_global_enabled() -> bool:
    """Check if profiling is globally enabled (thread-safe)."""
    return _PROFILER_ENABLED

def _get_profiler(profiler_id: int) -> Optional[Profiler]:
    """Get a profiler instance by ID (thread-safe)."""
    with _REGISTRY_LOCK:
        return _PROFILER_REGISTRY.get(profiler_id)
```

---

## Data Structures

### 1. ProfileBlock (Unchanged from Prototype)

**File**: `stichotrope/types.py`

**Rationale**: ProfileBlock does NOT need modification because:
- With thread-local storage, each thread has its own ProfileBlock instances
- No concurrent access to the same ProfileBlock instance
- record_time() is safe because it's called only from owning thread

**Structure**:

```python
from dataclasses import dataclass

@dataclass
class ProfileBlock:
    """
    Represents a single profiled code block with accumulated timing statistics.

    Thread Safety: Safe when used with thread-local storage.
    Each thread has its own ProfileBlock instances.
    """

    name: str                    # Human-readable name
    file: str                    # Source file
    line: int                    # Line number
    hit_count: int = 0           # Number of executions
    total_time_ns: int = 0       # Total accumulated time (nanoseconds)
    min_time_ns: int = 2**63 - 1 # Minimum execution time
    max_time_ns: int = 0         # Maximum execution time

    def record_time(self, elapsed_ns: int) -> None:
        """
        Record a single execution time.

        Thread Safety: Safe - called only from owning thread.
        """
        self.hit_count += 1
        self.total_time_ns += elapsed_ns
        self.min_time_ns = min(self.min_time_ns, elapsed_ns)
        self.max_time_ns = max(self.max_time_ns, elapsed_ns)

    @property
    def avg_time_ns(self) -> float:
        """Average execution time in nanoseconds."""
        return self.total_time_ns / self.hit_count if self.hit_count > 0 else 0.0
```

### 2. ProfileTrack (Unchanged from Prototype)

**File**: `stichotrope/types.py`

**Rationale**: ProfileTrack does NOT need modification because:
- With thread-local storage, each thread has its own ProfileTrack instances
- No concurrent access to the same ProfileTrack instance

**Structure**:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ProfileTrack:
    """
    Represents a logical track containing multiple profiled blocks.

    Thread Safety: Safe when used with thread-local storage.
    Each thread has its own ProfileTrack instances.
    """

    track_idx: int                              # Numeric index
    track_name: Optional[str] = None            # Human-readable name
    enabled: bool = True                        # Enabled flag
    blocks: Dict[int, ProfileBlock] = field(default_factory=dict)  # block_idx -> ProfileBlock

    def add_block(self, block_idx: int, name: str, file: str, line: int) -> ProfileBlock:
        """Add a new block to this track."""
        block = ProfileBlock(name=name, file=file, line=line)
        self.blocks[block_idx] = block
        return block

    def get_block(self, block_idx: int) -> Optional[ProfileBlock]:
        """Get a block by index."""
        return self.blocks.get(block_idx)

    @property
    def total_time_ns(self) -> int:
        """Total time across all blocks."""
        return sum(block.total_time_ns for block in self.blocks.values())

    @property
    def total_hits(self) -> int:
        """Total hit count across all blocks."""
        return sum(block.hit_count for block in self.blocks.values())
```

### 3. ProfilerResults (Unchanged from Prototype)

**File**: `stichotrope/types.py`

**Rationale**: ProfilerResults is the output of aggregation, created fresh each time.

**Structure**:

```python
@dataclass
class ProfilerResults:
    """
    Complete profiling results for a profiler instance.

    Thread Safety: Immutable after creation (returned by get_results()).
    """

    profiler_name: str                          # Profiler name
    tracks: Dict[int, ProfileTrack] = field(default_factory=dict)  # track_idx -> ProfileTrack

    @property
    def total_time_ns(self) -> int:
        """Total time across all tracks."""
        return sum(track.total_time_ns for track in self.tracks.values())

    @property
    def total_hits(self) -> int:
        """Total hit count across all tracks."""
        return sum(track.total_hits for track in self.tracks.values())

    def get_track(self, track_idx: int) -> Optional[ProfileTrack]:
        """Get a track by index."""
        return self.tracks.get(track_idx)
```

---

## Thread-Local Storage Strategy

### Overview

Thread-local storage is the cornerstone of the thread-safe design. Each thread maintains its own isolated profiling data, eliminating contention in the hot path.

### Implementation Details

**1. Thread-Local Initialization**

```python
def _get_thread_data(self) -> Any:
    """
    Get or create thread-local profiling data.

    Thread Safety: Safe - threading.local() handles thread isolation.
    Performance: ~10-20ns (hasattr check + dict access).
    """
    if not hasattr(self._thread_local, 'tracks'):
        # First access from this thread - initialize
        thread_id = threading.get_ident()
        thread_name = threading.current_thread().name

        # Initialize thread-local storage
        self._thread_local.tracks = {}
        self._thread_local.next_block_idx = {}
        self._thread_local.track_enabled = {}
        self._thread_local.thread_id = thread_id
        self._thread_local.thread_name = thread_name

        # Register this thread's data in global registry (LOCK REQUIRED)
        with self._global_lock:
            self._all_thread_data[thread_id] = self._thread_local

    return self._thread_local
```

**2. Thread-Local Track Management**

```python
def _get_or_create_track(self, thread_data: Any, track_idx: int) -> ProfileTrack:
    """
    Get or create a track in thread-local storage.

    Thread Safety: Safe - operates on thread-local data only.
    Performance: ~10-20ns (dict access).
    """
    if track_idx not in thread_data.tracks:
        # Create new track for this thread
        thread_data.tracks[track_idx] = ProfileTrack(track_idx=track_idx)
        thread_data.next_block_idx[track_idx] = 0

    return thread_data.tracks[track_idx]
```

**3. Thread-Local Block Registration**

```python
def _register_block(self, thread_data: Any, track_idx: int,
                   name: str, file: str, line: int) -> int:
    """
    Register a new profiling block in thread-local storage.

    Thread Safety: Safe - operates on thread-local data only.
    Performance: ~20-30ns (track creation + block creation).
    """
    track = self._get_or_create_track(thread_data, track_idx)

    # Allocate block index (thread-local, no race condition)
    block_idx = thread_data.next_block_idx[track_idx]
    thread_data.next_block_idx[track_idx] += 1

    # Create block in thread-local track
    track.add_block(block_idx, name, file, line)

    return block_idx
```

**4. Thread-Local Measurement Recording**

```python
def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int) -> None:
    """
    Record execution time for a block.

    Thread Safety: Safe - operates on thread-local data only.
    Performance: ~20-30ns (dict lookups + field updates).
    """
    thread_data = self._get_thread_data()  # Thread-local access

    # Get track from thread-local storage
    track = thread_data.tracks.get(track_idx)
    if track is None:
        return  # Track not found (shouldn't happen)

    # Get block from thread-local track
    block = track.get_block(block_idx)
    if block is None:
        return  # Block not found (shouldn't happen)

    # Record time (thread-local mutation, no lock needed)
    block.record_time(elapsed_ns)
```

### Thread Lifecycle

**Thread Creation**:
- First call to `_get_thread_data()` from a new thread initializes thread-local storage
- Thread data registered in `_all_thread_data` (lock-protected)

**Thread Execution**:
- All profiling operations use thread-local data (no locks)
- No interaction with other threads' data

**Thread Termination**:
- Python's `threading.local()` automatically cleans up thread-local data
- Thread data remains in `_all_thread_data` until profiler.clear() called
- **Trade-off**: Dead thread data persists until explicit clear (acceptable for profiling sessions)

### Memory Characteristics

**Per-Thread Memory**:
- O(tracks × blocks) per thread
- Typical: 10 tracks × 100 blocks × 100 bytes = ~100 KB per thread
- Acceptable for typical thread counts (10-100 threads)

**Total Memory**:
- O(threads × tracks × blocks)
- Example: 50 threads × 10 tracks × 100 blocks = 50,000 block instances
- Mitigated by: Profiling sessions are typically short-lived

---

## Lock Design

### Lock Hierarchy

To prevent deadlocks, locks must be acquired in a consistent order:

```
1. _REGISTRY_LOCK (module-level, profiler registration)
2. _GLOBAL_CACHE_LOCK (module-level, call-site cache)
3. Profiler._global_lock (instance-level, thread data registry)
```

**Rule**: Never acquire a higher-numbered lock while holding a lower-numbered lock.

### Lock Usage Patterns

**1. Module-Level Locks**

```python
# _REGISTRY_LOCK: Protects profiler registry and ID counter
_REGISTRY_LOCK = threading.RLock()

# Usage: Profiler instantiation (cold path)
def __init__(self, name: str = "Profiler"):
    with _REGISTRY_LOCK:
        self._profiler_id = _NEXT_PROFILER_ID
        _NEXT_PROFILER_ID += 1
        _PROFILER_REGISTRY[self._profiler_id] = self

# _GLOBAL_CACHE_LOCK: Protects call-site cache
_GLOBAL_CACHE_LOCK = threading.RLock()

# Usage: Decorator application (cold path)
def _get_or_register_block_cached(self, track_idx, file, line, name):
    cache_key = (track_idx, file, line, name)

    with _GLOBAL_CACHE_LOCK:
        if cache_key in _CALL_SITE_CACHE:
            profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
            return block_idx

        # Register block in thread-local storage (no lock needed)
        thread_data = self._get_thread_data()
        block_idx = self._register_block(thread_data, track_idx, name, file, line)

        # Cache result
        _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)
        return block_idx
```

**2. Instance-Level Lock**

```python
# Profiler._global_lock: Protects _all_thread_data
self._global_lock = threading.RLock()

# Usage 1: Thread registration (first access from new thread)
def _get_thread_data(self):
    if not hasattr(self._thread_local, 'tracks'):
        # Initialize thread-local storage
        thread_id = threading.get_ident()
        self._thread_local.tracks = {}
        # ... other initialization ...

        # Register thread data (LOCK REQUIRED)
        with self._global_lock:
            self._all_thread_data[thread_id] = self._thread_local

    return self._thread_local

# Usage 2: Results aggregation (cold path)
def get_results(self):
    with self._global_lock:
        # Aggregate data from all threads
        aggregated_tracks = {}
        for thread_id, thread_data in self._all_thread_data.items():
            # Merge thread data into aggregated_tracks
            pass
        return ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)

# Usage 3: Clear all data (cold path)
def clear(self):
    with self._global_lock:
        self._all_thread_data.clear()

    # Clear thread-local data for current thread
    if hasattr(self._thread_local, 'tracks'):
        self._thread_local.tracks.clear()
        self._thread_local.next_block_idx.clear()
        self._thread_local.track_enabled.clear()
```

### Lock-Free Operations (Hot Path)

**Critical**: The hot path (measurement recording) must NOT acquire locks.

```python
# Hot path: decorator wrapper
@functools.wraps(func)
def wrapper(*args, **kwargs):
    # Check enable flags (no lock - read-only or thread-local)
    if not _PROFILER_ENABLED:  # Global flag (read-only)
        return func(*args, **kwargs)

    thread_data = self._get_thread_data()  # Thread-local (no lock)

    if not thread_data.track_enabled.get(track_idx, True):  # Thread-local (no lock)
        return func(*args, **kwargs)

    if not self._started:  # Instance flag (read-only after init)
        return func(*args, **kwargs)

    # Measure execution time
    start = get_time_ns()
    try:
        result = func(*args, **kwargs)
        return result
    finally:
        end = get_time_ns()
        elapsed = end - start

        # Record time (thread-local, NO LOCK)
        self._record_block_time(track_idx, block_idx, elapsed)
```

### RLock vs Lock

**Choice**: Use `threading.RLock()` (reentrant lock) everywhere.

**Rationale**:
- Allows same thread to acquire lock multiple times (nested calls)
- Prevents deadlock in recursive profiling scenarios
- Minimal performance difference vs Lock (~10-20ns overhead)
- Safer default choice

**Example Scenario**:
```python
@profiler.track(0, "outer")
def outer():
    inner()  # Nested profiled call

@profiler.track(0, "inner")
def inner():
    pass

# If get_results() called from outer():
# - outer() holds lock (if we used locks in hot path)
# - inner() tries to acquire same lock
# - With Lock: deadlock
# - With RLock: succeeds (reentrant)
```

---

## API Design

### Public API (Backward Compatible)

All public API methods from prototype v0.5.0 are preserved with identical signatures.

**1. Profiler Instantiation**

```python
def __init__(self, name: str = "Profiler") -> None:
    """
    Initialize a new profiler instance.

    Thread Safety: Safe - uses _REGISTRY_LOCK.

    Args:
        name: Human-readable name for this profiler
    """
    # Allocate profiler ID (LOCK REQUIRED)
    with _REGISTRY_LOCK:
        self._profiler_id = _NEXT_PROFILER_ID
        _NEXT_PROFILER_ID += 1
        _PROFILER_REGISTRY[self._profiler_id] = self

    # Initialize instance state
    self._name = name
    self._started = True

    # Initialize thread-local storage
    self._thread_local = threading.local()

    # Initialize global state
    self._global_lock = threading.RLock()
    self._all_thread_data = {}
```

**2. Start/Stop Control**

```python
def start(self) -> None:
    """
    Start profiling (resume data collection).

    Thread Safety: Safe - simple flag write.
    """
    self._started = True

def stop(self) -> None:
    """
    Stop profiling (pause data collection).

    Thread Safety: Safe - simple flag write.
    """
    self._started = False

def is_started(self) -> bool:
    """
    Check if profiler is started.

    Thread Safety: Safe - simple flag read.
    """
    return self._started
```

**3. Track Management**

```python
def set_track_enabled(self, track_idx: int, enabled: bool) -> None:
    """
    Enable or disable a specific track.

    Thread Safety: Safe - modifies thread-local data only.

    Args:
        track_idx: Track index
        enabled: True to enable, False to disable
    """
    thread_data = self._get_thread_data()
    thread_data.track_enabled[track_idx] = enabled

def is_track_enabled(self, track_idx: int) -> bool:
    """
    Check if a specific track is enabled.

    Thread Safety: Safe - reads thread-local data only.

    Args:
        track_idx: Track index

    Returns:
        True if track is enabled (default: True)
    """
    thread_data = self._get_thread_data()
    return thread_data.track_enabled.get(track_idx, True)

def set_track_name(self, track_idx: int, name: str) -> None:
    """
    Set a human-readable name for a track.

    Thread Safety: Safe - modifies thread-local data only.

    Args:
        track_idx: Track index
        name: Track name
    """
    thread_data = self._get_thread_data()
    track = self._get_or_create_track(thread_data, track_idx)
    track.track_name = name
```

**4. Profiling Decorators and Context Managers**

```python
def track(self, track_idx: int, name: Optional[str] = None) -> Callable:
    """
    Decorator for profiling functions.

    Thread Safety: Safe - uses call-site cache with lock.

    Example:
        @profiler.track(0, "process_data")
        def process_data(data):
            return transform(data)

    Args:
        track_idx: Track index for this function
        name: Optional name (defaults to function.__name__)

    Returns:
        Decorator function
    """
    # Level 1: Global enable/disable (zero overhead when disabled)
    if not _PROFILER_ENABLED:
        return lambda func: func  # Identity decorator

    def decorator(func: Callable) -> Callable:
        # Use function name if not provided
        block_name = name if name is not None else func.__name__

        # Get call-site information
        frame = inspect.currentframe()
        if frame and frame.f_back:
            file = frame.f_back.f_code.co_filename
            line = frame.f_back.f_lineno
        else:
            file = "<unknown>"
            line = 0

        # Check call-site cache and register block (LOCK REQUIRED)
        cache_key = (track_idx, file, line, block_name)

        with _GLOBAL_CACHE_LOCK:
            if cache_key in _CALL_SITE_CACHE:
                profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
            else:
                # Register block in thread-local storage (no lock needed)
                thread_data = self._get_thread_data()
                block_idx = self._register_block(thread_data, track_idx, block_name, file, line)

                # Cache result
                _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Fast path checks (no locks)
            thread_data = self._get_thread_data()

            if not thread_data.track_enabled.get(track_idx, True):
                return func(*args, **kwargs)

            if not self._started:
                return func(*args, **kwargs)

            # Profile the function (NO LOCK)
            start = get_time_ns()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end = get_time_ns()
                elapsed = end - start
                self._record_block_time(track_idx, block_idx, elapsed)

        return wrapper

    return decorator

@contextmanager
def block(self, track_idx: int, name: str) -> Generator[None, None, None]:
    """
    Context manager for profiling code blocks.

    Thread Safety: Safe - uses call-site cache with lock.

    Example:
        with profiler.block(1, "database_query"):
            result = query_database()

    Args:
        track_idx: Track index for this block
        name: Block name (required)

    Yields:
        None
    """
    # Level 1: Global enable/disable
    if not _PROFILER_ENABLED:
        yield
        return

    # Fast path checks (no locks)
    thread_data = self._get_thread_data()

    if not thread_data.track_enabled.get(track_idx, True):
        yield
        return

    if not self._started:
        yield
        return

    # Get call-site information
    frame = inspect.currentframe()
    if frame and frame.f_back:
        file = frame.f_back.f_code.co_filename
        line = frame.f_back.f_lineno
    else:
        file = "<unknown>"
        line = 0

    # Check call-site cache and register block (LOCK REQUIRED)
    cache_key = (track_idx, file, line, name)

    with _GLOBAL_CACHE_LOCK:
        if cache_key in _CALL_SITE_CACHE:
            profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
        else:
            block_idx = self._register_block(thread_data, track_idx, name, file, line)
            _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

    # Profile the block (NO LOCK)
    start = get_time_ns()
    try:
        yield
    finally:
        end = get_time_ns()
        elapsed = end - start
        self._record_block_time(track_idx, block_idx, elapsed)
```

**5. Results and Export**

```python
def get_results(self) -> ProfilerResults:
    """
    Get aggregated profiling results from all threads.

    Thread Safety: Safe - uses _global_lock.

    Returns:
        ProfilerResults containing aggregated data from all threads
    """
    return self._aggregate_results()

def clear(self) -> None:
    """
    Clear all profiling data from all threads.

    Thread Safety: Safe - uses _global_lock.
    """
    with self._global_lock:
        self._all_thread_data.clear()

    # Clear current thread's data
    if hasattr(self._thread_local, 'tracks'):
        self._thread_local.tracks.clear()
        self._thread_local.next_block_idx.clear()
        self._thread_local.track_enabled.clear()

def export_csv(self, filename: str) -> None:
    """Export profiling results to CSV file."""
    from stichotrope.export import export_csv
    results = self.get_results()
    with open(filename, "w", newline="") as f:
        export_csv(results, f)

def export_json(self, filename: str, indent: int = 2) -> None:
    """Export profiling results to JSON file."""
    from stichotrope.export import export_json
    results = self.get_results()
    with open(filename, "w") as f:
        export_json(results, f, indent=indent)

def print_results(self) -> None:
    """Print profiling results to console."""
    from stichotrope.export import print_results
    results = self.get_results()
    print_results(results)
```

---

## Aggregation Algorithm

### Overview

The aggregation algorithm merges profiling data from all threads into a single `ProfilerResults` object. This is a cold-path operation (called infrequently).

### Algorithm Design

```python
def _aggregate_results(self) -> ProfilerResults:
    """
    Aggregate results from all threads.

    Thread Safety: Safe - uses _global_lock.
    Complexity: O(threads × tracks × blocks)
    Performance: Acceptable for cold path (infrequent operation)

    Returns:
        ProfilerResults with aggregated data
    """
    with self._global_lock:
        # Create aggregated tracks dictionary
        aggregated_tracks: Dict[int, ProfileTrack] = {}

        # Iterate over all threads
        for thread_id, thread_data in self._all_thread_data.items():
            # Iterate over tracks in this thread
            for track_idx, track in thread_data.tracks.items():
                # Create aggregated track if it doesn't exist
                if track_idx not in aggregated_tracks:
                    aggregated_tracks[track_idx] = ProfileTrack(
                        track_idx=track_idx,
                        track_name=track.track_name,
                        enabled=track.enabled
                    )

                # Merge blocks from this thread's track
                for block_idx, block in track.blocks.items():
                    self._merge_block(aggregated_tracks[track_idx], block_idx, block)

        # Create and return results
        return ProfilerResults(
            profiler_name=self._name,
            tracks=aggregated_tracks
        )
```

### Block Merging Logic

```python
def _merge_block(self, aggregated_track: ProfileTrack,
                block_idx: int, source_block: ProfileBlock) -> None:
    """
    Merge a block from one thread into aggregated results.

    Thread Safety: Safe - called within _global_lock.

    Args:
        aggregated_track: Target track for aggregation
        block_idx: Block index
        source_block: Source block from a thread
    """
    if block_idx not in aggregated_track.blocks:
        # First time seeing this block - create new aggregated block
        aggregated_track.blocks[block_idx] = ProfileBlock(
            name=source_block.name,
            file=source_block.file,
            line=source_block.line,
            hit_count=0,
            total_time_ns=0,
            min_time_ns=2**63 - 1,
            max_time_ns=0
        )

    # Get aggregated block
    agg_block = aggregated_track.blocks[block_idx]

    # Merge statistics
    agg_block.hit_count += source_block.hit_count
    agg_block.total_time_ns += source_block.total_time_ns
    agg_block.min_time_ns = min(agg_block.min_time_ns, source_block.min_time_ns)
    agg_block.max_time_ns = max(agg_block.max_time_ns, source_block.max_time_ns)
```

### Aggregation Example

**Scenario**: 3 threads profiling the same function

**Thread 1 Data**:
```
Track 0, Block 0 ("process_data"):
  hit_count: 100
  total_time_ns: 1,000,000
  min_time_ns: 5,000
  max_time_ns: 20,000
```

**Thread 2 Data**:
```
Track 0, Block 0 ("process_data"):
  hit_count: 150
  total_time_ns: 1,500,000
  min_time_ns: 4,000
  max_time_ns: 25,000
```

**Thread 3 Data**:
```
Track 0, Block 0 ("process_data"):
  hit_count: 200
  total_time_ns: 2,000,000
  min_time_ns: 6,000
  max_time_ns: 18,000
```

**Aggregated Result**:
```
Track 0, Block 0 ("process_data"):
  hit_count: 450 (100 + 150 + 200)
  total_time_ns: 4,500,000 (1,000,000 + 1,500,000 + 2,000,000)
  min_time_ns: 4,000 (min of 5,000, 4,000, 6,000)
  max_time_ns: 25,000 (max of 20,000, 25,000, 18,000)
  avg_time_ns: 10,000 (4,500,000 / 450)
```

### Performance Characteristics

**Time Complexity**: O(T × K × B)
- T = number of threads
- K = number of tracks per thread
- B = number of blocks per track

**Typical Case**:
- 50 threads × 10 tracks × 100 blocks = 50,000 iterations
- ~10-20ns per iteration (dict operations)
- Total: ~0.5-1ms (acceptable for cold path)

**Memory**: O(K × B) for aggregated results (independent of thread count)

---

## Synchronization Patterns

### Hot Path (No Locks)

**Definition**: Code executed during every measurement (high frequency).

**Operations**:
1. Decorator wrapper execution
2. Context manager entry/exit
3. Time measurement (get_time_ns)
4. Block time recording (_record_block_time)

**Synchronization**: NONE - all operations use thread-local data.

**Example**:
```python
# Hot path: profiler.track() wrapper
@functools.wraps(func)
def wrapper(*args, **kwargs):
    # All checks use thread-local or read-only data (NO LOCK)
    thread_data = self._get_thread_data()  # Thread-local

    if not thread_data.track_enabled.get(track_idx, True):  # Thread-local
        return func(*args, **kwargs)

    if not self._started:  # Read-only (simple flag)
        return func(*args, **kwargs)

    # Measurement (NO LOCK)
    start = get_time_ns()
    result = func(*args, **kwargs)
    end = get_time_ns()

    # Recording (NO LOCK - thread-local mutation)
    self._record_block_time(track_idx, block_idx, end - start)

    return result
```

**Performance**: ~130-250ns per measurement (no lock overhead).

### Cold Path (Lock-Protected)

**Definition**: Code executed infrequently (low frequency).

**Operations**:
1. Profiler instantiation (__init__)
2. Decorator application (first time)
3. Thread registration (first access from new thread)
4. Results aggregation (get_results)
5. Data clearing (clear)

**Synchronization**: RLock-protected.

**Example 1: Profiler Instantiation**
```python
def __init__(self, name: str = "Profiler"):
    # LOCK REQUIRED: Profiler registry and ID allocation
    with _REGISTRY_LOCK:
        self._profiler_id = _NEXT_PROFILER_ID
        _NEXT_PROFILER_ID += 1
        _PROFILER_REGISTRY[self._profiler_id] = self

    # No lock needed: Instance initialization
    self._name = name
    self._started = True
    self._thread_local = threading.local()
    self._global_lock = threading.RLock()
    self._all_thread_data = {}
```

**Example 2: Call-Site Cache**
```python
def track(self, track_idx: int, name: Optional[str] = None):
    def decorator(func: Callable):
        # Get call-site info
        cache_key = (track_idx, file, line, block_name)

        # LOCK REQUIRED: Call-site cache access
        with _GLOBAL_CACHE_LOCK:
            if cache_key in _CALL_SITE_CACHE:
                profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
            else:
                # Register block (thread-local, no lock)
                thread_data = self._get_thread_data()
                block_idx = self._register_block(thread_data, track_idx, block_name, file, line)

                # Cache result
                _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

        # Return wrapper (hot path has no locks)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # ... hot path code (no locks) ...
```

**Example 3: Results Aggregation**
```python
def get_results(self):
    # LOCK REQUIRED: Access to _all_thread_data
    with self._global_lock:
        aggregated_tracks = {}

        for thread_id, thread_data in self._all_thread_data.items():
            for track_idx, track in thread_data.tracks.items():
                # Merge data
                pass

        return ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)
```

### Lock Acquisition Summary

| Operation | Lock | Frequency | Performance Impact |
|-----------|------|-----------|-------------------|
| Measurement recording | None | High (hot path) | Zero |
| Decorator application | _GLOBAL_CACHE_LOCK | Low (once per call-site) | Negligible |
| Thread registration | _global_lock | Low (once per thread) | Negligible |
| Profiler instantiation | _REGISTRY_LOCK | Very low (once per profiler) | Negligible |
| Results aggregation | _global_lock | Very low (on-demand) | Acceptable |
| Data clearing | _global_lock | Very low (on-demand) | Acceptable |

---

## Prototype Comparison

### Side-by-Side Comparison

**Prototype v0.5.0** (Thread-Unsafe):

```python
class Profiler:
    def __init__(self, name: str = "Profiler"):
        global _NEXT_PROFILER_ID
        self._profiler_id = _NEXT_PROFILER_ID  # ❌ Race condition
        _NEXT_PROFILER_ID += 1                 # ❌ Non-atomic
        _PROFILER_REGISTRY[self._profiler_id] = self  # ❌ Unsafe dict access

        self._name = name
        self._tracks: dict[int, ProfileTrack] = {}  # ❌ Shared state
        self._track_enabled: dict[int, bool] = {}   # ❌ Shared state
        self._next_block_idx: dict[int, int] = {}   # ❌ Shared state
        self._started = True

    def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int):
        track = self._tracks.get(track_idx)  # ❌ Unsafe dict access
        if track:
            block = track.get_block(block_idx)
            if block:
                block.record_time(elapsed_ns)  # ❌ Unprotected mutation

    def get_results(self):
        results = ProfilerResults(profiler_name=self._name)
        results.tracks = self._tracks.copy()  # ❌ Unsafe copy (concurrent modifications)
        return results
```

**v1.0.0 Design** (Thread-Safe):

```python
class Profiler:
    def __init__(self, name: str = "Profiler"):
        # ✅ Lock-protected ID allocation
        with _REGISTRY_LOCK:
            self._profiler_id = _NEXT_PROFILER_ID
            _NEXT_PROFILER_ID += 1
            _PROFILER_REGISTRY[self._profiler_id] = self

        self._name = name
        self._started = True

        # ✅ Thread-local storage
        self._thread_local = threading.local()

        # ✅ Lock-protected global state
        self._global_lock = threading.RLock()
        self._all_thread_data: Dict[int, Any] = {}

    def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int):
        # ✅ Thread-local access (no lock needed)
        thread_data = self._get_thread_data()
        track = thread_data.tracks.get(track_idx)
        if track:
            block = track.get_block(block_idx)
            if block:
                block.record_time(elapsed_ns)  # ✅ Thread-local mutation

    def get_results(self):
        # ✅ Lock-protected aggregation
        with self._global_lock:
            aggregated_tracks = {}
            for thread_id, thread_data in self._all_thread_data.items():
                # Merge thread data
                pass
            return ProfilerResults(profiler_name=self._name, tracks=aggregated_tracks)
```

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

### Migration Path

**API Compatibility**: 100% backward compatible - no code changes required for users.

**Internal Changes**:
1. Add thread-local storage initialization
2. Add lock-protected global structures
3. Modify _record_block_time to use thread-local data
4. Implement aggregation algorithm in get_results
5. Add lock protection to clear()

**Testing**: Existing tests should pass without modification (API unchanged).

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
- [ ] Update `set_track_enabled()` to use thread-local data
- [ ] Update `is_track_enabled()` to use thread-local data
- [ ] Update `set_track_name()` to use thread-local data
- [ ] Update `track()` decorator to use call-site cache with lock
- [ ] Update `block()` context manager to use call-site cache with lock
- [ ] Update `_record_block_time()` to use thread-local data

**Step 5: Aggregation**
- [ ] Implement `_aggregate_results()` method
- [ ] Implement `_merge_block()` method
- [ ] Update `get_results()` to call `_aggregate_results()`

**Step 6: Clear Method**
- [ ] Update `clear()` to clear `_all_thread_data` with lock
- [ ] Update `clear()` to clear current thread's thread-local data

**Step 7: Testing**
- [ ] Run existing unit tests (should pass - API unchanged)
- [ ] Add thread-safety unit tests
- [ ] Add multi-threaded integration tests
- [ ] Add stress tests (100+ threads)

### Critical Implementation Notes

**1. Thread-Local Initialization Pattern**
```python
# CORRECT: Check hasattr before accessing
if not hasattr(self._thread_local, 'tracks'):
    self._thread_local.tracks = {}
    # ... initialize other attributes ...

# INCORRECT: Direct access (raises AttributeError on first access)
if self._thread_local.tracks is None:  # ❌ AttributeError
    pass
```

**2. Lock Ordering**
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

**3. Thread-Local Access in Hot Path**
```python
# CORRECT: Get thread data once, reuse
thread_data = self._get_thread_data()
if not thread_data.track_enabled.get(track_idx, True):
    return

# INCORRECT: Multiple calls (unnecessary overhead)
if not self._get_thread_data().track_enabled.get(track_idx, True):  # ❌ Slower
    return
```

**4. Aggregation Lock Scope**
```python
# CORRECT: Hold lock for entire aggregation
with self._global_lock:
    for thread_id, thread_data in self._all_thread_data.items():
        # Process all threads
        pass

# INCORRECT: Release lock between threads (inconsistent snapshot)
for thread_id, thread_data in self._all_thread_data.items():  # ❌ Unsafe
    with self._global_lock:  # ❌ Lock per thread (wrong)
        pass
```

### Performance Optimization Tips

**1. Minimize Lock Scope**
```python
# GOOD: Lock only critical section
thread_data = self._get_thread_data()  # No lock
block_idx = self._register_block(thread_data, ...)  # No lock

with _GLOBAL_CACHE_LOCK:  # Lock only for cache update
    _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

# AVOID: Holding lock longer than necessary
with _GLOBAL_CACHE_LOCK:  # ❌ Lock held too long
    thread_data = self._get_thread_data()
    block_idx = self._register_block(thread_data, ...)
    _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)
```

**2. Cache Thread-Local Data**
```python
# GOOD: Cache thread data in wrapper
def decorator(func):
    # ... get block_idx ...

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        thread_data = self._get_thread_data()  # Cache once

        if not thread_data.track_enabled.get(track_idx, True):
            return func(*args, **kwargs)

        # Use cached thread_data
        # ...
```

---

## Testing Considerations

### Unit Tests (Thread-Safety)

**Test 1: Thread-Local Isolation**
```python
def test_thread_local_isolation():
    """Verify each thread has isolated profiling data."""
    profiler = Profiler("test")
    results = {}

    def worker(thread_id):
        @profiler.track(0, f"func_{thread_id}")
        def func():
            time.sleep(0.001)

        for _ in range(100):
            func()

        # Get thread-local results
        thread_data = profiler._get_thread_data()
        results[thread_id] = len(thread_data.tracks[0].blocks)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Each thread should have exactly 1 block
    assert all(count == 1 for count in results.values())
```

**Test 2: Aggregation Correctness**
```python
def test_aggregation_correctness():
    """Verify aggregation merges data correctly."""
    profiler = Profiler("test")

    def worker():
        @profiler.track(0, "shared_func")
        def func():
            time.sleep(0.001)

        for _ in range(100):
            func()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    results = profiler.get_results()
    block = results.tracks[0].blocks[0]

    # Should have 1000 total hits (10 threads × 100 calls)
    assert block.hit_count == 1000
```

**Test 3: Concurrent get_results()**
```python
def test_concurrent_get_results():
    """Verify get_results() is thread-safe."""
    profiler = Profiler("test")

    @profiler.track(0, "func")
    def func():
        time.sleep(0.001)

    def worker():
        for _ in range(50):
            func()
            if random.random() < 0.1:
                profiler.get_results()  # Concurrent aggregation

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Should not crash or corrupt data
    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 500
```

### Integration Tests (Multi-Threaded Scenarios)

**Test 1: Thread Pool Profiling**
```python
def test_thread_pool_profiling():
    """Profile concurrent.futures.ThreadPoolExecutor."""
    profiler = Profiler("test")

    @profiler.track(0, "task")
    def task(n):
        return sum(range(n))

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(task, 1000) for _ in range(1000)]
        concurrent.futures.wait(futures)

    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 1000
```

**Test 2: Nested Profiling**
```python
def test_nested_profiling():
    """Profile nested function calls across threads."""
    profiler = Profiler("test")

    @profiler.track(0, "outer")
    def outer():
        inner()

    @profiler.track(1, "inner")
    def inner():
        time.sleep(0.001)

    def worker():
        for _ in range(100):
            outer()

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 1000  # outer
    assert results.tracks[1].blocks[0].hit_count == 1000  # inner
```

### Stress Tests

**Test 1: High Thread Count**
```python
def test_high_thread_count():
    """Stress test with 100+ threads."""
    profiler = Profiler("test")

    @profiler.track(0, "func")
    def func():
        pass

    def worker():
        for _ in range(1000):
            func()

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 100000
```

**Test 2: Rapid Thread Creation/Destruction**
```python
def test_rapid_thread_churn():
    """Stress test with rapid thread creation/destruction."""
    profiler = Profiler("test")

    @profiler.track(0, "func")
    def func():
        pass

    for _ in range(1000):
        t = threading.Thread(target=lambda: [func() for _ in range(10)])
        t.start()
        t.join()

    results = profiler.get_results()
    assert results.tracks[0].blocks[0].hit_count == 10000
```

---

## Conclusion

### Design Summary

This architecture design provides a complete, implementation-ready specification for Stichotrope v1.0.0's thread-safe profiler.

**Key Design Elements**:
1. **Thread-local storage** for zero-contention hot path
2. **RLock-protected global structures** for safe shared state
3. **Synchronous profiling** for accurate measurements
4. **Lazy aggregation** for efficient cold path
5. **Backward-compatible API** for smooth migration

**Performance Characteristics**:
- Hot path: ~130-250ns per measurement (no locks)
- Cold path: ~0.5-1ms aggregation (acceptable)
- Memory: O(threads × blocks) (acceptable for typical use)

**Complexity**:
- Moderate increase (~100 lines of code)
- Standard library primitives only
- Well-understood threading patterns

### Success Criteria Met

- ✅ **Architecture document includes**: thread-local storage strategy, lock design, data structure choices
- ✅ **Design decisions documented with rationale**: Based on approved evaluation (Task 2.1.0)
- ✅ **Comparison to prototype (v0.5.0)**: Side-by-side comparison provided
- ⏳ **Design review completed and approved**: Awaiting stakeholder review

### Next Steps

**Phase 1 (Current)**:
1. ✅ Task 2.1.0: Architecture Evaluation - APPROVED
2. ✅ Task 2.1.1: Architecture Design - COMPLETE (awaiting review)
3. ⏳ Task 2.1.2: Design Thread-Safe Test Suite (next)

**Phase 2 (Future)**:
4. Task 2.1.3: Implement Thread-Safe Profiler Core
5. Task 2.1.4: Implement Thread-Safe Test Suite

**Implementation Readiness**: This design is sufficiently detailed for Phase 3 implementation. All architectural decisions are documented, all edge cases addressed, and all implementation patterns specified.

---

**Report Version**: v0 (initial)
**Date**: 2025-11-04
**Author**: Architecture Design (Phase 1)
**Status**: Awaiting stakeholder review
**Next Action**: Stakeholder feedback and iteration to v1 if needed

