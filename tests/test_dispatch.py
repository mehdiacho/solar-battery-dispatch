import numpy as np
import pytest

from dispatch.components import Battery, Genset
from dispatch.load import load_profile
from dispatch.metrics import summarise
from dispatch.solar import HOURS, clear_sky_ghi, cos_zenith, modelled_ghi, pv_output_kw
from dispatch.strategies import run_optimal, run_rule

GEN = Genset(rated_kw=40, min_load_frac=0.3, fuel_a=0.08145, fuel_b=0.246, start_cost_p=5)
BAT = Battery(capacity_kwh=200, power_kw=50, round_trip_eff=0.92, soc_min=0.1, soc_max=1.0,
              soc_start=0.8, wear_p_per_kwh=0.5)


def _week(seed=0):
    ghi = modelled_ghi(-19.5, 23.0, 2150, [11, 12, 1, 2, 3], 0.92, 0.08, seed)
    pv = pv_output_kw(ghi, 60, 0.78)[: 24 * 14]
    rng = np.random.default_rng(seed)
    load = 8 + 10 * rng.random(24 * 14)
    return pv, load


def test_sun_is_up_by_day_and_down_at_night():
    cz = cos_zenith(-19.5, 23.0).reshape(365, 24)
    assert (cz[:, 0] == 0).all() and (cz[:, 23] == 0).all()
    assert (cz[:, 12] > 0.6).all()


def test_modelled_ghi_hits_the_annual_total():
    ghi = modelled_ghi(-19.5, 23.0, 2150, [11, 12, 1, 2, 3], 0.92, 0.08, seed=3)
    assert len(ghi) == HOURS
    assert ghi.sum() / 1000 == pytest.approx(2150, rel=1e-6)
    assert ghi.max() < 1250


def test_clear_sky_is_zero_below_horizon():
    assert clear_sky_ghi(np.array([0.0, -0.2]))[0] == 0


@pytest.mark.parametrize("name", ["load_following", "cycle_charging"])
def test_rules_balance_energy_and_respect_limits(name):
    pv, load = _week()
    d = run_rule(name, pv, load, GEN, BAT)
    assert d.balance_error() < 1e-9
    assert d.energy.min() >= BAT.e_min - 1e-9 and d.energy.max() <= BAT.e_max + 1e-9
    assert d.charge.max() <= BAT.power_kw + 1e-9 and d.discharge.max() <= BAT.power_kw + 1e-9
    on = d.genset_on > 0.5
    assert (d.genset_kw[on] >= GEN.min_kw - 1e-9).all()
    assert (d.genset_kw[~on] == 0).all()
    assert d.unserved.sum() == 0


def test_optimal_balances_and_beats_the_rules():
    pv, load = _week(1)
    price = 23.76
    opt = run_optimal(pv, load, GEN, BAT, price)
    assert opt.balance_error() < 1e-5
    on = opt.genset_on > 0.5
    assert (opt.genset_kw[on] >= GEN.min_kw - 1e-6).all()
    assert opt.energy.min() >= BAT.e_min - 1e-6
    best_rule = min(summarise(run_rule(n, pv, load, GEN, BAT), GEN, BAT, price)["running_cost_p"]
                    for n in ("load_following", "cycle_charging"))
    assert summarise(opt, GEN, BAT, price)["running_cost_p"] <= best_rule * 1.001


def test_diesel_only_fuel_matches_the_fuel_curve():
    load = np.full(24, 20.0)
    d = run_rule("diesel_only", np.zeros(24), load, GEN, None)
    s = summarise(d, GEN, None, 20.0)
    assert s["fuel_l"] == pytest.approx(24 * (0.08145 * 40 + 0.246 * 20))
    assert s["genset_hours"] == 24 and s["genset_starts"] == 1


def test_low_load_runs_generator_at_minimum_and_spills_the_rest():
    load = np.full(5, 5.0)  # below the 12 kW minimum
    d = run_rule("load_following", np.zeros(5), load, GEN, None)
    assert np.allclose(d.genset_kw, GEN.min_kw)
    assert np.allclose(d.spill, GEN.min_kw - 5)


def test_load_profile_follows_occupancy():
    cfg = {"base_kw": 5, "guest_kwh_per_day_full": 100, "hourly_shape": [1] * 24,
           "monthly_occupancy": [0.2] * 6 + [1.0] * 6, "day_noise": 0}
    kw = load_profile(cfg, base_dir=None)
    jan = kw[: 31 * 24].sum() / 31
    dec = kw[-31 * 24:].sum() / 31
    assert jan == pytest.approx(5 * 24 + 20)
    assert dec == pytest.approx(5 * 24 + 100)


def test_pvgis_daily_loader_keeps_totals_and_fills_gaps(tmp_path):
    from dispatch.solar import load_pvgis_daily
    days = [6000.0] * 365
    days[10] = 0.0
    p = tmp_path / "d.csv"
    p.write_text("# comment\nday,ghi_wh_m2\n" + "".join(f"{i + 1},{v}\n" for i, v in enumerate(days)))
    ghi = load_pvgis_daily(p, -19.5, 23.0)
    daily = ghi.reshape(365, 24).sum(axis=1)
    assert daily[10] == pytest.approx(6000)
    assert daily[0] == pytest.approx(6000)
    assert ghi.reshape(365, 24)[:, 0].max() == 0  # dark at midnight
