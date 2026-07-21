# Vivarium model reference

Framework-specific heuristics for annotating **Vivarium-core** models. Loaded conditionally from `SKILL.md` Pass 0 dispatch only when the Vivarium signal matches. This file adds *where to look* and *how to interpret* for Vivarium; it does **not** redefine schema fields — field names, envelopes (`{value, source, confidence}`), and the split across `metadata.yaml`/`execution.yaml` all come from `references/schema.md`. When this file and `schema.md` disagree on a field's shape, `schema.md` wins.

**Generic to any Vivarium model.** Key off the framework API, not any one repo's layout. Directory names (`composites/`, `processes/`, `experiments/`), output-dir constants, golden-data folders, argparse flags, and "canonical file" choices vary per repo — the examples below are illustrations, never assumptions. Vivarium-core also changed across versions: the composite base class was `Generator` (legacy) and is `Composer` now; the wiring methods were `generate_processes` + `generate_topology` and are `generate` now. Detect whichever the repo uses; don't hardcode one.

---

## Detection (Pass 0)

Treat the model as Vivarium if **any** of these hold:

- A dependency `vivarium` or `vivarium-core` in `setup.py`, `pyproject.toml`, `requirements.txt`, `environment.yml`, or `Pipfile`.
- Any import from `vivarium.core.*` — e.g. `Process`, `Composer` (or legacy `Generator`), `Composite`, `Engine`.
- Calls to a Vivarium run helper: `Engine(...)`, `simulate_process`, `simulate_process_in_experiment`, `simulate_compartment_in_experiment`, or an `Engine(...).update(...)` / `.run(...)` loop.

Once matched, apply the heuristics below through Passes 1–3.

## Vocabulary — what the three units are

- **Process** — the smallest unit: one mechanism with its own `ports_schema` and a `next_update` (legacy `update`) step. Subclass of `vivarium.core.process.Process`.
- **Composite / Composer** — wires several processes together into one runnable system via a topology (`generate` in current vivarium-core, `generate_processes` + `generate_topology` in legacy). This is "the model as an integrated unit."
- **Experiment** — places composite(s) in an environment/timeline and runs a full simulation, often to reproduce a specific scenario or figure. Highest-level run.

A repo may expose any subset of these tiers, under any directory names. Record the tiers that actually exist; do not assume a `processes/`+`composites/`+`experiments/` split.

## Entry points (Pass 2)

Determine `execution.entry_points` in priority order:

1. **Declared entry points win.** If the repo defines `[project.scripts]` (pyproject) or `console_scripts` (setup.py), use those commands verbatim. (Many Vivarium repos leave `console_scripts` empty — then fall through.)
2. **Self-launching modules.** Otherwise, every module with an `if __name__ == '__main__':` block that constructs and runs a Process/Composite through the `Engine` (or a `simulate_*` helper) is a runnable entry point. Command form is `python <relative/path/to/file.py>` — **not** `python -m …` and **not** a console script, unless the repo actually provides one.

For each entry point:

- **`source` is the module file path** — the `.py` file that holds the `__main__` block (e.g. `chemotaxis/composites/chemotaxis_master.py`), since that file *is* what makes the command runnable. Do not put a README line reference here; you may append one after the file path if the README also documents the command.
- **`confidence`** is `high` for any module you confirmed has an `if __name__ == '__main__':` block (a grep either finds it or not — the runnability is verified), `inferred` only if you wrote the command without confirming the block.
- Read the `__main__` argparse block and emit **one `arguments` entry per `add_argument`**, using the 7-field shape in `references/schema.md` (`name`/`description`/`default`/`enums`/`data_type`/`position`/`user_can_override`). Keep flags OUT of the `command` string — `command` is the base invocation only. Mapping: `store_true`/`store_false` → `data_type: "bool"` with `default: false`/`true`; a `choices=[...]` option → `enums`; a mutually-exclusive group (e.g. `--variable` vs `--expression`) → separate `bool` entries, note the exclusivity in each `description`; a positional arg → `position` (>=1, unique) and a `<NAME>` placeholder in `command`.
- **`default_output_location`** — determine where this specific entry writes results and record it as a **repo-relative** path (never absolute). In Vivarium the `__main__` block usually builds an output dir before running; look, in order, for: a package-level output-dir constant referenced in the block (e.g. an `OUT_DIR` / `COMPOSITE_OUT_DIR` / `EXPERIMENT_OUT_DIR` defined in the package `__init__.py`, often `out/<tier>/<NAME>/`), an argparse `--out`/`out_dir` default, a literal `os.makedirs(...)` / save path, or the emitter config. Resolve constants to their actual string value and make it relative to the repo root. If the entry writes nothing (e.g. a `--topology` diagram-only run) or you can't determine the location within the reading budget, omit the field or set it null — do not guess.
- Set `purpose` from the module's docstring / the composite or experiment it runs.
- Mark a **canonical** entry point in `purpose` only if the README/docs single one out (e.g. "the master composite"). Do not guess canonicality from filenames.
- The run logic often lives in a `test_*` or `run_*` function that `__main__` calls; these `test_*` functions are frequently also the pytest suite (`--doctest-modules` / `testpaths`), so record the test framework + invocation in `execution.tests` when present.

**Enumerate EXHAUSTIVELY — one `entry_points` entry per runnable module, not one representative per tier.** If the repo has 6 runnable composites, 4 runnable processes, and 1 experiment runner, that is 11 entries, not 3. "Cover every tier" is the floor, not the target: a list that samples one module per tier is a bug, not a valid reading. To build the list, actually enumerate the `if __name__ == '__main__':` blocks (e.g. `grep -rl "__main__"` over the source tree) — do not infer the set from the README's usage examples, which typically show only one command per tier. This is high-confidence **structural** extraction (a grep either finds the block or it doesn't), so it is exempt from the "copy only what the README states verbatim" bias in the generic passes — enumerate the modules even though the README does not spell out every command. If you deliberately leave any runnable module out (e.g. a budget cap on a huge repo), you MUST record the omitted modules in `provenance.partial_annotation_scope.deferred` — dropping them silently is not allowed.

## Classification (Pass 1)

Only assert what the **framework** implies; derive the rest from the actual processes composed.

- `time_dynamics: discrete` — Vivarium advances by a fixed timestep. Framework-level evidence; source = the Vivarium dependency/import. (This is the SKILL.md `discrete` vs `event-driven` tiebreaker.)
- `model_class` includes `multi-scale model` **only when** the composed processes genuinely span multiple scales (e.g. molecular + cellular). Don't add it for a single-scale composite.
- **Do not hardcode `formalism` or the remaining `model_class` entries.** A Vivarium composite is whatever its processes are — a process may be ODE, SDE, Boolean, stochastic, or agent-based. Read the process code (rate laws, solver imports, random draws, update logic) and record each `formalism` / `model_class` entry with its **own** `source` pointing at that evidence, per the SKILL.md multi-element-field rule.

## I/O (Pass 3)

Map the Vivarium API onto Section C, within the SKILL.md reading budget (entry point + 2–3 directly-imported modules):

- **Parameters** — a Process's or Composer's `defaults` dict (and any config passed at construction) → `io.inputs.parameters`. Key → `name`, value → `default_value`; infer units/meaning from surrounding names and docstrings.
- **State channels** — the `ports_schema` (and the composite's topology wiring) describes the state variables the model reads/writes → `io.inputs.initial_conditions` for stores with explicit initial values.
- **Data inputs** — external files the run reads (parameter tables, sequence/topology data, golden/reference CSVs used for comparison) → `io.data_inputs`, with format.
- **Outputs** — the Engine's emitter is what records results; **output destination is wherever the run script writes**, not an assumed `out/`. Inspect the emitter config, an argparse `--out`, or a package-level output-dir constant. Emitted variables (timeseries of the observed ports) and any generated plots → `io.outputs`.
