"""Tools."""

import bottleneck


def mean_over_k_largest(vector, k):
    '''Return the mean over the k largest values of a vector'''
    if k == 0:
        return 0

    if k >= len(vector):
        return vector.sum() / len(vector)

    z = -bottleneck.partition(-vector, kth = k)
    return z[:k].sum() / k


def mean_over_k_nonzero_largest(vector, k):
    '''Return the mean over the k largest values of a vector'''
    if k == 0:
        return 0

    nonzeros = (vector > 0.0).sum()
    if k >= nonzeros:
        return vector.sum() / (nonzeros + (nonzeros == 0))

    z = -bottleneck.partition(-vector, kth = k)
    upper_bound = min(k, nonzeros)
    return z[:upper_bound].sum() / upper_bound
