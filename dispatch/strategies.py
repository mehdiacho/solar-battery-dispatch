"""Dispatch strategies. Each returns an hourly `Dispatch`.

Rules (what most hybrid controllers do today):
- load_following: solar first, then battery; the generator runs only to cover what's left,
  at no less than its minimum load, and any extra charges the battery.
- cycle_charging: as above, but once the generator starts it runs near full power and keeps
  running until the battery reaches a set state of charge. Fewer starts, better fuel efficiency.

Optimal (the benchmark): a mixed-integer programme solved with HiGHS over a rolling 48-hour
window with a perfect forecast, committing 24 hours at a time. It shows how much a smarter
controller could save; a real one would use a forecast and land somewhere between.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from .components import Battery, Genset

VOLL_P_PER_KWH = 1000.0  # penalty for unserved energy, so the optimiser never chooses it


@dataclass
class Dispatch:
    name: str
    pv_avail: np.ndarray
    load: np.ndarray
    genset_kw: np.ndarray
    genset_on: np.ndarray
    charge: np.ndarray
    discharge: np.ndarray
    energy: np.ndarray        # battery energy at the end of each hour, kWh
    spill: np.ndarray         # curtailed solar + generator energy that had nowhere to go
    unserved: np.ndarray
    notes: list[str] = field(default_factory=list)

    def balance_error(self) -> float:
        lhs = self.pv_avail + self.genset_kw + self.discharge + self.unserved
        rhs = self.load + self.charge + self.spill
        return float(np.max(np.abs(lhs - rhs)))


def _empty(n: int) -> dict:
    return {k: np.zeros(n) for k in ("g", "on", "c", "d", "e", "spill", "uns")}


def run_rule(name: str, pv: np.ndarray, load: np.ndarray, genset: Genset, battery: Battery | None,
             cc_setpoint: float = 0.8) -> Dispatch:
    n = len(load)
    r = _empty(n)
    has_b = battery is not None
    eta = battery.eff_one_way if has_b else 1.0
    P = battery.power_kw if has_b else 0.0
    e_min = battery.e_min if has_b else 0.0
    e_max = battery.e_max if has_b else 0.0
    e = battery.capacity_kwh * battery.soc_start if has_b else 0.0
    latched = False
    cycle = name == "cycle_charging"

    for t in range(n):
        net = load[t] - pv[t]
        g = c = d = spill = uns = 0.0
        on = False
        room_in = max(0.0, min(P, (e_max - e) / eta)) if has_b else 0.0       # kWh the battery can take
        avail_out = max(0.0, min(P, (e - e_min) * eta)) if has_b else 0.0     # kWh it can give

        if cycle and latched and e >= battery.capacity_kwh * cc_setpoint - 1e-9:
            latched = False

        if net <= 0 and not (cycle and latched):
            c = min(-net, room_in)
            spill = -net - c
        else:
            deficit = max(net, 0.0)
            surplus = max(-net, 0.0)
            if not (cycle and latched) and avail_out >= deficit:
                d = deficit
            else:
                on = True
                if cycle:
                    latched = has_b
                    target = deficit + room_in
                else:
                    target = deficit
                g = min(genset.rated_kw, max(genset.min_kw, target))
                if g < deficit:
                    d = min(deficit - g, avail_out)
                    uns = deficit - g - d
                else:
                    extra = g - deficit + surplus
                    c = min(extra, room_in)
                    spill = extra - c
        if has_b:
            e = e + c * eta - d / eta
        r["g"][t], r["on"][t], r["c"][t], r["d"][t] = g, float(on), c, d
        r["e"][t], r["spill"][t], r["uns"][t] = e, spill, uns

    return Dispatch(name, pv, load, r["g"], r["on"], r["c"], r["d"], r["e"], r["spill"], r["uns"])


def run_optimal(pv: np.ndarray, load: np.ndarray, genset: Genset, battery: Battery | None,
                fuel_price: float, horizon: int = 48, step: int = 24) -> Dispatch:
    n = len(load)
    r = _empty(n)
    has_b = battery is not None
    e0 = battery.capacity_kwh * battery.soc_start if has_b else 0.0
    u_prev = 0.0
    t0 = 0
    while t0 < n:
        H = min(horizon, n - t0)
        sol = _solve_window(pv[t0:t0 + H], load[t0:t0 + H], genset, battery, fuel_price, e0, u_prev)
        k = min(step, H)
        for key in r:
            r[key][t0:t0 + k] = sol[key][:k]
        e0 = sol["e"][k - 1] if has_b else 0.0
        u_prev = sol["on"][k - 1]
        t0 += k
    return Dispatch("optimal", pv, load, r["g"], r["on"], r["c"], r["d"], r["e"], r["spill"], r["uns"],
                    notes=["perfect 48 h forecast, rolling daily"])


def _solve_window(pv, load, genset: Genset, battery: Battery | None, price, e0, u_prev):
    H = len(load)
    has_b = battery is not None
    # variable blocks: g, u, c, d, e, spill, uns, s
    G, U, C, D, E, SP, UN, S = (i * H for i in range(8))
    nv = 8 * H
    cost = np.zeros(nv)
    cost[G:G + H] = price * genset.fuel_b
    cost[U:U + H] = price * genset.fuel_a * genset.rated_kw
    if has_b:
        cost[C:C + H] = battery.wear_p_per_kwh / 2
        cost[D:D + H] = battery.wear_p_per_kwh / 2
    cost[SP:SP + H] = 1e-4
    cost[UN:UN + H] = VOLL_P_PER_KWH
    cost[S:S + H] = genset.start_cost_p
    if has_b:
        # Energy left in the battery at the end of the window is worth the diesel it will save
        # later; without this the optimiser empties the battery just before the horizon.
        cost[E + H - 1] = -(price * genset.fuel_b * battery.eff_one_way - battery.wear_p_per_kwh / 2)

    lb = np.zeros(nv)
    ub = np.full(nv, np.inf)
    ub[G:G + H] = genset.rated_kw
    ub[U:U + H] = 1
    ub[S:S + H] = 1
    if has_b:
        ub[C:C + H] = battery.power_kw
        ub[D:D + H] = battery.power_kw
        lb[E:E + H] = battery.e_min
        ub[E:E + H] = battery.e_max
    else:
        ub[C:C + H] = 0
        ub[D:D + H] = 0
        ub[E:E + H] = 0
    integrality = np.zeros(nv)
    integrality[U:U + H] = 1

    rows = 5 * H
    A = lil_matrix((rows, nv))
    lo = np.zeros(rows)
    hi = np.zeros(rows)
    eta = battery.eff_one_way if has_b else 1.0
    for t in range(H):
        # energy balance: g + d + uns - c - spill = load - pv
        i = t
        A[i, G + t] = 1; A[i, D + t] = 1; A[i, UN + t] = 1; A[i, C + t] = -1; A[i, SP + t] = -1
        lo[i] = hi[i] = load[t] - pv[t]
        # g <= rated * u
        i = H + t
        A[i, G + t] = 1; A[i, U + t] = -genset.rated_kw
        lo[i], hi[i] = -np.inf, 0
        # g >= min * u
        i = 2 * H + t
        A[i, G + t] = 1; A[i, U + t] = -genset.min_kw
        lo[i], hi[i] = 0, np.inf
        # battery: e_t - e_{t-1} - eta c + d/eta = 0
        i = 3 * H + t
        A[i, E + t] = 1; A[i, C + t] = -eta; A[i, D + t] = 1 / eta
        if t > 0:
            A[i, E + t - 1] = -1
            lo[i] = hi[i] = 0
        else:
            lo[i] = hi[i] = e0 if has_b else 0
        # starts: s_t >= u_t - u_{t-1}
        i = 4 * H + t
        A[i, S + t] = 1; A[i, U + t] = -1
        if t > 0:
            A[i, U + t - 1] = 1
            lo[i], hi[i] = 0, np.inf
        else:
            lo[i], hi[i] = -u_prev, np.inf

    res = milp(cost, constraints=LinearConstraint(A.tocsr(), lo, hi), integrality=integrality,
               bounds=Bounds(lb, ub), options={"disp": False, "mip_rel_gap": 1e-4})
    if res.x is None:
        raise RuntimeError(f"optimiser failed: {res.message}")
    x = res.x
    on = np.round(x[U:U + H])
    return {"g": x[G:G + H], "on": on, "c": x[C:C + H], "d": x[D:D + H], "e": x[E:E + H],
            "spill": x[SP:SP + H], "uns": x[UN:UN + H]}
