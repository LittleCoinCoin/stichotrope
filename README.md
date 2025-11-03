# Stichotrope

> **⚠️ Development Status**: This repository is currently in the setup phase. The library is not yet available for use.

A Python profiling library for deterministic function and block-level profiling.

## Overview

Stichotrope aims to provide a native Python equivalent of CppProfiler, offering:

- **Block-level profiling**: Fills the gap between function-level and line-level profiling
- **Multi-track organization**: Logical grouping of profiling data
- **Explicit instrumentation**: Decorators and context managers for precise control
- **Deterministic profiling**: Predictable, reproducible performance measurements

## Project Status

🚧 **In Development** - Phase 1: Infrastructure Foundation

This project is actively being developed following a structured roadmap toward v1.0.0. Current focus:

- ✅ Testing framework and performance baseline
- ✅ CI/CD pipeline
- 🔄 PyPI packaging setup
- ⏳ Documentation infrastructure
- ⏳ Thread-safe architecture
- ⏳ Configuration system
- ⏳ Production features

## Planned Features

- Thread-safe profiling for multi-threaded applications
- TOML-based configuration system
- CSV/JSON export (CppProfiler-compatible)
- Statistical benchmarking with confidence intervals
- Cross-platform support (Windows, Linux, macOS)
- Python 3.9-3.12 support

## Installation

**Not yet available on PyPI**

Once released, installation will be:

```bash
pip install stichotrope
```

## Quick Start

**Coming soon** - The library is not yet ready for use.

Example usage (planned):

```python
from stichotrope import Profiler

profiler = Profiler("MyApp")

@profiler.track(0, "process_data")
def process_data(data):
    return transform(data)

def complex_function():
    with profiler.block(1, "database_query"):
        result = query_database()
    return result
```

## Documentation

Documentation will be available at [Read the Docs](https://stichotrope.readthedocs.io) once the project reaches a stable release.

## Development

This project follows a milestone-based development workflow with strict quality gates. See the [roadmap](__design__/02-product_roadmap_v2.md) for detailed planning.

### Contributing

Contributions are welcome once the project reaches v1.0.0. For now, development is focused on establishing the core infrastructure and architecture.

## License

This project is licensed under the [GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)](LICENSE).

## Links

- **Repository**: [github.com/LittleCoinCoin/stichotrope](https://github.com/LittleCoinCoin/stichotrope)
- **Issues**: [github.com/LittleCoinCoin/stichotrope/issues](https://github.com/LittleCoinCoin/stichotrope/issues)
- **Roadmap**: [Product Roadmap](__design__/02-product_roadmap_v2.md)

---

**Target Release**: v1.0.0 (7-9 weeks from project start)  
**Current Version**: 0.0.0 (development)

