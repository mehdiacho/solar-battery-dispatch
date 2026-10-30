"""Generator and battery parameters, and the costs that drive dispatch."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Genset:
    rated_kw: float
    min_load_frac: float      # can't run below this share of rated power
    fuel_a: float             # L/h per kW rated (no-load burn)
    fuel_b: float             # L/h per kW output
    start_cost_p: float = 0.0  # wear per start, Pula

    @property
    def min_kw(self) -> float:
        return self.rated_kw * self.min_load_frac

    def fuel_l(self, kw: float, on: bool = True) -> float:
        return (self.fuel_a * self.rated_kw + self.fuel_b * kw) if on else 0.0


@dataclass(frozen=True)
class Battery:
    capacity_kwh: float
    power_kw: float
    round_trip_eff: float
    soc_min: float
    soc_max: float
    soc_start: float
    wear_p_per_kwh: float     # Pula per kWh of throughput (charge + discharge) / 2

    @property
    def eff_one_way(self) -> float:
        return self.round_trip_eff ** 0.5

    @property
    def e_min(self) -> float:
        return self.capacity_kwh * self.soc_min

    @property
    def e_max(self) -> float:
        return self.capacity_kwh * self.soc_max


def battery_wear_cost(replacement_p_per_kwh: float, cycle_life: float, usable_frac: float) -> float:
    """Pula per kWh moved through the battery: replacement cost spread over lifetime throughput."""
    return replacement_p_per_kwh / (cycle_life * usable_frac)


def make_components(sc: dict) -> tuple[Genset, Battery | None, float]:
    g = sc["genset"]
    genset = Genset(g["rated_kw"], g["min_load_frac"], g["fuel_a_l_per_h_per_kw_rated"],
                    g["fuel_b_l_per_kwh"], g.get("start_cost_p", 0.0))
    b = sc.get("battery", {})
    battery = None
    if b and b.get("capacity_kwh", 0) > 0:
        usable = b["soc_max"] - b["soc_min"]
        wear = battery_wear_cost(b["replacement_p_per_kwh"], b["cycle_life"], usable)
        battery = Battery(b["capacity_kwh"], b["power_kw"], b["round_trip_eff"], b["soc_min"],
                          b["soc_max"], b.get("soc_start", b["soc_max"]), wear)
    fuel_price = sc["costs"]["diesel_p_per_l"] + sc["costs"].get("diesel_delivery_p_per_l", 0.0)
    return genset, battery, fuel_price
