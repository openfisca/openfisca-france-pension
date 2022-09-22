"""Tests of tools."""


import numpy as np
import pandas as pd


from openfisca_france_pension.tools import (
    count_calendar_quarters,
    calendar_quarters_elapsed_this_year_asof,
    mean_over_k_nonzero_largest,
    next_calendar_quarter_start_date,
    previous_calendar_quarter_start_date,
    )


def test_calendar_quarters_elapsed_this_year_asof():
    datetime_vector = pd.to_datetime([
        "2004-01-02",
        "2004-02-19",
        "2004-04-01",
        "2004-04-02",
        "2004-04-01",
        "2004-01-01",
        "2009-09-19",
        "1978-10-12",
        "1978-12-31",
        ]).values
    target = [
        0,
        0,
        1,
        1,
        1,
        0,
        2,
        3,
        3,
        ]

    np.testing.assert_almost_equal(calendar_quarters_elapsed_this_year_asof(datetime_vector), target)


def test_mean_over_k_nonzero_largest():
    array = np.array([100] * 5 + [1000] * 5).astype(np.float32)
    assert mean_over_k_nonzero_largest(array, 4) == 1000
    assert mean_over_k_nonzero_largest(array, 5) == 1000
    assert mean_over_k_nonzero_largest(array, 6) == 850
    assert mean_over_k_nonzero_largest(array, 9) == 600
    assert mean_over_k_nonzero_largest(array, 10) == 550
    assert mean_over_k_nonzero_largest(array, 15) == 550

    array = np.array([0] * 5 + [1000] * 5).astype(np.float32)
    assert mean_over_k_nonzero_largest(array, 4) == 1000
    assert mean_over_k_nonzero_largest(array, 5) == 1000
    assert mean_over_k_nonzero_largest(array, 6) == 1000
    assert mean_over_k_nonzero_largest(array, 9) == 1000
    assert mean_over_k_nonzero_largest(array, 10) == 1000
    assert mean_over_k_nonzero_largest(array, 15) == 1000

    array = np.array([0] * 5 + [100] * 5 + [1000] * 5).astype(np.float32)
    assert mean_over_k_nonzero_largest(array, 4) == 1000
    assert mean_over_k_nonzero_largest(array, 5) == 1000
    assert mean_over_k_nonzero_largest(array, 6) == 850
    assert mean_over_k_nonzero_largest(array, 9) == 600
    assert mean_over_k_nonzero_largest(array, 10) == 550
    assert mean_over_k_nonzero_largest(array, 15) == 550


def test_previous_calendar_quarter_start_date():
    datetime_vector = pd.to_datetime([
        "2004-01-02",
        "2004-02-19",
        "2004-04-01",
        "2004-04-02",
        "2004-04-01",
        "2004-01-01",
        ]).values
    target = pd.to_datetime([
        "2004-01-01",
        "2004-01-01",
        "2004-01-01",
        "2004-04-01",
        "2004-01-01",
        "2003-10-01",
        ]).values

    result = previous_calendar_quarter_start_date(datetime_vector)
    assert all(result == target.astype('datetime64[M]'))


def test_next_calendar_quarter_start_date():
    datetime_vector = pd.to_datetime([
        "2004-01-02",
        "2004-02-19",
        "2004-04-01",
        "2004-04-02",
        "2004-01-01",
        "2004-10-01",
        "2004-10-24",
        ]).values
    target = pd.to_datetime([
        "2004-04-01",
        "2004-04-01",
        "2004-07-01",
        "2004-07-01",
        "2004-04-01",
        "2005-01-01",
        "2005-01-01",
        ]).values

    result = next_calendar_quarter_start_date(datetime_vector)
    assert all(result == target.astype('datetime64[M]'))


def test_count_calendar_quarters():
    start_date = pd.to_datetime([
        "2012-01-01",
        "2012-02-01",
        "2012-01-05",
        "2012-01-01",
        ]).values
    stop_date = pd.to_datetime([
        "2012-07-01",
        "2012-07-01",
        "2012-07-01",
        "2013-07-01",
        ]).values

    target = [
        2,
        1,
        1,
        6,
        ]

    np.testing.assert_almost_equal(count_calendar_quarters(start_date, stop_date), target)
