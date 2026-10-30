# Handoff: solar-battery-dispatch

Start here if you are picking this up cold. Update this file in the same commit as any milestone.

Last updated 2026-10-30.

## Goal

A desktop simulator that shows a Botswana site owner how much diesel solar and batteries would save, how to size them, and whether smarter control is worth paying for. First customer type: off-grid safari camps in the Okavango Delta. Idea #38 in `mehdiacho/frontier-research`, chosen 2026-10-30. It runs on whoever's PC opens it; nothing is hosted (Mehdi's rule: nothing runs day and night on his NAS).

## Where it is

- **Repo:** private [`mehdiacho/solar-battery-dispatch`](https://github.com/mehdiacho/solar-battery-dispatch), branch `main`.
- **Copy on Mehdi's PC:** `X:\FRONTIER\projects\solar-battery-dispatch` (files, not a git checkout). Clone the repo to `X:\Projects\solar-battery-dispatch` to work on it locally.
- **Toolchain:** Python 3.11+, numpy, scipy (HiGHS MILP), matplotlib, pytest. No PyBaMM yet.

## State

| Milestone | State |
|---|---|
| M1 Core model: solar, load, generator, battery; load-following and cycle-charging rules; MILP optimiser; report and charts; size sweep; 9 tests | **Done** 2026-10-30 |
| M2 Real inputs | **Part done** 2026-10-30: PVGIS solar for the site (daily totals, via the browser; the cloud session can't reach PVGIS); system sized like a real Delta camp (55 kWp, 195 kWh). Still placeholders: the load, delivered diesel price, capex. No public figures found for those. |
| M3 Check against Xigera's published figures (400 kW PV, 1.14 MWh, ~95% solar, ~175,000 L/yr saved) | Open |
| M4 Battery detail with PyBaMM: efficiency and ageing vs temperature, replacing the flat wear cost | Open (needs a PyBaMM install: Mehdi's OK) |
| M5 Forecast-based controller: replace the perfect forecast with a realistic one (yesterday's weather, or a forecast API) and measure how much of the optimiser's gain survives | Open |
| M6 Grid-tied sites: BPC tariffs (energy, demand in kVA), outages, export | Open |
| M7 Something a customer can use: a one-page report or small app per site | Open |

## Commands

```sh
python -m pytest -q
python -m dispatch run scenarios/delta-camp.toml          # results/delta-camp/: summary.md, summary.csv, charts
python -m dispatch run scenarios/delta-camp.toml --fast   # rules only
python -m dispatch sweep scenarios/delta-camp.toml        # sweep.csv, sweep-diesel.png
python scripts/fetch_pvgis.py scenarios/delta-camp.toml   # hourly PVGIS data; Mehdi OK'd PVGIS downloads 2026-10-30; script still untested
```

## Decisions

- 2026-10-30: Mehdi OK'd downloading PVGIS data.
- 2026-10-30: build idea #38 next; first site type is an off-grid Delta safari camp.
- Off-grid first, because that's where diesel savings are largest and no tariff data is needed.
- Hourly steps, one typical year. A 48 h rolling MILP with a perfect forecast is the benchmark, not a controller.
- PyBaMM deferred: PyPI was blocked in the first session, and the simple wear-cost model is enough to compare strategies.

## Known limits

- **The inputs are placeholders.** See `docs/assumptions.md`. The built-in solar model is probably too sunny; until PVGIS data is in, treat the solar share as optimistic.
- The optimiser sees the future and keeps no reserve: in the wet season it lets the battery fall to 10% overnight. A real controller would hold a reserve.
- Battery wear is a flat cost per kWh moved; there's no temperature or calendar ageing.
- Tilt is ignored (flat GHI × performance ratio).
- Payback is simple (capex / first-year saving): no financing, no replacements, no generator savings.

## Latest result (2026-10-30)

At the real camp size, diesel falls from 57,800 L/yr (diesel only) to 9,900 L (load-following rule), 12,700 L (cycle-charging) or 7,000 L (optimised). Smarter control is worth about 2,900 L/yr here. See `README.md` and `docs/results/`.

## Next 3 steps

1. Get one real camp's numbers: daily kWh or generator fuel logs, generator size, delivered diesel price. None found publicly; needs a camp operator or installer.
2. M5: a forecast-based controller, to see how much of the optimiser's 2,900 L survives without perfect foresight. This decides whether "smart control" is a product.
3. Model Xigera as a check (M3).

## Conventions

See `CLAUDE.md`.
