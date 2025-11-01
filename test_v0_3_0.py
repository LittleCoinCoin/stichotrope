"""
Ad-hoc test for v0.3.0 results export.

Tests:
- CSV export matching CppProfiler format
- JSON export with hierarchical structure
- Console pretty-print
- Format time utilities
"""

from stichotrope import Profiler, export_csv, export_json, print_results, format_time_ns
import time
import json
import csv


def create_sample_profiler():
    """Create a profiler with sample data for testing."""
    profiler = Profiler("ExportTest")

    # Set track names
    profiler.set_track_name(0, "Request Handling")
    profiler.set_track_name(1, "Database")
    profiler.set_track_name(2, "Business Logic")

    @profiler.track(0, "handle_request")
    def handle_request():
        with profiler.block(1, "query_users"):
            time.sleep(0.002)  # 2ms

        with profiler.block(1, "query_products"):
            time.sleep(0.003)  # 3ms

        with profiler.block(2, "process_data"):
            time.sleep(0.001)  # 1ms

        return "done"

    # Call multiple times
    for _ in range(5):
        handle_request()

    return profiler


def test_csv_export():
    """Test CSV export functionality."""
    print("Testing CSV export...")
    profiler = create_sample_profiler()

    # Export to file
    profiler.export_csv("test_output.csv")

    # Read and verify
    with open("test_output.csv", 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Should have 4 blocks (1 function + 3 context managers)
    assert len(rows) == 4

    # Check header columns
    expected_columns = [
        "Track", "Block Name", "Hit Count", "Total Time (ns)",
        "Avg Time (ns)", "Min Time (ns)", "Max Time (ns)", "% Track", "% Total"
    ]
    assert list(rows[0].keys()) == expected_columns

    # Check some data
    for row in rows:
        assert int(row["Hit Count"]) == 5
        assert float(row["% Track"]) >= 0.0
        assert float(row["% Total"]) >= 0.0

    print("  ✓ CSV export works")
    print(f"    Exported {len(rows)} blocks to test_output.csv")


def test_json_export():
    """Test JSON export functionality."""
    print("Testing JSON export...")
    profiler = create_sample_profiler()

    # Export to file
    profiler.export_json("test_output.json")

    # Read and verify
    with open("test_output.json", 'r') as f:
        data = json.load(f)

    # Check structure
    assert "profiler_name" in data
    assert data["profiler_name"] == "ExportTest"
    assert "tracks" in data
    assert len(data["tracks"]) == 3  # 3 tracks

    # Check track structure
    for track in data["tracks"]:
        assert "track_idx" in track
        assert "track_name" in track
        assert "blocks" in track

        # Check block structure
        for block in track["blocks"]:
            assert "name" in block
            assert "file" in block
            assert "line" in block
            assert "hit_count" in block
            assert "total_time_ns" in block
            assert "avg_time_ns" in block
            assert "min_time_ns" in block
            assert "max_time_ns" in block

    print("  ✓ JSON export works")
    print(f"    Exported {len(data['tracks'])} tracks to test_output.json")


def test_console_print():
    """Test console pretty-print functionality."""
    print("Testing console pretty-print...")
    profiler = create_sample_profiler()

    print("\n" + "=" * 60)
    print("Sample Console Output:")
    print("=" * 60)
    profiler.print_results()
    print("=" * 60)

    print("  ✓ Console pretty-print works")


def test_format_time_ns():
    """Test time formatting utility."""
    print("Testing format_time_ns...")

    # Test different time scales
    assert format_time_ns(500) == "500 ns"
    assert format_time_ns(1_500) == "1.50 μs"
    assert format_time_ns(1_500_000) == "1.50 ms"
    assert format_time_ns(1_500_000_000) == "1.50 s"

    print("  ✓ format_time_ns works")
    print(f"    500 ns -> {format_time_ns(500)}")
    print(f"    1,500 ns -> {format_time_ns(1_500)}")
    print(f"    1,500,000 ns -> {format_time_ns(1_500_000)}")
    print(f"    1,500,000,000 ns -> {format_time_ns(1_500_000_000)}")


def test_export_api():
    """Test export API functions."""
    print("Testing export API functions...")
    profiler = create_sample_profiler()
    results = profiler.get_results()

    # Test export_csv
    csv_str = export_csv(results)
    assert "Track,Block Name,Hit Count" in csv_str
    assert len(csv_str.split('\n')) > 1  # Header + data rows

    # Test export_json
    json_str = export_json(results)
    data = json.loads(json_str)
    assert data["profiler_name"] == "ExportTest"
    assert len(data["tracks"]) == 3

    print("  ✓ Export API functions work")


def test_csv_format_matches_cpprofiler():
    """Test that CSV format matches CppProfiler."""
    print("Testing CSV format matches CppProfiler...")
    profiler = create_sample_profiler()

    # Export to string
    results = profiler.get_results()
    csv_str = export_csv(results)

    # Parse CSV
    lines = csv_str.strip().split('\n')
    header = lines[0]

    # Check header matches CppProfiler format
    expected_header = "Track,Block Name,Hit Count,Total Time (ns),Avg Time (ns),Min Time (ns),Max Time (ns),% Track,% Total"
    assert header == expected_header

    # Check data rows have correct number of columns
    for line in lines[1:]:
        columns = line.split(',')
        # Note: Block names might contain commas, so we check minimum columns
        assert len(columns) >= 9

    print("  ✓ CSV format matches CppProfiler")


def main():
    """Run all tests."""
    print("=" * 60)
    print("v0.3.0 Results Export Tests")
    print("=" * 60)

    test_csv_export()
    test_json_export()
    test_console_print()
    test_format_time_ns()
    test_export_api()
    test_csv_format_matches_cpprofiler()

    print("=" * 60)
    print("✓ All v0.3.0 tests passed!")
    print("=" * 60)

    # Cleanup
    import os
    if os.path.exists("test_output.csv"):
        os.remove("test_output.csv")
    if os.path.exists("test_output.json"):
        os.remove("test_output.json")


if __name__ == "__main__":
    main()

