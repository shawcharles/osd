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

## Quick start

```bash
# clone your fork then
python3 -m venv venv && source venv/bin/activate
pip install -e .[dev]            # installs ASD and its dependencies

# design an experiment (example synthetic data)
python scripts/asd_design.py  \
       --input paper_assets/synthetic_units.csv \
       --output my_design.csv

# run the scalability benchmark & plot (Fig 2 of the paper)
python scripts/benchmark_scalability.py \
       --csv paper_assets/runtime_results.csv \
       --pdf paper_assets/scalability_plot.pdf
```

> **Note** `benchmark_scalability.py` automatically skips the (slow) exact ILP solver for *N* > 400.

---

## Repository Structure

| Path | Purpose |
|------|---------|
| `latex/` | LaTeX source for the research paper |
| `src/asd/` | Core Python implementation (PCA, clustering, MILP optimization) |
| `scripts/` | CLI tools for design, analysis, and benchmarking |
| `notes/` | Internal development notes (excluded from git) |

---

## Building the Paper

```bash
cd latex
latexmk -pdf main.tex   # compile, repeat to resolve references
```

The build produces `main.pdf`, which contains the full research paper on Optimized Supergeo Design.

---

## Contributing
Pull requests are welcome!  Please open an issue first to discuss major changes.

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
```
