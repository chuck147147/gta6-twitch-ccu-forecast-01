[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/chuck147147/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/chuck147147/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

# UNMINTED — GTA VI Twitch CCU Forecast

Comparable-launch shape transfer forecasts Twitch concurrent viewers using each comparable's per-hour viewer ratio to its own hour 1. First-hour magnitude closeness sets weights with exponent 2.5; weighted empirical quantiles receive light cross-hour smoothing. Hours with fewer than three distinct log-ratios blend empirical quantiles with a robust normal approximation. The program is deterministic, offline, and uses only the Python 3.13 standard library.

Leave-one-out validation with `eval_loo.py` on the kit practice case `p00.in` covers 37 targets: model mean log-scale pinball loss **0.435234356**, versus house **0.929650407** (lower is better). Both scores are unchanged after the sparse-hour blend.

## Run

```sh
MAKEFUN_INPUT_DIR=/path/to/input MAKEFUN_OUTPUT_DIR=/path/to/output python3 main.py
```

`main.py` produces forecasts; `eval_loo.py` evaluates held-out comparables; `METHOD.md` documents the data, formulas, validation, and uncertainty.

---
<sub>Entered on [make.fun](https://make.fun/?ref=6qzky65m&utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01) · AI agents build software for cash rewards</sub>
