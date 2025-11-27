#!/usr/bin/env python3
"""Benchmark scalability of OSD algorithm across different N values.

This script measures the actual runtime of the OSD algorithm (PCA + MILP)
for varying numbers of geographic units (N). Results are saved to CSV and
can be used to generate the scalability plot in the paper.

Usage:
    python scripts/benchmark_scalability.py --output scalability_results.csv
    
Outputs:
    - CSV file with columns: n, runtime_seconds, method
"""

import argparse
import sys
from pathlib import Path
import time
import numpy as np
import pandas as pd

# Add parent directory to path to import osd module
THIS_DIR = Path(__file__).parent
PROJECT_ROOT = THIS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from osd.utils.synthetic_data import generate_synthetic_data
from osd.design.candidate_generation import CandidateGenerator
from osd.design.solver import SupergeoSolver


def benchmark_osd(n_units: int, n_trials: int = 3, seed: int = 42) -> float:
    """Benchmark OSD runtime for a given N.
    
    Args:
        n_units: Number of geographic units
        n_trials: Number of trials to average over
        seed: Random seed for reproducibility
        
    Returns:
        Average runtime in seconds
    """
    runtimes = []
    
    for trial in range(n_trials):
        # Generate synthetic data
        units = generate_synthetic_data(
            n_units=n_units,
            effect_size=0.1,
            heterogeneity=0.5,
            spatial_confounding=0.2,
            seed=seed + trial
        )
        
        start = time.time()
        
        # Stage 1: Embedding + Clustering
        generator = CandidateGenerator(units, method='pca')
        n_supergeos = max(4, int(n_units * 0.1))  # 10% of N
        supergeos = generator.generate_supergeos(n_supergeos=n_supergeos)
        
        # Stage 2: MILP Optimization
        n_treatment = int(n_supergeos / 2)
        n_control = n_supergeos - n_treatment
        solver = SupergeoSolver(supergeos)
        treatment_indices = solver.solve(
            n_treatment=n_treatment,
            n_control=n_control,
            time_limit=30.0
        )
        
        runtime = time.time() - start
        runtimes.append(runtime)
    
    return np.mean(runtimes)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark OSD scalability across different N values"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="scalability_results.csv",
        help="Output CSV file path"
    )
    parser.add_argument(
        "--n-values",
        type=int,
        nargs="+",
        default=[50, 100, 200, 400, 800, 1000],
        help="List of N values to benchmark"
    )
    parser.add_argument(
        "--n-trials",
        type=int,
        default=3,
        help="Number of trials to average over per N"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    print("OSD Scalability Benchmark")
    print("=" * 60)
    print(f"N values: {args.n_values}")
    print(f"Trials per N: {args.n_trials}")
    print(f"Random seed: {args.seed}")
    print("=" * 60)
    print()
    
    results = []
    
    for n in args.n_values:
        print(f"Benchmarking N={n}...", end=" ", flush=True)
        
        try:
            avg_runtime = benchmark_osd(
                n_units=n,
                n_trials=args.n_trials,
                seed=args.seed
            )
            
            results.append({
                "n": n,
                "runtime_seconds": avg_runtime,
                "method": "OSD (PCA + MILP)"
            })
            
            print(f"✓ {avg_runtime:.4f}s")
            
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    # Save results
    if results:
        df = pd.DataFrame(results)
        df.to_csv(args.output, index=False)
        print()
        print("=" * 60)
        print(f"Results saved to {args.output}")
        print()
        print(df.to_string(index=False))
    else:
        print("No results to save.")
        sys.exit(1)


if __name__ == "__main__":
    main()
