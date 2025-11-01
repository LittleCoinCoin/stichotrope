"""
Core Profiler implementation for Stichotrope.

Provides the main Profiler class with multi-track support, runtime enable/disable,
and call-site caching.
"""

import functools
import inspect
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Tuple
from stichotrope.types import ProfileBlock, ProfileTrack, ProfilerResults
from stichotrope.timing import get_time_ns


# Global enable/disable flag (module-level)
_PROFILER_ENABLED = True

# Global call-site cache: (track_idx, file, line, name) -> (profiler_id, block_idx)
_CALL_SITE_CACHE: Dict[Tuple[int, str, int, str], Tuple[int, int]] = {}

# Global profiler registry: profiler_id -> Profiler instance
_PROFILER_REGISTRY: Dict[int, "Profiler"] = {}
_NEXT_PROFILER_ID = 0


def set_global_enabled(enabled: bool) -> None:
    """
    Enable or disable profiling globally across all profiler instances.

    When disabled, decorators return identity functions (zero overhead).

    Args:
        enabled: True to enable profiling, False to disable
    """
    global _PROFILER_ENABLED
    _PROFILER_ENABLED = enabled


def is_global_enabled() -> bool:
    """Check if profiling is globally enabled."""
    return _PROFILER_ENABLED


class Profiler:
    """
    Main profiler class with multi-track support and runtime enable/disable.

    Example:
        profiler = Profiler("MyApp")

        @profiler.track(0, "process_data")
        def process_data(data):
            return transform(data)

        def complex_function():
            with profiler.block(1, "database_query"):
                result = query_database()
            return result

        results = profiler.get_results()
    """

    def __init__(self, name: str = "Profiler"):
        """
        Initialize a new profiler instance.

        Args:
            name: Human-readable name for this profiler
        """
        global _NEXT_PROFILER_ID
        self._profiler_id = _NEXT_PROFILER_ID
        _NEXT_PROFILER_ID += 1
        _PROFILER_REGISTRY[self._profiler_id] = self

        self._name = name
        self._tracks: Dict[int, ProfileTrack] = {}
        self._track_enabled: Dict[int, bool] = {}  # Per-track enable/disable
        self._next_block_idx: Dict[int, int] = {}  # Next block index per track
        self._started = True  # Profiler starts enabled by default

    def start(self) -> None:
        """Start profiling (resume data collection)."""
        self._started = True

    def stop(self) -> None:
        """Stop profiling (pause data collection)."""
        self._started = False

    def is_started(self) -> bool:
        """Check if profiler is started."""
        return self._started

    def set_track_enabled(self, track_idx: int, enabled: bool) -> None:
        """
        Enable or disable a specific track.

        Args:
            track_idx: Track index
            enabled: True to enable, False to disable
        """
        self._track_enabled[track_idx] = enabled

    def is_track_enabled(self, track_idx: int) -> bool:
        """
        Check if a specific track is enabled.

        Args:
            track_idx: Track index

        Returns:
            True if track is enabled (default: True)
        """
        return self._track_enabled.get(track_idx, True)

    def set_track_name(self, track_idx: int, name: str) -> None:
        """
        Set a human-readable name for a track.

        Args:
            track_idx: Track index
            name: Track name
        """
        track = self._get_or_create_track(track_idx)
        track.track_name = name

    def _get_or_create_track(self, track_idx: int) -> ProfileTrack:
        """Get or create a track by index."""
        if track_idx not in self._tracks:
            self._tracks[track_idx] = ProfileTrack(track_idx=track_idx)
            self._next_block_idx[track_idx] = 0
        return self._tracks[track_idx]

    def _register_block(
        self, track_idx: int, name: str, file: str, line: int
    ) -> int:
        """
        Register a new profiling block and return its index.

        Args:
            track_idx: Track index
            name: Block name
            file: Source file
            line: Line number

        Returns:
            Block index within the track
        """
        track = self._get_or_create_track(track_idx)
        block_idx = self._next_block_idx[track_idx]
        self._next_block_idx[track_idx] += 1

        track.add_block(block_idx, name, file, line)
        return block_idx

    def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int) -> None:
        """
        Record execution time for a block.

        Args:
            track_idx: Track index
            block_idx: Block index
            elapsed_ns: Elapsed time in nanoseconds
        """
        track = self._tracks.get(track_idx)
        if track is None:
            return

        block = track.get_block(block_idx)
        if block is not None:
            block.record_time(elapsed_ns)

    def get_results(self) -> ProfilerResults:
        """
        Get profiling results.

        Returns:
            ProfilerResults containing all tracks and blocks
        """
        results = ProfilerResults(profiler_name=self._name)
        results.tracks = self._tracks.copy()
        return results

    def clear(self) -> None:
        """Clear all profiling data."""
        self._tracks.clear()
        self._track_enabled.clear()
        self._next_block_idx.clear()

    def track(self, track_idx: int, name: Optional[str] = None) -> Callable:
        """
        Decorator for profiling functions.

        Example:
            @profiler.track(0, "process_data")
            def process_data(data):
                return transform(data)

            # Auto-detect function name
            @profiler.track(0)
            def compute():
                return result

        Args:
            track_idx: Track index for this function
            name: Optional name (defaults to function.__name__)

        Returns:
            Decorator function
        """
        # Level 1: Global enable/disable (zero overhead when disabled)
        if not _PROFILER_ENABLED:
            return lambda func: func  # Identity decorator - ZERO overhead

        def decorator(func: Callable) -> Callable:
            # Use function name if not provided
            block_name = name if name is not None else func.__name__

            # Get call-site information
            frame = inspect.currentframe()
            if frame and frame.f_back:
                file = frame.f_back.f_code.co_filename
                line = frame.f_back.f_lineno
            else:
                file = "<unknown>"
                line = 0

            # Check call-site cache
            cache_key = (track_idx, file, line, block_name)
            if cache_key in _CALL_SITE_CACHE:
                profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
            else:
                # Register block and cache
                block_idx = self._register_block(track_idx, block_name, file, line)
                _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

            # Store block_idx in function attribute for fast access
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Level 2: Per-track enable/disable (fast guard)
                if not self.is_track_enabled(track_idx):
                    return func(*args, **kwargs)

                # Level 3: Instance start/stop
                if not self._started:
                    return func(*args, **kwargs)

                # Profile the function
                start = get_time_ns()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    end = get_time_ns()
                    elapsed = end - start
                    self._record_block_time(track_idx, block_idx, elapsed)

            return wrapper

        return decorator

    @contextmanager
    def block(self, track_idx: int, name: str):
        """
        Context manager for profiling code blocks.

        Example:
            with profiler.block(1, "database_query"):
                result = query_database()

        Args:
            track_idx: Track index for this block
            name: Block name (required)

        Yields:
            None
        """
        # Level 1: Global enable/disable
        if not _PROFILER_ENABLED:
            yield
            return

        # Level 2: Per-track enable/disable
        if not self.is_track_enabled(track_idx):
            yield
            return

        # Level 3: Instance start/stop
        if not self._started:
            yield
            return

        # Get call-site information
        frame = inspect.currentframe()
        if frame and frame.f_back:
            file = frame.f_back.f_code.co_filename
            line = frame.f_back.f_lineno
        else:
            file = "<unknown>"
            line = 0

        # Check call-site cache
        cache_key = (track_idx, file, line, name)
        if cache_key in _CALL_SITE_CACHE:
            profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
        else:
            # Register block and cache
            block_idx = self._register_block(track_idx, name, file, line)
            _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

        # Profile the block
        start = get_time_ns()
        try:
            yield
        finally:
            end = get_time_ns()
            elapsed = end - start
            self._record_block_time(track_idx, block_idx, elapsed)

    def __repr__(self) -> str:
        return (
            f"Profiler(name={self._name!r}, tracks={len(self._tracks)}, "
            f"started={self._started})"
        )


def _get_profiler(profiler_id: int) -> Optional[Profiler]:
    """Get a profiler instance by ID from the global registry."""
    return _PROFILER_REGISTRY.get(profiler_id)

