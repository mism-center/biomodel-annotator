# vivarium-chemotaxis — Annotation Package

**Model:** vivarium-chemotaxis — Multi-Scale E. coli Chemotaxis  
**Organism:** *Escherichia coli* K-12 MG1655  
**Model class:** agent-based model; constraint-based model  
**Formalism:** ODE (receptor cluster); stochastic (flagella motor)  
**SKILL.md passes completed:** 0, 1, 2 (Passes 3, 4 deferred)  
**Annotation date:** 2026-06-18  
**Validation:** EXIT 0 (2026-06-18T20:04:22Z)

---

## Package Contents

```
vivarium-chemotaxis/
  metadata.yaml          — Section A extract + flat mism_registry fields
  execution.yaml         — Section B extract; io: {} empty (Pass 3 deferred)
  README.md              — this file
  outputs/
    annotation.yaml      — master annotation artifact (Passes 0–2)
    sample_timeseries.json  — representative MeAsp stimulus-response timeseries
    validation_report.txt   — real validator output, EXIT 0
  references/
    source_links.md      — files read with line numbers; ontology status table
```

---

## SKILL.md Pass Status

| Pass | Description | Status |
|---|---|---|
| Pass 0 | Inventory — top-level file scan | Complete |
| Pass 1 | Model identity & biology (Section A) | Complete |
| Pass 2 | Execution environment (Section B) | Complete |
| Validation checkpoint | `src/validator.py` (programmatic — MCP not connected) | Complete — EXIT 0 |
| Pass 3 | Inputs and outputs (Section C) | Deferred — not executed |
| Pass 4 | Ontology mapping via ols-ontology MCP | Deferred — MCP not connected |

---

## What this annotation covers

- Model name, version, description, license
- Model class (agent-based + constraint-based) and formalism (ODE + stochastic) with distinct source evidence per entry
- E. coli K-12 MG1655 organism, biological processes (chemotaxis, signal transduction), key proteins (Tsr, Tar, CheY, CheA, CheB, CheR)
- All runtime dependencies and entry points (including the verbatim README typo at line 51)
- Authorship and contacts

## What is deferred

- `io:` block (Section C) — Pass 3 not executed
- All ontology IRIs — Pass 4 (ols-ontology MCP) not connected
- UniProt identifiers for proteins\_genes entries

---

## Structural Validation Results

Validated programmatically using `src/validator.py` with the project `.venv`:

```
C:\Users\powen\PycharmProjects\MISM\.venv\Scripts\python.exe
```

| Check | Result |
|---|---|
| Structural validation | PASS — 0 missing, 0 empty required fields |
| needs\_review warnings | 0 (threshold: >5) |
| Ontology coverage | null (eligible=0 — Pass 4 deferred; no `mapping_confidence` fields present) |
| Ontology coverage warning | false |
| Registry constructable | true |
| io\_slots\_constructed | 0 (W1 — expected; Pass 3 deferred) |
| **Overall** | **PASS, EXIT 0** |

### Reproducing the validation

```python
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

---

## Completing deferred passes

**Pass 3 (I/O):** Read `chemotaxis/composites/chemotaxis_minimal.py` and its 2–3 directly
imported modules. Populate `io.inputs.parameters`, `io.inputs.initial_conditions`, and
`io.outputs` in `outputs/annotation.yaml`.

**Pass 4 (Ontology mapping):** Connect `ols-ontology` MCP. For each field in
`provenance.partial_annotation_scope.deferred`, run `ols-ontology:searchClasses` per the
routing table in `references/ontologies.md`. Record `iri:`, `ontology_label:`, and
`mapping_confidence:` on each field.

---

## Key annotation decisions

**model_class:** Two entries — `agent-based model` (evidenced by MetaDivision import in
chemotaxis_flagella.py:22 and agent\_environment\_experiment import in paper_experiments.py:31)
and `constraint-based model` (FBA via iAF1260b in chemotaxis_master.py:23-24). Each entry
has a distinct source file per SKILL.md requirements.

**determinism:** `hybrid` (inferred) — receptor cluster uses deterministic Euler ODE
(chemoreceptor_cluster.py:30-44); flagella motor uses stochastic switching
(flagella_motor.py:43-46, Sneddon 2012).

**time\_dynamics:** `discrete` (inferred) — all processes use fixed-timestep updates
(`time_step: 0.01` in flagella\_motor.py:49; Euler steps in chemoreceptor\_cluster.py:30).

**numpy dependency:** Runtime requirement (imported throughout), but absent from
`setup.py install_requires`. Source is README.md:32-35 only.

**Entry point typo:** README.md:51 reads `chemoreptor_cluster.py` (one 'e' missing).
The command is preserved verbatim in `entry_points[0].command`.
