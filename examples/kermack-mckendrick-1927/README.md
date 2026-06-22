# kermack-mckendrick-1927 — Annotation Package

**Model:** Kermack-McKendrick SIR Epidemic Model  
**Artifact type:** Published paper (no local software repository)  
**Citation:** Kermack, W.O. & McKendrick, A.G. (1927). *A Contribution to the Mathematical Theory of Epidemics.* Proc. Roy. Soc. London A, 115(772):700–721. DOI: 10.1098/rspa.1927.0118  
**Canonical SBML encoding:** BioModels [BIOMD0000000018](https://www.ebi.ac.uk/biomodels/BIOMD0000000018) (SBML L2V4)  
**Model class:** ordinary differential equation model  
**Formalism:** ordinary differential equation model (pure ODE paradigm)  
**Organism:** N/A — model is pathogen/host-agnostic  
**SKILL.md passes completed:** 0, 1, 2 (Passes 3, 4 deferred)  
**Annotation date:** 2026-06-22 (Phase 10 rerun)  
**Validation:** EXIT 0 (2026-06-22T15:47:14Z)

---

## Package contents

```
kermack-mckendrick-1927/
  metadata.yaml          — Section A extract + flat mism_registry fields
  execution.yaml         — Section B extract; io: {} empty (Pass 3 deferred)
  README.md              — this file
  outputs/
    annotation.yaml      — master annotation artifact (Passes 0–2)
    validation_report.txt   — real validator output, EXIT 0
  references/
    source_links.md      — paper section/equation citations; ontology status table
```

---

## SKILL.md pass status

| Pass | Description | Status |
|---|---|---|
| Pass 0 | Inventory — artifact type identification | Complete |
| Pass 1 | Model identity & biology (Section A) | Complete |
| Pass 2 | Execution environment (Section B) | Complete |
| Validation checkpoint | `src/validator.py` (programmatic — MCP not connected) | Complete — EXIT 0 |
| Pass 3 | Inputs and outputs (Section C) | Deferred — per user instruction |
| Pass 4 | Ontology mapping via ols-ontology MCP | Deferred — MCP not connected |

---

## What this annotation covers

- Model name, description, license, publication DOI
- Model class (`ordinary differential equation model`) and formalism (same; pure-paradigm ODE) — each list entry carries distinct source evidence per SKILL.md requirement
- Epidemic threshold theorem: S₀ > l/κ (R₀ = κS₀/l > 1); governing ODEs: dS/dt = −κSI, dI/dt = κSI − lI, dR/dt = lI
- Biological processes: transmission of infectious disease, recovery from disease
- Authorship (Kermack & McKendrick; corrected: "Royal College of Physicians' Laboratory, Edinburgh")
- License: corrected to `LicenseRef-PublicDomain-US` — US public domain confirmed (pre-1928); UK copyright NOT fully expired (Kermack d.1970 → UK expiry 2040)
- Registry fields: `execution_type: other`; `source_repository` pointing to BioModels BIOMD0000000018

## What is deferred

- `io:` block (Section C) — Pass 3 not executed
- All ontology IRIs — Pass 4 (ols-ontology MCP) not connected
- `biology.species` — intentionally empty; model is organism-agnostic (not a mapping failure)

---

## Structural validation results

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
| Registry constructable | true (`ExecutionType.other` accepted by mism\_registry) |
| io\_slots\_constructed | 0 (W1 — expected; `io: {}` empty stub) |
| **Overall** | **PASS, EXIT 0** |

### Reproducing the validation

```python
import sys, json
from pathlib import Path
sys.path.insert(0, 'src')
from validator import Validator

ann  = Path('examples/kermack-mckendrick-1927/outputs/annotation.yaml').read_text(encoding='utf-8')
meta = Path('examples/kermack-mckendrick-1927/metadata.yaml').read_text(encoding='utf-8')
exe  = Path('examples/kermack-mckendrick-1927/execution.yaml').read_text(encoding='utf-8')

v = Validator(input_path=Path('examples/kermack-mckendrick-1927/outputs'),
              model_id='kermack-mckendrick/sir-1927')
report = v.validate(ann, meta, exe)
print(json.dumps(report, indent=2))
sys.exit(report['exit_code'])
```

---

## Completing deferred passes

**Pass 3 (I/O):** Download BioModels BIOMD0000000018 SBML file. Read the `<listOfParameters>` block for k (κ), l, and initial species values (S₀, I₀, R₀). Populate `io.inputs.parameters` (k, l, S₀, I₀) and `io.outputs` (S(t), I(t), R(t) timeseries).

**Pass 4 (Ontology mapping):** Connect `ols-ontology` MCP. For each field in `provenance.partial_annotation_scope.deferred`, run `ols-ontology:searchClasses` per the routing table in `references/ontologies.md`. Key targets: `model.model_class[0]` → MAMO, `model.biology.health_condition[0]` → MONDO, `model.biology.biological_processes` → GO.

---

## Key annotation decisions

**model_class vs formalism:** Both are `ordinary differential equation model` — this is a pure-paradigm ODE model where the modeling approach and the mathematical machinery coincide. Each list entry carries distinct source evidence: `model_class` cites the compartmental S/I/R structure (pp. 700–702); `formalism` cites the explicit dS/dt, dI/dt, dR/dt equations (1)–(3).

**biology.species: `[]`:** The SIR model names no host organism or specific pathogen — it is explicitly a generic framework. This deviates from the Pass 1 completeness checklist item (≥1 species entry). The deviation is documented in `provenance.partial_annotation_scope.deferred` and is not a mapping failure.

**execution.language.name: `SBML`:** The original paper contains no software. The canonical computable artifact is the BioModels SBML encoding (BIOMD0000000018). `SBML` is used as the language identifier to reflect this; `environment_kind: native` indicates any SBML-compatible ODE solver (COPASI, tellurium, MATLAB SimBiology) can execute it.

**execution.status: `partially_characterized`:** Equations are fully specified in the paper, but no build system, language runtime, or entry-point command exists in the original artifact. Status reflects that execution requires a third-party simulator not prescribed by the paper.

---

## Phase 10 corrections vs Phase 8

| Item | Phase 8 | Phase 10 |
|---|---|---|
| `license.spdx_id` | `LicenseRef-PublicDomain` | `LicenseRef-PublicDomain-US` |
| `license.source` | Claimed UK life+70 expired for both authors | Corrected: Kermack d.1970 → UK expiry 2040; only US law (pre-1928) confirmed |
| `authors[*].affiliation` | "Royal College of Physicians of Edinburgh" | "Royal College of Physicians' Laboratory, Edinburgh" |
| Validation timestamp | 2026-06-19T13:17:29Z | 2026-06-22T15:47:14Z |
| Annotation decisions | — | unchanged |
