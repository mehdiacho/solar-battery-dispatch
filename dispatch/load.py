"""Hourly site load for one year, built from a daily energy figure, an hourly shape and monthly
occupancy. All of these are assumptions until a real meter log replaces them
(put an 8760-row CSV with a `load_kw` column next to the scenario and set `load.csv`)."""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .solar import HOURS, _month_of_day


def load_profile(cfg: dict, base_dir: Path, seed: int = 1) -> np.ndarray:
    if cfg.get("csv"):
        path = base_dir / cfg["csv"]
        with open(path, newline="") as f:
            kw = np.array([float(r["load_kw"]) for r in csv.DictReader(f)])
        if len(kw) != HOURS:
            raise ValueError(f"{path}: expected {HOURS} rows, got {len(kw)}")
        return kw

    shape = np.asarray(cfg["hourly_shape"], dtype=float)
    if shape.size != 24:
        raise ValueError("load.hourly_shape needs 24 values")
    shape = shape / shape.sum()
    occupancy = np.asarray(cfg["monthly_occupancy"], dtype=float)
    cooling = np.asarray(cfg.get("monthly_cooling_factor", [1.0] * 12), dtype=float)
    base_kw = cfg["base_kw"]
    guest_kwh = cfg["guest_kwh_per_day_full"]
    noise = cfg.get("day_noise", 0.08)

    rng = np.random.default_rng(seed)
    kw = np.empty(HOURS)
    for d in range(365):
        m = _month_of_day(d + 1) - 1
        day_kwh = guest_kwh * occupancy[m] * cooling[m] * rng.normal(1.0, noise)
        kw[d * 24:(d + 1) * 24] = base_kw + day_kwh * shape
    return np.clip(kw, 0, None)
