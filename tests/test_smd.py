"""Unit tests for Standardized Mean Difference (SMD) calculations."""

import numpy as np
import pytest
import sys
from pathlib import Path

# Add src directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from osd.design.solver import SupergeoSolver
from osd.utils.data_structures import Supergeo


def test_smd_identical_groups():
    """Test SMD calculation when groups are identical (should be 0)."""
    vals_a = [1.0, 2.0, 3.0, 4.0, 5.0]
    vals_b = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    solver = SupergeoSolver([])
    smd = solver.calculate_smd(vals_a, vals_b)
    
    assert abs(smd) < 1e-9, f"Expected SMD ≈ 0, got {smd}"


def test_smd_known_value():
    """Test SMD calculation with known expected value."""
    # Group A: mean=5, var=2
    vals_a = [4.0, 5.0, 6.0]
    # Group B: mean=7, var=2
    vals_b = [6.0, 7.0, 8.0]
    
    # Expected SMD = (5-7) / sqrt((2+2)/2) = -2 / sqrt(2) ≈ -1.414
    expected_smd = -2.0 / np.sqrt(2.0)
    
    solver = SupergeoSolver([])
    smd = solver.calculate_smd(vals_a, vals_b)
    
    assert abs(smd - expected_smd) < 0.01, f"Expected SMD ≈ {expected_smd}, got {smd}"


def test_smd_pooled_std_formula():
    """Verify SMD uses pooled within-group std with Bessel's correction."""
    vals_a = np.array([10.0, 12.0, 14.0, 16.0])
    vals_b = np.array([20.0, 22.0, 24.0, 26.0])
    
    mean_a = np.mean(vals_a)  # 13.0
    mean_b = np.mean(vals_b)  # 23.0
    var_a = np.var(vals_a, ddof=1)  # Bessel's correction
    var_b = np.var(vals_b, ddof=1)  # Bessel's correction
    pooled_std = np.sqrt((var_a + var_b) / 2.0)
    expected_smd = (mean_a - mean_b) / pooled_std
    
    solver = SupergeoSolver([])
    smd = solver.calculate_smd(vals_a, vals_b)
    
    assert abs(smd - expected_smd) < 1e-9, f"Expected {expected_smd}, got {smd}"


def test_smd_zero_variance():
    """Test SMD when both groups have zero variance."""
    vals_a = [5.0, 5.0, 5.0]
    vals_b = [5.0, 5.0, 5.0]
    
    solver = SupergeoSolver([])
    smd = solver.calculate_smd(vals_a, vals_b)
    
    # Should return 0 when pooled_std < 1e-9
    assert abs(smd) < 1e-9


def test_smd_large_difference():
    """Test SMD with large mean difference."""
    vals_a = [0.0, 1.0, 2.0]
    vals_b = [100.0, 101.0, 102.0]
    
    solver = SupergeoSolver([])
    smd = solver.calculate_smd(vals_a, vals_b)
    
    # Large difference should result in large |SMD|
    assert abs(smd) > 50.0, f"Expected large |SMD|, got {smd}"


def test_smd_single_value_groups():
    """Test SMD with single-value groups (edge case)."""
    vals_a = [5.0]
    vals_b = [10.0]
    
    solver = SupergeoSolver([])
    smd = solver.calculate_smd(vals_a, vals_b)
    
    # With single values, variance is 0, pooled_std is 0, should handle gracefully
    assert not np.isnan(smd), "SMD should not be NaN"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
