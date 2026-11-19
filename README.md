# Forecasting GTA VI trophy rarity, v5

[![bounty](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![place](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v5/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![prize](https://make.fun/badge/gta6-trophy-rarity-forecast-01/rohitchanuwu69-bot/gta6-trophy-rarity-forecast-01-v5/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

For each of the 55 PlayStation 5 trophies of Grand Theft Auto VI, this entry predicts the share of Exophase-tracked players who will hold it one week after launch, as five quantiles per trophy.

When the launch-night reads do not move, the forecast treats the next refresh as a recount: the earned counts carry over, while the most common trophies pick up extra earners from the newly tracked players. When the reads move, every trophy's earned count and the tracked-player count are each fitted against log time since release, and their ratio at the target time is the forecast.

To run it on a folder of case files:

MAKEFUN_INPUT_DIR=<case-dir> MAKEFUN_OUTPUT_DIR=<out-dir> python3 main.py

It needs Python 3.13 and nothing else, touches no network, and repeats its output exactly.

Bounty page: https://make.fun/bounty/gta6-trophy-rarity-forecast-01
Referral link: https://make.fun/r/s1fmr9k0
