# Changelog

All notable changes to the Optimized Supergeo Design project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Major Method Pivot:** Replaced Graph Neural Networks with Principal Component Analysis (PCA) as the default embedding method
- Renamed project from "Adaptive Supergeo Design (ASD)" to "Optimized Supergeo Design (OSD)" to reflect the methodological pivot
- Updated theoretical framework to reflect PCA-based variance preservation (Assumption 2)
- Simplified code architecture by removing GNN dependencies

### Added
- Comprehensive ablation study (Section 8.3) comparing PCA, Spectral, and Random embeddings
- Enhanced limitations section acknowledging statistical parity with randomization
- Writing style guidelines following *The Economist* and Williams principles
- Professional repository structure with proper .gitignore
- CONTRIBUTING.md for open source collaboration guidelines
- requirements.txt for clear dependency specification

### Removed
- Graph Neural Network implementation (`src/asd/models/gnn.py`)
- GNN-related dependencies and training code
- All itemized lists from paper (converted to flowing prose)
- Semicolons from academic prose (style improvement)
- Hype language ("100% success rate", "gold-standard", etc.)

### Fixed
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
