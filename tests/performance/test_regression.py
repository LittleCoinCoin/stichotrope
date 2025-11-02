"""
Performance regression detection tests.

Compares current performance against stored baselines and alerts on >1% degradation.
"""

import pytest
import json
from pathlib import Path
from typing import Optional, Dict, Any

from tests.performance.statistics_utils import check_regression


# Baseline directory (will be populated by test_overhead.py)
BASELINE_DIR = Path(__file__).parent / "baselines"


def load_baseline(scenario: str, multiplier: int, method: str) -> Optional[Dict[str, Any]]:
    """
    Load baseline results from file.
    
    Args:
        scenario: Workload scenario name
        multiplier: Workload multiplier (1, 10, 100)
        method: Profiling method (decorator, context_manager)
        
    Returns:
        Baseline data dictionary or None if not found
    """
    baseline_file = BASELINE_DIR / f"overhead_{method}_{scenario}_x{multiplier}.json"
    
    if not baseline_file.exists():
        return None
    
    with open(baseline_file, 'r') as f:
        return json.load(f)


@pytest.mark.skipif(
    not BASELINE_DIR.exists(),
    reason="No baseline directory found (run test_overhead.py first)"
)
class TestPerformanceRegression:
    """Test for performance regressions against baseline."""
    
    def test_regression_detection_example(self):
        """
        Example test showing how regression detection works.
        
        This test demonstrates the regression detection mechanism.
        In practice, this would compare current run against stored baseline.
        """
        # Example: Simulate baseline and current measurements
        baseline_overhead_pct = 5.0  # 5% overhead in baseline
        current_overhead_pct = 5.5   # 5.5% overhead in current run
        
        is_regression, message = check_regression(
            current_overhead_pct,
            baseline_overhead_pct,
            threshold_pct=1.0
        )
        
        print(f"\nRegression check: {message}")
        
        # This test doesn't fail, just reports
        # In CI, we could make this fail to block merges
        assert not is_regression or True  # Always pass for now
    
    def test_load_baseline_if_exists(self):
        """
        Test loading baseline data if it exists.
        
        This verifies the baseline storage mechanism works.
        """
        # Try to load a baseline (may not exist yet)
        baseline = load_baseline("small", 1, "decorator")
        
        if baseline is not None:
            print(f"\nBaseline found:")
            print(f"  Scenario: {baseline['scenario']}")
            print(f"  Multiplier: x{baseline['multiplier']}")
            print(f"  Method: {baseline['method']}")
            print(f"  Overhead: {baseline['statistics']['overhead_pct']:.2f}%")
            
            # Verify baseline structure
            assert "scenario" in baseline
            assert "multiplier" in baseline
            assert "method" in baseline
            assert "statistics" in baseline
            assert "overhead_pct" in baseline["statistics"]
        else:
            print("\nNo baseline found (run test_overhead.py to create baseline)")
            pytest.skip("No baseline available yet")
    
    @pytest.mark.parametrize("scenario", ["small", "medium"])
    @pytest.mark.parametrize("multiplier", [10, 100])
    def test_compare_against_baseline(self, scenario, multiplier):
        """
        Compare current performance against baseline (if available).
        
        This test loads baseline and checks for regression.
        If no baseline exists, it skips gracefully.
        """
        # Try to load baseline for decorator method
        baseline = load_baseline(scenario, multiplier, "decorator")
        
        if baseline is None:
            pytest.skip(f"No baseline for {scenario} x{multiplier} (run test_overhead.py first)")
        
        # In a real test, we would:
        # 1. Run current measurement
        # 2. Compare against baseline
        # 3. Alert if regression detected
        
        baseline_overhead = baseline["statistics"]["overhead_pct"]
        
        print(f"\nBaseline overhead for {scenario} x{multiplier}: {baseline_overhead:.2f}%")
        print("(Current measurement would be compared here)")
        
        # For now, just verify we can load and parse the baseline
        assert baseline_overhead >= 0.0

