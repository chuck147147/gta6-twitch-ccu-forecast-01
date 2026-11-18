# Method: comparable-launch shape transfer

## Data provenance

The comparable observations are hourly Twitch category averages from SullyGnome, as packaged in the competition kit's cases. The kit's `input/NOTICE.txt` provides provenance and attribution. The program itself is offline and reads only the case file it is given; it does not fetch or extend the source data.

## Shape transfer

Let `p1` be the target's known hour-1 viewers, floored at 1. For each comparable, parse `day_start` and each hourly timestamp. Retain only points exactly at `day_start + (h-1) hours`, for hours 1 through 24. Discard a comparable if its hour-1 viewers `c1` are missing or nonpositive. Before weighting, retain only comparables within the magnitude window `|ln(c1 / p1)| <= 2.0`; exclude all others.

For positive observations, compute:

```text
r_c(h) = viewers_c(h) / viewers_c(1)
w_c = (1 + |ln(c1 / p1)|)^-2.5
```

For each hour 2 through 24, form the weighted distribution of `ln r_c(h)`. At levels `tau = [0.05, 0.25, 0.5, 0.75, 0.95]`, take the weighted step quantile: sort the values and choose the first whose cumulative weight reaches `tau * total_weight`. This transfers realised launch shapes while favouring comparables with similar first-hour magnitudes.

After the sparse-hour adjustment below, smooth each log-quantile independently across hours `h-2` through `h+2` with weights `0.1 / 0.2 / 0.4 / 0.2 / 0.1`. Renormalise over the hours present in the log-quantile map at boundaries. Then convert back to viewers:

```text
q_tau(h) = p1 * exp(smoothed_log_quantile_tau(h))
```

Sort quantiles, clamp to `[0.01, 1e9]`, and round half up to two decimals. The implementation is deterministic and uses only the Python 3.13 standard library.

## Spread calibration and sparse data

The ordinary quantiles describe the weighted empirical distribution of realised launch shapes. Their spread is calibrated on the comparables themselves rather than a fixed sigma; this does not guarantee coverage for a new launch.

When an hour has one or two distinct log-ratio values, compute its weighted median `m` and weighted median absolute deviation `MAD = weighted_median(|ln r_c(h) - m|)`. Use `s = max(0.12, 1.4826 * MAD)`, or `0.3` if the MAD is not computable. With `z = [-1.645, -0.674, 0, 0.674, 1.645]`, blend before cross-hour smoothing:

```text
adjusted_log_quantile_tau = 0.5 * empirical_log_quantile_tau
                          + 0.5 * (m + z_tau * s)
```

This MAD-based normal widening prevents a few distinct shapes from collapsing the empirical intervals. A singleton has computable MAD zero and therefore uses the 0.12 log-spread floor. Hours with at least three distinct values retain pure empirical quantiles.

An hour with no observations uses a normal approximation to all available log-ratios pooled over forecast hours, centred on the weighted mean with weighted population standard deviation floored at 0.12. With no usable comparables, or no usable forecast-hour ratios at all, the forecast is persistence with growing uncertainty:

```text
q_tau(h) = p1 * exp(z_tau * 0.15 * sqrt(h - 1))
```

## Magnitude anchors from the supplied data

These lines were computed directly from `input/p00.in` in the competition kit using the same exact timestamp matching as the forecaster. Hours are counted from each comparable's `day_start`; hour 1 is the first hour. Peaks refer to the largest recorded hourly average in release-day hours 1 through 24, not instantaneous audience peaks.

```text
Cyberpunk 2077: release-day peak hour=2, peak viewers=1069278
Hogwarts Legacy: release-day peak hour=18, peak viewers=504995
ELDEN RING: release-day peak hour=1, peak viewers=875155
```

## Validation

`eval_loo.py` imports the forecasting core from `main.py`. Every comparable with positive hour-1 viewers and at least 20 of the 24 release-day hours present becomes a target in turn. Its own observations are removed from the pool before forecasting hours 2 through 24 from its hour-1 value. Only recorded actual hours are scored; actual viewers are floored at 1.

For each target, hour, and quantile, the log-scale pinball loss is:

```text
d = ln(max(1, actual_viewers)) - ln(predicted_quantile)
loss = 2 * max(tau * d, (tau - 1) * d)
```

The aggregate averages over all scored items. The house comparison uses the persistence formula above, with the same output bounds and rounding as the runtime fallback.

Re-running on the kit's `p00.in` after the magnitude window exclusion and five-point smoothing gives **37 targets**, model mean pinball **0.429417342**, and house mean pinball **0.929650407**. These are held-out comparable results, not a measurement on the final competition target.

## Uncertainty

Shapes vary most for launches whose UTC hour 1 precedes their regional unlock: tiny hour-1 prints can lead to explosive ratios. Magnitude weighting mitigates this effect but cannot remove it. A single first-hour print cannot identify the unlock mix of the final case, so intervals stay wide where comparables disagree.
