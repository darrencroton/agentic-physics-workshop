# Client spec

Thanks for taking this on. I asked for a "weighted mean and error in each bin" and I should have said more. Here is what I actually need, written down properly this time. If you think I have got something wrong, tell me. Please do not quietly do something different in the code.

## Signature

```python
binned_weighted_mean(x, y, sigma, edges) -> BinnedResult(x_eff, mean, err, n, n_dropped)
```

It lives in `src/hzbin/binning.py`.

## Decisions

| ID | Decision |
|---|---|
| **S1** | Bins are half-open [e_k, e_k+1), except the **last bin, which is closed** [e_n-1, e_n]. |
| **S2** | Points outside [e_0, e_n] are excluded; their number is returned as `n_dropped`. |
| **S3** | Weights are w = 1/sigma^2. |
| **S4** | mean = sum(w*y) / sum(w); err = (sum(w))^-1/2 (the uncertainty of the weighted mean, not the scatter). |
| **S5** | x_eff = sum(w*x) / sum(w) within the bin (not the bin midpoint). |
| **S6** | Empty bins give x_eff, mean, err = NaN and n = 0. |
| **S7** | Any non-finite value in x, y or sigma raises `ValueError`. No silent dropping. |
| **S8** | Any sigma <= 0 raises `ValueError`. |
| **S9** | `edges` must be strictly increasing with length >= 2; x, y and sigma must be 1-D and of equal length. Otherwise `ValueError`. |
| **S10** | Inputs are not modified; lists are accepted; outputs are float64 arrays (`n` and `n_dropped` integer); accumulation is in float64 even for float32 input. |
