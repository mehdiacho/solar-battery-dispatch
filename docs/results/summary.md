# 10-tent Okavango Delta camp: solar + battery + diesel

Site: Okavango Delta (illustrative location) (-19.5, 23.0). Solar data: PVGIS typical year, daily totals with clear-sky hourly shape (pvgis_tmy_daily_-19.500_23.000.csv).
System: 55 kWp solar, 195 kWh / 50 kW battery, 40 kW generator. Diesel at P23.76/L.
Load: 107 MWh a year, peak 28 kW, average 293 kWh/day.

| Strategy | Diesel (L/yr) | Fuel cost (P/yr) | Battery wear (P/yr) | Running cost (P/yr) | Saving vs diesel (P/yr) | Solar share | Gen hours | Starts | Capex (P) | Payback (yrs) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Diesel only (today) | 57,792 | 1,373,127 | 0 | 1,373,132 | 0 | 0% | 8,760 | 1 |  |  |
| Solar + diesel, no battery | 37,042 | 880,113 | 0 | 881,903 | 491,229 | 30% | 5,694 | 358 | 495,000 | 1.0 |
| Solar + battery, load-following rule | 9,933 | 236,011 | 25,021 | 264,016 | 1,109,116 | 81% | 1,554 | 597 | 1,275,000 | 1.1 |
| Solar + battery, cycle-charging rule | 12,653 | 300,627 | 30,514 | 332,241 | 1,040,890 | 64% | 966 | 220 | 1,275,000 | 1.2 |
| Solar + battery, optimised (perfect forecast) | 7,026 | 166,939 | 27,589 | 195,863 | 1,177,269 | 81% | 640 | 267 | 1,275,000 | 1.1 |

Unserved energy (worst strategy): 0.0 kWh.

Every input is an assumption until replaced with site data; see the scenario file and docs/assumptions.md.
