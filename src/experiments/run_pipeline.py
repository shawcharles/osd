from osd.utils.synthetic_data import generate_synthetic_data
from osd.design.candidate_generation import CandidateGenerator
from osd.design.solver import SupergeoSolver
import numpy as np

def main():
    print("Generating data...")
    units = generate_synthetic_data(n_units=200)
    
    print("Stage 1: Candidate Generation (GNN + Clustering)...")
    generator = CandidateGenerator(units)
    # We want, say, 20 supergeos total (10 Treatment, 10 Control)
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

if __name__ == "__main__":
    main()
