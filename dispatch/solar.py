"""Hourly PV output for one year.

Two sources:
- PVGIS typical-year data, if `data/pvgis_tmy_<lat>_<lon>.csv` exists (see scripts/fetch_pvgis.py).
- Otherwise a built-in model: sun position + Haurwitz clear sky, scaled so the year matches the
  scenario's annual GHI, with a wet-season cloud factor and random cloudy days. Good enough to
  compare dispatch strategies; replace with PVGIS before quoting numbers to a customer.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np

HOURS = 8760


def _hour_index():
    """Day of year (1..365) and local solar-ish hour (0.5..23.5) for each of 8760 hours."""
    h = np.arange(HOURS)
    doy = h // 24 + 1
    hour = h % 24 + 0.5  # mid-hour
    return doy, hour


def cos_zenith(lat_deg: float, lon_deg: float, utc_offset: float = 2.0) -> np.ndarray:
    """Cosine of the solar zenith angle at mid-hour, local standard time (Spencer 1971)."""
    doy, hour = _hour_index()
    g = 2 * math.pi / 365 * (doy - 1 + (hour - 12) / 24)
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    eot = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                    - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))  # minutes
    solar_time = hour * 60 + eot + 4 * lon_deg - 60 * utc_offset  # minutes
    ha = np.radians(solar_time / 4 - 180)
    lat = math.radians(lat_deg)
    cz = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha)
    return np.clip(cz, 0, None)


def clear_sky_ghi(cz: np.ndarray) -> np.ndarray:
    """Haurwitz clear-sky global horizontal irradiance, W/m2."""
    out = np.zeros_like(cz)
    up = cz > 0.01
    out[up] = 1098 * cz[up] * np.exp(-0.057 / cz[up])
    return out


def modelled_ghi(lat: float, lon: float, annual_kwh_m2: float, wet_months: list[int],
                 wet_factor: float, cloudy_day_prob: float, seed: int, utc_offset: float = 2.0) -> np.ndarray:
    """Hourly GHI (W/m2) from clear sky, seasonal cloud and random cloudy days, scaled to the annual total."""
    ghi = clear_sky_ghi(cos_zenith(lat, lon, utc_offset))
    doy, _ = _hour_index()
    month = np.array([_month_of_day(d) for d in doy])
    rng = np.random.default_rng(seed)
    # Per-day cloudiness as a two-state chain, so overcast days come in runs (as they do in the
    # rains). Clear days still vary a little.
    day_factor = np.empty(365)
    cloudy = False
    for d in range(365):
        wet = _month_of_day(d + 1) in wet_months
        if cloudy:
            cloudy = rng.random() < (0.55 if wet else 0.30)          # chance an overcast spell continues
        else:
            cloudy = rng.random() < cloudy_day_prob * (2.5 if wet else 0.5)
        day_factor[d] = rng.uniform(0.2, 0.6) if cloudy else rng.uniform(0.85, 1.0)
    factor = day_factor[doy - 1] * np.where(np.isin(month, wet_months), wet_factor, 1.0)
    ghi = ghi * factor
    total = ghi.sum() / 1000  # kWh/m2
    return ghi * (annual_kwh_m2 / total)


def _month_of_day(doy: int) -> int:
    ends = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365]
    for i, e in enumerate(ends):
        if doy <= e:
            return i + 1
    return 12


def pvgis_path(data_dir: Path, lat: float, lon: float) -> Path:
    return data_dir / f"pvgis_tmy_{lat:.3f}_{lon:.3f}.csv"


def load_pvgis(path: Path) -> np.ndarray:
    """Hourly GHI (W/m2), 8760 values in local time, from a CSV written by scripts/fetch_pvgis.py."""
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    ghi = np.array([float(r["ghi_w_m2"]) for r in rows])
    if len(ghi) != HOURS:
        raise ValueError(f"{path}: expected {HOURS} hours, got {len(ghi)}")
    return ghi


def pv_output_kw(ghi_w_m2: np.ndarray, kwp: float, performance_ratio: float) -> np.ndarray:
    """AC output per hour (kW = kWh for a one-hour step). Tilt is ignored; the performance ratio
    absorbs heat, soiling, wiring and inverter losses."""
    return kwp * ghi_w_m2 / 1000 * performance_ratio


def pvgis_daily_path(data_dir: Path, lat: float, lon: float) -> Path:
    return data_dir / f"pvgis_tmy_daily_{lat:.3f}_{lon:.3f}.csv"


def load_pvgis_daily(path: Path, lat: float, lon: float, utc_offset: float = 2.0) -> np.ndarray:
    """Hourly GHI (W/m2) from 365 PVGIS daily totals: each day's total is spread over the hours
    with that day's clear-sky shape. Keeps the real day-to-day weather (what matters for battery
    sizing) but smooths cloud within a day. Days that are 0 in the source (missing data) are
    filled with the mean of the nearest non-zero days either side."""
    with open(path, newline="") as f:
        rows = [line for line in f if not line.startswith("#")]
    daily = np.array([float(r["ghi_wh_m2"]) for r in csv.DictReader(rows)])
    if len(daily) != 365:
        raise ValueError(f"{path}: expected 365 days, got {len(daily)}")
    for i in np.flatnonzero(daily <= 0):
        prev = next((daily[j] for j in range(i - 1, -1, -1) if daily[j] > 0), None)
        nxt = next((daily[j] for j in range(i + 1, 365) if daily[j] > 0), None)
        daily[i] = np.mean([v for v in (prev, nxt) if v is not None])
    shape = clear_sky_ghi(cos_zenith(lat, lon, utc_offset)).reshape(365, 24)
    shape = shape / shape.sum(axis=1, keepdims=True)
    return (shape * daily[:, None]).reshape(-1)


def site_ghi(site: dict, data_dir: Path) -> tuple[np.ndarray, str]:
    """GHI for the site, preferring PVGIS data when it has been fetched."""
    p = pvgis_path(data_dir, site["lat"], site["lon"])
    if p.exists():
        return load_pvgis(p), f"PVGIS typical year, hourly ({p.name})"
    p = pvgis_daily_path(data_dir, site["lat"], site["lon"])
    if p.exists():
        ghi = load_pvgis_daily(p, site["lat"], site["lon"], site.get("utc_offset", 2.0))
        return ghi, f"PVGIS typical year, daily totals with clear-sky hourly shape ({p.name})"
    s = site["solar_model"]
    ghi = modelled_ghi(site["lat"], site["lon"], s["annual_ghi_kwh_m2"], s["wet_months"],
                       s["wet_season_factor"], s["cloudy_day_prob"], s["seed"], site.get("utc_offset", 2.0))
    return ghi, "built-in model (clear sky scaled to annual GHI; replace with PVGIS)"
