import numpy as np

from midgard.gnss import solution_validation


def test_chi_squared_test_validated():
    """Test something TODO"""
    alpha_siglev = 0.01
    n_params = 5
    az = np.array([62.3, 87.2, 146.9, 61.5, 80.4, 60.2, 61.2, 46.8, 33.4])
    el = np.array([44.7, 47.3, 44.3, 81.3, 49.8, 34.7, 43.1, 71.0, 9.7])
    residuals = np.array(
        [0.58491034, -0.00412977, 0.60034029, 0.32305734, 0.13233223, 0.9004102, -1.19893119, -1.94621535, -0.80949456]
    )

    result = solution_validation.sol_validation(residuals, alpha_siglev, n_params, az, el)
    expected = True

    assert result == expected
