# API Reference

Complete API documentation for Stichotrope, automatically generated from source code docstrings.

## Overview

Stichotrope provides a simple yet powerful API for block-level profiling with multi-track organization. The API is designed to be familiar to users of CppProfiler while providing Pythonic interfaces.

## Core Components

### Profiler

The main profiler class for creating profiling instances and instrumenting code.

- **[Profiler Class](profiler.md)**: Core profiling functionality
  - Creating profiler instances
  - Decorator-based profiling (`@profiler.track()`)
  - Context manager profiling (`profiler.block()`)
  - Runtime control (start/stop, enable/disable)
  - Results retrieval

### Export Functions

Functions for exporting and displaying profiling results.

- **[Export Module](export.md)**: Result export and display
  - CSV export (`export_csv()`)
  - JSON export (`export_json()`)
  - Console output (`print_results()`)
  - Time formatting (`format_time_ns()`)

### Type Definitions

Type definitions for profiling data structures.

- **[Types Module](types.md)**: Data structures and type hints
  - `ProfileBlock`: Individual profiling block data
  - `ProfileTrack`: Track containing multiple blocks
  - `ProfilerResults`: Complete profiling results

## Quick Reference

### Creating a Profiler

```python
from stichotrope import Profiler

profiler = Profiler("MyApp")
```

### Profiling with Decorators

```python
@profiler.track(0, "function_name")
def my_function():
    # Function code
    pass
```

### Profiling with Context Managers

```python
with profiler.block(1, "block_name"):
    # Code to profile
    pass
```

### Getting Results

```python
results = profiler.get_results()
```

### Exporting Results

```python
from stichotrope import export_csv, export_json, print_results

# Print to console
print_results(results)

# Export to CSV
export_csv(results, "results.csv")

# Export to JSON
export_json(results, "results.json")
```

### Global Control

```python
from stichotrope import set_global_enabled, is_global_enabled

# Disable profiling globally
set_global_enabled(False)

# Check if enabled
if is_global_enabled():
    print("Profiling is active")
```

## Module Documentation

- **[Profiler](profiler.md)**: Core profiler class and global functions
- **[Export](export.md)**: Export and display functions
- **[Types](types.md)**: Type definitions and data structures

## Design Principles

### Zero Overhead When Disabled

When profiling is disabled globally, decorators return identity functions with zero overhead. This allows you to keep profiling instrumentation in production code without performance impact.

### Multi-Track Organization

Tracks provide logical grouping of profiling data, useful for organizing profiling by subsystem, feature, or any other categorization that makes sense for your application.

### Explicit Instrumentation

Stichotrope uses explicit instrumentation (decorators and context managers) rather than automatic instrumentation. This gives you precise control over what gets profiled and reduces overhead.

### CppProfiler Compatibility

The API is designed to be familiar to users of CppProfiler, making it easy to migrate Python code that needs to interoperate with C++ code using CppProfiler.

## Examples

### Basic Profiling

```python
from stichotrope import Profiler

profiler = Profiler("Example")

@profiler.track(0, "compute")
def compute(n):
    return sum(range(n))

result = compute(1000000)
profiler.print_results()
```

### Multi-Track Profiling

```python
from stichotrope import Profiler, export_csv

profiler = Profiler("WebApp")

# Track 0: Request handling
@profiler.track(0, "handle_request")
def handle_request(request):
    return process(request)

# Track 1: Database operations
@profiler.track(1, "db_query")
def query_db(query):
    return execute(query)

# Track 2: Cache operations
@profiler.track(2, "cache_get")
def get_cache(key):
    return cache.get(key)

# Run application
handle_request(request)

# Export results
export_csv(profiler.get_results(), "webapp_profile.csv")
```

### Selective Profiling

```python
from stichotrope import Profiler

profiler = Profiler("Selective")

# Disable specific tracks
profiler.set_track_enabled(1, False)  # Disable track 1

@profiler.track(0, "always_profiled")
def always_profiled():
    pass

@profiler.track(1, "conditionally_profiled")
def conditionally_profiled():
    pass  # Won't be profiled when track 1 is disabled

always_profiled()  # Profiled
conditionally_profiled()  # Not profiled

# Re-enable track 1
profiler.set_track_enabled(1, True)
conditionally_profiled()  # Now profiled
```

## See Also

- [Getting Started Guide](../users/GettingStarted.md)
- [Developer Documentation](../devs/index.md)

