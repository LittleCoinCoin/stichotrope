# Types Module

Type definitions and data structures for profiling results.

## Data Structures

### ProfileBlock

::: stichotrope.types.ProfileBlock
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

### ProfileTrack

::: stichotrope.types.ProfileTrack
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

### ProfilerResults

::: stichotrope.types.ProfilerResults
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

## Usage Examples

### Accessing Profile Data

```python
from stichotrope import Profiler

profiler = Profiler("MyApp")

# ... run profiled code ...

# Get results
results = profiler.get_results()

# Access profiler name
print(f"Profiler: {results.profiler_name}")

# Iterate over tracks
for track in results.tracks:
    print(f"Track {track.track_idx}:")
    
    # Iterate over blocks in track
    for block in track.blocks:
        print(f"  Block {block.block_idx} ({block.name}):")
        print(f"    Duration: {block.duration_ns} ns")
        print(f"    Location: {block.file}:{block.line}")
```

### Analyzing Results

```python
from stichotrope import Profiler

profiler = Profiler("MyApp")

# ... run profiled code ...

results = profiler.get_results()

# Find slowest block
slowest_block = None
slowest_duration = 0

for track in results.tracks:
    for block in track.blocks:
        if block.duration_ns > slowest_duration:
            slowest_duration = block.duration_ns
            slowest_block = block

if slowest_block:
    print(f"Slowest block: {slowest_block.name}")
    print(f"Duration: {slowest_block.duration_ns} ns")
    print(f"Location: {slowest_block.file}:{slowest_block.line}")
```

### Filtering Results

```python
from stichotrope import Profiler

profiler = Profiler("MyApp")

# ... run profiled code ...

results = profiler.get_results()

# Filter blocks by duration threshold (e.g., > 1ms)
threshold_ns = 1_000_000  # 1ms in nanoseconds

slow_blocks = []
for track in results.tracks:
    for block in track.blocks:
        if block.duration_ns > threshold_ns:
            slow_blocks.append(block)

print(f"Found {len(slow_blocks)} blocks slower than 1ms")
for block in slow_blocks:
    print(f"  {block.name}: {block.duration_ns / 1_000_000:.2f} ms")
```

### Aggregating Results

```python
from stichotrope import Profiler
from collections import defaultdict

profiler = Profiler("MyApp")

# ... run profiled code ...

results = profiler.get_results()

# Aggregate by block name
aggregated = defaultdict(lambda: {"count": 0, "total_ns": 0})

for track in results.tracks:
    for block in track.blocks:
        aggregated[block.name]["count"] += 1
        aggregated[block.name]["total_ns"] += block.duration_ns

# Print aggregated results
for name, stats in aggregated.items():
    avg_ns = stats["total_ns"] / stats["count"]
    print(f"{name}:")
    print(f"  Count: {stats['count']}")
    print(f"  Total: {stats['total_ns'] / 1_000_000:.2f} ms")
    print(f"  Average: {avg_ns / 1_000_000:.2f} ms")
```

### Track-Level Analysis

```python
from stichotrope import Profiler

profiler = Profiler("MyApp")

# ... run profiled code ...

results = profiler.get_results()

# Analyze each track
for track in results.tracks:
    total_duration = sum(block.duration_ns for block in track.blocks)
    block_count = len(track.blocks)
    
    print(f"Track {track.track_idx}:")
    print(f"  Blocks: {block_count}")
    print(f"  Total duration: {total_duration / 1_000_000:.2f} ms")
    
    if block_count > 0:
        avg_duration = total_duration / block_count
        print(f"  Average duration: {avg_duration / 1_000_000:.2f} ms")
```

## Type Hints

The types module provides type hints for better IDE support and type checking:

```python
from stichotrope import Profiler, ProfilerResults
from stichotrope.types import ProfileBlock, ProfileTrack

def analyze_results(results: ProfilerResults) -> None:
    """Analyze profiling results with full type hints."""
    track: ProfileTrack
    for track in results.tracks:
        block: ProfileBlock
        for block in track.blocks:
            print(f"{block.name}: {block.duration_ns} ns")

profiler = Profiler("MyApp")
# ... run profiled code ...
analyze_results(profiler.get_results())
```

## Data Structure Details

### ProfileBlock Fields

- `block_idx` (int): Unique index within the track
- `name` (str): Human-readable block name
- `file` (str): Source file path where block was defined
- `line` (int): Line number where block was defined
- `duration_ns` (int): Execution duration in nanoseconds

### ProfileTrack Fields

- `track_idx` (int): Track index
- `blocks` (list[ProfileBlock]): List of profiling blocks in this track

### ProfilerResults Fields

- `profiler_name` (str): Name of the profiler instance
- `tracks` (list[ProfileTrack]): List of tracks with profiling data

## See Also

- [Profiler Module](profiler.md) - Core profiling functionality
- [Export Module](export.md) - Exporting and displaying results
- [Getting Started](../users/GettingStarted.md) - Usage guide

