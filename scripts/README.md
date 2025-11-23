# Scripts

This directory contains utility scripts for the Optimized Supergeo Design project.

## Available Scripts

### `generate_paper_plots.py` ⭐ **Recommended**

Generate all publication-ready plots for the OSD paper.

**Usage:**
```bash
python scripts/generate_paper_plots.py
```

**Inputs:**
- Reads from `results/ablation_results.csv` (if available)
- Uses paper-reported values as fallback

**Outputs (to `latex/figures/`):**
- `ablation_comparison.pdf` - Figure for Section 8.3 (RMSE + Runtime comparison)
- `ablation_boxplot.pdf` - RMSE distributions across Monte Carlo replications
- `power_analysis.pdf` - Figure for Section 8.1 (Statistical power curves)
- `scalability.pdf` - Figure for Section 8.2 (Runtime vs N, cites Chen et al. 2023)
- `covariate_balance.pdf` - Covariate balance demonstration

All figures use publication-quality settings (300 DPI, serif fonts, consistent color scheme).

**Note on Scalability Plot:**
The scalability plot compares OSD to Chen et al. (2023)'s exact MIP approach. Chen reported 
the exact method requires "weeks" for N=210 DMAs. We cite this and use exponential projection 
for smaller N (appropriate for NP-hard problems). See `notes/SCALABILITY_PLOT_METHODOLOGY.md` 
for full methodology and scientific justification.

---

### `plot_results.py`

General-purpose plotting utility for experimental results.

**Usage:**
```bash
python scripts/plot_results.py --csv results/experiment_results.csv
```

**Inputs:**
- CSV file with experimental results (detailed rows + summary section)

**Outputs:**
- `abs_bias_boxplot.pdf` - Box plot of absolute bias by method
- `rmse_bar.pdf` - Bar chart of RMSE by method

**Options:**
- `--csv` - Path to input CSV (required)
- `--out-dir` - Output directory for plots (default: `paper_assets/`)

---

## Running Experiments

The main experimental pipelines are implemented in:
- `src/experiments/ablation_study.py` - Embedding method comparison
- `src/experiments/robustness_study.py` - Robustness analysis
- Other experiment modules in `src/experiments/`

Run these from the project root:

```bash
# Example: Run ablation study
python -m src.experiments.ablation_study

# Results will be saved to results/ directory
```

---

## Legacy Scripts

Previous versions of this repository contained additional benchmark scripts that referenced the old "Adaptive Supergeo Design" naming and implementation. These have been removed during the refactoring to Optimized Supergeo Design (OSD).

If you need to benchmark the current OSD implementation, please refer to the experiment modules in `src/experiments/` or create new scripts based on the updated architecture.

---

## Adding New Scripts

When adding new utility scripts:

1. **Use current naming:** Reference "OSD" or "Optimized Supergeo Design", not "ASD"
2. **Import from src/:** Use the current module structure in `src/asd/`
3. **Add CLI arguments:** Use `argparse` for flexibility
4. **Document usage:** Include docstring with examples
5. **Output to results/:** Save experimental outputs to `results/` directory
6. **Update this README:** Add your script to the "Available Scripts" section

---

## Questions?

See the main [README.md](../README.md) for project overview and setup instructions.
