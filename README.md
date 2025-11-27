# Optimized Supergeo Design (OSD)

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![GitHub](https://img.shields.io/badge/GitHub-shawcharles%2Fosd-blue)](https://github.com/shawcharles/osd)

A scalable, open-source framework for designing balanced geographic experiments at marketing scale.

## Overview

Geographic ("geo-lift") experiments remain a widely-used methodology for measuring the incremental return on ad spend (**iROAS**) of large advertising campaigns. Yet their design presents significant challenges: the number of markets is small, heterogeneity is large, and the exact Supergeo partitioning problem is NP-hard.

**OSD** addresses these challenges with a two-stage approach:

1. **PCA-based dimensionality reduction** creates interpretable geo-embeddings and generates candidate *supergeos* via hierarchical clustering.
2. **Mixed-Integer Linear Programming (MILP)** selects a treatment/control partition that balances both baseline outcomes and effect modifiers.

### Key Results

- **Statistical Parity with Randomization:** PCA-based clustering achieves statistical performance equivalent to unit-level randomization (1.07× RMSE ratio, p=0.68, n.s.)
- **Operational Benefits:** Enables coarser granularity for media buying without sacrificing statistical power
- **Scalability:** Completes in **< 60 seconds** on a single core for N=1,000 DMAs
- **Excellent Balance:** All standardized mean differences < 1%

Under mild community-structure assumptions, OSD's objective value is within $(1+\varepsilon)$ of optimal.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/shawcharles/osd.git
cd osd

# Create virtual environment and install dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the ablation study (generates CSV results)
python src/experiments/ablation_study.py

# Generate all publication plots
python scripts/generate_paper_plots.py

# Run scalability benchmark (optional)
python scripts/benchmark_scalability.py --output scalability_results.csv
```

> **Note:** The ablation study runs 50 Monte Carlo replications at N=40 and N=200, taking approximately 15-20 minutes on a modern laptop.

---

## Repository Structure

| Path | Purpose |
|------|---------|
| `latex/` | LaTeX source for the research paper |
| `src/osd/` | Core Python implementation (PCA, clustering, MILP optimization) |
| `src/experiments/` | Monte Carlo ablation studies and robustness tests |
| `scripts/` | Plotting and visualization tools |
| `memory-bank/` | Comprehensive project documentation and review findings |
| `results/` | Experimental outputs (CSVs) |
| `tests/` | Unit tests for core algorithms and statistical methods |

---

## Reproducing Paper Results

All results in the paper can be reproduced from the codebase. Here's a step-by-step guide:

### 1. Run the Ablation Study

```bash
# Run 50 Monte Carlo replications comparing methods at N=40 and N=200
python src/experiments/ablation_study.py
```

**Outputs:**
- `ablation_results_small_n.csv` — Aggregated metrics (RMSE, bias, SMD, bootstrap CIs)
- `ablation_per_rep_small_n.csv` — Per-replication data for all methods
- `ablation_stats_small_n.csv` — Statistical test results (Holm-Bonferroni adjusted p-values)

**Runtime:** ~15-20 minutes on a modern laptop

### 2. Generate All Figures

```bash
# Create all publication-ready plots
python scripts/generate_paper_plots.py
```

**Outputs:** (saved to `latex/figures/`)
- `ablation_comparison.pdf` — RMSE and runtime comparison (Section 8.3)
- `ablation_boxplot.pdf` — Error distributions across replications
- `covariate_balance.pdf` — SMD balance metrics
- `power_analysis.pdf` — Statistical power curves (illustrative)
- `scalability.pdf` — Runtime vs N comparison

### 3. Build the Paper

```bash
cd latex
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

**Output:** `main.pdf` — Full research paper with all figures and tables

---

## Statistical Rigor

This codebase implements rigorous statistical methodology:

- **Bootstrap Confidence Intervals:** Percentile method with 1,000 resamples
- **Multiple Testing Correction:** Holm-Bonferroni for family-wise error rate control
- **Effect Sizes:** Cohen's d for practical significance
- **True Random Baseline:** Unit-level randomization for unbiased comparison
- **Proper SMD Calculation:** Pooled within-group std with Bessel's correction

**Reproducibility Score:** 9/10 (per comprehensive zero-trust review)

---

## Testing

Run unit tests to verify core algorithms:

```bash
# Run all tests
pytest tests/ -v

# Run specific test modules
pytest tests/test_smd.py -v
pytest tests/test_statistical_methods.py -v
```

---

## Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for detailed guidelines.

---

## License

Apache 2.0 — see [`LICENSE`](LICENSE) for details.

## Citation

If you use this codebase in academic work, please cite:

```bibtex
@article{Shaw2025OSD,
  title   = {Optimized Supergeo Design: A Scalable Framework for Geographic Marketing Experiments},
  author  = {Charles Shaw},
  journal = {Under Review},
  year    = {2025}
}
