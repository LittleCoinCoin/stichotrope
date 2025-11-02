"""
Profiler wrapper classes for competitive benchmarking.

Provides unified interface for different profiling tools to enable
fair comparison of overhead, features, and output quality.
"""

import cProfile
import io
import pstats
import timeit
from abc import ABC, abstractmethod
from typing import Any, Callable


class ProfilerWrapper(ABC):
    """
    Abstract base class for profiler wrappers.

    Provides unified interface for benchmarking different profilers.
    """

    def __init__(self, name: str):
        """
        Initialize profiler wrapper.

        Args:
            name: Human-readable name of the profiler
        """
        self.name = name
        self.available = self._check_availability()

    @abstractmethod
    def _check_availability(self) -> bool:
        """
        Check if profiler is available.

        Returns:
            True if profiler can be imported and used
        """
        pass

    @abstractmethod
    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Profile a function execution.

        Args:
            func: Function to profile
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func execution
        """
        pass

    @abstractmethod
    def get_results(self) -> dict[str, Any]:
        """
        Get profiling results.

        Returns:
            Dictionary containing profiling data
        """
        pass

    def measure_overhead(self, func: Callable, iterations: int = 30) -> dict[str, Any]:
        """
        Measure profiler overhead.

        Args:
            func: Function to profile
            iterations: Number of measurements

        Returns:
            Dictionary with overhead statistics
        """
        # Measure baseline (unprofiled)
        baseline_times = timeit.repeat(func, repeat=iterations, number=1)

        # Measure profiled
        def profiled_func():
            return self.profile(func)

        profiled_times = timeit.repeat(profiled_func, repeat=iterations, number=1)

        # Calculate overhead
        baseline_mean = sum(baseline_times) / len(baseline_times)
        profiled_mean = sum(profiled_times) / len(profiled_times)

        overhead_ns = (profiled_mean - baseline_mean) * 1e9
        overhead_pct = (
            ((profiled_mean - baseline_mean) / baseline_mean * 100) if baseline_mean > 0 else 0.0
        )

        return {
            "profiler": self.name,
            "baseline_mean_ms": baseline_mean * 1000,
            "profiled_mean_ms": profiled_mean * 1000,
            "overhead_ns": overhead_ns,
            "overhead_pct": overhead_pct,
            "iterations": iterations,
        }


class StichotropeWrapper(ProfilerWrapper):
    """Wrapper for Stichotrope profiler."""

    def __init__(self):
        super().__init__("Stichotrope")
        self.profiler = None
        self.results = None

    def _check_availability(self) -> bool:
        """Check if Stichotrope is available."""
        try:
            from stichotrope import Profiler

            return True
        except (ImportError, AttributeError):
            return False

    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Profile function with Stichotrope."""
        if not self.available:
            raise RuntimeError("Stichotrope not available")

        from stichotrope import Profiler

        self.profiler = Profiler("CompetitiveBenchmark")

        @self.profiler.track(0, func.__name__)
        def wrapped():
            return func(*args, **kwargs)

        result = wrapped()
        self.results = self.profiler.get_results()
        return result

    def get_results(self) -> dict[str, Any]:
        """Get Stichotrope results."""
        if self.results is None:
            return {}

        # Extract relevant data from results
        return {
            "profiler": self.name,
            "tracks": len(self.results.tracks),
            "available": self.available,
        }


class CProfileWrapper(ProfilerWrapper):
    """Wrapper for cProfile (Python standard library)."""

    def __init__(self):
        super().__init__("cProfile")
        self.profiler = None
        self.stats = None

    def _check_availability(self) -> bool:
        """Check if cProfile is available (always true for Python 3.9+)."""
        return True

    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Profile function with cProfile."""
        self.profiler = cProfile.Profile()
        self.profiler.enable()
        try:
            result = func(*args, **kwargs)
        finally:
            self.profiler.disable()

        # Capture stats
        s = io.StringIO()
        self.stats = pstats.Stats(self.profiler, stream=s)

        return result

    def get_results(self) -> dict[str, Any]:
        """Get cProfile results."""
        if self.stats is None:
            return {}

        return {
            "profiler": self.name,
            "available": self.available,
            "stats_available": True,
        }


class PySpyWrapper(ProfilerWrapper):
    """Wrapper for py-spy (sampling profiler)."""

    def __init__(self):
        super().__init__("py-spy")

    def _check_availability(self) -> bool:
        """Check if py-spy is available."""
        try:
            import subprocess

            result = subprocess.run(["py-spy", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """
        Profile function with py-spy.

        Note: py-spy is a sampling profiler that runs as a separate process.
        This wrapper provides a simplified interface but may not capture
        short-running functions accurately.
        """
        if not self.available:
            raise RuntimeError("py-spy not available")

        # For now, just run the function without profiling
        # Full py-spy integration would require subprocess management
        return func(*args, **kwargs)

    def get_results(self) -> dict[str, Any]:
        """Get py-spy results."""
        return {
            "profiler": self.name,
            "available": self.available,
            "note": "py-spy requires subprocess integration",
        }


class LineProfilerWrapper(ProfilerWrapper):
    """Wrapper for line_profiler."""

    def __init__(self):
        super().__init__("line_profiler")
        self.profiler = None

    def _check_availability(self) -> bool:
        """Check if line_profiler is available."""
        try:
            import line_profiler

            return True
        except ImportError:
            return False

    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Profile function with line_profiler."""
        if not self.available:
            raise RuntimeError("line_profiler not available")

        import line_profiler

        self.profiler = line_profiler.LineProfiler()
        self.profiler.add_function(func)
        self.profiler.enable()
        try:
            result = func(*args, **kwargs)
        finally:
            self.profiler.disable()

        return result

    def get_results(self) -> dict[str, Any]:
        """Get line_profiler results."""
        return {
            "profiler": self.name,
            "available": self.available,
        }


class PyInstrumentWrapper(ProfilerWrapper):
    """Wrapper for pyinstrument (statistical profiler)."""

    def __init__(self):
        super().__init__("pyinstrument")
        self.profiler = None

    def _check_availability(self) -> bool:
        """Check if pyinstrument is available."""
        try:
            import pyinstrument

            return True
        except ImportError:
            return False

    def profile(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        """Profile function with pyinstrument."""
        if not self.available:
            raise RuntimeError("pyinstrument not available")

        import pyinstrument

        self.profiler = pyinstrument.Profiler()
        self.profiler.start()
        try:
            result = func(*args, **kwargs)
        finally:
            self.profiler.stop()

        return result

    def get_results(self) -> dict[str, Any]:
        """Get pyinstrument results."""
        return {
            "profiler": self.name,
            "available": self.available,
        }


def get_all_profilers() -> list[ProfilerWrapper]:
    """
    Get all available profiler wrappers.

    Returns:
        List of profiler wrapper instances
    """
    return [
        StichotropeWrapper(),
        CProfileWrapper(),
        PySpyWrapper(),
        LineProfilerWrapper(),
        PyInstrumentWrapper(),
    ]


def get_available_profilers() -> list[ProfilerWrapper]:
    """
    Get only available profiler wrappers.

    Returns:
        List of available profiler wrapper instances
    """
    return [p for p in get_all_profilers() if p.available]
