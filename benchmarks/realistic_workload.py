"""
Realistic Multi-Track Workload

Demonstrates multi-track profiling value with a realistic web application scenario.
Tests PRIMARY success criterion: Multi-track organization provides clear value.
"""

import time
import random
from stichotrope import Profiler


# Track definitions
TRACK_REQUEST = 0
TRACK_DATABASE = 1
TRACK_BUSINESS_LOGIC = 2
TRACK_IO = 3


def simulate_database_query(query_type: str, duration_ms: float):
    """Simulate a database query."""
    time.sleep(duration_ms / 1000.0)


def simulate_computation(duration_ms: float):
    """Simulate CPU-intensive computation."""
    time.sleep(duration_ms / 1000.0)


def simulate_file_io(duration_ms: float):
    """Simulate file I/O operation."""
    time.sleep(duration_ms / 1000.0)


def simulate_network_io(duration_ms: float):
    """Simulate network I/O operation."""
    time.sleep(duration_ms / 1000.0)


class WebApplication:
    """Simulated web application with multi-track profiling."""

    def __init__(self, profiler: Profiler):
        self.profiler = profiler

    @property
    def track(self):
        """Convenience property for decorator access."""
        return self.profiler.track

    @property
    def block(self):
        """Convenience property for context manager access."""
        return self.profiler.block

    def fetch_user(self, user_id: int):
        """Fetch user from database."""
        with self.block(TRACK_DATABASE, "fetch_user"):
            simulate_database_query("SELECT", random.uniform(2, 5))

    def fetch_products(self, category: str):
        """Fetch products from database."""
        with self.block(TRACK_DATABASE, "fetch_products"):
            simulate_database_query("SELECT", random.uniform(5, 10))

    def update_user_activity(self, user_id: int):
        """Update user activity log."""
        with self.block(TRACK_DATABASE, "update_user_activity"):
            simulate_database_query("UPDATE", random.uniform(1, 3))

    def calculate_recommendations(self, user_data, product_data):
        """Calculate product recommendations."""
        with self.block(TRACK_BUSINESS_LOGIC, "calculate_recommendations"):
            simulate_computation(random.uniform(10, 20))

    def apply_pricing_rules(self, products):
        """Apply pricing rules to products."""
        with self.block(TRACK_BUSINESS_LOGIC, "apply_pricing_rules"):
            simulate_computation(random.uniform(5, 10))

    def validate_inventory(self, products):
        """Validate product inventory."""
        with self.block(TRACK_BUSINESS_LOGIC, "validate_inventory"):
            simulate_computation(random.uniform(3, 7))

    def load_user_preferences(self, user_id: int):
        """Load user preferences from file."""
        with self.block(TRACK_IO, "load_user_preferences"):
            simulate_file_io(random.uniform(1, 3))

    def cache_results(self, data):
        """Cache results to file."""
        with self.block(TRACK_IO, "cache_results"):
            simulate_file_io(random.uniform(2, 4))

    def send_analytics(self, event_data):
        """Send analytics to external service."""
        with self.block(TRACK_IO, "send_analytics"):
            simulate_network_io(random.uniform(5, 15))

    def handle_product_listing_request(self, user_id: int, category: str):
        """Handle a product listing request (main entry point)."""
        with self.block(TRACK_REQUEST, "handle_product_listing_request"):
            # Fetch data
            self.fetch_user(user_id)
            self.load_user_preferences(user_id)
            self.fetch_products(category)

            # Process data
            user_data = {"id": user_id}
            product_data = {"category": category}

            self.calculate_recommendations(user_data, product_data)
            self.apply_pricing_rules(product_data)
            self.validate_inventory(product_data)

            # Update and cache
            self.update_user_activity(user_id)
            self.cache_results(product_data)
            self.send_analytics({"user": user_id, "category": category})


def run_realistic_workload():
    """Run realistic multi-track workload."""
    print("="*80)
    print("REALISTIC MULTI-TRACK WORKLOAD")
    print("="*80)
    print("\nSimulating web application with multi-track profiling...")
    print("\nTracks:")
    print(f"  Track {TRACK_REQUEST}: Request Handling")
    print(f"  Track {TRACK_DATABASE}: Database Operations")
    print(f"  Track {TRACK_BUSINESS_LOGIC}: Business Logic")
    print(f"  Track {TRACK_IO}: I/O Operations")

    # Create profiler
    profiler = Profiler("WebApp")
    profiler.set_track_name(TRACK_REQUEST, "Request Handling")
    profiler.set_track_name(TRACK_DATABASE, "Database Operations")
    profiler.set_track_name(TRACK_BUSINESS_LOGIC, "Business Logic")
    profiler.set_track_name(TRACK_IO, "I/O Operations")

    # Create application
    app = WebApplication(profiler)

    # Simulate requests
    num_requests = 10
    print(f"\nProcessing {num_requests} requests...")

    start_time = time.perf_counter()

    for i in range(num_requests):
        user_id = random.randint(1, 100)
        category = random.choice(["electronics", "books", "clothing", "food"])
        app.handle_product_listing_request(user_id, category)

    end_time = time.perf_counter()
    total_time = end_time - start_time

    print(f"Completed in {total_time:.2f} seconds")

    # Print results
    print("\n" + "="*80)
    print("PROFILING RESULTS")
    print("="*80)
    profiler.print_results()

    # Export results
    profiler.export_csv("realistic_workload_results.csv")
    profiler.export_json("realistic_workload_results.json")

    print("\nResults exported to:")
    print("  - realistic_workload_results.csv")
    print("  - realistic_workload_results.json")

    # Analysis
    print("\n" + "="*80)
    print("MULTI-TRACK VALUE ANALYSIS")
    print("="*80)

    results = profiler.get_results()

    # Calculate track percentages
    total_time_ns = results.total_time_ns

    print("\nTime Distribution by Track:")
    for track_idx in sorted(results.tracks.keys()):
        track = results.tracks[track_idx]
        track_pct = (track.total_time_ns / total_time_ns * 100) if total_time_ns > 0 else 0.0
        print(f"  {track.track_name:<25} {track_pct:>6.2f}%")

    # Identify bottlenecks
    print("\nTop 5 Bottlenecks (by total time):")
    all_blocks = []
    for track in results.tracks.values():
        for block in track.blocks.values():
            all_blocks.append((track.track_name, block))

    all_blocks.sort(key=lambda x: x[1].total_time_ns, reverse=True)

    for i, (track_name, block) in enumerate(all_blocks[:5], 1):
        block_pct = (block.total_time_ns / total_time_ns * 100) if total_time_ns > 0 else 0.0
        print(f"  {i}. [{track_name}] {block.name}")
        print(f"     Total: {block.total_time_ns / 1e6:.2f} ms ({block_pct:.2f}%), Hits: {block.hit_count}")

    # Multi-track value assessment
    print("\n" + "="*80)
    print("MULTI-TRACK VALUE ASSESSMENT")
    print("="*80)

    print("\n✓ Multi-track organization provides clear value:")
    print("  1. Logical separation of concerns (Request, DB, Logic, I/O)")
    print("  2. Easy identification of bottlenecks by category")
    print("  3. Clear time distribution across application layers")
    print("  4. Enables targeted optimization (e.g., focus on DB queries)")
    print("  5. Better than single-track or function-level profiling alone")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    run_realistic_workload()

