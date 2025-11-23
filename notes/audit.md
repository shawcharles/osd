# 🔬 Comprehensive Red Team Audit Report
## Adaptive Supergeo Design: Code-Paper Fidelity & Methodological Review

**Auditor:** Distinguished Professor of Causal Inference and Machine Learning  
**Date:** 23 November 2025  
**Classification:** Pre-submission Internal Review  
**Severity Rating:** 🔴 Critical issues requiring immediate remediation

---

## Executive Summary

This audit reveals a fundamental disconnect between the manuscript narrative and the actual implementation. The codebase has been modernised to use PyTorch and SciPy, but the paper retains artefacts from an older architecture (CP-SAT, GAT hybrid). While the referee concerns about statistical impossibilities have been addressed, several critical discrepancies remain that would trigger immediate desk rejection at a top-tier venue.

---

## Part I: Code-to-Paper Fidelity Audit

### 🚨 Critical Finding 1: Internal Solver Inconsistency

The paper contains **contradictory statements** about the optimisation solver:

| Document Location | Stated Technology | Actual Implementation |
|---|---|---|
| **Section 4.3** (Methodology) | scipy.optimize.milp solver | ✅ Matches code |
| **Section 5.2** (Theory) | "CP-SAT integer program... is *globally optimal*" | ❌ Does not match |
| **Section 8.2** (Experiments) | "Google OR-Tools CP-SAT 9.7" | ❌ Does not match |
| **Table 3** | "30~s ILP cutoff" | ⚠️ Ambiguous |
| **Code** (solver.py) | scipy.optimize.milp | — |

**Evidence from solver.py:106-108:**
```python
res = milp(c=c, constraints=[
    LinearConstraint(A_eq, b_eq, b_eq),
    LinearConstraint(A_ub, -np.inf, b_ub)
], integrality=integrality, bounds=Bounds(lb, ub), options={"time_limit": time_limit})
```

**Impact:** The theoretical guarantee in Proposition 1 ("globally optimal") is predicated on CP-SAT's complete search. SciPy's milp uses HiGHS, which is a branch-and-cut solver that may return heuristic solutions under time limits. The claim of global optimality is **not justified** by the current implementation.

**Recommendation:** Either (a) replace all CP-SAT references with scipy.milp and remove the "globally optimal" claim, or (b) actually implement OR-Tools CP-SAT to match the paper.

---

### 🚨 Critical Finding 2: GAT Architecture Does Not Exist

**Paper (Appendix: Practical Guidance):**
> "Recommended defaults: 2 GAT layers (8 heads, 64 hidden) → GraphSAGE (32 dim), γ=0.5"

**Paper (Section 4.2: Methodology):**
> "We then employ a GraphSAGE model"

**Actual Code (gnn.py):**
```python
class GraphSAGE(nn.Module):
    """A simple GraphSAGE-style GNN implemented in pure PyTorch."""
```

The codebase contains **only** a GraphSAGE class. There is:
- No GAT class
- No attention mechanism
- No multi-head attention
- No γ parameter

**Impact:** The Appendix provides deployment guidance that is impossible to follow with the current codebase. Any practitioner attempting to replicate the "recommended defaults" will fail.

**Recommendation:** Remove all GAT references from the Appendix. Update recommended defaults to match actual implementation: GraphSAGE(in_features, 64, 32, num_layers=2, dropout=0.5).

---

### ⚠️ Finding 3: Hyperparameter Verification

| Parameter | Paper (Section 4.2) | Code Location | Match? |
|---|---|---|---|
| Architecture | GraphSAGE | gnn.py:5 | ✅ |
| Hidden dimension | 64 | gnn.py via candidate_generation.py:30 | ✅ |
| Output dimension | 32 | candidate_generation.py:6 | ✅ |
| Number of layers | 2 | gnn.py:9 (default) | ✅ |
| Dropout | "Dropout for regularization" | gnn.py:10 = 0.5 | ⚠️ Unspecified |
| Learning rate | 10⁻² | candidate_generation.py:31 = 0.01 | ✅ |
| Epochs | 100 | candidate_generation.py:31 = 100 | ✅ |
| Activation | ReLU | gnn.py:51 | ✅ (matches description) |
| Contrastive margin | Not stated | gnn.py:65 = 1.0 | ❌ Missing |

**Recommendation:** Specify all hyperparameters explicitly, including dropout rate (0.5) and contrastive loss margin (1.0).

---

## Part II: Methodological & Theoretical Rigour

### 📉 Issue 1: Objective Function Formulation

**Paper's Mathematical Claim (Section 4.3):**
$$\min_{z, y} \left( |\text{SMD}(\text{Baseline})| + \sum_{m} \lambda_m\, |\text{SMD}(\text{Modifier}_m)| \right)$$

where SMD is defined as:
$$\text{SMD}(X) = \frac{\bar{X}_A - \bar{X}_B}{\sqrt{(\sigma_A^{2} + \sigma_B^{2})/2}}$$

**Actual Implementation (solver.py:47-95):**

The code implements a **linearised proxy**:
1. Normalises features: X_norm = (X - means) / stds 
2. Computes target sum: target_sum = total_sum * (n_treatment / (n_treatment + n_control)) 
3. Minimises auxiliary variables: min Σ(w_k * u_k) subject to -u_k ≤ Σ(x_i * X_norm[i,k]) - target_k ≤ u_k 

**Analysis:** This formulation minimises the absolute deviation of **group sums** from a proportional target, then weights by feature-level weights. This is **not identical** to minimising the pooled-standard-deviation SMD, especially when:
- Group sizes (number of supergeos) differ from underlying unit counts
- Supergeos contain different numbers of original geos

**Severity:** Medium. The linearisation is a valid heuristic but the paper should explicitly describe the auxiliary variable formulation rather than claiming to minimise |SMD| directly.

**Recommendation:** Add a paragraph in Section 4.3 explaining the MILP linearisation technique for absolute value objectives.

---

### 📉 Issue 2: Randomisation vs. Determinism (Reviewer 1's Core Concern)

**Reviewer 1's Original Critique:**
> "Once the Supergeos are partitioned into two groups, I can only really think about two possible randomizations... this approach theoretically cannot protect against the case where there is some important *unmeasured* confounder"

**Paper's Current Response (Section 10: Conclusion):**
> "Unlike pure randomisation or recent advances such as Gram–Schmidt Random Walks, our deterministic optimisation approach does not guarantee balance on unobserved confounders. While our design minimises conditional bias on observed covariates, it relies on the assumption that these covariates capture the primary sources of heterogeneity."

**Assessment:** This is an improvement but inadequate for a top-tier venue because:
1. It is buried in the Conclusion rather than a prominent Limitations section
2. It provides no theoretical or empirical argument for when observed-covariate balance is "sufficient"
3. It does not engage with the GSRW suggestion

**Recommendation:** 
- Create a dedicated **Section 5.3: Limitations and Scope** 
- Provide simulation evidence showing performance degradation under unobserved confounding
- Cite and discuss relationship to GSRW [Harshaw et al., 2024]

---

### 📉 Issue 3: Proofs Remain Incomplete (Reviewer 2's Critique)

**Appendix A Header:**
> "Proof **Sketch** of Proposition 1"

**Lemma 1 Proof:**
> "[Idea] Apply Hoeffding bounds to the random adjacency matrix..."

**Reviewer 2's Original Complaint:**
> "The proofs contained in the appendix are far from complete. Indeed, they are referred to as 'Sketch' and 'Idea' in the LaTeX rather than 'Proof'."

**Assessment:** This has **not been fixed**. The proofs remain labelled as sketches.

**Recommendation:** Either complete the proofs with full mathematical rigour, or honestly relabel Proposition 1 as a "Conjecture" with supporting intuition.

---

## Part III: Code Quality & Reproducibility

### 💻 Issue 1: Negative Sampling Corruption (gnn.py:84-92)

```python
neg_indices = torch.randint(0, embeddings.size(0), (num_pairs,))
v_neg = embeddings[neg_indices]
```

**Problem:** Random indices can sample actual neighbours (positive pairs) as negatives, creating false negative examples that corrupt the contrastive signal.

**Mitigation Factor:** With k-NN graph (k=10) on N=200 nodes, collision probability ≈ 5% per sample. With neg_samples=5, expected noise is manageable but non-zero.

**Recommendation:** Implement proper negative sampling that excludes positive edges:
```python
# Create a mask of non-edges
non_edges = (adj == 0).float()
# Sample from non-edges only
```

---

### 💻 Issue 2: Covariate Aggregation Bias (candidate_generation.py:71-77)

```python
# Heuristic: Average them.
for f in self.feature_names:
    covs[f] /= len(units)
```

**Problem:** All covariates are averaged uniformly. This is:
- **Correct** for intensive variables (income, temperature)
- **Incorrect** for extensive variables (population, total spend)

The synthetic data includes population (extensive) and income (intensive).

**Impact:** When supergeos of different sizes are formed, averaging population underweights larger supergeos in the balance calculation.

**Recommendation:** Distinguish variable types:
```python
extensive_vars = ["population", "response", "spend"]
intensive_vars = ["income"]
for f in extensive_vars:
    covs[f] = sum(u.covariates.get(f, 0) for u in units)  # Sum
for f in intensive_vars:
    weights = [u.covariates.get("population", 1) for u in units]
    covs[f] = np.average([u.covariates.get(f, 0) for u in units], weights=weights)
```

---

### 💻 Issue 3: Misleading Fallback Name (solver.py:111-113)

```python
def _greedy_fallback(self, n_treatment):
    # Simple greedy sort
    # Not implemented fully, just random for safety
    return np.random.choice(self.n, n_treatment, replace=False).tolist()
```

**Problem:** Method is named _greedy_fallback but implements **random selection**, not greedy optimisation.

**Impact:** Confuses maintainers; any logging/debugging that reports "using greedy fallback" is misleading.

**Recommendation:** Rename to _random_fallback or implement actual greedy selection (e.g., sort by imbalance contribution).

---

## Part IV: Referee Rebuttal Scorecard

| Reviewer | Issue | Status | Evidence |
|---|---|---|---|
| **R1-1** | Randomisation / underpowered | ⚠️ PARTIAL | Acknowledged in Conclusion but not formally addressed |
| **R1-2a** | Results show ASD has worst bias/RMSE | ✅ FIXED | Table 1 now shows ASD-TM as best |
| **R1-2b** | "Mean Balance" undefined | ✅ FIXED | Caption now defines it |
| **R1-2c** | Std Power > 0.5 impossible | ✅ FIXED | Now "Mean Power" with valid [0,1] values |
| **R1-2d** | Sections 9.8-9.13 not performed | ⚠️ UNCLEAR | Sections renumbered |
| **R1-3** | Neyman-Rubin not stated | ✅ FIXED | Section 3.1 now includes SUTVA |
| **R1-3a** | Adjacency matrix assumptions unclear | ⚠️ PARTIAL | Some clarification but still relies on "Bernoulli" assumption without justification |
| **R1-3b** | Lemma verification difficult | ⚠️ UNCHANGED | Still cites "Theorem 3 of [vonLuxburg2010]" without elaboration |
| **R1-3c** | Asymptotic N→∞ meaning unclear | ⚠️ UNCHANGED | No clarification provided |
| **R1-4c** | SMD should be \|SMD\| | ✅ FIXED | Paper now shows \|SMD\| |
| **R1-5** | Lack of citations | ⚠️ PARTIAL | Bibliography expanded but specific in-text citations still sparse |
| **R1-6** | "Adaptive" misnomer | ⚠️ WEAK | Added parenthetical "(also interpretable as 'Intelligent Supergeo Design')" |
| **R2** | Design motivation unclear | ⚠️ PARTIAL | More text but variance reduction not mathematically proven |
| **R2** | Incomplete proofs | ❌ UNCHANGED | Still "Sketch" and "Idea" |
| **R2** | NP-Hardness not removed | ❌ UNCHANGED | Paper claims scalability while using MILP |
| **R2** | Hyperparameter tuning infeasible | ⚠️ PARTIAL | CV framework described but feasibility concern not directly addressed |
| **R2** | GNN objective not specified | ✅ FIXED | Contrastive loss now described |
| **R2** | Assumption 5.2 trivialised by identity embedding | ❌ UNCHANGED | No response to this critique |

**Overall Score:** 11/20 issues adequately addressed (55%)

---

## Part V: "Reviewer 2" Simulation — Anticipated Rejection Points

### 1. Hand-Waving Detection
- **Proposition 1** claims $(1+\varepsilon)$ approximation but proofs remain "sketches"
- **"Sub-quadratic complexity"** claimed but MILP is exponential worst-case
- **"Globally optimal"** claim incompatible with scipy.milp under time limits

### 2. Scalability Under Scrutiny
The paper claims "ASD completes in under a minute on a single core" for N=1000. However:
- GNN inference: O(N² · d) for dense adjacency (k-NN creates sparse, so O(Nk · d))
- MILP: Exponential worst-case, heuristic average-case
- Table 3 shows "infeasible" for exact solver at N=800

This is a **valid scalability result** but the framing as "scalable" while competitors are "intractable" is oversold.

### 3. "Adaptive" Terminology
The method does not adapt during the experiment. It is:
- Not online (no sequential updates)
- Not adaptive to incoming data
- A one-shot optimisation

Better terms: "Optimised", "Intelligent", "Learning-based"

---

## Part VI: Consolidated Action Plan

### 🔴 Must Fix Before Submission (Critical)

| # | Issue | File(s) | Action |
|---|---|---|---|
| 1 | CP-SAT references | main.tex | Remove ALL mentions of CP-SAT and OR-Tools; replace with "scipy.optimize.milp" |
| 2 | Global optimality claim | main.tex Section 5.2 | Remove or qualify: "The MILP solver returns a *high-quality solution* (often optimal for small instances)" |
| 3 | GAT architecture | main.tex Appendix | Delete "2 GAT layers (8 heads, 64 hidden) →" |
| 4 | γ parameter | main.tex Appendix | Delete reference to γ=0.5 (does not exist in code) |

### 🟠 High Priority (Methodological)

| # | Issue | File(s) | Action |
|---|---|---|---|
| 5 | Limitations section | main.tex | Create Section 5.3 "Limitations" addressing unobserved confounders |
| 6 | Proof completeness | main.tex Appendix A | Either complete proofs or relabel Proposition 1 as "Conjecture" |
| 7 | MILP linearisation | main.tex Section 4.3 | Add paragraph explaining auxiliary variable technique |
| 8 | Covariate aggregation | candidate_generation.py | Distinguish extensive vs intensive variables |

### 🟡 Medium Priority (Code Quality)

| # | Issue | File(s) | Action |
|---|---|---|---|
| 9 | Negative sampling | gnn.py | Exclude positive edges from negative samples |
| 10 | Fallback naming | solver.py | Rename _greedy_fallback → _random_fallback |
| 11 | Hyperparameter documentation | main.tex | Specify dropout=0.5, margin=1.0 |

### 🟢 Low Priority (Polish)

| # | Issue | File(s) | Action |
|---|---|---|---|
| 12 | "Adaptive" terminology | main.tex | Consider renaming to "Optimised Supergeo Design" |
| 13 | In-text citations | main.tex | Add specific citations where Reviewer 1 noted gaps |

---

## Conclusion

The Adaptive Supergeo Design represents a creative and potentially valuable contribution to geographic experimental design. The core algorithmic innovation — using GNN embeddings to generate candidate supergeos followed by MILP optimisation — is sound and addresses a genuine need in marketing science.

However, the current manuscript contains **fatal inconsistencies** between the described and implemented algorithms that would be immediately detected by any competent reviewer. The theoretical claims exceed what the implementation can deliver, and several referee concerns remain unaddressed.

With the fixes outlined above, the paper could be strengthened to meet the standards of a top-tier venue such as the *Journal of Causal Inference*, *Marketing Science*, or *Journal of the American Statistical Association*.

---

