import numpy as np
import pandas as pd
import time
from osd.utils.synthetic_data import generate_synthetic_data
from osd.design.candidate_generation import CandidateGenerator
from osd.design.solver import SupergeoSolver
from experiments.ablation_study import evaluate_design

def run_robustness():
    confounding_levels = [0.0, 0.2, 0.5, 0.8]
    n_replications = 20
    results = []
    
    print(f"Running Adversarial Robustness Study...")
    print(f"{'Confounding':<15} {'Method':<10} {'RMSE':<10} {'Bias':<10}")
    print("-" * 50)
    
    for alpha in confounding_levels:
        # Compare ASD (GNN) vs Random Assignment
        methods = ['asd', 'random_design'] 
        
        for method_name in methods:
            errors = []
            
            for _ in range(n_replications):
                # Generate Adversarial Data
                # spatial_confounding = alpha
                units = generate_synthetic_data(
                    n_units=200, 
                    effect_size=0.1, 
                    heterogeneity=0.5,
                    spatial_confounding=alpha,
                    non_linear_effect=True # Always on for robustness check
                )
                
                if method_name == 'asd':
                    generator = CandidateGenerator(units, method='gnn')
                    supergeos = generator.generate_supergeos(n_supergeos=20)
                    solver = SupergeoSolver(supergeos)
                    # Solve
                    t_sg_indices = solver.solve(n_treatment=10, n_control=10, time_limit=5)
                    
                    t_units_indices = []
                    for sg_idx in t_sg_indices:
                        for u_id in supergeos[sg_idx].units:
                            t_units_indices.append(int(u_id))
                            
                else: # random_design
                    # Pure random assignment of units
                    all_indices = np.arange(len(units))
                    np.random.shuffle(all_indices)
                    t_units_indices = all_indices[:len(units)//2]
                
                error = evaluate_design(units, t_units_indices)
                errors.append(error)
                
            rmse = np.sqrt(np.mean(np.array(errors)**2))
            bias = np.mean(errors)
            
            results.append({
                "confounding": alpha,
                "method": method_name,
                "rmse": rmse,
                "bias": bias
            })
            
            print(f"{alpha:<15} {method_name:<10} {rmse:.4f}     {bias:.4f}")

    df = pd.DataFrame(results)
    df.to_csv("robustness_results.csv", index=False)
    print("\nResults saved to robustness_results.csv")

if __name__ == "__main__":
    run_robustness()
