import os
import sys

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_SRC = os.path.dirname(THIS_DIR)
if PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)

from osd.utils.synthetic_data import generate_synthetic_data
from osd.design.candidate_generation import CandidateGenerator
from osd.design.solver import SupergeoSolver
import numpy as np

def main(seed=42, use_multi_partition=True, n_partitions=10):
    print("Generating data...")
    units = generate_synthetic_data(n_units=200, seed=seed)
    
    if use_multi_partition:
        print(f"Stage 1: Generating {n_partitions} candidate partitions...")
        generator = CandidateGenerator(units, method='pca')
        candidate_partitions = generator.generate_candidate_partitions(
            n_partitions=n_partitions, 
            n_supergeos=20,
            seed=seed
        )
        print(f"Generated {len(candidate_partitions)} candidate partitions.")
        
        print("Stage 2: Multi-Partition Selection (MILP)...")
        # Use first partition to initialize solver, but will try all partitions
        solver = SupergeoSolver(candidate_partitions[0])
        best_partition_idx, treatment_indices, best_cost = solver.solve_multi_partition(
            candidate_partitions=candidate_partitions,
            n_treatment=10,
            n_control=10,
            verbose=True
        )
        print(f"Selected partition {best_partition_idx} with cost {best_cost:.4f}")
        
        # Get the supergeos from the best partition
        supergeos = candidate_partitions[best_partition_idx]
    else:
        # Original single-partition approach
        print("Stage 1: Candidate Generation (Single Partition)...")
        generator = CandidateGenerator(units, method='pca')
        supergeos = generator.generate_supergeos(n_supergeos=20)
        print(f"Generated {len(supergeos)} supergeos.")
        
        print("Stage 2: Optimal Partitioning (MILP)...")
        solver = SupergeoSolver(supergeos)
        treatment_indices = solver.solve(n_treatment=10, n_control=10)
    
    # Evaluate
    t_set = [supergeos[i] for i in treatment_indices]
    c_set = [supergeos[i] for i in range(len(supergeos)) if i not in treatment_indices]
    
    print(f"Assigned {len(t_set)} to Treatment, {len(c_set)} to Control.")
    
    # Calc balance
    def get_mean(objs, attr):
        if attr in ["response", "spend"]:
            vals = [getattr(o, attr) for o in objs]
        else:
            vals = [o.covariates[attr] for o in objs]
        return np.mean(vals)
        
    print("\nBalance Check (Means):")
    for feat in ["response", "spend", "population", "income"]:
        mu_t = get_mean(t_set, feat)
        mu_c = get_mean(c_set, feat)
        diff = abs(mu_t - mu_c)
        pct = diff / mu_c * 100
        print(f"{feat:<12}: T={mu_t:,.0f}, C={mu_c:,.0f}, Diff={pct:.2f}%")

    # Compute covariate balance using Standardized Mean Differences (SMD)
    smds = solver.evaluate_balance(treatment_indices)
    print("\nBalance Check (SMD):")
    for feat_name, smd in smds.items():
        print(f"{feat_name:<12}: SMD={smd:.4f}")

if __name__ == "__main__":
    main()
