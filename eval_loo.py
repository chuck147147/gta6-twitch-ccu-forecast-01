"""Leave-one-out launch evaluation using the runtime forecasting core."""

import argparse
import json
import math
from pathlib import Path

from main import LEVELS, build_pool, forecast_from_pool, house_forecast, release_hours


def score(actual, prediction):
    losses = []
    for row in prediction:
        if row['hour'] not in actual:
            continue
        log_y = math.log(max(1, actual[row['hour']]))
        for tau, q in zip(LEVELS, row['q']):
            d = log_y - math.log(q)
            losses.append(2 * max(tau * d, (tau - 1) * d))
    return sum(losses), len(losses)


def evaluate(case):
    valid = [c for c in case['comparables'] if release_hours(c).get(1, 0) > 0]
    pool = build_pool(valid)
    targets = []
    model_total = house_total = 0.0
    item_count = 0
    cyberpunk = None
    for index, (comparable, (p1, hours)) in enumerate(zip(valid, pool)):
        if len(hours) < 20:
            continue
        predicted = forecast_from_pool(p1, pool[:index] + pool[index + 1:])
        model_sum, count = score(hours, predicted)
        house_sum, _ = score(hours, house_forecast(p1))
        model_total += model_sum
        house_total += house_sum
        item_count += count
        targets.append({'name': comparable['name'], 'model_loss': model_sum / count,
                        'house_loss': house_sum / count, 'scored_items': count})
        if comparable['name'] == 'Cyberpunk 2077':
            peak_hour = max(sorted(hours), key=hours.get)
            medians = {row['hour']: row['q'][2] for row in predicted}
            predicted_peak = max(medians, key=medians.get)
            cyberpunk = {'actual_peak_hour': peak_hour, 'actual_peak_viewers': hours[peak_hour],
                         'predicted_median_at_actual_peak': medians.get(peak_hour, p1),
                         'predicted_peak_median_hour': predicted_peak,
                         'predicted_peak_median_viewers': medians[predicted_peak]}
    return {'number_of_targets': len(targets), 'scored_items': item_count,
            'model_mean_pinball': model_total / item_count if item_count else None,
            'house_mean_pinball': house_total / item_count if item_count else None,
            'targets': targets, 'cyberpunk_2077': cyberpunk}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('case')
    parser.add_argument('--json-out')
    args = parser.parse_args()
    result = evaluate(json.loads(Path(args.case).read_text()))
    print(f"Targets: {result['number_of_targets']}")
    for label, key in [('Model mean pinball', 'model_mean_pinball'), ('House mean pinball', 'house_mean_pinball')]:
        value = result[key]
        print(f'{label}: {value:.9f}' if value is not None else f'{label}: N/A')
    print('Name | Model loss | House loss')
    for row in result['targets']:
        print(f"{row['name']} | {row['model_loss']:.9f} | {row['house_loss']:.9f}")
    c = result['cyberpunk_2077']
    if c is not None:
        print(f"Cyberpunk 2077: actual peak hour={c['actual_peak_hour']}, viewers={c['actual_peak_viewers']}; "
              f"predicted median at actual peak={c['predicted_median_at_actual_peak']}; "
              f"predicted peak median hour={c['predicted_peak_median_hour']}, value={c['predicted_peak_median_viewers']}")
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
