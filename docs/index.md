# Stichotrope

**Python profiling library with block-level profiling and multi-track organization**

## Overview

Stichotrope is a native Python profiling library that provides a Python equivalent of CppProfiler, offering precise block-level profiling with multi-track organization for complex applications.

## Key Features

- **Block-level profiling**: Fills the gap between function-level and line-level profiling
- **Multi-track organization**: Logical grouping of profiling data for complex applications
- **Explicit instrumentation**: Decorators and context managers for precise control
- **Thread-safe**: Built-in support for multi-threaded applications
- **Low overhead**: ≤1% overhead for functions ≥1ms (verified)
- **Zero overhead when disabled**: Runtime enable/disable with no performance impact
- **CppProfiler-compatible**: Familiar API for users of CppProfiler
- **Export capabilities**: CSV and JSON export for analysis and visualization

## Quick Example

```python
from stichotrope import Profiler

# Create a profiler instance
profiler = Profiler("MyApp")

# Profile a function with decorator
@profiler.track(0, "process_data")
def process_data(data):
    return transform(data)

# Profile a code block with context manager
def complex_function():
    with profiler.block(1, "database_query"):
        result = query_database()
    return result

# Get and display results
results = profiler.get_results()
profiler.print_results()
```

## Installation

!!! info "Development Status"
    Stichotrope v0.2.0 is in active development with verified performance characteristics. The API is stabilizing toward v1.0.0.

```bash
# Install from PyPI (when available)
pip install stichotrope

# Install from source
git clone https://github.com/LittleCoinCoin/stichotrope.git
cd stichotrope
pip install -e .
```

## Documentation Structure

- **[Getting Started](articles/users/GettingStarted.md)**: Installation and basic usage
- **[API Reference](articles/api/index.md)**: Complete API documentation
- **[Developer Guide](articles/devs/index.md)**: Contributing and development guidelines

## Project Status

**Current Version**: v0.2.0 (development)  
**Phase**: Phase 2 - Core Architecture & Features (Milestone 2.1 complete)  
**Target Release**: v1.0.0

### Milestone Progress

- ✅ **Phase 1**: Infrastructure Foundation (Testing, CI/CD, Packaging, Documentation)
- ✅ **Phase 2.1**: Thread-Safe Architecture (v0.2.0 complete with verified performance)
- ⏳ **Phase 2.2+**: Configuration System, Production Features
- 📋 **Phase 3**: Release Preparation (Documentation completion, Final validation)

## License

Stichotrope is licensed under the [GNU Affero General Public License v3.0 or later (AGPLv3+)](https://github.com/LittleCoinCoin/stichotrope/blob/main/LICENSE).

## Links

- [GitHub Repository](https://github.com/LittleCoinCoin/stichotrope)
- [Issue Tracker](https://github.com/LittleCoinCoin/stichotrope/issues)
- [PyPI Package](https://pypi.org/project/stichotrope/) (coming soon)

