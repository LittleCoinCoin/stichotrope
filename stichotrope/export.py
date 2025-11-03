"""
Export utilities for Stichotrope profiler results.

Provides CSV, JSON, and console output formats.
"""

import csv
import json
from io import StringIO
from typing import Any, Optional, TextIO

from stichotrope.types import ProfilerResults


def export_csv(results: ProfilerResults, file: Optional[TextIO] = None) -> str:
    """
    Export profiling results to CSV format matching CppProfiler.

    CSV Format:
        Track,Block Name,Hit Count,Total Time (ns),Avg Time (ns),Min Time (ns),Max Time (ns),% Track,% Total

    Args:
        results: ProfilerResults to export
        file: Optional file object to write to (if None, returns string)

    Returns:
        CSV string if file is None, otherwise empty string
    """
    output = StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(
        [
            "Track",
            "Block Name",
            "Hit Count",
            "Total Time (ns)",
            "Avg Time (ns)",
            "Min Time (ns)",
            "Max Time (ns)",
            "% Track",
            "% Total",
        ]
    )

    # Calculate total time across all tracks
    total_time_all = results.total_time_ns

    # Write data rows
    for track_idx in sorted(results.tracks.keys()):
        track = results.tracks[track_idx]
        track_total_time = track.total_time_ns

        for block_idx in sorted(track.blocks.keys()):
            block = track.blocks[block_idx]

            # Calculate percentages
            pct_track = (
                (block.total_time_ns / track_total_time * 100) if track_total_time > 0 else 0.0
            )
            pct_total = (block.total_time_ns / total_time_all * 100) if total_time_all > 0 else 0.0

            # Handle min_time_ns initialization value
            min_time = block.min_time_ns if block.hit_count > 0 else 0

            writer.writerow(
                [
                    track_idx,
                    block.name,
                    block.hit_count,
                    block.total_time_ns,
                    f"{block.avg_time_ns:.0f}",
                    min_time,
                    block.max_time_ns,
                    f"{pct_track:.2f}",
                    f"{pct_total:.2f}",
                ]
            )

    csv_str = output.getvalue()

    if file is not None:
        file.write(csv_str)
        return ""
    else:
        return csv_str


def export_json(results: ProfilerResults, file: Optional[TextIO] = None, indent: int = 2) -> str:
    """
    Export profiling results to JSON format.

    JSON Structure:
        {
            "profiler_name": "...",
            "tracks": [
                {
                    "track_idx": 0,
                    "track_name": "...",
                    "blocks": [
                        {
                            "name": "...",
                            "file": "...",
                            "line": 123,
                            "hit_count": 10,
                            "total_time_ns": 1000000,
                            "avg_time_ns": 100000.0,
                            "min_time_ns": 90000,
                            "max_time_ns": 110000
                        }
                    ]
                }
            ]
        }

    Args:
        results: ProfilerResults to export
        file: Optional file object to write to (if None, returns string)
        indent: JSON indentation level

    Returns:
        JSON string if file is None, otherwise empty string
    """
    data: dict[str, Any] = {"profiler_name": results.profiler_name, "tracks": []}

    for track_idx in sorted(results.tracks.keys()):
        track = results.tracks[track_idx]
        track_data: dict[str, Any] = {
            "track_idx": track.track_idx,
            "track_name": track.track_name,
            "enabled": track.enabled,
            "blocks": [],
        }

        for block_idx in sorted(track.blocks.keys()):
            block = track.blocks[block_idx]

            # Handle min_time_ns initialization value
            min_time = block.min_time_ns if block.hit_count > 0 else 0

            block_data = {
                "name": block.name,
                "file": block.file,
                "line": block.line,
                "hit_count": block.hit_count,
                "total_time_ns": block.total_time_ns,
                "avg_time_ns": block.avg_time_ns,
                "min_time_ns": min_time,
                "max_time_ns": block.max_time_ns,
            }
            track_data["blocks"].append(block_data)

        data["tracks"].append(track_data)

    json_str = json.dumps(data, indent=indent)

    if file is not None:
        file.write(json_str)
        return ""
    else:
        return json_str


def format_time_ns(time_ns: int) -> str:
    """
    Format nanoseconds to human-readable time units.

    Args:
        time_ns: Time in nanoseconds

    Returns:
        Formatted string (e.g., "1.23 ms", "456 μs", "789 ns")
    """
    if time_ns >= 1_000_000_000:  # >= 1 second
        return f"{time_ns / 1_000_000_000:.2f} s"
    elif time_ns >= 1_000_000:  # >= 1 millisecond
        return f"{time_ns / 1_000_000:.2f} ms"
    elif time_ns >= 1_000:  # >= 1 microsecond
        return f"{time_ns / 1_000:.2f} μs"
    else:
        return f"{time_ns} ns"


def print_results(results: ProfilerResults) -> None:
    """
    Print profiling results to console in a formatted table.

    Args:
        results: ProfilerResults to print
    """
    print("=" * 120)
    print(f"Profiler: {results.profiler_name}")
    print(f"Total Time: {format_time_ns(results.total_time_ns)}")
    print(f"Total Hits: {results.total_hits:,}")
    print("=" * 120)

    for track_idx in sorted(results.tracks.keys()):
        track = results.tracks[track_idx]
        track_name = track.track_name if track.track_name else f"Track {track_idx}"

        print(f"\n{track_name} (Track {track_idx})")
        print(f"  Total Time: {format_time_ns(track.total_time_ns)}")
        print(f"  Total Hits: {track.total_hits:,}")
        print("-" * 120)

        # Print header
        print(
            f"{'Block Name':<40} {'Hits':>10} {'Total':>15} {'Avg':>15} {'Min':>15} {'Max':>15} {'%Track':>8}"
        )
        print("-" * 120)

        # Print blocks
        for block_idx in sorted(track.blocks.keys()):
            block = track.blocks[block_idx]

            # Calculate percentage of track
            pct_track = (
                (block.total_time_ns / track.total_time_ns * 100)
                if track.total_time_ns > 0
                else 0.0
            )

            # Handle min_time_ns initialization value
            min_time = block.min_time_ns if block.hit_count > 0 else 0

            print(
                f"{block.name:<40} "
                f"{block.hit_count:>10,} "
                f"{format_time_ns(block.total_time_ns):>15} "
                f"{format_time_ns(int(block.avg_time_ns)):>15} "
                f"{format_time_ns(min_time):>15} "
                f"{format_time_ns(block.max_time_ns):>15} "
                f"{pct_track:>7.2f}%"
            )

    print("=" * 120)
