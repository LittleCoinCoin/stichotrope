# Thread-Safe Architecture

This document describes the internal design of Stichotrope's thread-safe profiling implementation in v0.2.0+. This is intended for developers contributing to the project or understanding the implementation details.

## Overview

Stichotrope uses a **thread-local storage** design with a **global registry** and **minimal locking** strategy to achieve thread-safe profiling with negligible overhead impact.

## Design Principles

1. **Per-thread lock-free operations**: Each thread's profiling data is independent, requiring no synchronization for track/block profiling
2. **Minimal lock contention**: Locks are only acquired for cross-thread aggregation operations
3. **Automatic cleanup**: Thread-local data is automatically cleaned up when threads terminate
4. **Zero overhead when disabled**: Global enable/disable avoids profiling completely when not needed

## Data Structures

### Thread-Local Storage

```python
# Per-thread structure (threading.local())
_tracks: Dict[int, Track]
```

Each thread maintains its own `_tracks` dictionary mapping track indices to `Track` objects. Track objects contain:

```python
class Track:
    track_idx: int                      # Track identifier
    track_name: Optional[str]           # User-friendly track name
    enabled: bool                       # Whether track is enabled
    blocks: Dict[int, ProfileBlock]     # Blocks in this track
```

ProfileBlock objects store timing data:

```python
class ProfileBlock:
    name: str                           # Block name
    file: str                          # Source file
    line: int                          # Source line
    hit_count: int                     # Number of times executed
    total_time_ns: int                 # Total execution time
    min_time_ns: int                   # Minimum execution time
    max_time_ns: int                   # Maximum execution time
```

### Global Registry

```python
_all_thread_data: Dict[int, threading.local]
```

The global registry maps thread IDs to their `threading.local()` objects. This allows aggregating results across threads while maintaining per-thread independence.

## Lock Strategy

### Global Lock

```python
_lock: threading.RLock()
```

A single `RLock` (reentrant lock) protects the global `_all_thread_data` registry and cross-thread aggregation operations.

### Lock Acquisition Points

**Locked operations** (require global lock):
- `__init__()`: Register profiler instance in global registry
- `get_all_thread_data()`: Aggregate results from all threads
- Cross-thread cache validation

**Lock-free operations** (no lock needed):
- `track()` decorator application
- `block()` context manager entry/exit
- `get_results()` for current thread
- Per-thread profiling updates

### Lock Contention Impact

- **Minimal contention**: Locks are held for microseconds (only during aggregation)
- **No locks in hot path**: Decorator and context manager execution don't acquire locks
- **Per-thread efficiency**: 99%+ of profiling operations are lock-free

## Call-Site Caching

Stichotrope uses **call-site caching** to minimize overhead:

```python
# Global cache maps (file, line, function_name) to ProfileBlock
_call_site_cache: Dict[Tuple[str, int, str], ProfileBlock]
```

When a decorated function is called:

1. Inspect call site (file, line, function name)
2. Check if this call site is already cached
3. If cached: retrieve existing ProfileBlock
4. If not cached: create new ProfileBlock and cache it

This reduces overhead for repeated calls to the same function.

## Thread Lifecycle

### Thread Creation

When a thread begins profiling:

1. Thread-local storage is automatically created by `threading.local()`
2. Global registry entry is created on first profiling operation
3. `_tracks` dictionary is initialized for this thread

### Thread Termination

When a thread terminates:

1. Thread-local storage is automatically cleaned up (no manual cleanup needed)
2. Global registry entry becomes inactive
3. Data can still be accessed via `get_all_thread_data()` until profiler is destroyed

## Implementation Reference

The complete implementation is in `stichotrope/profiler.py`. Key sections:

- **Thread-local initialization**: `_setup_thread_local()` method
- **Global registry management**: `_register_thread()` and `_unregister_thread()` methods
- **Decorator/context manager**: `track()` and `block()` methods
- **Lock acquisition**: `get_all_thread_data()` method uses lock for aggregation
- **Call-site caching**: `_get_or_create_block()` method implements cache logic

## Testing

Thread-safety is verified through:

1. **Unit tests**: `tests/unit/test_thread_safety.py` - Basic thread-safety tests
2. **Integration tests**: `tests/integration/test_threaded_profiling.py` - Real-world scenarios
3. **Performance tests**: `tests/performance/test_thread_safety_overhead.py` - Overhead measurement
4. **Stress tests**: Multiple threads with high contention scenarios

## See Also

- [API Reference - Profiler](../api/profiler.md) - User-facing API documentation
- [Performance Characteristics](../users/performance.md) - Performance expectations and guarantees
- [Getting Started - Multi-Threading](../users/GettingStarted.md#multi-threaded-applications) - Usage example
