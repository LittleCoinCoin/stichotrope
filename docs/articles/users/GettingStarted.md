# Getting Started

This guide will help you get started with Stichotrope, a Python profiling library with block-level profiling and multi-track organization.

## Installation

### Requirements

- Python 3.9 or later
- pip package manager

### Install from PyPI

!!! info "Development Status"
    Stichotrope v0.2.0 is in active development with verified performance. The PyPI package will be available with the v1.0.0 release.

```bash
pip install stichotrope
```

### Install from Source

For development or to use the latest features:

```bash
git clone https://github.com/LittleCoinCoin/stichotrope.git
cd stichotrope
pip install -e .
```

## Basic Usage

### Creating a Profiler

Start by creating a `Profiler` instance:

```python
from stichotrope import Profiler

profiler = Profiler("MyApplication")
```

### Profiling Functions with Decorators

Use the `@profiler.track()` decorator to profile entire functions:

```python
@profiler.track(0, "data_processing")
def process_data(data):
    # Your function code here
    result = transform(data)
    return result
```

**Parameters:**
- `track_idx` (int): Track index for organizing profiling data (e.g., 0, 1, 2)
- `block_name` (str): Human-readable name for this profiling block

### Profiling Code Blocks with Context Managers

Use the `profiler.block()` context manager to profile specific code sections:

```python
def complex_function():
    # Profile a specific section
    with profiler.block(1, "database_query"):
        result = query_database()
    
    # Profile another section
    with profiler.block(1, "data_transformation"):
        transformed = transform(result)
    
    return transformed
```

### Getting Results

Retrieve profiling results:

```python
# Get results as a structured object
results = profiler.get_results()

# Print results to console
profiler.print_results()

# Export to CSV
from stichotrope import export_csv
export_csv(results, "profiling_results.csv")

# Export to JSON
from stichotrope import export_json
export_json(results, "profiling_results.json")
```

## Multi-Track Organization

Stichotrope supports organizing profiling data into multiple tracks, which is useful for complex applications with different subsystems:

```python
profiler = Profiler("WebApp")

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
```

## Multi-Threaded Applications

Stichotrope supports profiling in multi-threaded applications. Each thread maintains its own profiling data, which can be aggregated when needed:

```python
from stichotrope import Profiler
import threading

profiler = Profiler("ThreadedApp")

@profiler.track(0, "worker_task")
def worker_task(task_id):
    with profiler.block(1, "process_item"): 
        # Simulate work
        time.sleep(0.1)
        print(f"Task {task_id} completed")

# Create and start threads
threads = [
    threading.Thread(target=worker_task, args=(i,))
    for i in range(4)
]

for thread in threads:
    thread.start()

# Wait for all threads to complete
for thread in threads:
    thread.join()

# Get profiling results from all threads
all_thread_results = profiler.get_all_thread_data()

# Process results by thread
for thread_id, results in all_thread_results.items():
    print(f"\nThread {thread_id}:")
    for track in results.tracks.values():
        for block in track.blocks.values():
            print(f"  {block.name}: {block.total_time_ns / 1e6:.2f}ms ({block.hit_count} calls)")
```

**Key methods for multi-threaded profiling:**

- `get_results()`: Get profiling results for the current thread only
- `get_all_thread_data()`: Get profiling results from all threads in a dictionary keyed by thread ID

For more details on performance expectations and when to use Stichotrope, see [Performance Characteristics](./performance.md).


### Global Enable/Disable

Control profiling globally across all profiler instances:

```python
from stichotrope import set_global_enabled, is_global_enabled

# Disable profiling globally (zero overhead)
set_global_enabled(False)

# Re-enable profiling
set_global_enabled(True)

# Check if profiling is enabled
if is_global_enabled():
    print("Profiling is active")
```

### Per-Profiler Control

Control individual profiler instances:

```python
profiler = Profiler("MyApp")

# Stop profiling
profiler.stop()

# Resume profiling
profiler.start()

# Check if profiler is started
if profiler.is_started():
    print("Profiler is running")
```

### Per-Track Control

Enable or disable specific tracks:

```python
# Disable track 1
profiler.set_track_enabled(1, False)

# Re-enable track 1
profiler.set_track_enabled(1, True)

# Check if track is enabled
if profiler.is_track_enabled(1):
    print("Track 1 is enabled")
```

## Complete Example

Here's a complete example demonstrating Stichotrope's features:

```python
from stichotrope import Profiler, export_csv

# Create profiler
profiler = Profiler("DataPipeline")

# Profile data loading
@profiler.track(0, "load_data")
def load_data(filename):
    with open(filename, 'r') as f:
        return f.read()

# Profile data processing with multiple blocks
def process_pipeline(filename):
    # Load data
    data = load_data(filename)
    
    # Parse data
    with profiler.block(1, "parse_data"):
        parsed = parse(data)
    
    # Transform data
    with profiler.block(1, "transform_data"):
        transformed = transform(parsed)
    
    # Save results
    with profiler.block(2, "save_results"):
        save(transformed)
    
    return transformed

# Run pipeline
result = process_pipeline("input.txt")

# Display and export results
profiler.print_results()
export_csv(profiler.get_results(), "pipeline_profile.csv")
```

## Next Steps

- Explore the [API Reference](../api/index.md) for detailed documentation
- Learn about [advanced features](../devs/index.md) and contributing
