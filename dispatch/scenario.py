"""Read a scenario TOML file."""

from __future__ import annotations

import tomllib
from pathlib import Path


def load_scenario(path: Path) -> dict:
    with open(path, "rb") as f:
        sc = tomllib.load(f)
    sc["_path"] = path.resolve()
    sc["_dir"] = path.resolve().parent
    sc.setdefault("name", path.stem)
    for key in ("site", "load", "pv", "genset", "costs"):
        if key not in sc:
            raise ValueError(f"{path}: missing [{key}]")
    return sc
