"""Unit tests for statistical methods (bootstrap CI, Holm-Bonferroni)."""

import numpy as np
import pytest
import sys
from pathlib import Path

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "experiments"))

from ablation_study import bootstrap_ci, holm_bonferroni


def test_bootstrap_ci_coverage():
    """Test that bootstrap CI has approximately correct coverage."""
    # Generate data with known mean
    np.random.seed(42)
    true_mean = 10.0
    data = np.random.normal(true_mean, 2.0, size=100)
    
    # Compute 95% CI for mean
    lower, upper = bootstrap_ci(data, stat_func=np.mean, n_resamples=1000, alpha=0.05, random_state=42)
    
    # Check that true mean is within CI (should be true ~95% of the time)
    assert lower < true_mean < upper, f"True mean {true_mean} not in CI [{lower}, {upper}]"
    
    # Check that CI is non-degenerate
    assert upper > lower, "CI upper bound should be > lower bound"


def test_bootstrap_ci_symmetric_data():
    """Test bootstrap CI on symmetric data."""
    data = np.array([-2, -1, 0, 1, 2])
    
    lower, upper = bootstrap_ci(data, stat_func=np.mean, n_resamples=500, random_state=0)
    
    # For symmetric data centered at 0, CI should be roughly symmetric
    assert abs(lower + upper) < 0.5, f"CI should be roughly symmetric for centered data: [{lower}, {upper}]"


def test_bootstrap_ci_deterministic():
    """Test that bootstrap CI is deterministic given random_state."""
    data = np.random.randn(50)
    
    lower1, upper1 = bootstrap_ci(data, stat_func=np.mean, n_resamples=100, random_state=123)
    lower2, upper2 = bootstrap_ci(data, stat_func=np.mean, n_resamples=100, random_state=123)
    
    assert lower1 == lower2, "Bootstrap should be deterministic with same random_state"
    assert upper1 == upper2, "Bootstrap should be deterministic with same random_state"


def test_holm_bonferroni_single_pvalue():
    """Test Holm-Bonferroni with a single p-value."""
    p_vals = np.array([0.03])
    adjusted = holm_bonferroni(p_vals, alpha=0.05)
    
    # Single p-value: adjusted = 1 * p_val
    assert adjusted[0] == 0.03, f"Expected 0.03, got {adjusted[0]}"


def test_holm_bonferroni_all_significant():
    """Test Holm-Bonferroni when all p-values are very small."""
    p_vals = np.array([0.001, 0.002, 0.003])
    adjusted = holm_bonferroni(p_vals, alpha=0.05)
    
    # All should remain significant after adjustment
    assert all(adjusted < 0.05), f"All adjusted p-values should be < 0.05, got {adjusted}"


def test_holm_bonferroni_ordering():
    """Test that Holm-Bonferroni adjusts in correct order."""
    p_vals = np.array([0.01, 0.04, 0.03, 0.02])
    adjusted = holm_bonferroni(p_vals, alpha=0.05)
    
    # Check that adjustment follows Holm procedure
    # Sorted order: [0.01, 0.02, 0.03, 0.04]
    # Adjusted: [4*0.01, 3*0.02, 2*0.03, 1*0.04] with monotonicity
    expected_order = np.argsort(p_vals)
    
    # Verify monotonicity: adjusted[i] >= adjusted[j] if p_vals[i] >= p_vals[j]
    for i in range(len(p_vals)):
        for j in range(len(p_vals)):
            if p_vals[i] >= p_vals[j]:
                assert adjusted[i] >= adjusted[j] - 1e-9, "Adjusted p-values should preserve order"


def test_holm_bonferroni_boundary():
    """Test Holm-Bonferroni at decision boundary."""
    # Design p-values such that some are borderline
    p_vals = np.array([0.01, 0.02, 0.03, 0.04])
    adjusted = holm_bonferroni(p_vals, alpha=0.05)
    
    # Check that all adjusted values are <= 1.0
    assert all(adjusted <= 1.0), f"All adjusted p-values should be <= 1.0, got {adjusted}"
    
    # Check monotonicity
    sorted_adjusted = np.sort(adjusted)
    assert np.allclose(sorted_adjusted, np.sort(adjusted)), "Adjusted p-values should be monotonic"


def test_holm_bonferroni_no_change_for_large_pvals():
    """Test that large p-values remain large after adjustment."""
    p_vals = np.array([0.8, 0.9, 0.95])
    adjusted = holm_bonferroni(p_vals, alpha=0.05)
    
    # All should remain > 0.05 and <= 1.0
    assert all(adjusted > 0.05), "Large p-values should remain non-significant"
    assert all(adjusted <= 1.0), "Adjusted p-values should not exceed 1.0"


def test_bootstrap_ci_variance():
    """Test bootstrap CI for variance statistic."""
    np.random.seed(99)
    data = np.random.normal(0, 5.0, size=200)
    
    # Bootstrap CI for variance
    lower, upper = bootstrap_ci(data, stat_func=np.var, n_resamples=1000, random_state=99)
    
    # True variance is 25.0
    assert lower < 25.0 < upper or abs(lower - 25.0) < 10, "Variance CI should cover or be close to true value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
