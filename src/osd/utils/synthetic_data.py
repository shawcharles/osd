import numpy as np
from typing import List
from osd.utils.data_structures import GeoUnit

def generate_synthetic_data(n_units=200, effect_size=0.1, heterogeneity=0.5, 
                          spatial_confounding=0.0, non_linear_effect=False) -> List[GeoUnit]:
    """
    Generates synthetic geographic data with optional adversarial features.
    
    Args:
        n_units: Number of geographic units
        effect_size: Base treatment effect size (relative to spend)
        heterogeneity: Scale of heterogeneity driven by observed covariates
        spatial_confounding: Strength of unobserved spatial confounder (0.0 to 1.0)
                             0.0 = No unobserved confounding
                             1.0 = Heterogeneity driven entirely by unobserved spatial variable
        non_linear_effect: If True, treatment effect depends on quadratic/interaction terms
    """
    np.random.seed(42)
    
    # 1. Geography (Lat/Long) for spatial correlation
    # Generate points in a 2D grid [0,1]x[0,1]
    coords = np.random.rand(n_units, 2)
    
    # 2. Unobserved Spatial Confounder (U)
    # Generated via Gaussian Process-like smoothing over coords
    # Simple approximation: sum of radial basis functions
    U_raw = np.zeros(n_units)
    for _ in range(5):
        center = np.random.rand(2)
        width = np.random.uniform(0.1, 0.3)
        dist = np.sum((coords - center)**2, axis=1)
        U_raw += np.random.normal() * np.exp(-dist / width)
    U = (U_raw - U_raw.mean()) / (U_raw.std() + 1e-9) # Standardize
    
    # 3. Observed Covariates
    # Multi-modal distribution (Urban vs Rural)
    # 30% Urban (High Revenue, High Variance), 70% Rural (Low Revenue, Low Variance)
    is_urban = np.random.rand(n_units) < 0.3
    
    revenue = np.zeros(n_units)
    # Urban: LogNormal(12, 1.0) - Fat tail
    revenue[is_urban] = np.random.lognormal(12, 1.0, np.sum(is_urban))
    # Rural: LogNormal(10, 0.3) - Tight
    revenue[~is_urban] = np.random.lognormal(10, 0.3, np.sum(~is_urban))
    
    # Spend correlated with revenue but different ratios
    spend = np.zeros(n_units)
    spend[is_urban] = 0.15 * revenue[is_urban] * (1 + np.random.normal(0, 0.1, np.sum(is_urban)))
    spend[~is_urban] = 0.08 * revenue[~is_urban] * (1 + np.random.normal(0, 0.05, np.sum(~is_urban)))
    
    # Population 
    pop = np.zeros(n_units)
    pop[is_urban] = revenue[is_urban] * 0.5 # Dense
    pop[~is_urban] = revenue[~is_urban] * 2.0 # Sparse value but high pop? No, Rural has low rev/capita
    # Let's say Rural has Lower Rev/Pop.
    
    # Income
    income = np.zeros(n_units)
    income[is_urban] = np.random.normal(80000, 20000, np.sum(is_urban))
    income[~is_urban] = np.random.normal(40000, 5000, np.sum(~is_urban))
    
    # Add Unobserved spatial confounding to Income
    income += 10000 * U 
    
    # 4. Treatment Effect Generation
    # Base heterogeneity
    # Urban markets respond differently than Rural
    # observed_het = (is_urban - 0.3) + (revenue z-score)
    
    rev_z = (revenue - revenue.mean()) / revenue.std()
    observed_het = 1.0 * is_urban + 0.5 * rev_z
    
    if non_linear_effect:
        # Adversarial: Effect depends on Income^2 or interactions
        # Let's make it depend on (Income - Mean)^2 to punish linear balancing
        inc_z = (income - income.mean()) / (income.std() + 1e-9)
        observed_het = 0.5 * inc_z**2 + 0.5 * observed_het
        
    # Combine Observed and Unobserved Heterogeneity
    # tau_i = base * (1 + heterogeneity * ( (1-alpha)*Obs + alpha*Unobs ))
    
    # alpha = spatial_confounding
    alpha = spatial_confounding
    
    combined_driver = (1 - alpha) * observed_het + alpha * U
    
    tau = effect_size * spend * (1 + heterogeneity * combined_driver)
    
    units = []
    for i in range(n_units):
        units.append(GeoUnit(
            id=str(i),
            response=revenue[i],
            spend=spend[i],
            covariates={
                "population": pop[i],
                "income": income[i],
                # Hidden from the model: "spatial_U": U[i],
                # Hidden from the model: "true_lift": tau[i] / spend[i]
            }
        ))
        # Attach truth for evaluation (but not in covariates dict)
        units[-1].true_tau = tau[i]
        units[-1].latent_u = U[i]
        
    return units
