"""Tests of tools."""


import numpy as np


from openfisca_france_pension.tools import mean_over_k_nonzero_largest


def test_mean_over_k_nonzero_largest():
    array = np.array([100] * 5 + [1000] * 5)
    assert mean_over_k_nonzero_largest(array, 4) == 1000
    assert mean_over_k_nonzero_largest(array, 5) == 1000
    assert mean_over_k_nonzero_largest(array, 6) == 850
    assert mean_over_k_nonzero_largest(array, 9) == 600
    assert mean_over_k_nonzero_largest(array, 10) == 550
    assert mean_over_k_nonzero_largest(array, 15) == 550

    array = np.array([0] * 5 + [1000] * 5)
    assert mean_over_k_nonzero_largest(array, 4) == 1000
    assert mean_over_k_nonzero_largest(array, 5) == 1000
    assert mean_over_k_nonzero_largest(array, 6) == 1000
    assert mean_over_k_nonzero_largest(array, 9) == 1000
    assert mean_over_k_nonzero_largest(array, 10) == 1000
    assert mean_over_k_nonzero_largest(array, 15) == 1000

    array = np.array([0] * 5 + [100] * 5 + [1000] * 5)
    assert mean_over_k_nonzero_largest(array, 4) == 1000
    assert mean_over_k_nonzero_largest(array, 5) == 1000
    assert mean_over_k_nonzero_largest(array, 6) == 850
    assert mean_over_k_nonzero_largest(array, 9) == 600
    assert mean_over_k_nonzero_largest(array, 10) == 550
    assert mean_over_k_nonzero_largest(array, 15) == 550
