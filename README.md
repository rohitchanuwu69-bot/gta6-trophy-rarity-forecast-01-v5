# Trophy Dilution Forecaster v5

[![make.fun bounty](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v5/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v5/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

A forecast of how many of the players Exophase tracks for Grand Theft Auto VI on PS5 will hold each trophy a week after launch, given as five quantiles per trophy.

It treats a flat launch-night history as a recount: earned counts stay put except for the most common trophies, whose newly tracked players earn a share of the current rate. A moving history is fitted trophy by trophy against the log of the time since release.

Run it locally with:

MAKEFUN_INPUT_DIR=<cases> MAKEFUN_OUTPUT_DIR=<out> python3 main.py

Python 3.13 standard library only, no network, deterministic.

Bounty: https://make.fun/bounty/gta6-trophy-rarity-forecast-01
Referral: https://make.fun/r/s1fmr9k0
