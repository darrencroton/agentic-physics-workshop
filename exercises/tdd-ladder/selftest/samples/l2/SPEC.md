# SPEC: binned_weighted_mean

Our group's decisions for `binned_weighted_mean(x, y, sigma, edges)`.

1. Bins are half-open, [lower, upper), including the last bin. A point exactly on the final edge is outside the binning.
2. Points outside the edges are excluded and counted in `n_dropped`.
3. Weights are inverse variance, w = 1/sigma^2.
4. The bin mean is sum(w*y)/sum(w) and its error is 1/sqrt(sum(w)).
5. x_eff is the weighted mean of x in the bin, using the same weights.
6. Empty bins have n = 0, mean = 0 and err = inf. Any NaN, inf or sigma <= 0 in the inputs raises ValueError.
7. Edges must be strictly increasing and x, y, sigma must be 1-D and of equal length, otherwise ValueError. The inputs are never modified.
