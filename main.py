"""Trophy Dilution Forecaster v5.

Forecasts, for every trophy of Grand Theft Auto VI on PlayStation 5, the
percent of the players Exophase tracks who will have earned it at the case
target time, as five quantiles per trophy.

The entry reads every case file in the input directory and writes one
forecast file per case in the output directory. It uses only the Python
standard library, makes no network calls, and always gives the same output
for the same input.

How it reasons, in brief: when a case history is flat (every read shows the
same tracked-player count and the same rates), the next refresh is treated
as a recount of the same players plus a wave of newly tracked players, so
earned counts stay put except for the most common trophies, whose newcomers
earn a share of their current rate. When a history moves, each trophy's
earned count and the tracked-player count are each fitted against the log
of the time since release, and the ratio of the two fits at the target time
is the median.
"""

import json
import math
import os
import sys
from datetime import datetime, timezone

# The documented first refresh of the launch-night page: 638 players
# tracked became 3,868. On a flat history the target is assumed to sit at
# the same recount, so the tracked count grows by this ratio.
REFRESH_PLAYERS_BEFORE = 638.0
REFRESH_PLAYERS_AFTER = 3868.0

# Share of a fast trophy's current rate that the newly tracked players are
# assumed to have earned by the target.
FAST_EARN_SHARE = 0.30

# Total width, in logit units, between the 5th and 95th percentiles of a
# flat-history forecast. The median is nearly exact there, so the band is
# kept narrow; it is never tightened below this.
FLAT_SPREAD_TOTAL = 0.13

# How far above the median, in logit units, the 95th percentile of a fast
# trophy is allowed to reach. Fast trophies carry the uncertainty, so only
# their upper side is stretched.
FAST_UPPER_REACH = 0.30

# Widest total spread, in logit units, the moving-history branch may use.
MOVING_SPREAD_CAP = 1.1

# Normal scores for the five reported levels, in order.
LEVEL_Z = (-1.644854, -0.674490, 0.0, 0.674490, 1.644854)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)


def parse_time(text):
    """Parse an ISO-8601 timestamp into an aware datetime, or None."""
    if not isinstance(text, str) or not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def logit(rate_percent):
    """Logit of a percent, clamped away from the 0 and 100 edges."""
    p = min(max(rate_percent / 100.0, 0.0001), 0.9999)
    return math.log(p / (1.0 - p))


def inv_logit(value):
    """Percent for a logit value."""
    return 100.0 / (1.0 + math.exp(-value))


def band(median_percent, spread_total, upper_reach=None):
    """Five quantiles around a median percent, on the logit scale.

    The lower side and (unless a wider upper reach is given) the upper side
    share one scale, so the 5th and 95th percentiles sit spread_total apart.
    A wider upper reach stretches only the percentiles above the median.
    """
    centre = logit(median_percent)
    half = spread_total / (2.0 * 1.644854)
    out = []
    for z in LEVEL_Z:
        if z >= 0 and upper_reach is not None:
            step = z * (upper_reach / 1.644854)
        else:
            step = z * half
        value = inv_logit(centre + step)
        out.append(round(min(max(value, 0.0), 100.0), 4))
    for i in range(1, len(out)):
        if out[i] < out[i - 1]:
            out[i] = out[i - 1]
    return out


def least_squares(xs, ys):
    """Slope, intercept and residual spread of y on x, or None."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx <= 0.0:
        return None
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    resid = math.sqrt(sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys)) / n)
    return slope, intercept, resid


def flat_forecast(last_rates, last_players):
    """Forecasts for a flat history, as a list of quantile lists."""
    target_players = last_players * REFRESH_PLAYERS_AFTER / REFRESH_PLAYERS_BEFORE
    gained_players = target_players - last_players
    earned = []
    for rate in last_rates:
        earned.append(int(round(rate * last_players / 100.0)))
    below_full = sorted({r for r in last_rates if r < 100.0}, reverse=True)
    fast_values = set(below_full[:3])
    rows = []
    for i, rate in enumerate(last_rates):
        if rate >= 100.0:
            rows.append([100.0, 100.0, 100.0, 100.0, 100.0])
            continue
        if rate in fast_values:
            fresh = earned[i] + gained_players * (rate / 100.0) * FAST_EARN_SHARE
        else:
            fresh = float(earned[i])
        median = 100.0 * fresh / target_players
        if rate in fast_values:
            rows.append(band(median, FLAT_SPREAD_TOTAL, FAST_UPPER_REACH))
        else:
            rows.append(band(median, FLAT_SPREAD_TOTAL))
    return rows


def moving_forecast(case, history, release_start, target_time):
    """Forecasts for a moving history, as a list of quantile lists."""
    last = history[-1]
    last_rates = last["rates"]
    last_players = float(last["players_tracked"])
    last_time = parse_time(last["at"]) or parse_time(last["slot"])
    ages = []
    for read in history:
        moment = parse_time(read["at"]) or parse_time(read["slot"])
        if moment is None:
            continue
        age = (moment - release_start).total_seconds() / 3600.0
        ages.append(max(age, 0.25))
    target_age = (target_time - release_start).total_seconds() / 3600.0
    target_age = max(target_age, 0.25)
    last_age = ages[-1] if ages else 0.25
    log_ages = [math.log(a) for a in ages]
    horizon = math.log(target_age / last_age) if target_age > last_age else 0.0
    players_fit = least_squares(
        log_ages, [math.log(max(float(r["players_tracked"]), 1.0)) for r in history]
    )
    if players_fit is None:
        return flat_forecast(last_rates, last_players)
    p_slope, p_intercept, p_resid = players_fit
    players_at_target = math.exp(p_intercept + p_slope * math.log(target_age))
    players_at_target = max(players_at_target, last_players)
    rows = []
    for i, rate in enumerate(last_rates):
        if rate >= 100.0:
            rows.append([100.0, 100.0, 100.0, 100.0, 100.0])
            continue
        earned_series = []
        for read in history:
            count = int(round(read["rates"][i] * float(read["players_tracked"]) / 100.0))
            earned_series.append(max(count, 0.5))
        earned_fit = least_squares(log_ages, [math.log(c) for c in earned_series])
        if earned_fit is None:
            earned_at_target = float(earned_series[-1])
            resid = 0.0
        else:
            e_slope, e_intercept, resid = earned_fit
            earned_at_target = math.exp(e_intercept + e_slope * math.log(target_age))
        earned_at_target = max(earned_at_target, 0.5)
        median = 100.0 * earned_at_target / players_at_target
        median = min(max(median, 0.01), 99.99)
        combined = math.sqrt(resid * resid + p_resid * p_resid)
        if combined > 0.4:
            combined = 0.4
        spread = 0.35 + 0.45 * horizon + combined
        if spread > MOVING_SPREAD_CAP:
            spread = MOVING_SPREAD_CAP
        rows.append(band(median, spread))
    return rows


def forecast_case(case):
    """Forecast one case, returning the output document."""
    history = case.get("history") or []
    trophies = case.get("trophies") or []
    if not history:
        return {"trophies": []}
    last = history[-1]
    last_rates = list(last["rates"])
    last_players = float(last["players_tracked"])
    flat = True
    for read in history:
        if read.get("players_tracked") != last["players_tracked"]:
            flat = False
        if list(read.get("rates") or []) != last_rates:
            flat = False
    if flat:
        rows = flat_forecast(last_rates, last_players)
    else:
        target_time = parse_time(case.get("target"))
        game = case.get("game") or {}
        release_text = game.get("release_date") or ""
        release_start = None
        if release_text:
            try:
                day = datetime.fromisoformat(release_text)
                release_start = day.replace(tzinfo=timezone.utc)
            except ValueError:
                release_start = None
        if release_start is None:
            first = parse_time(history[0].get("at")) or parse_time(history[0].get("slot"))
            release_start = first or datetime(2026, 11, 19, tzinfo=timezone.utc)
        if target_time is None:
            target_time = parse_time(case.get("at")) or release_start
        rows = moving_forecast(case, history, release_start, target_time)
    out_rows = []
    for i, quantiles in enumerate(rows):
        if i < len(trophies):
            tid = trophies[i].get("id", i + 1)
        else:
            tid = i + 1
        out_rows.append({"id": int(tid), "q": quantiles})
    return {"trophies": out_rows}


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(input_dir) if n.endswith(".in"))
    for name in names:
        with open(os.path.join(input_dir, name), "r", encoding="utf-8") as handle:
            case = json.load(handle)
        result = forecast_case(case)
        stem = name[:-3]
        with open(os.path.join(output_dir, stem + ".out"), "w", encoding="utf-8") as handle:
            json.dump(result, handle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
