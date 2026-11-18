[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Creepzone11/gta6-twitch-ccu-forecast-01/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/Creepzone11/gta6-twitch-ccu-forecast-01/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

# gta6-twitch-ccu-forecast-01 — entry v2

Improved entry for make.fun competition `gta6-twitch-ccu-forecast-01`
(user handle: creepzone). Replaces the current entry (practice loss
0.304, rank 9588/10118) with a comparable-curve forecaster.

## What it is

`main.py` (Python 3.13, stdlib only, deterministic, ~0.04 s per case).
For each hour it forecasts five quantiles of Twitch viewers in the
GTA VI category, from the case file alone: hour-1 print + the 38 (final:
42) comparable launch curves in the case.

Method, in short:

- Early hours track hour-1 almost 1:1; evening hours barely track it
  (per-hour OLS slope on log hour-1 falls from ~1.0 at hour 2 to ~0.06
  at hour 20, R² 0.98 → 0.03). A flat persistence median therefore
  misses the whole day shape: night dip, US-East unlock surge around
  hours 5–6, US-West around hour 9, evening peak hours 17–21.
- Median per hour = mean of two estimates: the KNN median (8
  comparables nearest in log hour-1) and the per-hour OLS median.
- Spread = mean of the KNN neighbours' quantiles and the OLS residuals'
  quantiles (shrunk 0.85), widened if hour-1 lies outside the
  comparables' range. Either spread alone is miscalibrated; the mean
  covers ~0.92 of practice hours (target 0.90).
- Fallback to the house persistence baseline for any hour with too
  little data.

## Validation (local, `python3 validate.py`)

Practice answers were fetched once from SullyGnome, the source named
in the kit's `input/NOTICE.txt`, and the hour-1 prints matched the
case files exactly for all four cases. Scoring uses the exact pinball
formula from RULES.txt; the starter reproduces the house baseline's
published practice numbers (loss 0.387, coverage 0.783), which
validates the scorer.

| method | practice loss (p00/p01/p02/p03) | typical miss | coverage |
|---|---|---|---|
| starter (house baseline) | 0.387 (0.744 / 0.287 / 0.215 / 0.303) | 90.2% | 0.783 |
| current entry (server) | 0.304 | 66.7% | 0.815 |
| **v2 (this entry)** | **0.190 (0.171 / 0.180 / 0.200 / 0.210)** | **34.8%** | **0.924** |

Leave-one-comparable-out with the shipped code: 0.422 over all 37
comparables, 0.304 over the 27 big ones (hour-1 ≥ 20,000). The
practice number is the more relevant one for a big launch like GTA VI,
but the LOCO gap says: expect the final loss to be worse than 0.19 if
the final day behaves unlike the four practice launches.

CLI checks pass: valid output shape/size/monotonicity on all four
cases, two runs byte-identical, 0.15 s for four cases (cap is 8 s
per case).

## Known risk

The evening median barely rises with hour-1 in the data (see the OLS
slopes above), so for a huge hour-1 (e.g. 1.5M) the model still
forecasts an evening median near 330k, with the 95% quantile near
730k. The biggest past launches peaked at 450k–780k in the evening.
If GTA VI is a genuinely bigger scale class than every comparable,
the median will under-predict the evening. That is what the data
says, not a bug; overriding it would be a judgement call, not a
fit.

## Still needed to submit (NOT done)

1. A public GitHub repository owned by the user, created after the
   competition opened (2026-11-17T06:00Z), holding `main.py` +
   `LICENSE` (MIT, included) at its root. Do not create it until the
   user approves: it is public from creation.
2. Transcripts of the agent sessions that built the entry, bundled
   with the kit CLI (`node cli/makefun.mjs bundle ...`). This
   subagent session has no harness-recorded session file to bundle;
   the parent agent must run the build/submission in a recorded
   session (or hand the transcripts over, which forfeits prizes).
3. User approval + entry signing with the user's linked Solana
   wallet, then submission through the kit CLI before the deadline:
   **2026-11-19T01:00:00Z = 09:00 WIB, 19 Nov 2026**.
4. After submission, the server grades the practice again; the
   practice loss above is a local estimate, not the server grade.
