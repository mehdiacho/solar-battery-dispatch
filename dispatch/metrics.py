"""Turn an hourly dispatch into the numbers a site owner cares about."""

from __future__ import annotations

import numpy as np

from .components import Battery, Genset
from .strategies import Dispatch

CO2_KG_PER_L_DIESEL = 2.68


def summarise(d: Dispatch, genset: Genset, battery: Battery | None, fuel_price: float) -> dict:
    on = d.genset_on > 0.5
    fuel_l = float(np.sum((genset.fuel_a * genset.rated_kw + genset.fuel_b * d.genset_kw) * on))
    starts = int(np.sum(np.diff(np.concatenate([[0], on.astype(int)])) == 1))
    load_kwh = float(d.load.sum())
    gen_kwh = float(d.genset_kw.sum())
    throughput = float((d.charge.sum() + d.discharge.sum()) / 2)
    wear = throughput * battery.wear_p_per_kwh if battery else 0.0
    usable = (battery.e_max - battery.e_min) if battery else 0.0
    fuel_cost = fuel_l * fuel_price
    start_cost = starts * genset.start_cost_p
    return {
        "strategy": d.name,
        "load_mwh": load_kwh / 1000,
        "solar_available_mwh": float(d.pv_avail.sum()) / 1000,
        "genset_mwh": gen_kwh / 1000,
        "renewable_fraction": max(0.0, 1 - gen_kwh / load_kwh) if load_kwh else 0.0,
        "spilled_mwh": float(d.spill.sum()) / 1000,
        "unserved_kwh": float(d.unserved.sum()),
        "fuel_l": fuel_l,
        "fuel_cost_p": fuel_cost,
        "genset_hours": int(on.sum()),
        "genset_starts": starts,
        "l_per_kwh_generated": fuel_l / gen_kwh if gen_kwh else 0.0,
        "battery_cycles": throughput / usable if usable else 0.0,
        "battery_wear_p": wear,
        "running_cost_p": fuel_cost + wear + start_cost,
        "co2_t": fuel_l * CO2_KG_PER_L_DIESEL / 1000,
    }


def simple_payback_years(capex_p: float, saving_p_per_year: float) -> float | None:
    return capex_p / saving_p_per_year if saving_p_per_year > 0 else None
