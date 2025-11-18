# Profiler Module

Core profiler implementation with multi-track support and runtime control.

## Profiler Class

::: stichotrope.profiler.Profiler
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

## Global Functions

### set_global_enabled

::: stichotrope.profiler.set_global_enabled
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

### is_global_enabled

::: stichotrope.profiler.is_global_enabled
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

## Usage Examples

### Basic Profiler Usage

```python
from stichotrope import Profiler

# Create a profiler instance
profiler = Profiler("MyApplication")

# Profile a function with decorator
@profiler.track(0, "process_data")
def process_data(data):
    return transform(data)

# Profile a code block with context manager
def complex_function():
    with profiler.block(1, "database_query"):
        result = query_database()
    return result

# Get results
results = profiler.get_results()
profiler.print_results()
```

### Runtime Control

```python
from stichotrope import Profiler, set_global_enabled

profiler = Profiler("MyApp")

# Per-profiler control
profiler.stop()  # Pause profiling
profiler.start()  # Resume profiling

# Per-track control
profiler.set_track_enabled(0, False)  # Disable track 0
profiler.set_track_enabled(0, True)   # Re-enable track 0

# Global control (affects all profilers)
set_global_enabled(False)  # Disable all profiling (zero overhead)
set_global_enabled(True)   # Re-enable profiling
```

### Multi-Track Organization

```python
from stichotrope import Profiler

profiler = Profiler("WebServer")

# Track 0: Request handling
@profiler.track(0, "handle_request")
def handle_request(request):
    return process_request(request)

# Track 1: Database operations
@profiler.track(1, "db_query")
def query_database(query):
    return execute_query(query)

# Track 2: Cache operations
@profiler.track(2, "cache_lookup")
def check_cache(key):
    return cache.get(key)

# Results are organized by track
results = profiler.get_results()
for track in results.tracks:
    print(f"Track {track.track_idx}: {len(track.blocks)} blocks")
```

### Nested Profiling

```python
from stichotrope import Profiler

profiler = Profiler("DataPipeline")

def process_pipeline(data):
    # Outer block
    with profiler.block(0, "full_pipeline"):
        # Inner blocks
        with profiler.block(1, "load_data"):
            loaded = load(data)
        
        with profiler.block(1, "transform_data"):
            transformed = transform(loaded)
        
        with profiler.block(1, "save_data"):
            save(transformed)
    
    return transformed
```

### Multi-Threaded Usage

```python
from stichotrope import Profiler
import threading

profiler = Profiler("MultiThreadApp")

@profiler.track(0, "worker_task")
def worker_task(task_id):
    # Profiling in thread
    with profiler.block(1, "task_processing"):
        process(task_id)

# Start multiple threads
threads = [
    threading.Thread(target=worker_task, args=(i,))
    for i in range(5)
]

for t in threads:
    t.start()
for t in threads:
    t.join()

# Retrieve results from all threads
all_results = profiler.get_all_thread_data()
for thread_id, thread_results in all_results.items():
    print(f"Thread {thread_id}: {thread_results}")
```

## Implementation Details

### Call-Site Caching

The profiler uses call-site caching to minimize overhead. Each unique call site (file, line number, function name) is cached, so subsequent calls to the same profiled function have minimal overhead.

### Thread Safety

The Profiler is thread-safe by design in v0.2.0+. Each thread maintains its own profiling data independently, with a thread-safe aggregation mechanism for retrieving cross-thread results.

**Per-thread operations** (lock-free):
- `track()` decorator on functions
- `block()` context manager
- `get_results()` for current thread's data

**Cross-thread operations** (synchronized):
- `get_all_thread_data()` for aggregating results across threads

For multi-threaded applications, use `get_all_thread_data()` to retrieve and aggregate profiling results from all threads.

### Performance Characteristics

- **Overhead when enabled**: ≤1% for blocks over 1ms. The raw overhead is typically 4µs so profiling anything within the same order of magnitude will result in significant timing distortions.
- **Overhead when disabled**: Zero overhead (decorators return identity functions)

For detailed performance analysis and benchmarking methodology, see [Performance Documentation](../users/performance.md).

## See Also

- [Export Module](export.md) - Exporting and displaying results
- [Types Module](types.md) - Data structure definitions
- [Getting Started](../users/GettingStarted.md) - Usage guide

