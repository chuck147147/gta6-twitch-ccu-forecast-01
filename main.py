"""Deterministic launch-shape transfer; standard-library-only runtime entry point."""

import json
import math
import os
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
Z = (-1.645, -0.674, 0.0, 0.674, 1.645)


def release_hours(comparable):
    """Match parsed timestamps exactly, including timezone equivalence."""
    start = datetime.fromisoformat(comparable['day_start'])
    hours = {}
    for point in comparable['hourly']:
        seconds = (datetime.fromisoformat(point['from']) - start).total_seconds()
        if 0 <= seconds < 86400 and seconds % 3600 == 0:
            hours[int(seconds // 3600) + 1] = point['viewers']
    return hours


def build_pool(comparables):
    pool = []
    for comparable in comparables:
        hours = release_hours(comparable)
        c1 = hours.get(1, 0)
        if c1 > 0:
            pool.append((c1, hours))
    return pool


def weighted_quantile(data, level):
    ordered = sorted(data)
    threshold = level * sum(weight for _, weight in ordered)
    cumulative = 0.0
    for value, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return value
    return ordered[-1][0]


def normal_logs(data):
    """Missing-hour fallback: weighted pooled mean and population deviation."""
    total = sum(w for _, w in data)
    mean = sum(x * w for x, w in data) / total
    spread = max(0.12, math.sqrt(sum(w * (x - mean) ** 2 for x, w in data) / total))
    return [mean + z * spread for z in Z]


def rounded_quantile(value):
    value = min(1e9, max(0.01, value))
    result = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return int(result) if result == result.to_integral_value() else float(result)


def quantiles_from_logs(p1, logs):
    # Bound the exponent before exponentiation to avoid overflow.
    lower, upper = math.log(0.01 / p1), math.log(1e9 / p1)
    return [rounded_quantile(p1 * math.exp(min(upper, max(lower, x))))
            for x in sorted(logs)]


def house_forecast(p1):
    p1 = max(1, p1)
    return [{'hour': h, 'q': quantiles_from_logs(p1, [z * 0.15 * math.sqrt(h - 1) for z in Z])}
            for h in range(2, 25)]


def forecast_from_pool(p1, pool):
    """Return the 23 output rows from (hour-one viewers, release-hour map) pairs."""
    p1 = max(1, p1)
    if not pool:
        return house_forecast(p1)
    data = {h: [] for h in range(2, 25)}
    for c1, hours in pool:
        weight = (1 + abs(math.log(c1 / p1))) ** -2.5
        for h in data:
            viewers = hours.get(h, 0)
            if viewers > 0:
                data[h].append((math.log(viewers / c1), weight))
    pooled = [pair for points in data.values() for pair in points]
    if not pooled:
        return house_forecast(p1)
    fallback = normal_logs(pooled)
    logs = {}
    for h, points in data.items():
        if not points:
            logs[h] = fallback
        else:
            logs[h] = [weighted_quantile(points, level) for level in LEVELS]
            if len({x for x, _ in points}) < 3:
                # Sparse empirical shapes understate uncertainty; blend before smoothing.
                median = logs[h][2]
                mad = weighted_quantile([(abs(x - median), w) for x, w in points], 0.5)
                spread = max(0.12, 1.4826 * mad) if math.isfinite(mad) else 0.3
                logs[h] = [0.5 * empirical + 0.5 * (median + z * spread)
                           for empirical, z in zip(logs[h], Z)]
    result = []
    for h in range(2, 25):
        neighbors = [(k, w) for k, w in ((h - 1, 0.25), (h, 0.5), (h + 1, 0.25)) if k in logs]
        total = sum(w for _, w in neighbors)
        smooth = [sum(w * logs[k][i] for k, w in neighbors) / total for i in range(5)]
        result.append({'hour': h, 'q': quantiles_from_logs(p1, smooth)})
    return result


def main():
    input_dir = Path(os.environ.get('MAKEFUN_INPUT_DIR', '/input'))
    output_dir = Path(os.environ.get('MAKEFUN_OUTPUT_DIR', '/output'))
    output_dir.mkdir(parents=True, exist_ok=True)
    for path in sorted(input_dir.glob('*.in')):
        case = json.loads(path.read_text())
        p1 = max(1, next(row['viewers'] for row in case['known'] if row['hour'] == 1))
        hours = forecast_from_pool(p1, build_pool(case['comparables']))
        (output_dir / (path.stem + '.out')).write_text(
            json.dumps({'hours': hours}, separators=(',', ':'), allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
