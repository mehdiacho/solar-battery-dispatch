# Assumptions and sources

Checked 2026-10-30. **Sourced** = from a source below. **Assumption** = a placeholder to replace with site data.

## Prices

| Input | Value | Status |
|---|---|---|
| Diesel 50ppm | P23.76/L from 23 Oct 2026 (up 283 thebe) | **Sourced**: BERA via Daily News |
| Delivery to the Delta | P0/L in the scenario | **Assumption**, and deliberately low. Trucking, barging or flying fuel in costs more, so real savings are higher. Set `diesel_delivery_p_per_l` per site. |
| Solar capex | P9,000/kWp installed | **Assumption** |
| Battery capex | P4,000/kWh installed, with inverters | **Assumption** |
| Battery replacement | P3,000/kWh; LFP, 6,000 cycles | **Assumption**; gives a wear cost of about P0.56 per kWh moved |
| BPC grid tariffs | Not used yet (camp is off-grid) | 9% increase across all categories from 1 Aug 2026; large users' maximum demand now in kVA over 6 months (**sourced**, BERA). Exact rates not found online yet. |

## Solar

| Input | Value | Status |
|---|---|---|
| Annual GHI | 2,150 kWh/m² | **Assumption** (Botswana is roughly 2,000–2,300). Replace with PVGIS via `scripts/fetch_pvgis.py`. |
| Weather | Wet season Nov–Mar, 8% overcast-day chance (×2.5 wet, ×0.5 dry), spells continue 55% (wet) / 30% (dry) | **Assumption**, probably too sunny |
| Performance ratio | 0.78 | **Assumption** (typical for hot, dusty sites) |

## Load (the biggest unknown)

| Input | Value | Status |
|---|---|---|
| Always-on base | 6 kW (cold rooms, pumps, comms, staff village) | **Assumption** |
| Guest energy at full occupancy | 200 kWh/day | **Assumption** |
| Occupancy | 40–45% Jan–Mar, 90–95% Jun–Oct | **Assumption** (green vs dry season) |
| Result | ~293 kWh/day average, 28 kW peak, 107 MWh/yr | Modelled |

## Generator

| Input | Value | Status |
|---|---|---|
| Fuel curve | 0.08145 L/h per kW rated + 0.246 L per kWh | **Assumption**: a common default curve used in hybrid-system tools. Gives ~0.49 L/kWh for this lightly loaded 40 kW set. |
| Minimum load | 30% of rated | **Assumption** (common maker guidance) |

## For scale: a real Delta lodge

Xigera Safari Lodge (Okavango Delta, 2019): 400 kW of solar, five Tesla Powerpacks with 1.14 MWh usable, two 350 kVA diesel generators as backup, over 95% solar, about 175,000 L of diesel saved a year (design figures from when it was being built). A good later check: model it and see whether the numbers come out close.

## Sources

- Diesel price: [Daily News, fuel price adjustment, 23 Oct 2026](https://dailynews.gov.bw/news-detail/93795)
- BPC tariffs 2026/27: [BERA press release](https://www.bera.co.bw/downloads/Electricity/BPC%202026-27%20Tariff%20Application%20-%20Public%20Notice/Press%20Release%20-%20Electricity%20Tariff%20Adjustments%20For%202026_27%20-%20signed.pdf)
- Xigera: [Fully Charged, Powered by the Sun: Xigera Safari Lodge](https://fullycharged.show/blog/powered-by-the-sun-xigera-safari-lodge)
- Market context: [500 MW Maun solar + 500 MWh battery breaks ground (gov.bw, 16 Apr 2026)](https://www.gov.bw/botswana-breaks-ground-landmark-500mw-maun-solar-project), [mining company opens 30 MW solar tender (pv magazine, Jun 2026)](https://www.pv-magazine.com/2026/06/17/mining-company-opens-30-mw-solar-tender-in-botswana/)
