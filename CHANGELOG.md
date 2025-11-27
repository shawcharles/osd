# Changelog

All notable changes to the Optimized Supergeo Design project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Critical Bug Fixes (27 Nov 2025)
- **Fixed Random Seed Bug:** Removed fixed `np.random.seed(42)` from `generate_synthetic_data()` function body, causing all Monte Carlo replications to use identical data. Now uses optional `seed` parameter with per-replication seeding.
- **Fixed SMD Implementation:** Corrected Standardized Mean Difference calculation to use pooled within-group standard deviation with Bessel's correction, matching statistical definition in Section 4.3.
- **Fixed Fabricated Boxplot:** Updated `plot_ablation_boxplot()` to read from `ablation_per_rep_small_n.csv` instead of using simulated data via `np.random.normal()`.
- **Algorithm Concordance:** Implemented missing multi-partition selection algorithm to match paper's description (code was using single-partition approach).

### Added (27 Nov 2025)
- **Multi-partition Selection:** Added `generate_candidate_partitions()` and `solve_multi_partition()` methods implementing two-stage algorithm from Section 4.3
- **Statistical Rigor Enhancements:**
  - Bootstrap 95% confidence intervals (`bootstrap_ci()` function)
  - Holm-Bonferroni multiple testing correction
  - Cohen's d effect sizes for practical significance
  - Paired t-tests on squared errors
- **True Random Baseline:** Added `unit_random` method for unit-level randomization comparison
- **Proper SMD Calculation:** Implemented `calculate_smd()` using pooled std: SMD = (μ_A - μ_B) / √((σ²_A + σ²_B)/2)
- **Balance Evaluation:** Added `evaluate_balance()` method to compute SMDs for all features
- **Comprehensive Documentation:**
  - `memory-bank/scientific_review_prompt.md` — Zero-trust verification framework
  - `memory-bank/osd_comprehensive_review.md` — 15-issue detailed review
  - `memory-bank/implementation_fixes_summary.md` — Technical fix summary
  - `memory-bank/zero_trust_review_final.md` — Final assessment (Reproducibility: 2/10 → 9/10)

### Changed (27 Nov 2025)
- **Per-replication Seeding:** Ablation study now computes unique seeds per replication: `seed = base_seed + rep + n*1000 + hash(method)%10000`
- **Plotting Pipeline:** All plots now attempt to read from real experimental CSV files before falling back to synthetic defaults
- **Solver Normalization:** Clarified that `X_norm` is for MILP numerical stability only; true SMD uses original scale

### Changed (Earlier)
- **Major Method Pivot:** Replaced Graph Neural Networks with Principal Component Analysis (PCA) as the default embedding method
- Renamed project from "Adaptive Supergeo Design (ASD)" to "Optimized Supergeo Design (OSD)" to reflect the methodological pivot
- Updated theoretical framework to reflect PCA-based variance preservation (Assumption 2)
- Simplified code architecture by removing GNN dependencies

### Added (Earlier)
- Comprehensive ablation study (Section 8.3) comparing PCA, Spectral, and Random embeddings
- Enhanced limitations section acknowledging statistical parity with randomization
- Professional repository structure with proper .gitignore
- CONTRIBUTING.md for open source collaboration guidelines
- requirements.txt for clear dependency specification

### Removed
- Graph Neural Network implementation (`src/asd/models/gnn.py`)
- GNN-related dependencies and training code
- All itemized lists from paper (converted to flowing prose)
- Semicolons from academic prose (style improvement)
- Hype language ("100% success rate", "gold-standard", etc.)

### Fixed (Earlier)
- All passive voice constructions in key sections
- Weak verbs replaced with stronger, more specific verbs
- Inconsistent terminology (ASD → OSD throughout)

## [0.1.0] - 2025-01-XX

### Initial Research Implementation
- Two-stage heuristic: PCA + MILP optimization
- Synthetic data generation with multi-modal structure
- Ablation framework for embedding method comparison
- LaTeX manuscript with comprehensive simulations

---

## Key Scientific Findings

### Ablation Study Results (N=200, 50 replications)
| Method | RMSE | Relative to Random |
|--------|------|---------------------|
| Random | 1,111 | 1.00× (baseline) |
| **PCA** | **1,184** | **1.07×** (p=0.68, n.s.) |
| Spectral | 4,820 | 4.34× |

**Conclusion:** PCA achieves statistical parity with randomization while enabling operational benefits through Supergeo formation.
