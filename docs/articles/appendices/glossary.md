# Glossary

Definitions of terms used in Stichotrope documentation.

## A

**API (Application Programming Interface)**
: The set of functions, classes, and methods that Stichotrope provides for users to interact with the profiling library.

## B

**Block**
: A unit of code that is profiled. Can be a function (using decorators) or a code section (using context managers).

**Block-level profiling**
: Profiling at the granularity of code blocks, which fills the gap between function-level profiling (cProfile) and line-level profiling (line_profiler).

## C

**Call-site caching**
: An optimization technique where profiling metadata for each unique call site (file, line, function name) is cached to reduce overhead on subsequent calls.

**Context manager**
: A Python construct using `with` statements. Stichotrope provides `profiler.block()` as a context manager for profiling code sections.

**CppProfiler**
: A C++ profiling library that inspired Stichotrope's design and API. Stichotrope aims to be compatible with CppProfiler's data formats.

## D

**Decorator**
: A Python function that wraps another function. Stichotrope provides `@profiler.track()` as a decorator for profiling entire functions.

**Duration**
: The time taken to execute a profiled block, measured in nanoseconds and provided in multiple units (ns, ms, s).

## E

**Export**
: The process of saving profiling results to a file format (CSV or JSON) for analysis or visualization.

## G

**Global enable/disable**
: A mechanism to enable or disable profiling across all profiler instances simultaneously, with zero overhead when disabled.

## I

**Instrumentation**
: The process of adding profiling code to your application. Stichotrope uses explicit instrumentation via decorators and context managers.

## M

**Multi-track organization**
: A feature that allows organizing profiling data into multiple tracks, useful for categorizing profiling by subsystem, feature, or any logical grouping.

## N

**Nanosecond (ns)**
: One billionth of a second (10⁻⁹ s). Stichotrope measures execution time in nanoseconds for precision.

## O

**Overhead**
: The performance cost of profiling itself. Stichotrope aims for ≤1% overhead for blocks ≥1ms and zero overhead when disabled.

## P

**Profiler**
: The main class in Stichotrope that manages profiling operations. Each profiler instance has a name and can manage multiple tracks.

**ProfileBlock**
: A data structure representing a single profiled execution, containing block index, name, location, and duration.

**ProfileTrack**
: A data structure representing a collection of profiling blocks organized under a single track index.

**ProfilerResults**
: A data structure containing all profiling data from a profiler instance, including profiler name and all tracks.

## R

**Runtime control**
: The ability to enable/disable profiling at runtime without restarting the application or removing instrumentation code.

## T

**Track**
: A logical grouping of profiling blocks, identified by a track index. Tracks allow organizing profiling data by subsystem, feature, or any categorization.

**Track index**
: An integer identifier for a track (e.g., 0, 1, 2). Used when calling `profiler.track()` or `profiler.block()`.

## Z

**Zero overhead**
: When profiling is disabled globally, decorators return identity functions with no performance impact, allowing profiling instrumentation to remain in production code.

## Acronyms

**AGPL**
: GNU Affero General Public License - The license under which Stichotrope is distributed.

**API**
: Application Programming Interface

**CI/CD**
: Continuous Integration / Continuous Deployment

**CSV**
: Comma-Separated Values - A file format for exporting profiling results.

**JSON**
: JavaScript Object Notation - A file format for exporting profiling results.

**ns**
: Nanoseconds (10⁻⁹ seconds)

**ms**
: Milliseconds (10⁻³ seconds)

**μs**
: Microseconds (10⁻⁶ seconds)

**PyPI**
: Python Package Index - The repository where Python packages are published.

## See Also

- [Getting Started Guide](../users/GettingStarted.md)
- [API Reference](../api/index.md)
- [Developer Documentation](../devs/index.md)

