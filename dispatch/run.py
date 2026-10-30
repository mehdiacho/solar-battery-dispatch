"""Run a scenario: every strategy for one year, then a report and charts."""

from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import numpy as np

from .components import make_components
from .load import load_profile
from .metrics import simple_payback_years, summarise
from .solar import pv_output_kw, site_ghi
from .strategies import run_optimal, run_rule

STRATEGY_LABELS = {
    "diesel_only": "Diesel only (today)",
    "solar_diesel": "Solar + diesel, no battery",
    "load_following": "Solar + battery, load-following rule",
    "cycle_charging": "Solar + battery, cycle-charging rule",
    "optimal": "Solar + battery, optimised (perfect forecast)",
}


def build_inputs(sc: dict):
    ghi, solar_source = site_ghi(sc["site"], sc["_dir"] / "data")
    pv = pv_output_kw(ghi, sc["pv"]["kwp"], sc["pv"]["performance_ratio"])
    load = load_profile(sc["load"], sc["_dir"], seed=sc["load"].get("seed", 1))
    genset, battery, fuel_price = make_components(sc)
    return pv, load, genset, battery, fuel_price, solar_source


def run_all(sc: dict, optimal: bool = True):
    pv, load, genset, battery, price, solar_source = build_inputs(sc)
    cc = sc.get("dispatch", {}).get("cycle_charging_setpoint", 0.8)
    zero = np.zeros_like(pv)
    runs = [
        run_rule("diesel_only", zero, load, genset, None),
        run_rule("solar_diesel", pv, load, genset, None),
    ]
    if battery:
        runs += [run_rule("load_following", pv, load, genset, battery),
                 run_rule("cycle_charging", pv, load, genset, battery, cc)]
        if optimal:
            runs.append(run_optimal(pv, load, genset, battery, price))
    runs[1].name = "solar_diesel"
    summaries = [summarise(d, genset, battery if d.name not in ("diesel_only", "solar_diesel") else None, price)
                 for d in runs]
    for d in runs:
        err = d.balance_error()
        if err > 1e-3:
            raise AssertionError(f"{d.name}: energy balance off by {err:.4f} kWh")
    return runs, summaries, dict(pv=pv, load=load, genset=genset, battery=battery, price=price,
                                 solar_source=solar_source)


def capex_p(sc: dict, with_battery: bool) -> float:
    c = sc["costs"]
    total = sc["pv"]["kwp"] * c["pv_capex_p_per_kwp"]
    if with_battery and sc.get("battery", {}).get("capacity_kwh", 0) > 0:
        total += sc["battery"]["capacity_kwh"] * c["battery_capex_p_per_kwh"]
    return total


def run_scenario(sc: dict, out_root: Path, optimal: bool = True) -> Path:
    out = out_root / sc["name"]
    out.mkdir(parents=True, exist_ok=True)
    runs, summaries, ctx = run_all(sc, optimal)
    base = summaries[0]["running_cost_p"]
    for s in summaries:
        s["saving_vs_diesel_p"] = base - s["running_cost_p"]
        cap = 0.0 if s["strategy"] == "diesel_only" else capex_p(sc, s["strategy"] != "solar_diesel")
        s["capex_p"] = cap
        pb = simple_payback_years(cap, s["saving_vs_diesel_p"]) if cap else None
        s["payback_years"] = pb if pb is not None else float("nan")

    with open(out / "summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summaries[0].keys()))
        w.writeheader()
        w.writerows(summaries)
    (out / "summary.md").write_text(_report(sc, summaries, ctx))
    _charts(out, runs, ctx)
    print((out / "summary.md").read_text())
    return out


def _report(sc: dict, rows: list[dict], ctx: dict) -> str:
    b = sc.get("battery", {})
    lines = [
        f"# {sc.get('title', sc['name'])}",
        "",
        f"Site: {sc['site']['name']} ({sc['site']['lat']}, {sc['site']['lon']}). "
        f"Solar data: {ctx['solar_source']}.",
        f"System: {sc['pv']['kwp']:.0f} kWp solar, {b.get('capacity_kwh', 0):.0f} kWh / "
        f"{b.get('power_kw', 0):.0f} kW battery, {sc['genset']['rated_kw']:.0f} kW generator. "
        f"Diesel at P{ctx['price']:.2f}/L.",
        f"Load: {ctx['load'].sum() / 1000:.0f} MWh a year, peak {ctx['load'].max():.0f} kW, "
        f"average {ctx['load'].mean() * 24:.0f} kWh/day.",
        "",
        "| Strategy | Diesel (L/yr) | Fuel cost (P/yr) | Battery wear (P/yr) | Running cost (P/yr) | Saving vs diesel (P/yr) | Solar share | Gen hours | Starts | Capex (P) | Payback (yrs) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        pb = "" if np.isnan(r["payback_years"]) else f"{r['payback_years']:.1f}"
        cap = "" if not r["capex_p"] else f"{r['capex_p']:,.0f}"
        lines.append(
            f"| {STRATEGY_LABELS.get(r['strategy'], r['strategy'])} | {r['fuel_l']:,.0f} | {r['fuel_cost_p']:,.0f} | "
            f"{r['battery_wear_p']:,.0f} | {r['running_cost_p']:,.0f} | {r['saving_vs_diesel_p']:,.0f} | "
            f"{r['renewable_fraction']:.0%} | {r['genset_hours']:,} | {r['genset_starts']:,} | {cap} | {pb} |")
    unserved = max(r["unserved_kwh"] for r in rows)
    lines += ["", f"Unserved energy (worst strategy): {unserved:.1f} kWh.",
              "", "Every input is an assumption until replaced with site data; see the scenario file and docs/assumptions.md."]
    return "\n".join(lines) + "\n"


def _charts(out: Path, runs, ctx) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    show = [d for d in runs if d.name in ("load_following", "optimal")] or runs[1:2]
    for label, start_day in (("dry-season-week", 196), ("wet-season-week", 32)):
        fig, axes = plt.subplots(len(show), 1, figsize=(12, 3.4 * len(show)), sharex=True, squeeze=False)
        sl = slice(start_day * 24, start_day * 24 + 7 * 24)
        hrs = np.arange(7 * 24)
        for ax, d in zip(axes[:, 0], show):
            # What serves the load each hour: battery first, then generator, the rest is solar.
            batt = np.minimum(d.discharge[sl], d.load[sl])
            gen = np.minimum(d.genset_kw[sl], d.load[sl] - batt)
            solar = np.clip(d.load[sl] - batt - gen - d.unserved[sl], 0, None)
            ax.stackplot(hrs, solar, batt, gen, labels=["Solar", "Battery", "Generator"],
                         colors=["#f2b705", "#2f7ed8", "#7f7f7f"], alpha=0.85)
            ax.plot(hrs, d.pv_avail[sl], color="#d68910", lw=0.8, ls=":", label="Solar available")
            ax.plot(hrs, d.load[sl], color="black", lw=1.2, label="Load")
            if ctx["battery"]:
                ax2 = ax.twinx()
                ax2.plot(hrs, d.energy[sl] / ctx["battery"].capacity_kwh * 100, color="#c0392b", lw=1, ls="--")
                ax2.set_ylim(0, 105)
                ax2.set_ylabel("Battery %", color="#c0392b")
            ax.set_title(STRATEGY_LABELS.get(d.name, d.name))
            ax.set_ylabel("kW")
            ax.legend(loc="upper left", fontsize=8, ncol=5)
        axes[-1, 0].set_xlabel("Hour of week")
        fig.tight_layout()
        fig.savefig(out / f"{label}.png", dpi=110)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4))
    months = np.repeat(np.arange(12), [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
    months = np.repeat(months, 24)
    g = ctx["genset"]
    width = 0.8 / len(runs)
    for i, d in enumerate(runs):
        fuel = (g.fuel_a * g.rated_kw + g.fuel_b * d.genset_kw) * (d.genset_on > 0.5)
        monthly = np.bincount(months, weights=fuel, minlength=12)
        ax.bar(np.arange(12) + i * width, monthly, width, label=STRATEGY_LABELS.get(d.name, d.name))
    ax.set_xticks(np.arange(12) + 0.4 - width / 2)
    ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    ax.set_ylabel("Diesel, litres")
    ax.set_title("Diesel per month by strategy")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "monthly-diesel.png", dpi=110)
    plt.close(fig)


def sweep_sizes(sc: dict, out_root: Path) -> Path:
    out = out_root / sc["name"]
    out.mkdir(parents=True, exist_ok=True)
    sw = sc.get("sweep", {})
    pv_sizes = sw.get("pv_kwp", [0, 50, 100, 150, 200, 250])
    bat_sizes = sw.get("battery_kwh", [0, 150, 300, 450, 600])
    ghi, _ = site_ghi(sc["site"], sc["_dir"] / "data")
    load = load_profile(sc["load"], sc["_dir"], seed=sc["load"].get("seed", 1))
    genset, battery, price = make_components(sc)
    c_rate = sc["battery"]["power_kw"] / sc["battery"]["capacity_kwh"] if battery else 0.5
    zero = np.zeros(len(load))
    base = summarise(run_rule("diesel_only", zero, load, genset, None), genset, None, price)["running_cost_p"]
    rows = []
    for kwp in pv_sizes:
        pv = pv_output_kw(ghi, kwp, sc["pv"]["performance_ratio"])
        for kwh in bat_sizes:
            b = replace(battery, capacity_kwh=kwh, power_kw=kwh * c_rate) if (battery and kwh) else None
            s = summarise(run_rule("load_following", pv, load, genset, b), genset, b, price)
            cap = kwp * sc["costs"]["pv_capex_p_per_kwp"] + kwh * sc["costs"]["battery_capex_p_per_kwh"]
            saving = base - s["running_cost_p"]
            rows.append({"pv_kwp": kwp, "battery_kwh": kwh, "fuel_l": round(s["fuel_l"]),
                         "renewable_fraction": round(s["renewable_fraction"], 3),
                         "running_cost_p": round(s["running_cost_p"]), "saving_p": round(saving),
                         "capex_p": round(cap),
                         "payback_years": round(cap / saving, 1) if saving > 0 and cap else ""})
    with open(out / "sweep.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    grid = np.array([[r["fuel_l"] for r in rows if r["pv_kwp"] == p] for p in pv_sizes]) / 1000
    fig, ax = plt.subplots(figsize=(7, 5))
    im = ax.imshow(grid, origin="lower", cmap="viridis_r", aspect="auto")
    ax.set_xticks(range(len(bat_sizes)), [str(b) for b in bat_sizes])
    ax.set_yticks(range(len(pv_sizes)), [str(p) for p in pv_sizes])
    ax.set_xlabel("Battery, kWh")
    ax.set_ylabel("Solar, kWp")
    for i in range(len(pv_sizes)):
        for j in range(len(bat_sizes)):
            ax.text(j, i, f"{grid[i, j]:.0f}", ha="center", va="center", fontsize=8,
                    color="black" if grid[i, j] < 0.5 * grid.max() else "white")
    ax.set_title("Diesel per year, thousand litres (load-following rule)")
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(out / "sweep-diesel.png", dpi=110)
    plt.close(fig)
    for r in rows:
        print(r)
    return out / "sweep.csv"
