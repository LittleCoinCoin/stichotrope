# Export Module

Functions for exporting and displaying profiling results.

## Export Functions

### export_csv

::: stichotrope.export.export_csv
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

### export_json

::: stichotrope.export.export_json
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

## Display Functions

### print_results

::: stichotrope.export.print_results
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

### format_time_ns

::: stichotrope.export.format_time_ns
    options:
      show_source: true
      show_root_heading: true
      heading_level: 3

## Usage Examples

### CSV Export

```python
from stichotrope import Profiler, export_csv

profiler = Profiler("MyApp")

# ... run profiled code ...

# Export to CSV
results = profiler.get_results()
export_csv(results, "profiling_results.csv")
```

**CSV Format:**

The CSV file contains the following columns:

- `track_idx`: Track index
- `block_idx`: Block index within track
- `name`: Block name
- `file`: Source file path
- `line`: Line number
- `duration_ns`: Execution duration in nanoseconds
- `duration_ms`: Execution duration in milliseconds
- `duration_s`: Execution duration in seconds

### JSON Export

```python
from stichotrope import Profiler, export_json

profiler = Profiler("MyApp")

# ... run profiled code ...

# Export to JSON
results = profiler.get_results()
export_json(results, "profiling_results.json")
```

**JSON Format:**

```json
{
  "profiler_name": "MyApp",
  "tracks": [
    {
      "track_idx": 0,
      "blocks": [
        {
          "block_idx": 0,
          "name": "process_data",
          "file": "/path/to/file.py",
          "line": 42,
          "duration_ns": 1234567,
          "duration_ms": 1.234567,
          "duration_s": 0.001234567
        }
      ]
    }
  ]
}
```

### Console Output

```python
from stichotrope import Profiler, print_results

profiler = Profiler("MyApp")

# ... run profiled code ...

# Print to console
results = profiler.get_results()
print_results(results)
```

**Console Output Format:**

```
Profiler: MyApp
Track 0:
  Block 0 (process_data): 1.23 ms
  Block 1 (transform_data): 2.45 ms
Track 1:
  Block 0 (database_query): 10.50 ms
  Block 1 (cache_lookup): 0.15 ms
```

### Time Formatting

```python
from stichotrope import format_time_ns

# Format nanoseconds to human-readable string
duration_ns = 1234567890
formatted = format_time_ns(duration_ns)
print(formatted)  # "1.23 s" or "1234.57 ms" depending on magnitude
```

## CppProfiler Compatibility

The CSV export format is compatible with CppProfiler, allowing you to:

- Use the same analysis tools for Python and C++ profiling data
- Compare performance between Python and C++ implementations
- Integrate Python profiling into existing CppProfiler workflows

### Compatibility Notes

- Column names match CppProfiler CSV format
- Duration values provided in multiple units (ns, ms, s)
- Track and block indices use the same semantics

## Advanced Usage

### Conditional Export

```python
from stichotrope import Profiler, export_csv, export_json

profiler = Profiler("MyApp")

# ... run profiled code ...

results = profiler.get_results()

# Export only if profiling was enabled
if results.tracks:
    export_csv(results, "results.csv")
    export_json(results, "results.json")
```

### Custom Export Path

```python
import os
from datetime import datetime
from stichotrope import Profiler, export_csv

profiler = Profiler("MyApp")

# ... run profiled code ...

# Create timestamped export
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
export_dir = "profiling_results"
os.makedirs(export_dir, exist_ok=True)

export_path = os.path.join(export_dir, f"profile_{timestamp}.csv")
export_csv(profiler.get_results(), export_path)
```

### Multiple Export Formats

```python
from stichotrope import Profiler, export_csv, export_json, print_results

profiler = Profiler("MyApp")

# ... run profiled code ...

results = profiler.get_results()

# Export in all formats
print_results(results)  # Console output
export_csv(results, "results.csv")  # CSV for spreadsheets
export_json(results, "results.json")  # JSON for programmatic analysis
```

## See Also

- [Profiler Module](profiler.md) - Core profiling functionality
- [Types Module](types.md) - Data structure definitions
- [Getting Started](../users/GettingStarted.md) - Usage guide

