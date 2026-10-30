"""Command line.

    python -m dispatch run scenarios/delta-camp.toml            # all strategies, report + charts
    python -m dispatch run scenarios/delta-camp.toml --fast     # skip the optimiser
    python -m dispatch sweep scenarios/delta-camp.toml          # PV x battery sizes, load-following
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .scenario import load_scenario
from .run import run_scenario, sweep_sizes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="dispatch")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="simulate one year with every strategy")
    r.add_argument("scenario", type=Path)
    r.add_argument("--fast", action="store_true", help="skip the optimal (MILP) benchmark")
    r.add_argument("--out", type=Path, default=Path("results"))
    s = sub.add_parser("sweep", help="try a grid of PV and battery sizes")
    s.add_argument("scenario", type=Path)
    s.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args(argv)

    sc = load_scenario(args.scenario)
    t = time.time()
    if args.cmd == "run":
        out = run_scenario(sc, args.out, optimal=not args.fast)
    else:
        out = sweep_sizes(sc, args.out)
    print(f"\nWrote {out} in {time.time() - t:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
