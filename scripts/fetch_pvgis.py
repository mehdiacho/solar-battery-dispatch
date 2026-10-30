"""Fetch a typical-year hourly solar series from PVGIS (EU Joint Research Centre, free, no key)
and save it where the simulator looks for it. Standard library only.

    python scripts/fetch_pvgis.py scenarios/delta-camp.toml

This is a download (about 1 MB from re.jrc.ec.europa.eu), so run it yourself. Written without
network access to PVGIS, so check the first run: it should report about 2,000-2,300 kWh/m2.
"""

from __future__ import annotations

import csv
import json
import sys
import tomllib
import urllib.request
from pathlib import Path

URL = "https://re.jrc.ec.europa.eu/api/v5_3/tmy?lat={lat}&lon={lon}&outputformat=json"


def main(scenario: str) -> None:
    path = Path(scenario).resolve()
    with open(path, "rb") as f:
        site = tomllib.load(f)["site"]
    lat, lon, offset = site["lat"], site["lon"], int(site.get("utc_offset", 2))
    with urllib.request.urlopen(URL.format(lat=lat, lon=lon), timeout=60) as r:
        data = json.load(r)
    rows = data["outputs"]["tmy_hourly"]
    ghi_utc = [float(row["G(h)"]) for row in rows]
    if len(ghi_utc) != 8760:
        raise SystemExit(f"expected 8760 hours, got {len(ghi_utc)}")
    # PVGIS times are UTC; shift to local time (Botswana is UTC+2).
    ghi = ghi_utc[-offset:] + ghi_utc[:-offset] if offset else ghi_utc

    out = path.parent / "data" / f"pvgis_tmy_{lat:.3f}_{lon:.3f}.csv"
    out.parent.mkdir(exist_ok=True)
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hour", "ghi_w_m2"])
        for i, g in enumerate(ghi):
            w.writerow([i, f"{g:.1f}"])
    print(f"wrote {out}: {sum(ghi) / 1000:,.0f} kWh/m2 a year")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(sys.argv[1])
