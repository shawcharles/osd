import numpy as np
import pandas as pd
from typing import List, Dict
import time
import sys
import os

from osd.utils.synthetic_data import generate_synthetic_data
from osd.design.candidate_generation import CandidateGenerator
from osd.design.solver import SupergeoSolver

def evaluate_design(units, treatment_indices):
    """
    Calculate RMSE and Bias for a given design.
    """
    t_idx = set(treatment_indices)
    c_idx = set(range(len(units))) - t_idx
    
    if len(t_idx) == 0 or len(c_idx) == 0:
        return 999.0, 999.0 # Failure
        
    # Observed Outcomes (using potential outcomes framework)
    # Y_obs = Y(1) if T else Y(0)
    # We simulate the experiment outcome
    
    # True ATT (Average Treatment Effect on the Treated)
    # We want to compare the estimated ATT vs the true ATT for the specific group selected.
    
    true_att = np.mean([units[i].true_tau for i in t_idx])
    
    y_pre = np.array([u.response for u in units])
    y_post = y_pre.copy()
    
    # SIMULATE COVARIATE-DRIVEN TREND (The "Killer Feature")
    # Areas with high Income grow faster naturally.
    # If Design doesn't balance Income, DiD will be biased.
    incomes = np.array([u.covariates['income'] for u in units])
    inc_z = (incomes - incomes.mean()) / (incomes.std() + 1e-9)
    
    # Trend Effect: 10% growth differential per SD of Income
    trend_factor = 0.1 * inc_z
    
    # Apply Trend
    y_post = y_post * (1 + trend_factor)
    
    # Add treatment effect to simulated outcome
    for i in t_idx:
        y_post[i] += units[i].true_tau

    mu_post_t = np.mean([y_post[i] for i in t_idx])
    mu_pre_t = np.mean([y_pre[i] for i in t_idx])
    mu_post_c = np.mean([y_post[i] for i in c_idx])
    mu_pre_c = np.mean([y_pre[i] for i in c_idx])
    
    est_att = (mu_post_t - mu_pre_t) - (mu_post_c - mu_pre_c)
    
    error = est_att - true_att
    return error

def run_ablation():
    methods = ['gnn', 'pca', 'spectral', 'random']
    sample_sizes = [40, 200]
    n_replications = 50 # Increased for stability
    results = []
    
    print(f"Running Ablation Study ({n_replications} replications)...")
    print(f"{'N':<5} {'Method':<15} {'RMSE':<10} {'Bias':<10} {'Runtime':<10}")
    print("-" * 60)
    
    for n in sample_sizes:
        for method in methods:
            errors = []
            runtimes = []
            
            for _ in range(n_replications):
                # Generate fresh data with Multi-Modal structure
                units = generate_synthetic_data(
                    n_units=n, 
                    effect_size=0.1, 
                    heterogeneity=0.5,
                    spatial_confounding=0.2,
                    non_linear_effect=True
                )
                
                start = time.time()
                
                # 1. Candidate Generation
                generator = CandidateGenerator(units, method=method)
                # Supergeos: 10% of N
                n_super = max(4, int(n * 0.1)) 
                supergeos = generator.generate_supergeos(n_supergeos=n_super)
                
                # 2. Optimization
                # Treatment size: 50%
                n_treat = int(n_super / 2)
                n_control = n_super - n_treat
                
                solver = SupergeoSolver(supergeos)
                treatment_indices = solver.solve(n_treatment=n_treat, n_control=n_control, time_limit=5)
                
                duration = time.time() - start
                runtimes.append(duration)
                
                # 3. Evaluation
                t_units_indices = []
                for sg_idx in treatment_indices:
                    sg = supergeos[sg_idx]
                    for u_id in sg.units:
                        t_units_indices.append(int(u_id))
                
                error = evaluate_design(units, t_units_indices)
                errors.append(error)
                
            rmse = np.sqrt(np.mean(np.array(errors)**2))
            bias = np.mean(errors)
            avg_runtime = np.mean(runtimes)
            
            results.append({
                "n": n,
                "method": method,
                "rmse": rmse,
                "bias": bias,
                "runtime": avg_runtime
            })
            
            print(f"{n:<5} {method:<15} {rmse:.4f}     {bias:.4f}     {avg_runtime:.4f}s")
        
    # Save results
    df = pd.DataFrame(results)
    df.to_csv("ablation_results_small_n.csv", index=False)
    print("\nResults saved to ablation_results_small_n.csv")

if __name__ == "__main__":
    run_ablation()
