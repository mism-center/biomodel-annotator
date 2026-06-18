# Source Files Read — vivarium-chemotaxis

Files read during SKILL.md Passes 0–2 (2026-06-18).
All citations in annotation.yaml use `filename:line` format.

## Pass 0 — Inventory

Top-level file scan of `C:\Users\powen\PycharmProjects\MISM\vivarium-chemotaxis\`.

Files and directories present:
- `README.md` (82 lines)
- `LICENSE`
- `setup.py` (31 lines)
- `requirements.txt` (1 line: `-e .`)
- `pytest.ini` (6 lines)
- `release.sh`
- `chemotaxis/` — Python packages: `processes/`, `composites/`, `experiments/`, `plots/`, `data/`
- `chemotaxis/data/fasta/` — E. coli K-12 MG1655 FASTA file (filename carries organism identity)
- `doc/`, `out/` — documentation and output directories

No top-level YAML files or pre-existing annotation artifacts were found.

Entry points located: `chemotaxis/processes/` (process files with `__main__` blocks),
`chemotaxis/composites/` (composite files with `__main__` blocks),
`chemotaxis/experiments/paper_experiments.py` (command-line argument dispatch).

## Pass 1 — Files Read (Model identity & biology)

| File | Lines read | Key content extracted |
|---|---|---|
| `README.md` | full (82) | Name, description, organism, publications, entry points (lines 51, 56, 63, 69), setup instructions |
| `LICENSE` | full (22) | MIT license, copyright 2020 Vivarium Collective |
| `setup.py` | full (31) | version=0.0.2 (line 12), authors (line 19), email (line 20), URL (line 21), install_requires (lines 27-31) |
| `chemotaxis/processes/chemoreceptor_cluster.py` | lines 1–120 | DEFAULT_LIGAND='MeAsp' (26), Euler ODE run_step (30-44), ReceptorCluster class (49-60), MWC model (52-60), Tsr/Tar (53), defaults CheR/CheB/n_Tar/n_Tsr (97-117) |
| `chemotaxis/processes/flagella_motor.py` | lines 1–100 | FlagellaMotor stochastic model (43-46), time_step=0.01 (49), CheY=2.59 initial (88) |
| `chemotaxis/processes/coarse_motor.py` | lines 1–90 | MotorActivity class (27), CheA/CheY/CheZ initial concentrations (72-76), Vladimirov 2008 + Scharf 1998 model references (33-41) |
| `chemotaxis/processes/membrane_potential.py` | lines 1–80 | MembranePotential class (27), K/Na/Cl/PROTON defaults (49-60), PMF ~170mV note (36) |
| `chemotaxis/composites/chemotaxis_master.py` | full (308) | ChemotaxisMaster Generator (74), iAF1260b FBA import (23-24), MetaDivision (20), full process list (115-135) |
| `chemotaxis/composites/chemotaxis_flagella.py` | lines 1–50 | MetaDivision import (22), DEFAULT_LIGAND (45-46) |
| `chemotaxis/experiments/paper_experiments.py` | lines 1–40 | agent_environment_experiment import (31), available figure numbers (10-11) |

## Pass 2 — Files Read (Execution environment)

| File | Lines read | Key content extracted |
|---|---|---|
| `requirements.txt` | full (1) | `-e .` (editable install; no pinned deps) |
| `pytest.ini` | full (6) | `python_files = *.py`, `testpaths = chemotaxis`, `addopts = --doctest-modules` |

## Ontology mapping status

Pass 4 (ontology mapping via `ols-ontology` MCP) was not executed in this session.
All ontology-eligible fields have `iri: null` in the annotation. Per the SKILL.md
reproducibility invariant, `mapping_confidence` is **omitted entirely** for these fields
(not set to `none`) because the queries were never attempted.

The deferred scope is recorded in `annotation.yaml` under
`provenance.partial_annotation_scope.deferred`.

| Field | Ontology | Status |
|---|---|---|
| `model.model_class[*]` | MAMO | Deferred (Pass 4) |
| `model.formalism[*]` | MAMO | Deferred (Pass 4) |
| `model.biology.species[0]` | NCBITaxon | Deferred (Pass 4) |
| `model.biology.biological_processes[*]` | GO | Deferred (Pass 4) |
| `model.biology.molecular_entities[0]` | ChEBI | Deferred (Pass 4) |
| `model.biology.proteins_genes[*]` identifiers | UniProt | Deferred (Pass 4) |
| `execution.language` | SWO | Deferred (Pass 4) |

## Notes

- numpy is imported throughout the codebase but is absent from `setup.py install_requires`. Its only documented installation instruction is README.md:32-35.
- The FASTA filename in `chemotaxis/data/fasta/` confirms the E. coli strain; the iAF1260b metabolic reconstruction (chemotaxis_master.py:23) is the genome-scale model for K-12 MG1655 specifically.
- README.md:51 contains a typo: `chemoreptor_cluster.py`. The actual filename is `chemoreceptor_cluster.py`. The entry point command is preserved verbatim from the README.
