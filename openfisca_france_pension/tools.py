"""Tools."""

import bottleneck

from numba import float32, int64, jit

import numpy as np


def mean_over_k_largest(vector, k):
    '''Return the mean over the k largest values of a vector'''
    if k == 0:
        return 0

    if k >= len(vector):
        return vector.sum() / len(vector)

    z = -bottleneck.partition(-vector, kth = k)
    return z[:k].sum() / k


@jit(float32(float32[:], int64), nopython=True)
def mean_over_k_nonzero_largest(vector, k):
    '''Return the mean over the k largest values of a vector'''
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


def calendar_quarters_elapsed_this_year_asof(datetime_vector):
    return (
        datetime_vector.astype('datetime64[M]') - datetime_vector.astype('datetime64[Y]').astype('datetime64[M]')
        ).astype(int) // 3
