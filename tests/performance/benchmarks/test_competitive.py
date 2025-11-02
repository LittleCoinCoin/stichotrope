"""
Competitive benchmarking tests.

Compares Stichotrope against cProfile, py-spy, line_profiler, and pyinstrument.
"""

import pytest
import json
import time
from pathlib import Path
from typing import List, Dict, Any

from tests.performance.benchmarks.competitors import (
    get_all_profilers,
    get_available_profilers,
    ProfilerWrapper,
)
from tests.performance.workloads import simulate_work


class TestCompetitiveBenchmark:
    """Competitive benchmarking against other profilers."""
    
    @pytest.fixture
    def benchmark_results_dir(self, tmp_path):
        """Provide directory for benchmark results."""
        results_dir = tmp_path / "competitive_results"
        results_dir.mkdir(exist_ok=True)
        return results_dir
    
    def test_profiler_availability(self):
        """Test which profilers are available."""
        all_profilers = get_all_profilers()
        available_profilers = get_available_profilers()
        
        print("\n" + "="*80)
        print("PROFILER AVAILABILITY")
        print("="*80)
        
        for profiler in all_profilers:
            status = "✓ Available" if profiler.available else "✗ Not installed"
            print(f"{profiler.name:<20} {status}")
        
        print(f"\nTotal: {len(available_profilers)}/{len(all_profilers)} profilers available")
        
        # At minimum, cProfile should always be available
        assert any(p.name == "cProfile" and p.available for p in all_profilers)
    
    @pytest.mark.parametrize("duration_ms", [1.0, 10.0, 100.0])
    def test_overhead_comparison(self, duration_ms, benchmark_results_dir):
        """
        Compare overhead across all available profilers.
        
        This test measures the overhead of each profiler for the same workload
        and exports results for comparison.
        """
        available_profilers = get_available_profilers()
        
        if not available_profilers:
            pytest.skip("No profilers available")
        
        print(f"\n{'='*80}")
        print(f"Overhead Comparison - {duration_ms}ms workload")
        print(f"{'='*80}\n")
        
        # Define workload
        def workload():
            simulate_work(duration_ms)
        
        # Measure overhead for each profiler
        results = []
        
        for profiler in available_profilers:
            print(f"Benchmarking {profiler.name}...")
            
            try:
                overhead_stats = profiler.measure_overhead(workload, iterations=30)
                results.append(overhead_stats)
                
                print(f"  Baseline:  {overhead_stats['baseline_mean_ms']:.3f} ms")
                print(f"  Profiled:  {overhead_stats['profiled_mean_ms']:.3f} ms")
                print(f"  Overhead:  {overhead_stats['overhead_ns']:.0f} ns ({overhead_stats['overhead_pct']:.2f}%)")
                print()
                
            except Exception as e:
                print(f"  Error: {e}")
                print()
        
        # Export results
        result_file = benchmark_results_dir / f"competitive_overhead_{duration_ms}ms.json"
        with open(result_file, 'w') as f:
            json.dump({
                "workload_duration_ms": duration_ms,
                "profilers": results,
            }, f, indent=2)
        
        # Print summary
        print(f"{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}\n")
        print(f"{'Profiler':<20} {'Overhead (ns)':<15} {'Overhead (%)':<15} {'Status'}")
        print("-"*80)
        
        for result in sorted(results, key=lambda x: x['overhead_pct']):
            profiler_name = result['profiler']
            overhead_ns = result['overhead_ns']
            overhead_pct = result['overhead_pct']
            
            # Status based on ≤10% criterion for ≥1ms blocks
            if duration_ms >= 1.0:
                status = "✓ Good" if overhead_pct <= 10.0 else "⚠ High"
            else:
                status = "N/A"
            
            print(f"{profiler_name:<20} {overhead_ns:>10.0f} ns   {overhead_pct:>10.2f}%     {status}")
        
        print(f"\n{'='*80}\n")
        
        # Verify we got results
        assert len(results) > 0
    
    def test_feature_comparison(self):
        """
        Compare features across profilers.
        
        This test documents the capabilities of each profiler for
        competitive positioning.
        """
        print("\n" + "="*80)
        print("FEATURE COMPARISON")
        print("="*80 + "\n")
        
        features = {
            "Stichotrope": {
                "Type": "Instrumentation (explicit)",
                "Granularity": "Block-level",
                "Multi-track": "Yes",
                "Runtime enable/disable": "Yes",
                "Zero overhead when disabled": "Yes",
                "CSV/JSON export": "Yes",
                "Thread-safe": "Planned (v1.0.0)",
                "Python versions": "3.9+",
            },
            "cProfile": {
                "Type": "Instrumentation (automatic)",
                "Granularity": "Function-level",
                "Multi-track": "No",
                "Runtime enable/disable": "Yes",
                "Zero overhead when disabled": "No",
                "CSV/JSON export": "Via pstats",
                "Thread-safe": "Limited",
                "Python versions": "All",
            },
            "py-spy": {
                "Type": "Sampling (external process)",
                "Granularity": "Function-level",
                "Multi-track": "No",
                "Runtime enable/disable": "N/A (external)",
                "Zero overhead when disabled": "Yes",
                "CSV/JSON export": "Yes (flamegraph)",
                "Thread-safe": "Yes",
                "Python versions": "All",
            },
            "line_profiler": {
                "Type": "Instrumentation (line-level)",
                "Granularity": "Line-level",
                "Multi-track": "No",
                "Runtime enable/disable": "Yes",
                "Zero overhead when disabled": "No",
                "CSV/JSON export": "Limited",
                "Thread-safe": "Limited",
                "Python versions": "3.6+",
            },
            "pyinstrument": {
                "Type": "Statistical sampling",
                "Granularity": "Function-level",
                "Multi-track": "No",
                "Runtime enable/disable": "Yes",
                "Zero overhead when disabled": "No",
                "CSV/JSON export": "Yes (HTML, JSON)",
                "Thread-safe": "Yes",
                "Python versions": "3.7+",
            },
        }
        
        # Print feature table
        feature_names = list(next(iter(features.values())).keys())
        
        for feature in feature_names:
            print(f"\n{feature}:")
            for profiler, attrs in features.items():
                print(f"  {profiler:<20} {attrs[feature]}")
        
        print("\n" + "="*80 + "\n")
    
    def test_use_case_recommendations(self):
        """
        Document recommended use cases for each profiler.
        
        This helps users choose the right tool for their needs.
        """
        print("\n" + "="*80)
        print("USE CASE RECOMMENDATIONS")
        print("="*80 + "\n")
        
        recommendations = {
            "Stichotrope": [
                "Block-level profiling (between function and line granularity)",
                "Multi-track organization (logical grouping)",
                "Explicit instrumentation with decorators/context managers",
                "Production profiling with runtime enable/disable",
                "CppProfiler-compatible workflows",
            ],
            "cProfile": [
                "Quick function-level profiling",
                "Standard library (no installation needed)",
                "Automatic instrumentation (no code changes)",
                "General-purpose profiling",
            ],
            "py-spy": [
                "Production profiling (no code changes)",
                "Sampling profiler (low overhead)",
                "External process (can attach to running programs)",
                "Flamegraph visualization",
            ],
            "line_profiler": [
                "Line-by-line profiling (fine-grained)",
                "Identifying slow lines within functions",
                "Development/debugging (not production)",
            ],
            "pyinstrument": [
                "Statistical profiling (low overhead)",
                "Call tree visualization",
                "Web-friendly HTML output",
                "General-purpose profiling",
            ],
        }
        
        for profiler, use_cases in recommendations.items():
            print(f"{profiler}:")
            for use_case in use_cases:
                print(f"  • {use_case}")
            print()
        
        print("="*80 + "\n")

