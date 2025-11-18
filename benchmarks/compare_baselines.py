"""
Compare performance baselines across multiple versions of Stichotrope.

Supports comparing arbitrary number of dataset directories with flexible configuration.
Generates comparison reports with bar charts including error bars and statistical tests.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
import numpy as np

# Add tests/performance to path for statistics_utils
sys.path.insert(0, str(Path(__file__).parent.parent / "tests" / "performance"))
from statistics_utils import perform_welch_ttest


def load_baseline(baseline_path: Path) -> Dict:
    """Load baseline JSON file."""
    with open(baseline_path, 'r') as f:
        return json.load(f)


def load_all_baselines(baseline_dir: Path) -> Dict[str, Dict]:
    """Load all overhead baselines from directory (skip constant_overhead and cprofile_comparison)."""
    baselines = {}
    for json_file in baseline_dir.glob("overhead_*.json"):  # Only load overhead_* files
        key = json_file.stem  # e.g., "overhead_decorator_small_x10"
        baselines[key] = load_baseline(json_file)
    return baselines


class Dataset:
    """Represents a single dataset (version) for comparison."""

    def __init__(self, path: Path, name: Optional[str] = None):
        """
        Initialize dataset.

        Args:
            path: Path to directory containing overhead_*.json files
            name: Optional custom name for this dataset. If None, auto-generated from directory stem.
        """
        self.path = path
        self.name = name or self._auto_generate_name()
        self.baselines = load_all_baselines(path)

    def _auto_generate_name(self) -> str:
        """Auto-generate dataset name from directory stem."""
        stem = self.path.stem
        # Special case: "prototype" directory should be labeled "Prototype" (no version)
        if stem.lower() == "prototype":
            return "Prototype"
        # Otherwise use the stem as-is (e.g., "v0.2.0" → "v0.2.0")
        return stem


def extract_dataset_stats(data: Dict) -> Dict:
    """Extract statistics from a single dataset's baseline data."""
    # Extract raw data if available (new format), otherwise use aggregated stats
    if 'raw_data' in data:
        # New format with raw data
        baseline = np.array(data['raw_data']['baseline_times_ms'])
        profiled = np.array(data['raw_data']['profiled_times_ms'])

        # Calculate overhead percentages for each measurement
        overhead_pcts = ((profiled - baseline) / baseline) * 100

        # Calculate standard deviation of overhead percentages
        std_pct = np.std(overhead_pcts, ddof=1)  # Sample std dev

        # Calculate std dev in microseconds
        overhead_us_std = np.std(overhead_pcts * data['statistics']['baseline_mean_ms'] * 10, ddof=1)
    else:
        # Old format without raw data - use coefficient of variation as approximation
        std_pct = (data['statistics'].get('baseline_std_ms', 0) /
                  data['statistics']['baseline_mean_ms'] * 100) if 'baseline_std_ms' in data['statistics'] else 0
        # Approximate from percentage std dev
        overhead_us_std = std_pct * data['statistics']['baseline_mean_ms'] * 10

    # Calculate absolute overhead in microseconds
    overhead_us = data['statistics'].get('overhead_ns', 0) / 1000  # ns to µs

    return {
        'overhead_pct': data['statistics']['overhead_pct'],
        'std_pct': std_pct,
        'overhead_us': overhead_us,
        'overhead_us_std': overhead_us_std,
        'raw_data': data.get('raw_data'),
    }


def compare_baselines(datasets: List[Dataset]) -> List[Dict]:
    """
    Compare baselines across multiple datasets with statistical testing.

    Args:
        datasets: List of Dataset objects to compare

    Returns:
        List of comparison dictionaries, one per scenario/method/multiplier combination
    """
    if len(datasets) < 2:
        raise ValueError("Need at least 2 datasets to compare")

    # Use first dataset as reference to get all keys
    reference = datasets[0]

    comparisons = []
    for key in sorted(reference.baselines.keys()):
        # Check if all datasets have this key
        if not all(key in ds.baselines for ds in datasets):
            continue

        # Extract metadata from reference dataset
        ref_data = reference.baselines[key]

        # Extract stats for all datasets
        dataset_stats = {}
        for ds in datasets:
            dataset_stats[ds.name] = extract_dataset_stats(ds.baselines[key])

        # Perform pairwise statistical tests (first dataset vs others)
        p_values = {}
        if len(datasets) >= 2:
            ref_raw = dataset_stats[reference.name]['raw_data']
            if ref_raw:
                ref_profiled = np.array(ref_raw['profiled_times_ms'])
                for ds in datasets[1:]:
                    comp_raw = dataset_stats[ds.name]['raw_data']
                    if comp_raw:
                        comp_profiled = np.array(comp_raw['profiled_times_ms'])
                        try:
                            ttest_result = perform_welch_ttest(
                                ref_profiled / 1000,  # Convert to seconds
                                comp_profiled / 1000
                            )
                            p_values[ds.name] = ttest_result['p_value']
                        except ImportError:
                            p_values[ds.name] = None

        comparison = {
            'key': key,
            'scenario': ref_data['scenario'],
            'multiplier': ref_data['multiplier'],
            'method': ref_data['method'],
            'datasets': dataset_stats,
            'p_values': p_values,
        }
        comparisons.append(comparison)

    return comparisons


def create_bar_chart(comparisons: List[Dict], datasets: List[Dataset], output_path: Path, multiplier: int):
    """
    Create bar chart comparing multiple datasets for specific multiplier.

    Args:
        comparisons: List of comparison dictionaries
        datasets: List of Dataset objects being compared
        output_path: Path to save the chart
        multiplier: Workload multiplier to filter by (10, 100, etc.)
    """
    # Filter by multiplier
    data = [c for c in comparisons if c['multiplier'] == multiplier]

    # Group by scenario and method
    scenarios = ['tiny', 'small', 'medium', 'large']
    methods = ['decorator', 'context_manager']

    # Prepare data
    x = np.arange(len(scenarios))
    n_datasets = len(datasets)

    # Calculate bar width based on number of datasets
    total_width = 0.8  # Total width for all bars in a group
    width = total_width / n_datasets

    # Generate colors for each dataset
    colors = plt.cm.tab10(np.linspace(0, 0.9, n_datasets))

    # Dynamic title based on number of datasets
    if n_datasets == 2:
        title = f'{datasets[0].name} vs {datasets[1].name} Overhead (x{multiplier} multiplier)'
    else:
        title = f'Multi-Version Overhead Comparison (x{multiplier} multiplier)'

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(title, fontsize=14, fontweight='bold')

    for idx, method in enumerate(methods):
        ax = axes[idx]

        # Collect data for each dataset
        all_bars = []
        for ds_idx, ds in enumerate(datasets):
            values = []
            errors = []

            for scenario in scenarios:
                # Find matching comparison
                matching = [c for c in data if c['scenario'] == scenario and c['method'] == method]
                if matching and ds.name in matching[0]['datasets']:
                    c = matching[0]
                    stats = c['datasets'][ds.name]
                    # Use overhead percentage
                    mean_val = stats['overhead_pct']
                    std_val = stats['std_pct']

                    values.append(mean_val)
                    errors.append(std_val)
                else:
                    values.append(0)
                    errors.append(0)

            # Calculate bar positions (centered around x)
            offset = (ds_idx - (n_datasets - 1) / 2) * width
            positions = x + offset

            # Create bars with error bars (±1 SD)
            bars = ax.bar(positions, values, width,
                         yerr=errors, capsize=5,
                         label=ds.name, color=colors[ds_idx],
                         error_kw={'elinewidth': 1, 'capthick': 1})
            all_bars.append((bars, values))

        # Customize
        ax.set_ylabel('Overhead (%)', fontweight='bold')
        ax.set_title(f'{method.replace("_", " ").title()}', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([s.capitalize() for s in scenarios])
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        # Add value labels on bars
        for bars, values in all_bars:
            for i, bar in enumerate(bars):
                height = bar.get_height()
                label = f'{height:+.2f}%'
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       label,
                       ha='center', va='bottom' if height >= 0 else 'top', fontsize=7)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ Chart saved: {output_path}")


def generate_markdown_report(comparisons: List[Dict], datasets: List[Dataset], output_path: Path):
    """
    Generate markdown comparison report for multiple datasets.

    Args:
        comparisons: List of comparison dictionaries
        datasets: List of Dataset objects being compared
        output_path: Path to save the report
    """
    from datetime import datetime

    lines = [
        f"# Performance Comparison: {' vs '.join(ds.name for ds in datasets)}",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d')}  ",
    ]

    # Add dataset information
    for ds in datasets:
        lines.append(f"**{ds.name}**: {ds.path}  ")

    lines.extend([
        "",
        "---",
        "",
        "## Detailed Comparison",
        "",
    ])

    # Group by multiplier
    for multiplier in [10, 100]:
        lines.append(f"### x{multiplier} Multiplier")
        lines.append("")

        # Build table header dynamically
        header = "| Scenario | Method |"
        separator = "|----------|--------|"
        for ds in datasets:
            header += f" {ds.name} |"
            separator += "--------|"
        lines.append(header)
        lines.append(separator)

        data = [c for c in comparisons if c['multiplier'] == multiplier]
        for c in sorted(data, key=lambda x: (x['scenario'], x['method'])):
            scenario = c['scenario'].capitalize()
            method = c['method'].capitalize()

            row = f"| {scenario} | {method} |"
            for ds in datasets:
                if ds.name in c['datasets']:
                    pct = c['datasets'][ds.name]['overhead_pct']
                    row += f" {pct:.2f}% |"
                else:
                    row += " N/A |"

            lines.append(row)

        lines.append("")

    lines.append("## Charts")
    lines.append("")
    lines.append("![x10 Comparison](./comparison_x10.png)")
    lines.append("")
    lines.append("![x100 Comparison](./comparison_x100.png)")
    lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"✅ Report saved: {output_path}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Compare performance baselines across multiple versions of Stichotrope.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two versions (backward compatible)
  python compare_baselines.py benchmarks/data/prototype benchmarks/data/v0.2.0

  # Compare three versions
  python compare_baselines.py benchmarks/data/prototype benchmarks/data/v0.2.0 benchmarks/data/v0.3.0

  # Use custom names
  python compare_baselines.py benchmarks/data/prototype benchmarks/data/v0.2.0 --names "Prototype" "Thread-Safe"

  # Specify output directory
  python compare_baselines.py benchmarks/data/prototype benchmarks/data/v0.2.0 --output benchmarks/reports/custom
        """
    )

    parser.add_argument(
        'datasets',
        nargs='*',
        type=Path,
        help='Paths to dataset directories (each containing overhead_*.json files). '
             'If not provided, defaults to prototype and v0.2.0.'
    )

    parser.add_argument(
        '--names',
        nargs='*',
        type=str,
        help='Optional custom names for datasets (must match number of datasets). '
             'If not provided, names are auto-generated from directory stems.'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path("benchmarks/reports/analysis_performance_benchmarking"),
        help='Output directory for reports and charts (default: benchmarks/reports/analysis_performance_benchmarking)'
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    # Use defaults if no datasets provided (backward compatibility)
    if not args.datasets:
        dataset_paths = [
            Path("benchmarks/data/prototype"),
            Path("benchmarks/data/v0.2.0")
        ]
    else:
        dataset_paths = args.datasets

    # Validate dataset paths
    for path in dataset_paths:
        if not path.exists():
            print(f"❌ Error: Dataset directory not found: {path}")
            sys.exit(1)
        if not path.is_dir():
            print(f"❌ Error: Not a directory: {path}")
            sys.exit(1)

    # Validate names if provided
    if args.names:
        if len(args.names) != len(dataset_paths):
            print(f"❌ Error: Number of names ({len(args.names)}) must match number of datasets ({len(dataset_paths)})")
            sys.exit(1)
        names = args.names
    else:
        names = [None] * len(dataset_paths)  # Auto-generate names

    # Create Dataset objects
    datasets = [Dataset(path, name) for path, name in zip(dataset_paths, names)]

    print(f"📊 Comparing {len(datasets)} datasets:")
    for ds in datasets:
        print(f"  - {ds.name}: {ds.path}")

    # Create output directory if needed
    args.output.mkdir(parents=True, exist_ok=True)

    # Compare baselines
    comparisons = compare_baselines(datasets)

    # Generate charts
    create_bar_chart(comparisons, datasets, args.output / "comparison_x10.png", 10)
    create_bar_chart(comparisons, datasets, args.output / "comparison_x100.png", 100)

    # Generate report
    generate_markdown_report(comparisons, datasets, args.output / "02-prototype_comparison_v1.md")

    print("\n✅ Comparison complete!")

