import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Supergeo:
    id: str
    units: List[str] # Unit IDs
    response: float
    spend: float
    covariates: Dict[str, float] # e.g. {"pop": 1000, "income": 50000}
    
    @property
    def size(self):
        return len(self.units)

class SupergeoSolver:
    """
    Exact solver for assigning Supergeos to Treatment/Control
    using Mixed-Integer Linear Programming (MILP).
    """
    def __init__(self, supergeos: List[Supergeo], weights: Dict[str, float] = None):
        self.supergeos = supergeos
        self.weights = weights or {"response": 1.0}
        self.n = len(supergeos)
        
        # Precompute feature matrix [N_supergeos, N_features]
        # We balance on Means. So we need sums and counts.
        # Features: Response, Spend, Covariates
        self.features = ["response", "spend"] + sorted(list(supergeos[0].covariates.keys()))
        
        self.X = np.zeros((self.n, len(self.features)))
        for i, sg in enumerate(supergeos):
            self.X[i, 0] = sg.response
            self.X[i, 1] = sg.spend
            for k, feat in enumerate(self.features[2:]):
                self.X[i, k+2] = sg.covariates.get(feat, 0.0)
                
        # Normalize features for numerical stability (and SMD calculation)
        # We use Standard Deviation of the *original units* ideally, 
        # but here we scale by the supergeo population std dev estimate.
        # For simplicity in MILP, we minimize sum differences on standardized scale.
        self.means = self.X.mean(axis=0)
        self.stds = self.X.std(axis=0) + 1e-6
        self.X_norm = (self.X - self.means) / self.stds

    def solve(self, n_treatment: int, n_control: int, time_limit: float = 30.0):
        """
        Assign supergeos to Treatment (1) or Control (0).
        
        Objective: Minimize sum of absolute differences in means.
        Note: Minimizing |Mean(T) - Mean(C)| is non-linear if sizes vary.
        If sizes are fixed (n_treatment supergeos), Mean(T) = Sum(T)/n_treatment.
        Diff = |Sum(T)/n_t - Sum(C)/n_c|.
        Since Sum(C) = Sum(Total) - Sum(T),
        Diff = |Sum(T)/n_t - (Sum(Total)-Sum(T))/n_c|
             = |Sum(T) * (1/n_t + 1/n_c) - Sum(Total)/n_c|
        
        So we just need to target Sum(T) close to Target = Sum(Total) * (n_t / (n_t + n_c)).
        
        Variables:
        x[i] : binary, 1 if Treatment, 0 if Control.
        u[k] : continuous, deviation for feature k.
        
        Minimize Sum(w_k * u_k)
        Subject to:
        -u_k <= Sum(x_i * V_ik) - Target_k <= u_k
        Sum(x_i) = n_treatment
        """
        n_features = len(self.features)
        
        # Problem dimension: n binaries (x) + n_features continuous (u)
        # Vector structure: [x_0...x_n-1, u_0...u_k-1]
        
        c = np.concatenate([np.zeros(self.n), np.ones(n_features)])
        
        # Adjust weights
        # weights dict maps feature name to weight.
        w_vec = np.ones(n_features)
        for i, f in enumerate(self.features):
            if f in self.weights:
                w_vec[i] = self.weights[f]
        c[self.n:] = w_vec
        
        # Targets
        # Total sum of each feature
        total_sum = self.X_norm.sum(axis=0)
        target_sum = total_sum * (n_treatment / (n_treatment + n_control))
        
        # Constraints
        # 1. Cardinality: Sum(x) = n_treatment
        A_eq = np.zeros((1, self.n + n_features))
        A_eq[0, :self.n] = 1
        b_eq = np.array([n_treatment])
        
        # 2. Balance Constraints (Inequalities)
        # -u_k <= Sum(x * v_k) - Target <= u_k
        # Rewritten:
        # Sum(x * v_k) - u_k <= Target
        # -Sum(x * v_k) - u_k <= -Target
        
        A_ub = np.zeros((2 * n_features, self.n + n_features))
        b_ub = np.zeros(2 * n_features)
        
        for k in range(n_features):
            # Row 1: Sum - u <= Target
            A_ub[2*k, :self.n] = self.X_norm[:, k]
            A_ub[2*k, self.n + k] = -1
            b_ub[2*k] = target_sum[k]
            
            # Row 2: -Sum - u <= -Target
            A_ub[2*k+1, :self.n] = -self.X_norm[:, k]
            A_ub[2*k+1, self.n + k] = -1
            b_ub[2*k+1] = -target_sum[k]
            
        # Variable Bounds
        # x in [0, 1], u in [0, inf]
        integrality = np.concatenate([np.ones(self.n), np.zeros(n_features)]) # 1=Integer, 0=Continuous
        lb = np.concatenate([np.zeros(self.n), np.zeros(n_features)])
        ub = np.concatenate([np.ones(self.n), np.inf * np.ones(n_features)])
        
        # Solve
        res = milp(c=c, constraints=[
            LinearConstraint(A_eq, b_eq, b_eq), # Equality
            LinearConstraint(A_ub, -np.inf, b_ub) # Inequality
        ], integrality=integrality, bounds=Bounds(lb, ub), options={"time_limit": time_limit})
        
        if not res.success:
            print(f"Optimization failed: {res.message}")
            # Fallback: Random
            return self._random_fallback(n_treatment)
            
        x_sol = res.x[:self.n]
        treatment_indices = np.where(x_sol > 0.5)[0]
        return treatment_indices.tolist()

    def _random_fallback(self, n_treatment):
        # Not implemented fully, just random for safety
        return np.random.choice(self.n, n_treatment, replace=False).tolist()
