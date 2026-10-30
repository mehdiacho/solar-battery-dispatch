# Assumptions and sources

Checked 2026-10-30. **Sourced** = from a source below. **Assumption** = a placeholder to replace with site data.

## Prices

| Input | Value | Status |
|---|---|---|
| Diesel 50ppm | P23.76/L from 23 Oct 2026 (up 283 thebe) | **Sourced**: BERA via Daily News |
| Delivery to the Delta | P0/L in the scenario | **Assumption**, deliberately low. No public figure found. Trucking, barging or flying fuel in costs more, so real savings are higher. Set `diesel_delivery_p_per_l` per site. |
| Solar capex | P9,000/kWp installed | **Assumption**; no public Botswana figure found |
| Battery capex | P4,000/kWh installed, with inverters | **Assumption**; no public Botswana figure found |
| Battery replacement | P3,000/kWh; LFP, 6,000 cycles | **Assumption**; a wear cost of about P0.56 per kWh moved |
| BPC grid tariffs | Not used yet (camp is off-grid) | 9% increase across all categories from 1 Aug 2026; large users' maximum demand now in kVA over 6 months (**sourced**, BERA). Exact rates not found online. |

## Solar

| Input | Value | Status |
|---|---|---|
| Irradiation | 2,169 kWh/m² a year at -19.5, 23.0 | **Sourced**: PVGIS 5.3 typical meteorological year, PVGIS-SARAH3 database, fetched 2026-10-30. Stored as 365 daily totals in `scenarios/data/`. |
| Hourly shape | Each day's total spread with that day's clear-sky curve | Method choice. Keeps real day-to-day weather (cloudy spells) but smooths cloud within a day. Hourly PVGIS data (`scripts/fetch_pvgis.py`) would remove this. |
| Data gaps | Days 23, 109 and 110 are zero in PVGIS (missing) | Filled with the neighbouring days' mean |
| Performance ratio | 0.78 | **Assumption** (typical for hot, dusty sites) |
| Fallback model | 2,150 kWh/m², wet season Nov–Mar, overcast spells | Only used when no PVGIS file exists |

## System size

| Input | Value | Status |
|---|---|---|
| Solar | 55 kWp | **Sourced**: a real Okavango Delta camp install (The Solar Zone, 2018) |
| Battery | 195 kWh lithium (Blue Nova) | **Sourced**: same install |
| Battery power | 50 kW | **Assumption** (inverter ratings not published) |
| Generator | 40 kW | **Assumption** |

## Load (the biggest unknown)

| Input | Value | Status |
|---|---|---|
| Always-on base | 6 kW (cold rooms, pumps, comms, staff village) | **Assumption** |
| Guest energy at full occupancy | 200 kWh/day | **Assumption** |
| Occupancy | 40–45% Jan–Mar, 90–95% Jun–Oct | **Assumption** (green vs dry season) |
| Result | ~293 kWh/day average, 28 kW peak, 107 MWh/yr | Modelled. Consistent with a 55 kWp camp (about 255 kWh/day of solar). Wilderness's 18 solar camps make over 10,000 kWh/day together, about 555 kWh/day each, but those are larger camps. |

## Generator

| Input | Value | Status |
|---|---|---|
| Fuel curve | 0.08145 L/h per kW rated + 0.246 L per kWh | **Assumption**: a common default curve used in hybrid-system tools. Gives ~0.49 L/kWh for this lightly loaded 40 kW set. |
| Minimum load | 30% of rated | **Assumption** (common maker guidance) |

## Real camps, for checking

| Site | Figures | Source |
|---|---|---|
| A Delta safari camp | 55 kWp, 195 kWh Blue Nova lithium, Fronius 20 kVA and Victron Quattro inverters | The Solar Zone, 2018 |
| Xigera Safari Lodge (Moremi, Delta) | 400–460 kW solar (1,312 panels), 1.14 MWh Tesla Powerpacks, 2 × 350 kVA generators, 95% solar, ~175,000 L diesel saved a year | Fully Charged 2019; Getaway 2022 |
| Wilderness (all camps) | 18 solar camps make over 10,000 kWh/day; hybrids cut generator use by up to 66% | Wilderness, 26 Oct 2023 |
| Nambwa / Kazile (Namibia) | 50 kWp and 25 kWp, rent-to-own (pay per kWh, no capital outlay) | BizNews, 2021 |

## Sources

- Diesel price: [Daily News, fuel price adjustment, 23 Oct 2026](https://dailynews.gov.bw/news-detail/93795)
- BPC tariffs 2026/27: [BERA press release](https://www.bera.co.bw/downloads/Electricity/BPC%202026-27%20Tariff%20Application%20-%20Public%20Notice/Press%20Release%20-%20Electricity%20Tariff%20Adjustments%20For%202026_27%20-%20signed.pdf)
- Solar: [PVGIS 5.3 TMY API, -19.5, 23.0](https://re.jrc.ec.europa.eu/api/v5_3/tmy?lat=-19.5&lon=23.0&outputformat=json)
- Delta camp install: [The Solar Zone, Safari camp off-grid solar system](https://thesolarzone.wordpress.com/2018/02/10/safari-camp-60kwp-off-grid-solar-system/)
- Xigera: [Fully Charged](https://fullycharged.show/blog/powered-by-the-sun-xigera-safari-lodge), [Getaway](https://www.getaway.co.za/destinations/africa/botswana-africa/this-botswana-safari-lodge-runs-on-more-than-90-solar-power/)
- Wilderness: [Wilderness drives commitment to sustainable energy solutions](https://wildernessdestinations.com/journal/press-releases/wilderness-drives-commitment-to-sustainable-energy-solutions)
- Namibia lodges: [BizNews, Off-grid safari lodges turn to solar power](https://www.biznews.com/news/off-grid-safari-lodges-solarsaver)
- Market context: [500 MW Maun solar + 500 MWh battery breaks ground (gov.bw, 16 Apr 2026)](https://www.gov.bw/botswana-breaks-ground-landmark-500mw-maun-solar-project), [mining company opens 30 MW solar tender (pv magazine, Jun 2026)](https://www.pv-magazine.com/2026/06/17/mining-company-opens-30-mw-solar-tender-in-botswana/)
