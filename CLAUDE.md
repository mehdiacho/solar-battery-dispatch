# solar-battery-dispatch

Read `docs/HANDOFF.md` first: goal, state, commands, decisions and next steps. Assumptions and their sources are in `docs/assumptions.md`.

- Commit as `mehdiacho <mehdiacho@gmail.com>`. No `Co-Authored-By`, AI trailers or "Generated with" lines, and no model names in commits or code.
- Run `python -m pytest -q` before every commit.
- Every number in a scenario is either sourced (say where, with the date) or marked as an assumption. Never present modelled results as measured.
- Downloads (PVGIS data, PyBaMM, new packages) need Mehdi's OK in his own words.
- Update `docs/HANDOFF.md` in the same commit as any milestone.
- This project grew out of idea #38 in `mehdiacho/frontier-research`; keep its `IDEAS.md` status true.
- Write in plain English for Mehdi: lead with the answer, short sentences.
