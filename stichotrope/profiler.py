"""
Core Profiler implementation for Stichotrope.

Provides the main Profiler class with multi-track support, runtime enable/disable,
and call-site caching.
"""

import functools
import inspect
import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, Callable, Optional

from stichotrope.timing import get_time_ns
from stichotrope.types import ProfilerResults, ProfileTrack

# Global enable/disable flag (module-level)
_PROFILER_ENABLED = True

# Global call-site cache: (track_idx, file, line, name) -> (profiler_id, block_idx)
_CALL_SITE_CACHE: dict[tuple[int, str, int, str], tuple[int, int]] = {}
_GLOBAL_CACHE_LOCK = threading.RLock()

# Global profiler registry: profiler_id -> Profiler instance
_PROFILER_REGISTRY: dict[int, "Profiler"] = {}
_NEXT_PROFILER_ID = 0
_REGISTRY_LOCK = threading.RLock()


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

        # Register profiler with lock protection
        with _REGISTRY_LOCK:
            self._profiler_id = _NEXT_PROFILER_ID
            _NEXT_PROFILER_ID += 1
            _PROFILER_REGISTRY[self._profiler_id] = self

        self._name = name

        # Thread-local storage for per-thread profiling data
        self._thread_local = threading.local()

        # Global lock protects _all_thread_data registry
        self._global_lock = threading.RLock()

        # Registry of all thread-local data: thread_id -> thread_local
        self._all_thread_data: dict[int, Any] = {}

        # Instance enable/disable flag
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

    def _get_thread_data(self) -> Any:
        """
        Get or initialize thread-local data for the current thread.

        Uses hasattr pattern to avoid AttributeError on first access.
        Registers thread in global registry on first access.
        Caches thread_data reference in thread-local storage for fast access.

        Returns:
            Thread-local data object with tracks, track_enabled, next_block_idx
        """
        if not hasattr(self._thread_local, 'data'):
            # First access from this thread - initialize thread-local storage
            thread_id = threading.get_ident()
            thread_name = threading.current_thread().name

            # Register thread in global registry (LOCK REQUIRED)
            # Create a data object to hold this thread's profiling data
            with self._global_lock:
                if thread_id not in self._all_thread_data:
                    # Create a simple object to hold thread data
                    class ThreadData:
                        pass

                    thread_data = ThreadData()
                    thread_data.tracks = {}
                    thread_data.track_enabled = {}
                    thread_data.next_block_idx = {}
                    thread_data.thread_id = thread_id
                    thread_data.thread_name = thread_name

                    self._all_thread_data[thread_id] = thread_data

                else:
                    # Thread was already registered (e.g., after clear())
                    thread_data = self._all_thread_data[thread_id]

            # Cache thread_data reference in thread-local storage for fast access
            # This eliminates dict lookup on every _get_thread_data() call
            self._thread_local.data = thread_data

        # Return cached thread_data reference (fast - no dict lookup)
        return self._thread_local.data

    def set_track_enabled(self, track_idx: int, enabled: bool) -> None:
        """
        Enable or disable a specific track.

        Args:
            track_idx: Track index
            enabled: True to enable, False to disable
        """
        thread_data = self._get_thread_data()
        thread_data.track_enabled[track_idx] = enabled

    def is_track_enabled(self, track_idx: int) -> bool:
        """
        Check if a specific track is enabled.

        Args:
            track_idx: Track index

        Returns:
            True if track is enabled (default: True)
        """
        thread_data = self._get_thread_data()
        return thread_data.track_enabled.get(track_idx, True)

    def set_track_name(self, track_idx: int, name: str) -> None:
        """
        Set a human-readable name for a track.

        Args:
            track_idx: Track index
            name: Track name
        """
        thread_data = self._get_thread_data()
        track = self._get_or_create_track(thread_data, track_idx)
        track.track_name = name

    def _get_or_create_track(self, thread_data: Any, track_idx: int) -> ProfileTrack:
        """
        Get or create a track by index in thread-local storage.

        Args:
            thread_data: Thread-local data object
            track_idx: Track index

        Returns:
            ProfileTrack instance
        """
        if track_idx not in thread_data.tracks:
            thread_data.tracks[track_idx] = ProfileTrack(track_idx=track_idx)
            thread_data.next_block_idx[track_idx] = 0
        return thread_data.tracks[track_idx]

    def _register_block(self, thread_data: Any, track_idx: int, name: str, file: str, line: int) -> int:
        """
        Register a new profiling block and return its index.

        Args:
            thread_data: Thread-local data object
            track_idx: Track index
            name: Block name
            file: Source file
            line: Line number

        Returns:
            Block index within the track
        """
        track = self._get_or_create_track(thread_data, track_idx)
        block_idx = thread_data.next_block_idx[track_idx]
        thread_data.next_block_idx[track_idx] += 1

        track.add_block(block_idx, name, file, line)
        return block_idx

    def _record_block_time(self, track_idx: int, block_idx: int, elapsed_ns: int) -> None:
        """
        Record execution time for a block.

        HOT PATH - NO LOCKS. Uses thread-local data only.

        Args:
            track_idx: Track index
            block_idx: Block index
            elapsed_ns: Elapsed time in nanoseconds
        """
        thread_data = self._get_thread_data()
        track = thread_data.tracks.get(track_idx)
        if track is None:
            return

        block = track.get_block(block_idx)
        if block is not None:
            block.record_time(elapsed_ns)

    def _aggregate_results(self) -> ProfilerResults:
        """
        Aggregate profiling data from all threads.

        Uses sequential merge algorithm (GIL-friendly).
        Acquires _global_lock to safely iterate _all_thread_data.

        Returns:
            ProfilerResults with aggregated data from all threads
        """
        aggregated_tracks: dict[int, ProfileTrack] = {}

        # Acquire lock to safely iterate all thread data
        with self._global_lock:
            # Iterate all threads and merge their data
            for thread_id, thread_local in self._all_thread_data.items():
                # Merge each track from this thread
                for track_idx, source_track in thread_local.tracks.items():
                    # Get or create aggregated track
                    if track_idx not in aggregated_tracks:
                        aggregated_tracks[track_idx] = ProfileTrack(
                            track_idx=track_idx,
                            track_name=source_track.track_name
                        )

                    aggregated_track = aggregated_tracks[track_idx]

                    # Merge all blocks from source track
                    for block_idx, source_block in source_track.blocks.items():
                        self._merge_block(aggregated_track, block_idx, source_block)

        results = ProfilerResults(profiler_name=self._name)
        results.tracks = aggregated_tracks
        return results

    def _merge_block(self, aggregated_track: ProfileTrack, block_idx: int, source_block: Any) -> None:
        """
        Merge a source block into the aggregated track.

        Args:
            aggregated_track: Target track for aggregation
            block_idx: Block index
            source_block: Source ProfileBlock to merge
        """
        if block_idx not in aggregated_track.blocks:
            # First occurrence of this block - add it
            aggregated_track.add_block(
                block_idx,
                source_block.name,
                source_block.file,
                source_block.line
            )
            target_block = aggregated_track.blocks[block_idx]
            target_block.hit_count = source_block.hit_count
            target_block.total_time_ns = source_block.total_time_ns
            target_block.min_time_ns = source_block.min_time_ns
            target_block.max_time_ns = source_block.max_time_ns
        else:
            # Block already exists - merge statistics
            target_block = aggregated_track.blocks[block_idx]
            target_block.hit_count += source_block.hit_count
            target_block.total_time_ns += source_block.total_time_ns
            target_block.min_time_ns = min(target_block.min_time_ns, source_block.min_time_ns)
            target_block.max_time_ns = max(target_block.max_time_ns, source_block.max_time_ns)

    def get_results(self) -> ProfilerResults:
        """
        Get profiling results aggregated from all threads.

        Returns:
            ProfilerResults containing all tracks and blocks from all threads
        """
        return self._aggregate_results()

    def clear(self) -> None:
        """Clear all profiling data from all threads."""
        # Clear global thread data registry
        with self._global_lock:
            self._all_thread_data.clear()

        # Invalidate cached thread_data reference in current thread
        # This ensures the thread re-initializes on next access
        if hasattr(self._thread_local, 'data'):
            delattr(self._thread_local, 'data')

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

            # Check call-site cache with lock protection
            # We only cache the block_idx here, not register the block yet
            # Block registration happens in each thread when wrapper is first executed
            cache_key = (track_idx, file, line, block_name)
            block_idx_container = [None]  # Use list to allow modification in wrapper

            with _GLOBAL_CACHE_LOCK:
                if cache_key in _CALL_SITE_CACHE:
                    profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
                    block_idx_container[0] = block_idx
                else:
                    # Allocate a block_idx without registering the block yet
                    # We'll use a counter to allocate unique block indices
                    # For now, use the cache size as the block_idx
                    block_idx = len(_CALL_SITE_CACHE)
                    _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)
                    block_idx_container[0] = block_idx

            # Store block_idx in function attribute for fast access
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                # Level 2: Per-track enable/disable (fast guard)
                if not self.is_track_enabled(track_idx):
                    return func(*args, **kwargs)

                # Level 3: Instance start/stop
                if not self._started:
                    return func(*args, **kwargs)

                # Get the cached block_idx
                block_idx = block_idx_container[0]

                # Ensure block exists in current thread's storage
                thread_data = self._get_thread_data()
                track = thread_data.tracks.get(track_idx)
                if track is None or block_idx not in track.blocks:
                    # Block not yet registered in this thread - register it
                    track = self._get_or_create_track(thread_data, track_idx)
                    if block_idx not in track.blocks:
                        track.add_block(block_idx, block_name, file, line)

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
    def block(self, track_idx: int, name: str) -> Generator[None, None, None]:
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

        # Check call-site cache with lock protection
        # We only cache the block_idx here, not register the block yet
        cache_key = (track_idx, file, line, name)
        with _GLOBAL_CACHE_LOCK:
            if cache_key in _CALL_SITE_CACHE:
                profiler_id, block_idx = _CALL_SITE_CACHE[cache_key]
            else:
                # Allocate a block_idx without registering the block yet
                block_idx = len(_CALL_SITE_CACHE)
                _CALL_SITE_CACHE[cache_key] = (self._profiler_id, block_idx)

        # Ensure block exists in current thread's storage
        thread_data = self._get_thread_data()
        track = thread_data.tracks.get(track_idx)
        if track is None or block_idx not in track.blocks:
            # Block not yet registered in this thread - register it
            track = self._get_or_create_track(thread_data, track_idx)
            if block_idx not in track.blocks:
                track.add_block(block_idx, name, file, line)

        # Profile the block
        start = get_time_ns()
        try:
            yield
        finally:
            end = get_time_ns()
            elapsed = end - start
            self._record_block_time(track_idx, block_idx, elapsed)

    def export_csv(self, filename: str) -> None:
        """
        Export profiling results to CSV file.

        Args:
            filename: Output CSV filename
        """
        from stichotrope.export import export_csv

        results = self.get_results()
        with open(filename, "w", newline="") as f:
            export_csv(results, f)

    def export_json(self, filename: str, indent: int = 2) -> None:
        """
        Export profiling results to JSON file.

        Args:
            filename: Output JSON filename
            indent: JSON indentation level
        """
        from stichotrope.export import export_json

        results = self.get_results()
        with open(filename, "w") as f:
            export_json(results, f, indent=indent)

    def print_results(self) -> None:
        """Print profiling results to console in a formatted table."""
        from stichotrope.export import print_results

        results = self.get_results()
        print_results(results)

    def __repr__(self) -> str:
        # Count unique tracks across all threads
        track_indices = set()
        thread_count = 0

        with self._global_lock:
            thread_count = len(self._all_thread_data)
            for thread_data in self._all_thread_data.values():
                track_indices.update(thread_data.tracks.keys())

        return (
            f"Profiler(name={self._name!r}, tracks={len(track_indices)}, "
            f"threads={thread_count}, started={self._started})"
        )


def _get_profiler(profiler_id: int) -> Optional[Profiler]:
    """Get a profiler instance by ID from the global registry."""
    return _PROFILER_REGISTRY.get(profiler_id)
