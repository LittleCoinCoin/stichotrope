"""
Ad-hoc test for v0.1.0 core infrastructure.

Tests:
- ProfileBlock data structure
- ProfileTrack data structure
- Profiler class with multi-track support
- Timing mechanism
- Call-site caching
- Profiler lifecycle
"""

from stichotrope import Profiler, ProfileBlock, ProfileTrack, ProfilerResults
from stichotrope.timing import get_time_ns, measure_timing_overhead
import time


def test_profile_block():
    """Test ProfileBlock data structure."""
    print("Testing ProfileBlock...")
    block = ProfileBlock(name="test_block", file="test.py", line=10)

    # Record some times
    block.record_time(1000)
    block.record_time(2000)
    block.record_time(1500)

    assert block.hit_count == 3
    assert block.total_time_ns == 4500
    assert block.min_time_ns == 1000
    assert block.max_time_ns == 2000
    assert block.avg_time_ns == 1500.0

    print(f"  ✓ ProfileBlock: {block}")


def test_profile_track():
    """Test ProfileTrack data structure."""
    print("Testing ProfileTrack...")
    track = ProfileTrack(track_idx=0, track_name="Test Track")

    # Add blocks
    block1 = track.add_block(0, "block1", "test.py", 10)
    block2 = track.add_block(1, "block2", "test.py", 20)

    # Record times
    block1.record_time(1000)
    block2.record_time(2000)

    assert len(track.blocks) == 2
    assert track.total_time_ns == 3000
    assert track.total_hits == 2

    print(f"  ✓ ProfileTrack: {track}")


def test_profiler_basic():
    """Test basic Profiler functionality."""
    print("Testing Profiler basic functionality...")
    profiler = Profiler("TestProfiler")

    # Register blocks
    block_idx_0 = profiler._register_block(0, "block_a", "test.py", 10)
    block_idx_1 = profiler._register_block(0, "block_b", "test.py", 20)
    block_idx_2 = profiler._register_block(1, "block_c", "test.py", 30)

    # Record times
    profiler._record_block_time(0, block_idx_0, 1000)
    profiler._record_block_time(0, block_idx_1, 2000)
    profiler._record_block_time(1, block_idx_2, 3000)

    # Get results
    results = profiler.get_results()
    assert len(results.tracks) == 2
    assert results.total_time_ns == 6000
    assert results.total_hits == 3

    print(f"  ✓ Profiler: {profiler}")
    print(f"  ✓ Results: {results}")


def test_profiler_lifecycle():
    """Test Profiler start/stop lifecycle."""
    print("Testing Profiler lifecycle...")
    profiler = Profiler("LifecycleTest")

    assert profiler.is_started() == True

    profiler.stop()
    assert profiler.is_started() == False

    profiler.start()
    assert profiler.is_started() == True

    print("  ✓ Profiler lifecycle works")


def test_track_enable_disable():
    """Test per-track enable/disable."""
    print("Testing per-track enable/disable...")
    profiler = Profiler("TrackEnableTest")

    # Set track names
    profiler.set_track_name(0, "Track 0")
    profiler.set_track_name(1, "Track 1")

    # Check default enabled
    assert profiler.is_track_enabled(0) == True
    assert profiler.is_track_enabled(1) == True

    # Disable track 1
    profiler.set_track_enabled(1, False)
    assert profiler.is_track_enabled(0) == True
    assert profiler.is_track_enabled(1) == False

    print("  ✓ Per-track enable/disable works")


def test_timing_mechanism():
    """Test timing mechanism."""
    print("Testing timing mechanism...")

    # Measure timing overhead
    overhead = measure_timing_overhead(iterations=10000)
    print(f"  Timing overhead: ~{overhead:.0f} ns per call")

    # Test basic timing
    start = get_time_ns()
    time.sleep(0.001)  # 1ms
    end = get_time_ns()
    elapsed = end - start

    # Should be approximately 1ms (1,000,000 ns)
    assert 900_000 < elapsed < 1_100_000, f"Expected ~1ms, got {elapsed}ns"

    print(f"  ✓ Timing mechanism works (1ms sleep = {elapsed:,} ns)")


def test_profiler_results():
    """Test ProfilerResults data structure."""
    print("Testing ProfilerResults...")
    results = ProfilerResults(profiler_name="TestResults")

    # Add tracks
    track0 = ProfileTrack(track_idx=0, track_name="Track 0")
    track1 = ProfileTrack(track_idx=1, track_name="Track 1")

    track0.add_block(0, "block_a", "test.py", 10).record_time(1000)
    track1.add_block(0, "block_b", "test.py", 20).record_time(2000)

    results.tracks[0] = track0
    results.tracks[1] = track1

    assert results.total_time_ns == 3000
    assert results.total_hits == 2

    print(f"  ✓ ProfilerResults: {results}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("v0.1.0 Core Infrastructure Tests")
    print("=" * 60)

    test_profile_block()
    test_profile_track()
    test_profiler_basic()
    test_profiler_lifecycle()
    test_track_enable_disable()
    test_timing_mechanism()
    test_profiler_results()

    print("=" * 60)
    print("✓ All v0.1.0 tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

