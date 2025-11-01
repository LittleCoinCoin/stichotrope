"""
Stichotrope - Python profiling library with block-level profiling and multi-track organization.

This library provides a native Python equivalent of CppProfiler, offering:
- Block-level profiling (fills gap between function-level and line-level profiling)
- Multi-track organization (logical grouping of profiling data)
- Explicit instrumentation (decorators and context managers)
- Zero overhead when disabled (runtime enable/disable)

Example usage:
    >>> from stichotrope import Profiler
    >>> profiler = Profiler("MyApp")
    >>>
    >>> @profiler.track(0, "process_data")
    >>> def process_data(data):
    ...     return transform(data)
    >>>
    >>> def complex_function():
    ...     with profiler.block(1, "database_query"):
    ...         result = query_database()
    ...     return result
"""

try:
    from importlib.metadata import version
    __version__ = version(__package__ or __name__)
except Exception:
    # Fallback for development or when package is not installed
    __version__ = "0.0.0"

__all__ = [
    "__version__",
]

