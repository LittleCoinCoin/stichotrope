"""
Data structures for Stichotrope profiler.

Defines ProfileBlock, ProfileTrack, and ProfilerResults for organizing profiling data.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProfileBlock:
    """
    Represents a single profiled code block with accumulated timing statistics.

    Attributes:
        name: Human-readable name of the block
        file: Source file where block is defined
        line: Line number where block is defined
        hit_count: Number of times this block was executed
        total_time_ns: Total accumulated time in nanoseconds
        min_time_ns: Minimum execution time in nanoseconds
        max_time_ns: Maximum execution time in nanoseconds
    """

    name: str
    file: str
    line: int
    hit_count: int = 0
    total_time_ns: int = 0
    min_time_ns: int = 2**63 - 1  # Initialize to max int64
    max_time_ns: int = 0

    def record_time(self, elapsed_ns: int) -> None:
        """
        Record a single execution time for this block.

        Args:
            elapsed_ns: Elapsed time in nanoseconds
        """
        self.hit_count += 1
        self.total_time_ns += elapsed_ns
        self.min_time_ns = min(self.min_time_ns, elapsed_ns)
        self.max_time_ns = max(self.max_time_ns, elapsed_ns)

    @property
    def avg_time_ns(self) -> float:
        """Average execution time in nanoseconds."""
        return self.total_time_ns / self.hit_count if self.hit_count > 0 else 0.0

    def __repr__(self) -> str:
        return (
            f"ProfileBlock(name={self.name!r}, file={self.file!r}, line={self.line}, "
            f"hit_count={self.hit_count}, total_time_ns={self.total_time_ns}, "
            f"avg_time_ns={self.avg_time_ns:.0f}, min_time_ns={self.min_time_ns}, "
            f"max_time_ns={self.max_time_ns})"
        )


@dataclass
class ProfileTrack:
    """
    Represents a logical track containing multiple profiled blocks.

    Tracks provide logical grouping of profiling data (e.g., I/O, computation, database).

    Attributes:
        track_idx: Numeric index of this track
        track_name: Optional human-readable name
        enabled: Whether this track is currently enabled for profiling
        blocks: Dictionary mapping block_index -> ProfileBlock
    """

    track_idx: int
    track_name: Optional[str] = None
    enabled: bool = True
    blocks: dict[int, ProfileBlock] = field(default_factory=dict)

    def add_block(self, block_idx: int, name: str, file: str, line: int) -> ProfileBlock:
        """
        Add a new block to this track.

        Args:
            block_idx: Unique index for this block within the track
            name: Human-readable name
            file: Source file
            line: Line number

        Returns:
            The created ProfileBlock
        """
        block = ProfileBlock(name=name, file=file, line=line)
        self.blocks[block_idx] = block
        return block

    def get_block(self, block_idx: int) -> Optional[ProfileBlock]:
        """Get a block by index, or None if not found."""
        return self.blocks.get(block_idx)

    @property
    def total_time_ns(self) -> int:
        """Total time across all blocks in this track."""
        return sum(block.total_time_ns for block in self.blocks.values())

    @property
    def total_hits(self) -> int:
        """Total hit count across all blocks in this track."""
        return sum(block.hit_count for block in self.blocks.values())

    def __repr__(self) -> str:
        name_str = f" ({self.track_name!r})" if self.track_name else ""
        return (
            f"ProfileTrack(track_idx={self.track_idx}{name_str}, "
            f"enabled={self.enabled}, blocks={len(self.blocks)}, "
            f"total_time_ns={self.total_time_ns}, total_hits={self.total_hits})"
        )


@dataclass
class ProfilerResults:
    """
    Complete profiling results for a profiler instance.

    Attributes:
        profiler_name: Name of the profiler instance
        tracks: Dictionary mapping track_idx -> ProfileTrack
    """

    profiler_name: str
    tracks: dict[int, ProfileTrack] = field(default_factory=dict)

    @property
    def total_time_ns(self) -> int:
        """Total time across all tracks."""
        return sum(track.total_time_ns for track in self.tracks.values())

    @property
    def total_hits(self) -> int:
        """Total hit count across all tracks."""
        return sum(track.total_hits for track in self.tracks.values())

    def get_track(self, track_idx: int) -> Optional[ProfileTrack]:
        """Get a track by index, or None if not found."""
        return self.tracks.get(track_idx)

    def __repr__(self) -> str:
        return (
            f"ProfilerResults(profiler_name={self.profiler_name!r}, "
            f"tracks={len(self.tracks)}, total_time_ns={self.total_time_ns}, "
            f"total_hits={self.total_hits})"
        )
