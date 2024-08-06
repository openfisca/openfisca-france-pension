"""Tools."""

import bottleneck

from numba import float32, int64, jit

import numpy as np


def mean_over_k_largest(vector, k):
    """Return the mean over the k largest values of a vector"""
    if k == 0:
        return 0

    if k >= len(vector):
        return vector.sum() / len(vector)

    z = -bottleneck.partition(-vector, kth = k)
    return z[:k].sum() / k


@jit(float32(float32[:], int64), nopython=True)
def mean_over_k_nonzero_largest(vector, k):
    """Return the mean over the k largest values of a vector"""
    if k == 0:
        return 0
    nonzeros = (vector > 0.0).sum()
    if k >= nonzeros:
        return vector.sum() / (nonzeros + (nonzeros == 0))

    z = -np.partition(-vector, kth = k)
    upper_bound = min(k, nonzeros)
    return z[:upper_bound].sum() / upper_bound


def previous_calendar_quarter_start_date(datetime_vector):
    # Fisrt day of of first month of the calendar quarter is part of the calendar quarter and thus cannot be the first day
    # of the immedaite previous calendar quarter
    result_year_start_date = (datetime_vector - np.timedelta64(1, 'D')).astype('datetime64[Y]').astype('datetime64[M]')
    months = (((((datetime_vector - np.timedelta64(1, 'D')).astype('datetime64[M]').astype(int) % 12) // 3) * 3)).astype("timedelta64[M]")
    return result_year_start_date + months


def next_calendar_quarter_start_date(datetime_vector):
    # Fisrt day of of first month of the calendar quarter is part of the calendar quarter and thus cannot be the first day
    # of the immediate previous calendar quarter
    result_year_start_date = (datetime_vector).astype('datetime64[Y]').astype('datetime64[M]')
    months = (((((datetime_vector).astype('datetime64[M]').astype(int) % 12) // 3) * 3) + 3).astype("timedelta64[M]")
    return result_year_start_date + months


def calendar_quarters_elapsed_this_year_asof(datetime_vector):
    return (
        datetime_vector.astype('datetime64[M]') - datetime_vector.astype('datetime64[Y]').astype('datetime64[M]')
        ).astype(int) // 3


def count_calendar_quarters(start_date, stop_date):
    start_date_year = start_date.astype('datetime64[Y]').astype(int) + 1970
    start_date_month = start_date.astype('datetime64[M]').astype(int) % 12 + 1
    start_date_day = start_date - start_date.astype('datetime64[M]') + 1

    stop_date_year = stop_date.astype('datetime64[Y]').astype(int) + 1970
    stop_date_month = stop_date.astype('datetime64[M]').astype(int) % 12 + 1
    stop_date_day = stop_date - stop_date.astype('datetime64[M]') + 1

    d = (stop_date_year - start_date_year) * 12 + (stop_date_month - start_date_month) - 1 * (stop_date_day < start_date_day)
    return d // 3


def add_vectorial_timedelta(date, years = 0, months = 0):
    return (
        date.astype('datetime64[M]') + np.array(12 * years + months, dtype = "int")
        + (date.astype('datetime64[D]') - date.astype('datetime64[M]'))
        )


def year_(date):
    return date.astype('datetime64[Y]').astype('int') + 1970
