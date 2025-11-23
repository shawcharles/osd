# EDITORIAL DECISION LETTER

**Manuscript:** "Adaptive Supergeo Design: A Scalable Framework for Geographic Marketing Experiments"  
**Submission to:** *Journal of Causal Inference*  
**Decision:** **Major Revision (Conditional Reject)**

---

## ⚖️ EDITORIAL DECISION

This manuscript presents a two-stage approach combining graph neural networks with mixed-integer programming for geographic experimental design. While the engineering is competent and the problem is practically relevant, the paper fails to meet the scientific standards required for publication in this venue.

**Primary concerns:**
1. No ablation study demonstrating the GNN is necessary
2. Weak baseline comparisons
3. Unrealistically favorable simulation design
4. Theoretical claims without rigorous proof
5. Marketing language inappropriate for academic publication

I would consider a substantially revised version that addresses these fundamental issues.

---

## 📉 THE ABLATION CRITIQUE

**The Central Scientific Failure:** The paper introduces a GraphSAGE neural network but never demonstrates it outperforms simpler alternatives.

### Missing Comparisons

| Method | Complexity | Included? |
|--------|------------|-----------|
| GraphSAGE + HAC (proposed) | High | ✅ |
| PCA + K-Means | Low | ❌ |
| Spectral Clustering | Medium | ❌ |
| Geographic proximity clustering | Low | ❌ |
| Random candidate generation | Baseline | ❌ |

**The devastating question:** If PCA + K-Means produces equivalent candidate sets, why use a GNN?

The paper claims (Section 4.2):
> "We then employ a GraphSAGE model to learn an embedding $h_i \\in \\mathbb{R}^d$ for each geo"

But never shows:
- Embedding quality vs. PCA embeddings
- Clustering quality vs. simpler methods
- Design quality degradation when GNN is replaced

**Required experiment:** Run the full pipeline with Stage 1 replaced by:
1. PCA (d=32) + K-Means
2. Spectral clustering on k-NN graph
3. Geographic proximity clustering (lat/long)
4. Random assignment to clusters

If ASD does not significantly outperform these baselines, the GNN contribution is zero.

---

## 🔬 SIMULATION REALISM AUDIT

### Data Generating Process (`synthetic_data.py`)

```python
revenue = np.random.lognormal(10, 0.5, n_units)
spend = 0.12 * revenue * (1 + np.random.normal(0, 0.1, n_units))
pop = revenue * (1 + np.random.normal(0, 0.2, n_units))
income = np.random.normal(50000, 10000, n_units)
```

**Critique:**

| Aspect | Implementation | Real-World Validity |
|--------|----------------|---------------------|
| Revenue distribution | Log-normal | ⚠️ Plausible but σ=0.5 is low |
| Spend-revenue ratio | 12% ± 1.2% | ⚠️ Unrealistically tight |
| Population correlation | r ≈ 0.98 with revenue | ❌ Too deterministic |
| Income distribution | i.i.d. Normal | ❌ Spatially uncorrelated |
| Treatment effect heterogeneity | Linear in revenue | ⚠️ Favors covariate balance |
| Network structure | k-NN on features | ❌ Not geographic |

**Critical flaw:** The DGP is designed so that covariate balance directly reduces estimator variance. This circular reasoning guarantees ASD wins:

1. Treatment effects scale with revenue
2. Revenue is a covariate in the optimization
3. Optimizer balances revenue
4. Estimator has low variance

**A fair test would include:**
- Unobserved confounders that drive heterogeneity
- Non-linear treatment effect functions
- Spatial correlation in outcomes (not just features)
- Heavy-tailed distributions (σ > 1.0)

### Missing Scenarios

The paper claims robustness testing (Section 8) but the scenarios are soft:
- "Community structure violations" — but the GNN was designed for community structure
- "Heterogeneity variations" — within the linear model
- "Sample size effects" — doesn't test adversarial DGPs

**Required experiment:** Run simulations where:
1. Treatment effect depends on an unobserved covariate $U_i$
2. The covariate $U_i$ is correlated with geography but not features
3. Measure bias under this misspecification

If ASD's bias explodes, the Limitations section needs to quantify when the method fails.

---

## ✍️ RHETORICAL PRECISION

### Hype Detection in `main.tex` 

| Location | Problematic Text | Issue |
|----------|------------------|-------|
| Abstract | "gold-standard for measuring incremental return on ad spend" | Hyperbolic; geo experiments are *a* standard, not *the* gold standard |
| Abstract | "100% success rate" | Meaningless — success was self-defined |
| Abstract | "turns geo-lift testing into a routine, scalable component" | Marketing copy, not scientific claim |
| Section 1 | "formidable statistical and computational hurdles" | Dramatic; "challenges" suffices |
| Section 4.1 | "Our central insight" | Self-aggrandizing; state the insight without fanfare |
| Section 10 | "exceptional sensitivity" | Replace with "high power" |
| Conclusion | "game-changing" (if present) | Remove entirely |

### Defensiveness in Limitations Section

Current text:
> "While our design minimises conditional bias on observed covariates, it relies on the assumption that these covariates capture the primary sources of heterogeneity."

**Issue:** This is defensive framing. A proper limitation would state:

> "If unmeasured confounders drive treatment effect heterogeneity, ASD provides no protection against bias. Simulation studies (Appendix X) show bias increases by Y% when Z% of heterogeneity is driven by unobservables."

Without quantifying the failure mode, the limitation is lip service.

### Missing Acknowledgment

The paper never states:
> "We do not know if the GNN provides value over simpler methods."

This is the elephant in the room. Acknowledging uncertainty would strengthen, not weaken, the paper.

---

## 🚀 ACTIONABLE ROADMAP

To elevate this paper to JCI standards:

### Experiment 1: GNN Ablation (Critical)
- Replace GraphSAGE with PCA + K-Means, spectral clustering, and random clustering
- Report RMSE, bias, and runtime for each
- If GNN wins, explain *why* (what structure does it capture?)
- If GNN loses, remove it and simplify the method

### Experiment 2: Adversarial DGP (Critical)
- Create synthetic data with:
  - Unobserved confounder $U_i$ driving 50% of heterogeneity
  - Non-linear treatment effects: $\tau_i = \rho \cdot S_i \cdot (1 + X_i^2)$
  - Spatial correlation: $\text{Cov}(Y_i, Y_j) = \sigma^2 \exp(-d_{ij}/\ell)$
- Show when ASD fails and quantify the failure

### Experiment 3: Real Baseline Comparison (Important)
- Compare against:
  - GeoLift (Facebook's tool)
  - Randomized block design (stratified by region)
  - Gram-Schmidt Random Walk design [Harshaw et al., 2024]
- If ASD doesn't beat GSRW, the determinism critique is fatal

### Text Change 1: Rename the Method (Important)
- "Adaptive" is inaccurate
- Propose: "GNN-Optimized Supergeo Design" or "Heterogeneity-Aware Supergeo Design"
- Be honest about what the method does

### Text Change 2: Theory Section (Important)
- Either prove Proposition 1 rigorously (define constants, verify conditions) or remove it
- Replace with honest statement: "We conjecture that under community structure, ASD is near-optimal, but a formal proof remains open."

---

## SUMMARY

This paper solves a real problem with reasonable engineering. But it commits the cardinal sin of applied ML: using complex tools (GNNs, MILP) without demonstrating they outperform simple baselines. The simulations are designed to make the method look good, and the theory is hand-waving.

For a top causal inference journal, the bar is:
1. Prove your method works better than simpler alternatives
2. Show when it fails
3. State claims precisely

This paper does none of these convincingly.

**Path forward:** Conduct the ablation study. If the GNN wins, you have a paper. If it loses, you have a different (simpler, possibly better) paper.

---

*Signed,*  
*Senior Scientific Editor*
