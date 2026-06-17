# Model Package — vivarium-chemotaxis

**GitHub:** vivarium-collective/vivarium-chemotaxis  
**Version:** 0.0.2  
**DOI:** 10.3390/e22101101  
**Annotated:** 2026-06-17 with `biomodel-annotator/0.1`

This package demonstrates the output of the `biomodel-annotator` skill applied to
vivarium-chemotaxis following the SKILL.md four-pass workflow. **Passes 0, 1, and 2
were executed in this session.** Passes 3 and 4 are deferred (see below).

---

## Passes Completed vs Deferred

| Pass | Name | Status | Notes |
|---|---|---|---|
| Pass 0 | Inventory | **Complete** | 53 files enumerated; key files confirmed |
| Pass 1 | Model identity / biology (Section A) | **Complete** | 8 source files read with file:line citations |
| Pass 2 | Execution environment (Section B) | **Complete** | 4 source files read; 4 entry points documented |
| Pass 3 | I/O | **Deferred** | Reading budget allocated to Passes 0-2 |
| Pass 4 | Ontology mapping | **Deferred** | `ols-ontology` MCP not connected; all `iri:` null |

Because Pass 4 was not executed, this annotation uses `iri: null` throughout. Fields
requiring OLS queries are listed in `provenance.partial_annotation_scope.deferred`,
not in `provenance.unmapped_fields` (which would imply failed attempts). This distinction
is load-bearing per the CLAUDE.md reproducibility invariant.

---

## What was annotated

**vivarium-chemotaxis** is a Python library implementing a multi-scale model of
*E. coli* chemotaxis described in Agmon & Spangler (2020). The library provides four
composable processes:

| Process | File | Formalism | Key output |
|---|---|---|---|
| `ReceptorCluster` | `processes/chemoreceptor_cluster.py` | ODE (MWC) | `chemoreceptor_activity`, `n_methyl` |
| `FlagellaMotor` | `processes/flagella_motor.py` | Stochastic | `motor_state`, `thrust` |
| `MembranePotential` | `processes/membrane_potential.py` | ODE (GHK) | `PMF`, `d_V`, `d_pH` |
| `CoarseMotor` | `processes/coarse_motor.py` | Stochastic | `motor_state`, `motor_bias` |

These compose into three progressively richer models:

| Composite | Processes | Entry point |
|---|---|---|
| `ChemotaxisMinimal` | Receptor + CoarseMotor | `chemotaxis/composites/chemotaxis_minimal.py` |
| `ChemotaxisFlagella` | + FlagellaMotor + gene expression | `chemotaxis/composites/chemotaxis_flagella.py` |
| `ChemotaxisMaster` | + metabolism (iAF1260b) + division | `chemotaxis/composites/chemotaxis_master.py` |

**Annotation scope:** `ChemotaxisMinimal` as the primary experiment unit.
`ChemotaxisMaster` internals (vivarium-cell dependencies) are deferred.

---

## Package layout

```
vivarium-chemotaxis/
  metadata.yaml                    # Section A — model identity and biology (Pass 1)
  execution.yaml                   # Section B — execution environment (Pass 2); io: empty
  README.md                        # this file
  outputs/
    annotation.yaml                # complete annotation (master artifact)
    sample_timeseries.json         # representative ChemotaxisMinimal output (unchanged)
    validation_report.txt          # real validator output — run 2026-06-17T20:05:19Z, EXIT 0
  references/
    source_links.md                # actual files read with line citations; ontology status
```

---

## What was tested

### Annotation passes

| Pass | Description | Status |
|---|---|---|
| Pass 0 | Inventory — README, setup.py, pytest.ini, directory tree | Complete |
| Pass 1 | Identity/biology — name, model_class, formalism, E. coli biology | Complete |
| Pass 2 | Execution — Python/pip, 4 pinned deps, 4 entry points, pytest | Complete |
| Pass 3 | I/O — parameters, initial conditions, data inputs, outputs | **Deferred** |
| Pass 4 | Ontology mapping — ols-ontology MCP queries | **Deferred** |
| Assembly | Full annotation YAML written per schema v0.1 | Complete |

### Structural validation (`Validator().validate()` — run 2026-06-17T20:05:19Z)

```
Checking Section A (model) required fields ... 7/7 OK
Checking Section B (execution) required fields ... 4/4 OK
Structural overall: PASS
```

### Semantic validation

| Check | Result |
|---|---|
| needs_review count | 0 (threshold >5) — OK |
| Ontology coverage | N/A — no eligible fields (Pass 4 not executed; no mapping_confidence fields present) |
| Mapped fields | 0 / 0 eligible |
| Unmapped fields | 0 in provenance.unmapped_fields (not tried ≠ tried-and-failed) |
| Exit code | 0 |

Ontology coverage returns `null` (not 0%) because there are zero eligible fields — the
validator emits no coverage warning when `eligible = 0`.

### Registry check

`mism_registry` is installed; real check executed (not optimistic). Passed after adding
flat registry fields (`name`, `source_repository`, `execution_type: python`) to
`metadata.yaml`. `io_slots_constructed = 0` (W1 warning — `io:` empty, Pass 3 deferred).

---

## Reproducing validation

`src/validator.py` is a library (no `__main__` block). Call it programmatically:

```python
# From the biomodel-annotator repo root
import sys, json
from pathlib import Path
sys.path.insert(0, 'src')
from validator import Validator

ann  = Path('examples/vivarium-chemotaxis/outputs/annotation.yaml').read_text(encoding='utf-8')
meta = Path('examples/vivarium-chemotaxis/metadata.yaml').read_text(encoding='utf-8')
exe  = Path('examples/vivarium-chemotaxis/execution.yaml').read_text(encoding='utf-8')

v = Validator(input_path=Path('examples/vivarium-chemotaxis/outputs'),
              model_id='vivarium-collective/vivarium-chemotaxis')
report = v.validate(ann, meta, exe)
print(json.dumps(report, indent=2))
sys.exit(report['exit_code'])
```

Using the project venv: `C:\Users\powen\PycharmProjects\MISM\.venv\Scripts\python.exe`

Expected: EXIT 0, W1 warning (io_slots_constructed = 0, Pass 3 deferred).

To reproduce a minimal run of the model itself:

```bash
cd /path/to/vivarium-chemotaxis
pip install numpy
pip install -r requirements.txt
python chemotaxis/composites/chemotaxis_minimal.py
# Output written to out/composites/
```

---

## Key annotation decisions

| Decision | Rationale |
|---|---|
| `proteins_genes: []` | Protein names (CheA, CheB, CheR, CheY, Tar, Tsr) found in code; UniProt lookup requires Pass 4 |
| `iri: null` everywhere | Pass 4 not executed — no IRIs asserted, none fabricated |
| `mapping_confidence` omitted | Belongs to Pass 4 output; omitting is more honest than setting to `none` (which means tried-and-failed) |
| Entry point typo preserved | README.md:49-50 says `chemoreptor_cluster.py`; SKILL.md requires verbatim transcription |
| `python_version: null` | No `python_requires` in setup.py; version requirement inferred but not determinable |

---

## Known limitations

| Item | Detail |
|---|---|
| Pass 3 deferred | `io:` block is empty; parameters, initial conditions, and outputs not documented |
| Pass 4 deferred | All ontology IRIs are null; MAMO, GO, NCBITaxon, CL, SWO mappings require ols-ontology MCP |
| proteins_genes empty | CheA/CheB/CheR/CheY/Tar/Tsr accessions not looked up |
| Python version unknown | `python_requires` absent from setup.py; vivarium-core==0.0.34 may require Python <3.10 |
| vivarium-cell deferred | Metabolism (iAF1260b), transcription/translation, and division processes not annotated |
| validator is a library | `src/validator.py` has no `__main__`; must be called via `Validator().validate()`, not as a CLI script |
