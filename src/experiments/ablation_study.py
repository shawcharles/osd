import numpy as np
import pandas as pd
from typing import List, Dict
import time
import sys
import os
from itertools import combinations
from scipy import stats

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_SRC = os.path.dirname(THIS_DIR)
if PROJECT_SRC not in sys.path:
    sys.path.insert(0, PROJECT_SRC)

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

def calculate_smd(vals_a, vals_b):
    """Calculate Standardized Mean Difference using pooled within-group std."""
    mean_a = np.mean(vals_a)
    mean_b = np.mean(vals_b)
    var_a = np.var(vals_a, ddof=1) if len(vals_a) > 1 else 0.0
    var_b = np.var(vals_b, ddof=1) if len(vals_b) > 1 else 0.0
    pooled_std = np.sqrt((var_a + var_b) / 2.0)
    if pooled_std < 1e-9:
        return 0.0
    return (mean_a - mean_b) / pooled_std


def bootstrap_ci(data: np.ndarray, stat_func, n_resamples: int = 1000, alpha: float = 0.05, random_state: int = 0):
    """Simple percentile bootstrap confidence interval for a scalar statistic."""
    rng = np.random.default_rng(random_state)
    data = np.asarray(data)
    n = len(data)
    stats_samples = np.empty(n_resamples)
    for b in range(n_resamples):
        sample = rng.choice(data, size=n, replace=True)
        stats_samples[b] = stat_func(sample)
    lower = np.quantile(stats_samples, alpha / 2.0)
    upper = np.quantile(stats_samples, 1.0 - alpha / 2.0)
    return lower, upper


def holm_bonferroni(p_vals: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Compute Holm-Bonferroni adjusted p-values for a 1D array of p-values."""
    m = len(p_vals)
    order = np.argsort(p_vals)
    adjusted = np.empty(m)
    prev = 0.0
    for rank, idx in enumerate(order):
        factor = m - rank
        adj = factor * p_vals[idx]
        adj = max(adj, prev)
        adjusted[idx] = min(adj, 1.0)
        prev = adjusted[idx]
    return adjusted


def run_ablation(base_seed=42, use_multi_partition=False, n_partitions=5):
    """Run ablation study comparing embedding methods.
    
    Args:
        base_seed: Base random seed for reproducibility
        use_multi_partition: If True, use multi-partition selection (as in paper Section 4.3)
        n_partitions: Number of candidate partitions to generate (only if use_multi_partition=True)
    """
    methods = ['gnn', 'pca', 'spectral', 'random', 'unit_random']
    sample_sizes = [40, 200]
    n_replications = 50 # number of Monte Carlo replications
    results = []
    per_rep_records = []  # store per-replication metrics for statistical tests
    
    mp_str = f" (multi-partition: {n_partitions} candidates)" if use_multi_partition else " (single-partition)"
    print(f"Running Ablation Study ({n_replications} replications{mp_str})...")
    print(f"{'N':<5} {'Method':<15} {'RMSE':<10} {'Bias':<10} {'Runtime':<10}")
    print("-" * 60)
    
    for n in sample_sizes:
        for method in methods:
            errors = []
            runtimes = []
            max_smds = []
            mean_smds = []
            
            for rep in range(n_replications):
                # Generate fresh data with Multi-Modal structure
                # Use different seed for each replication to ensure true Monte Carlo variance
                seed = base_seed + rep + n * 1000 + hash(method) % 10000
                units = generate_synthetic_data(
                    n_units=n, 
                    effect_size=0.1, 
                    heterogeneity=0.5,
                    spatial_confounding=0.2,
                    non_linear_effect=True,
                    seed=seed
                )
                
                start = time.time()

                if method == 'unit_random':
                    # True unit-level randomization baseline (no supergeos)
                    n_treat_units = n // 2
                    t_units_indices = np.random.choice(n, n_treat_units, replace=False).tolist()
                    duration = time.time() - start
                    runtimes.append(duration)

                    # Covariate balance at unit level
                    t_idx = set(t_units_indices)
                    c_idx = set(range(n)) - t_idx
                    feature_names = sorted(list(units[0].covariates.keys()))
                    features = ['response', 'spend'] + feature_names

                    abs_smd_values = []
                    for feat in features:
                        if feat == 'response':
                            vals_t = [units[i].response for i in t_idx]
                            vals_c = [units[i].response for i in c_idx]
                        elif feat == 'spend':
                            vals_t = [units[i].spend for i in t_idx]
                            vals_c = [units[i].spend for i in c_idx]
                        else:
                            vals_t = [units[i].covariates.get(feat, 0.0) for i in t_idx]
                            vals_c = [units[i].covariates.get(feat, 0.0) for i in c_idx]
                        smd = abs(calculate_smd(vals_t, vals_c))
                        abs_smd_values.append(smd)

                    if abs_smd_values:
                        rep_max_smd = float(max(abs_smd_values))
                        rep_mean_smd = float(np.mean(abs_smd_values))
                        max_smds.append(rep_max_smd)
                        mean_smds.append(rep_mean_smd)
                    else:
                        rep_max_smd = np.nan
                        rep_mean_smd = np.nan

                else:
                    # Supergeo-based methods (gnn, pca, spectral, random embeddings)
                    # 1. Candidate Generation
                    generator = CandidateGenerator(units, method=method)
                    # Supergeos: 10% of N
                    n_super = max(4, int(n * 0.1))
                    
                    # Treatment size: 50%
                    n_treat = int(n_super / 2)
                    n_control = n_super - n_treat
                    
                    if use_multi_partition:
                        # Multi-partition selection (as described in paper Section 4.3)
                        candidate_partitions = generator.generate_candidate_partitions(
                            n_partitions=n_partitions,
                            n_supergeos=n_super,
                            seed=seed
                        )
                        solver = SupergeoSolver(candidate_partitions[0])
                        best_partition_idx, treatment_indices, _ = solver.solve_multi_partition(
                            candidate_partitions=candidate_partitions,
                            n_treatment=n_treat,
                            n_control=n_control,
                            time_limit=5,
                            verbose=False
                        )
                        # Use the best partition
                        supergeos = candidate_partitions[best_partition_idx]
                    else:
                        # Single-partition approach (original)
                        supergeos = generator.generate_supergeos(n_supergeos=n_super)
                        solver = SupergeoSolver(supergeos)
                        treatment_indices = solver.solve(n_treatment=n_treat, n_control=n_control, time_limit=5)

                    duration = time.time() - start
                    runtimes.append(duration)

                    # 3. Covariate balance evaluation via SMD at supergeo level
                    smds = solver.evaluate_balance(treatment_indices)
                    abs_smd_values = [abs(v) for v in smds.values()]
                    if abs_smd_values:
                        rep_max_smd = float(max(abs_smd_values))
                        rep_mean_smd = float(np.mean(abs_smd_values))
                        max_smds.append(rep_max_smd)
                        mean_smds.append(rep_mean_smd)
                    else:
                        rep_max_smd = np.nan
                        rep_mean_smd = np.nan

                    # 4. Outcome evaluation (RMSE/Bias) at unit level
                    t_units_indices = []
                    for sg_idx in treatment_indices:
                        sg = supergeos[sg_idx]
                        for u_id in sg.units:
                            t_units_indices.append(int(u_id))

                # Outcome evaluation (RMSE/Bias) for both cases
                error = evaluate_design(units, t_units_indices)
                errors.append(error)

                # Store per-replication record for later statistical analysis
                per_rep_records.append({
                    "n": n,
                    "method": method,
                    "rep": rep,
                    "error": float(error),
                    "max_smd": float(rep_max_smd),
                    "mean_smd": float(rep_mean_smd)
                })
                
            errors_arr = np.array(errors)
            rmse = float(np.sqrt(np.mean(errors_arr**2)))
            bias = float(np.mean(errors_arr))
            avg_runtime = np.mean(runtimes)
            avg_max_smd = float(np.mean(max_smds)) if max_smds else np.nan
            avg_mean_smd = float(np.mean(mean_smds)) if mean_smds else np.nan

            # Bootstrap CIs for RMSE and bias
            rmse_ci_low, rmse_ci_high = bootstrap_ci(
                errors_arr,
                stat_func=lambda e: np.sqrt(np.mean(e**2)),
                n_resamples=1000,
                random_state=base_seed
            )
            bias_ci_low, bias_ci_high = bootstrap_ci(
                errors_arr,
                stat_func=np.mean,
                n_resamples=1000,
                random_state=base_seed + 1
            )
            
            results.append({
                "n": n,
                "method": method,
                "rmse": rmse,
                "bias": bias,
                "runtime": avg_runtime,
                "avg_max_smd": avg_max_smd,
                "avg_mean_smd": avg_mean_smd,
                "rmse_ci_low": float(rmse_ci_low),
                "rmse_ci_high": float(rmse_ci_high),
                "bias_ci_low": float(bias_ci_low),
                "bias_ci_high": float(bias_ci_high)
            })
            
            print(f"{n:<5} {method:<15} {rmse:.4f}     {bias:.4f}     {avg_runtime:.4f}s   max|SMD|={avg_max_smd:.4f}")
        
    # Save aggregated results
    df = pd.DataFrame(results)
    df.to_csv("ablation_results_small_n.csv", index=False)
    print("\nAggregated results saved to ablation_results_small_n.csv")

    # Save per-replication results
    per_rep_df = pd.DataFrame(per_rep_records)
    per_rep_df.to_csv("ablation_per_rep_small_n.csv", index=False)
    print("Per-replication results saved to ablation_per_rep_small_n.csv")

    # Statistical tests: paired t-tests on squared errors with Holm-Bonferroni
    stats_records = []
    for n in sample_sizes:
        df_n = per_rep_df[per_rep_df["n"] == n]
        methods_n = sorted(df_n["method"].unique())
        pairs = list(combinations(methods_n, 2))
        p_vals = []
        tmp_records = []
        for m1, m2 in pairs:
            e1 = df_n[df_n["method"] == m1]["error"].values
            e2 = df_n[df_n["method"] == m2]["error"].values
            # Paired t-test on squared error
            se1 = e1**2
            se2 = e2**2
            t_stat, p_val = stats.ttest_rel(se1, se2)
            diff = se1 - se2
            std_diff = diff.std(ddof=1)
            cohen_d = float(diff.mean() / (std_diff + 1e-9))
            tmp_records.append({
                "n": n,
                "method_1": m1,
                "method_2": m2,
                "t_stat": float(t_stat),
                "p_value": float(p_val),
                "cohen_d": cohen_d
            })
            p_vals.append(p_val)

        if p_vals:
            p_vals = np.array(p_vals)
            p_adj = holm_bonferroni(p_vals)
            for rec, adj in zip(tmp_records, p_adj):
                rec["p_value_holm"] = float(adj)
                stats_records.append(rec)

    if stats_records:
        stats_df = pd.DataFrame(stats_records)
        stats_df.to_csv("ablation_stats_small_n.csv", index=False)
        print("Statistical test results saved to ablation_stats_small_n.csv")

if __name__ == "__main__":
    run_ablation()
