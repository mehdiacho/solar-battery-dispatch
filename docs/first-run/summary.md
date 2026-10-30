# 10-tent Okavango Delta camp: solar + battery + diesel

Site: Okavango Delta (illustrative location) (-19.5, 23.0). Solar data: built-in model (clear sky scaled to annual GHI; replace with PVGIS).
System: 100 kWp solar, 300 kWh / 75 kW battery, 40 kW generator. Diesel at P23.76/L.
Load: 107 MWh a year, peak 28 kW, average 293 kWh/day.

| Strategy | Diesel (L/yr) | Fuel cost (P/yr) | Battery wear (P/yr) | Running cost (P/yr) | Saving vs diesel (P/yr) | Solar share | Gen hours | Starts | Capex (P) | Payback (yrs) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Diesel only (today) | 57,792 | 1,373,127 | 0 | 1,373,132 | 0 | 0% | 8,760 | 1 |  |  |
| Solar + diesel, no battery | 34,141 | 811,194 | 0 | 813,024 | 560,107 | 35% | 5,238 | 366 | 900,000 | 1.6 |
| Solar + battery, load-following rule | 472 | 11,219 | 31,753 | 43,122 | 1,330,010 | 99% | 74 | 30 | 2,100,000 | 1.6 |
| Solar + battery, cycle-charging rule | 681 | 16,183 | 31,983 | 48,206 | 1,324,926 | 98% | 52 | 8 | 2,100,000 | 1.6 |
| Solar + battery, optimised (perfect forecast) | 325 | 7,729 | 31,915 | 39,719 | 1,333,413 | 99% | 30 | 15 | 2,100,000 | 1.6 |

Unserved energy (worst strategy): 0.0 kWh.

Every input is an assumption until replaced with site data; see the scenario file and docs/assumptions.md.
