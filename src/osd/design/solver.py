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
                
        # Normalize features for numerical stability in MILP
        # Note: This normalization is for optimization only.
        # True SMD calculation uses pooled within-group std (see calculate_smd method)
        self.means = self.X.mean(axis=0)
        self.stds = self.X.std(axis=0) + 1e-6
        self.X_norm = (self.X - self.means) / self.stds
    
    def calculate_smd(self, vals_a, vals_b):
        """
        Calculate Standardized Mean Difference using pooled within-group standard deviation.
        
        This implements the SMD formula from the paper (Section 4.3):
        SMD(X) = (mean_A - mean_B) / sqrt((var_A + var_B) / 2)
        
        Args:
            vals_a: Array of values for group A
            vals_b: Array of values for group B
            
        Returns:
            SMD value
        """
        mean_a = np.mean(vals_a)
        mean_b = np.mean(vals_b)
        
        # Use ddof=1 for sample variance (Bessel's correction)
        var_a = np.var(vals_a, ddof=1) if len(vals_a) > 1 else 0.0
        var_b = np.var(vals_b, ddof=1) if len(vals_b) > 1 else 0.0
        
        # Pooled standard deviation
        pooled_std = np.sqrt((var_a + var_b) / 2)
        
        # Avoid division by zero
        if pooled_std < 1e-9:
            return 0.0
        
        return (mean_a - mean_b) / pooled_std

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
    
    def solve_multi_partition(self, candidate_partitions: List[List[Supergeo]], 
                             n_treatment: int, n_control: int, 
                             time_limit: float = 30.0, verbose: bool = False):
        """
        Solve the multi-partition selection problem as described in the paper.
        
        This implements Stage 2 of the OSD algorithm:
        - For each candidate partition, solve optimal T/C assignment
        - Select the partition with minimum cost
        
        Args:
            candidate_partitions: List of partitions (each is a List[Supergeo])
            n_treatment: Number of supergeos to assign to treatment
            n_control: Number of supergeos to assign to control
            time_limit: Time limit per partition optimization
            verbose: Print progress information
            
        Returns:
            Tuple of (best_partition_idx, treatment_indices, best_cost)
        """
        best_cost = np.inf
        best_partition_idx = 0
        best_treatment_indices = []
        
        if verbose:
            print(f"Evaluating {len(candidate_partitions)} candidate partitions...")
        
        for partition_idx, partition in enumerate(candidate_partitions):
            # Temporarily set this partition as the active one
            old_supergeos = self.supergeos
            old_n = self.n
            old_features = self.features
            old_X = self.X
            old_X_norm = self.X_norm
            
            try:
                # Re-initialize solver with this partition
                self.__init__(partition, self.weights)
                
                # Solve assignment for this partition
                treatment_indices = self.solve(n_treatment, n_control, time_limit)
                
                # Evaluate cost
                cost = self._evaluate_cost(treatment_indices)
                
                if verbose:
                    print(f"  Partition {partition_idx}: cost = {cost:.4f}")
                
                # Update best if this is better
                if cost < best_cost:
                    best_cost = cost
                    best_partition_idx = partition_idx
                    best_treatment_indices = treatment_indices
                    
            except Exception as e:
                if verbose:
                    print(f"  Partition {partition_idx}: failed with error {e}")
            finally:
                # Restore original state
                self.supergeos = old_supergeos
                self.n = old_n
                self.features = old_features
                self.X = old_X
                self.X_norm = old_X_norm
        
        if verbose:
            print(f"Selected partition {best_partition_idx} with cost {best_cost:.4f}")
        
        # Set the best partition as active
        self.__init__(candidate_partitions[best_partition_idx], self.weights)
        
        return best_partition_idx, best_treatment_indices, best_cost
    
    def evaluate_balance(self, treatment_indices):
        """
        Evaluate covariate balance for a given assignment using proper SMD calculations.
        
        This computes SMD for each feature using the pooled within-group standard deviation
        as defined in the paper (Section 4.3).
        
        Args:
            treatment_indices: List of supergeo indices assigned to treatment
            
        Returns:
            Dictionary mapping feature names to SMD values
        """
        t_idx = set(treatment_indices)
        c_idx = set(range(self.n)) - t_idx
        
        if len(t_idx) == 0 or len(c_idx) == 0:
            return {feat: np.inf for feat in self.features}
        
        smds = {}
        
        for feat_idx, feat_name in enumerate(self.features):
            # Get values for this feature (original scale, not normalized)
            t_vals = self.X[list(t_idx), feat_idx]
            c_vals = self.X[list(c_idx), feat_idx]
            
            # Compute SMD using proper formula
            smd = self.calculate_smd(t_vals, c_vals)
            smds[feat_name] = smd
        
        return smds
    
    def _evaluate_cost(self, treatment_indices, use_proper_smd=True):
        """
        Evaluate the cost (objective function value) for a given assignment.
        
        This computes the weighted sum of absolute SMDs across all features.
        
        Args:
            treatment_indices: List of supergeo indices assigned to treatment
            use_proper_smd: If True, use proper SMD calculation (pooled std).
                          If False, use normalized scale (for backward compatibility).
            
        Returns:
            Total cost (sum of weighted absolute SMDs)
        """
        t_idx = set(treatment_indices)
        c_idx = set(range(self.n)) - t_idx
        
        if len(t_idx) == 0 or len(c_idx) == 0:
            return np.inf
        
        total_cost = 0.0
        
        for feat_idx, feat_name in enumerate(self.features):
            # Get values for this feature
            t_vals = self.X[list(t_idx), feat_idx]
            c_vals = self.X[list(c_idx), feat_idx]
            
            if use_proper_smd:
                # Use proper SMD with pooled within-group std
                smd = abs(self.calculate_smd(t_vals, c_vals))
            else:
                # Use normalized scale difference (backward compatible)
                t_vals_norm = self.X_norm[list(t_idx), feat_idx]
                c_vals_norm = self.X_norm[list(c_idx), feat_idx]
                smd = abs(t_vals_norm.mean() - c_vals_norm.mean())
            
            # Apply weight
            weight = self.weights.get(feat_name, 1.0) if isinstance(self.weights, dict) else 1.0
            
            total_cost += weight * smd
        
        return total_cost
