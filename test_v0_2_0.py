"""
Ad-hoc test for v0.2.0 instrumentation API.

Tests:
- @profiler.track() decorator
- profiler.block() context manager
- Three-level runtime control (global, per-track, instance)
- Call-site caching
- Auto-name detection
"""

from stichotrope import Profiler, set_global_enabled, is_global_enabled
import time


def test_decorator_basic():
    """Test basic decorator functionality."""
    print("Testing @profiler.track() decorator...")
    profiler = Profiler("DecoratorTest")

    @profiler.track(0, "test_function")
    def test_function():
        time.sleep(0.001)  # 1ms
        return 42

    # Call function multiple times
    for _ in range(5):
        result = test_function()
        assert result == 42

    # Check results
    results = profiler.get_results()
    track = results.get_track(0)
    assert track is not None
    assert len(track.blocks) == 1

    block = track.blocks[0]
    assert block.name == "test_function"
    assert block.hit_count == 5
    assert block.total_time_ns > 5_000_000  # At least 5ms total

    print(f"  ✓ Decorator works: {block}")


def test_decorator_auto_name():
    """Test decorator with auto-name detection."""
    print("Testing decorator auto-name detection...")
    profiler = Profiler("AutoNameTest")

    @profiler.track(0)  # No name provided
    def my_function():
        return "hello"

    result = my_function()
    assert result == "hello"

    # Check that function name was auto-detected
    results = profiler.get_results()
    track = results.get_track(0)
    block = track.blocks[0]
    assert block.name == "my_function"

    print(f"  ✓ Auto-name detection works: {block.name}")


def test_context_manager():
    """Test context manager functionality."""
    print("Testing profiler.block() context manager...")
    profiler = Profiler("ContextManagerTest")

    def complex_function():
        with profiler.block(0, "block_a"):
            time.sleep(0.001)  # 1ms

        with profiler.block(1, "block_b"):
            time.sleep(0.002)  # 2ms

        return "done"

    result = complex_function()
    assert result == "done"

    # Check results
    results = profiler.get_results()
    assert len(results.tracks) == 2

    track0 = results.get_track(0)
    track1 = results.get_track(1)

    assert track0.blocks[0].name == "block_a"
    assert track1.blocks[0].name == "block_b"
    assert track0.blocks[0].hit_count == 1
    assert track1.blocks[0].hit_count == 1

    print(f"  ✓ Context manager works")
    print(f"    Track 0: {track0.blocks[0]}")
    print(f"    Track 1: {track1.blocks[0]}")


def test_global_enable_disable():
    """Test global enable/disable (Level 1)."""
    print("Testing global enable/disable...")

    # Disable globally
    set_global_enabled(False)
    assert is_global_enabled() == False

    profiler = Profiler("GlobalDisabledTest")

    @profiler.track(0, "disabled_function")
    def disabled_function():
        return 42

    # Function should work but not be profiled
    result = disabled_function()
    assert result == 42

    results = profiler.get_results()
    assert len(results.tracks) == 0  # No profiling data

    # Re-enable globally
    set_global_enabled(True)
    assert is_global_enabled() == True

    profiler2 = Profiler("GlobalEnabledTest")

    @profiler2.track(0, "enabled_function")
    def enabled_function():
        return 99

    result = enabled_function()
    assert result == 99

    results2 = profiler2.get_results()
    assert len(results2.tracks) == 1  # Profiling data collected

    print("  ✓ Global enable/disable works")


def test_per_track_enable_disable():
    """Test per-track enable/disable (Level 2)."""
    print("Testing per-track enable/disable...")
    profiler = Profiler("PerTrackTest")

    @profiler.track(0, "track0_function")
    def track0_function():
        return "track0"

    @profiler.track(1, "track1_function")
    def track1_function():
        return "track1"

    # Disable track 1
    profiler.set_track_enabled(1, False)

    # Call both functions
    track0_function()
    track1_function()

    # Check results
    results = profiler.get_results()
    track0 = results.get_track(0)
    track1 = results.get_track(1)

    assert track0 is not None
    assert track0.blocks[0].hit_count == 1  # Track 0 profiled

    # Track 1 block is registered but should have 0 hits (disabled)
    assert track1 is not None
    assert track1.blocks[0].hit_count == 0  # No profiling data collected

    print("  ✓ Per-track enable/disable works")


def test_instance_start_stop():
    """Test instance start/stop (Level 3)."""
    print("Testing instance start/stop...")
    profiler = Profiler("StartStopTest")

    @profiler.track(0, "test_function")
    def test_function():
        return "result"

    # Call while started
    test_function()

    # Stop profiler
    profiler.stop()
    assert profiler.is_started() == False

    # Call while stopped (should not profile)
    test_function()

    # Restart profiler
    profiler.start()
    assert profiler.is_started() == True

    # Call while started again
    test_function()

    # Check results
    results = profiler.get_results()
    track = results.get_track(0)
    block = track.blocks[0]

    # Should have 2 hits (1st and 3rd calls), not 3
    assert block.hit_count == 2

    print(f"  ✓ Instance start/stop works (hit_count={block.hit_count})")


def test_multi_track_organization():
    """Test multi-track organization."""
    print("Testing multi-track organization...")
    profiler = Profiler("MultiTrackTest")

    # Set track names
    profiler.set_track_name(0, "Request Handling")
    profiler.set_track_name(1, "Database")
    profiler.set_track_name(2, "Business Logic")

    @profiler.track(0, "handle_request")
    def handle_request():
        with profiler.block(1, "query_db"):
            time.sleep(0.001)

        with profiler.block(2, "process_data"):
            time.sleep(0.001)

        return "done"

    handle_request()

    # Check results
    results = profiler.get_results()
    assert len(results.tracks) == 3

    track0 = results.get_track(0)
    track1 = results.get_track(1)
    track2 = results.get_track(2)

    assert track0.track_name == "Request Handling"
    assert track1.track_name == "Database"
    assert track2.track_name == "Business Logic"

    print("  ✓ Multi-track organization works")
    print(f"    {track0}")
    print(f"    {track1}")
    print(f"    {track2}")


def test_call_site_caching():
    """Test call-site caching."""
    print("Testing call-site caching...")
    profiler = Profiler("CachingTest")

    @profiler.track(0, "cached_function")
    def cached_function():
        return 42

    # Call multiple times - should use cached block index
    for _ in range(100):
        cached_function()

    results = profiler.get_results()
    track = results.get_track(0)

    # Should only have 1 block (cached)
    assert len(track.blocks) == 1
    assert track.blocks[0].hit_count == 100

    print(f"  ✓ Call-site caching works (100 calls -> 1 block)")


def main():
    """Run all tests."""
    print("=" * 60)
    print("v0.2.0 Instrumentation API Tests")
    print("=" * 60)

    test_decorator_basic()
    test_decorator_auto_name()
    test_context_manager()
    test_global_enable_disable()
    test_per_track_enable_disable()
    test_instance_start_stop()
    test_multi_track_organization()
    test_call_site_caching()

    print("=" * 60)
    print("✓ All v0.2.0 tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

