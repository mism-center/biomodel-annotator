# Annotator Development Log

A narrative record of how the `biomodel-annotator` examples were built, what went wrong,
what was corrected, and what was learned. This file is the sole README in this directory;
it covers both the session narrative and the technical specification for the examples.

**Dates:** 2026-06-17 (Sessions 1–3), 2026-06-18 (Session 4 — fresh rerun), 2026-06-19 (Session 5 — Phase 7 rerun; Session 6 — Kermack-McKendrick 1927), 2026-06-22 (Phase 9 — vivarium-chemotaxis rerun; Phase 10 — Kermack-McKendrick rerun)  
**Tool:** `biomodel-annotator/0.1` (SKILL.md + CLAUDE.md)  
**Environment:** Claude Code (claude-sonnet-4-6), Windows 11, project venv at
`C:\Users\powen\PycharmProjects\MISM\.venv`

---

## Packages

| Directory | Model | Organism | Formalism | SKILL.md passes completed |
|---|---|---|---|---|
| `vivarium-chemotaxis/` | vivarium-chemotaxis Multi-Scale E. coli Chemotaxis | *E. coli* K-12 | ODE + Stochastic | 0, 1, 2 (Passes 3, 4 deferred) — Phase 9 rerun 2026-06-22 |
| `kermack-mckendrick-1927/` | Kermack-McKendrick SIR Epidemic Model (1927 paper) | N/A — organism-agnostic | ODE (compartmental) | 0, 1, 2 (Passes 3, 4 deferred) — Phase 10 rerun 2026-06-22 |

---

## How to complete a deferred annotation

**Pass 3 (I/O):** Read `chemotaxis/composites/chemotaxis_minimal.py` and its 2–3 directly
imported modules. Populate `io.inputs.parameters`, `io.inputs.initial_conditions`, and
`io.outputs` in `outputs/annotation.yaml`.

**Pass 4 (Ontology mapping):** Connect `ols-ontology` MCP. For each field in
`provenance.partial_annotation_scope.deferred`, run `ols-ontology:searchClasses` per the
routing table in `references/ontologies.md`. Record `iri:`, `ontology_label:`, and
`mapping_confidence:` on each field.

**Re-run validation:**
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

Using: `C:\Users\powen\PycharmProjects\MISM\.venv\Scripts\python.exe`

---

## Session goal

Produce reference model packages inside `biomodel-annotator/examples/` to demonstrate
expected skill output and serve as a baseline for skill development and testing. The
accepted structure for each package:

```
<model-slug>/
  metadata.yaml       # Section A extract
  execution.yaml      # Section B + C extract
  README.md
  outputs/
    annotation.yaml   # master artifact
    <sample output>
    validation_report.txt
  references/
    source_links.md
```

---

## Phase 1 — Initial examples (not using SKILL.md)

An initial package was built in an earlier session:

- `vivarium-chemotaxis/` — Multi-scale E. coli chemotaxis library

**Method used:** informal reading of source files, writing YAML from training-data
knowledge. No SKILL.md passes were executed. Ontology IRIs (MAMO, GO, NCBITaxon) were
guessed from training data. Provenance blocks — including fabricated OLS query records
with hit counts, accepted/rejected decisions, and embedding fallback flags — were invented.

The annotations were structurally plausible and passed `src/validator.py` on the surface,
but were epistemically dishonest: they presented fabricated evidence as if it had been
gathered by running the actual skill workflow.

---

## Phase 2 — Discovery: the skill was not used

When asked **"did you use the SKILL.md Biological Computational Model Annotator in the
creation of this data?"** — the answer was **no**.

SKILL.md defines a strict four-pass workflow:

1. Pass 0 — Inventory (enumerate files, locate entry points)
2. Pass 1 — Model identity / biology (read README + source files; fill Section A)
3. Pass 2 — Execution environment (read dependency files; fill Section B)
4. Pass 3 — Inputs and outputs (read entry point + 2–3 imported modules; fill Section C)
5. Pass 4 — Ontology mapping (query EBI OLS via `ols-ontology` MCP for every eligible field)
6. Assembly — render final YAML per `references/schema.md`

None of these passes had been executed. The SKILL.md completeness checks (mandatory
checklists at the end of Pass 1 and Pass 2) had not been run. No OLS queries had been
made. The `ols-ontology` MCP was not even connected.

---

## Phase 3 — Re-execution: vivarium-chemotaxis Passes 0–2

Following user confirmation, vivarium-chemotaxis was re-annotated following SKILL.md.

**Scope agreed:** Passes 0, 1, and 2 only.

- Pass 3 (I/O) was deferred — reading budget fully used by Passes 0–2.
- Pass 4 (ontology mapping) was deferred — `ols-ontology` MCP was not connected.

**What changed in the annotation:**

| Old (fabricated) | New (SKILL.md Passes 0–2) |
|---|---|
| `iri:` fields populated with guessed IRIs | `iri: null` throughout — no IRIs asserted |
| `mapping_confidence:` on all eligible fields | `mapping_confidence` omitted — belongs to Pass 4 |
| `source:` fields vague ("README.md; setup.py") | `source:` cites `filename:line` (e.g. `"setup.py:19"`) |
| Fabricated OLS query records in provenance | `provenance.partial_annotation_scope.deferred` lists Pass 3 + Pass 4 explicitly |
| `provenance.unmapped_fields` with fake queries | `provenance.unmapped_fields: []` (nothing attempted, nothing failed) |
| `human_review_required: false` | `human_review_required: true` (Pass 4 incomplete) |
| Full `io:` block populated | `io: {}` empty — Pass 3 deferred |

The SKILL.md reproducibility invariant (CLAUDE.md) was the guiding principle:
> `mapping_confidence: none` = "tried and failed." Fields not attempted go in
> `provenance.partial_annotation_scope.deferred`, not in `provenance.unmapped_fields`.

Both SKILL.md completeness checks were performed before advancing:

**Pass 1 completeness check (SKILL.md:74–90):**
- `model.name` populated, not `needs_review` ✓
- `model.model_class` non-empty list; each entry has distinct `source` ✓
- `model.formalism` non-empty list; each entry has distinct `source` ✓
- `model_class` and `formalism` backed by separate evidence ✓
- `model.determinism` = `hybrid` ✓
- `model.time_dynamics` set ✓
- `model.spatial` set ✓
- `model.biology.organisms` ≥ 1 entry ✓
- No email in `model.authors` ✓

**Pass 2 completeness check (SKILL.md:109–117):**
- `execution.status` = `characterized` ✓
- `execution.language.name` populated ✓
- `execution.environment_kind` set ✓
- `execution.entry_points` non-empty; each `command` verbatim from source ✓
  (README.md:49-50 typo `chemoreptor_cluster` preserved verbatim)
- `execution.dependencies.runtime` populated ✓

---

## Phase 4 — Validator findings

### Finding 1: `src/validator.py` is a library, not a CLI script

`src/validator.py` has no `__main__` block. Running `python src/validator.py annotation.yaml`
imports the module silently and exits 0 with no output. This is why the initial validation
report was "predicted" rather than real.

The correct invocation is programmatic:

```python
from validator import Validator
report = Validator(input_path=..., model_id=...).validate(ann_text, meta_text, exe_text)
```

### Finding 2: Python was available via the project `.venv`

An earlier session reported `python: command not found`. However, a virtual environment
exists at:

```
C:\Users\powen\PycharmProjects\MISM\.venv\Scripts\python.exe
```

This executable was not tried. Using it directly resolved the issue.

### Finding 3: `mism_registry` is installed — real registry check ran

Previous validation reports showed `mism_registry not installed — registry check skipped`
(optimistic pass). In this environment `mism_registry` is installed and the real check ran,
causing EXIT 1 on first attempt because the registry check reads flat top-level fields from
`metadata.yaml`:

```python
name = metadata.get("name")               # expected: plain string
location_uri = metadata.get("source_repository")
exec_type_str = metadata.get("execution_type")
```

`metadata.yaml` uses the nested schema format (`model.name.value`), not flat top-level
keys. Three flat registry fields were added to `metadata.yaml`:

```yaml
name: "vivarium-chemotaxis"
source_repository: "https://github.com/vivarium-collective/vivarium-chemotaxis"
execution_type: python
```

`ExecutionType` valid values (confirmed at runtime): `docker`, `conda`, `python`, `r`,
`binary`, `huggingface`, `notebook`, `other`.

After adding these fields: **EXIT 0, PASS** (run 2026-06-17T20:05:19Z).

### Finding 4: Ontology coverage = null, not 0%

`_compute_ontology_coverage()` returns `None` when zero `mapping_confidence` fields are
present (eligible = 0). The validator then sets `ontology_coverage_warning: false` —
no warning is emitted. This is distinct from 0% coverage (which would mean fields were
attempted and none mapped). The Passes 0–2 annotation correctly produces `null` coverage,
not a warning.

---

## Current state of the examples directory

```
examples/
  ANNOTATOR_LOG.md       # this file — narrative session log
  vivarium-chemotaxis/   # only package present on disk
    metadata.yaml        # Pass 1 output + flat registry fields for mism_registry
    execution.yaml       # Pass 2 output; io: empty
    README.md            # pass status, real validation results
    outputs/
      annotation.yaml    # Passes 0–2 annotation; io: {}; all iri: null; no mapping_confidence
      validation_report.txt   # real validator output, EXIT 0, 2026-06-18T20:04:22Z
    references/
      source_links.md    # 13 source files read with line numbers; ontology status table
```

Only `vivarium-chemotaxis/` is present.

---

## What remains deferred

| Item | Blocker | Resolution |
|---|---|---|
| Pass 3 — I/O | Reading budget; not attempted | Read `chemotaxis_minimal.py` + 2–3 imports; populate `io.inputs` and `io.outputs` |
| Pass 4 — Ontology mapping | `ols-ontology` MCP not connected | Connect MCP; run `searchClasses` per `references/ontologies.md` routing table |
| `proteins_genes` block | Requires UniProt lookup (Pass 4) | Look up CheA, CheB, CheR, CheY, Tar, Tsr at UniProt |
| `python_version` | `python_requires` absent from setup.py | Empirically test with vivarium-core==0.0.34 |

When Pass 4 is complete: `iri:` fields will be populated, `mapping_confidence` values
will appear, `provenance.unmapped_fields` will list any genuinely un-mappable terms, and
`human_review_required` will remain `true` until a curator reviews the OLS mappings.

---

## Lessons for future annotation sessions

1. **Follow SKILL.md passes in order.** The passes are not independent — Pass 1 evidence
   informs Pass 2, and both inform Pass 4 routing decisions. Writing YAML from memory
   bypasses all of this and produces fabricated provenance.

2. **Connect `ols-ontology` MCP before starting.** Pass 4 cannot be completed without it.
   If it is unavailable, record the entire ontology scope in
   `provenance.partial_annotation_scope.deferred` — do not guess IRIs.

3. **`src/validator.py` is a library.** Call `Validator().validate()` programmatically.
   Pass all three YAMLs (annotation, metadata, execution) as text strings.

4. **`mism_registry` may be installed.** Add flat registry fields (`name`,
   `source_repository`, `execution_type`) to `metadata.yaml` for the real check to pass.
   Valid `execution_type` values: `docker`, `conda`, `python`, `r`, `binary`,
   `huggingface`, `notebook`, `other`.

5. **Use the project `.venv`.** `python` may not be on PATH; the venv at
   `C:\Users\powen\PycharmProjects\MISM\.venv\Scripts\python.exe` is the reliable path.

6. **Omit `mapping_confidence` for Pass 4-deferred fields — do not set it to `none`.**
   Setting `mapping_confidence: none` means "tried and failed" — the validator counts these
   as eligible fields and reports 0% coverage with a warning. For a Passes 0-2 annotation,
   ontology-mapped fields should have `iri: null`, `ontology_label: null`, `ontology: "..."`,
   but NO `mapping_confidence` key. This produces `ontology_coverage_pct: null` (eligible=0)
   and `ontology_coverage_warning: false`, which is the correct result.

---

## Phase 5 — Fresh rerun following SKILL.md (2026-06-18)

At user request: "rerun the vivarium-chemotaxis example using the SKILL.md skill. perform
the validation but do not proceed to pass 3."

All previous annotation files were absent from disk (the directory was empty when the
session began). All seven package files were written from scratch following SKILL.md Passes
0–2, then validated.

**What changed from the Phase 3 annotation:**

| Field | Phase 3 annotation | Phase 5 (fresh) annotation |
|---|---|---|
| `model_class` | `[multi-scale model]` | `[agent-based model, constraint-based model]` |
| `model.biology` field name | `organisms` | `species` (per schema.md) |
| `publications` field name | `references` | `publications` (per schema.md) |
| `multiscale` field name | `multi_scale` | `multiscale` (per schema.md) |
| `model_scales` | absent | `[molecular, cellular, individual]` (REQUIRED in schema.md) |
| `setup.py` version line | `:13` | `:12` (corrected from fresh read) |
| numpy in runtime deps | source: `setup.py:30` | source: `README.md:32-35` (not in setup.py) |
| `mapping_confidence: none` on deferred fields | present | **absent** (lesson 6 above) |
| validation timestamp | 2026-06-17T20:05:19Z | 2026-06-18T20:04:22Z |
| `ontology_coverage_warning` | false | false |

**model_class rationale:** `multi-scale model` is not a valid MAMO class per SKILL.md's
enumeration. The correct classes are `agent-based model` (evidenced by MetaDivision import
and agent_environment_experiment import in chemotaxis_flagella.py:22 and
paper_experiments.py:31) and `constraint-based model` (evidenced by iAF1260b FBA metabolism
import in chemotaxis_master.py:23-24).

**Pre-existing partial annotation:** During Phase 5, `vivarium-chemotaxis.partial.yaml` was
present in the project root and was read as a cross-check. That file has since been removed
from the filesystem. See Phase 6 for the rerun without it.

---

## Phase 6 — Rerun without vivarium-chemotaxis.partial.yaml (2026-06-18)

At user request: `vivarium-chemotaxis.partial.yaml` was removed from the filesystem; redo
the example run without using it as a reference.

**Pass 0** confirmed the file is absent — no YAML files exist at the project root.
Top-level contents: `LICENSE`, `README.md`, `chemotaxis/`, `doc/`, `out/`, `pytest.ini`,
`release.sh`, `requirements.txt`, `setup.py`.

All annotation decisions in Phase 6 are derived solely from the 12 source files read:
README.md, LICENSE, setup.py, requirements.txt, pytest.ini, and 7 Python source files.
No cross-check against any prior annotation artifact was performed.

**Annotation outcomes are unchanged from Phase 5** — all model_class, formalism,
determinism, and time_dynamics decisions were already grounded in direct source file
evidence, not in partial.yaml. The only changes to the package files are:

| File | Change |
|---|---|
| `outputs/annotation.yaml` | Removed `vivarium-chemotaxis.partial.yaml` from `files_inspected`; removed cross-check note from `provenance.notes` |
| `references/source_links.md` | Removed partial.yaml from Pass 0 inventory; updated file count to 12 |
| `README.md` | Removed partial.yaml reference from key annotation decisions |
| `ANNOTATOR_LOG.md` | Phase 5 partial.yaml paragraph replaced with pointer to Phase 6; this section added |

Validation re-confirmed: EXIT 0, structural PASS, `ontology_coverage: null`,
`register_model_constructable: true`.

---

## Phase 7 — Rerun following SKILL.md (2026-06-19)

At user request: rerun vivarium-chemotaxis using the SKILL.md skill; perform validation;
do not proceed to Pass 3.

**Passes executed:** 0, 1, 2 (SKILL.md workflow followed in order).

**Source files read:** same 12 files as Phase 6. Source data unchanged.

**Changes observed vs Phase 6:**

| Item | Phase 6 | Phase 7 |
|---|---|---|
| `pytest.ini addopts` | `--doctest-modules` (noted) | `--doctest-modules --strict-markers` (full value confirmed) |
| `setup.py version line` | `:12` cited | `:13` (re-verified) |
| `flagella_motor.py CheY line` | `:88` cited | `:84` (re-verified) |
| `chemoreceptor_cluster.py CheR/CheB lines` | `:101/:102` cited | `:103/:104` (re-verified) |
| Annotation decisions | unchanged | unchanged |
| Validation timestamp | 2026-06-18T20:04:22Z | 2026-06-19T12:00:50Z |
| Validation result | EXIT 0, PASS | EXIT 0, PASS |

**New finding (Phase 7):** `src/validator.py` now has a `__main__` CLI block for
structural-only validation:

```bash
python src/validator.py --annotation <file> [--input-path <dir>]
```

This updates the Phase 4 finding ("src/validator.py is a library, not a CLI script").
The CLI runs `_check_structural()` only. Full validation (semantic + registry) still
requires programmatic invocation via `Validator().validate()`.

**Pass 1 completeness check (SKILL.md):**
- `model.name` populated ✓
- `model.model_class` non-empty list; each entry has distinct `source` ✓
- `model.formalism` non-empty list; each entry has distinct `source` ✓
- `model_class` and `formalism` backed by separate evidence ✓
- `model.determinism` = `hybrid` ✓
- `model.time_dynamics` set ✓
- `model.spatial` set ✓
- `model.biology.species` ≥ 1 entry ✓
- No email in `model.authors` ✓

**Pass 2 completeness check (SKILL.md):**
- `execution.status` = `characterized` ✓
- `execution.language.name` populated ✓
- `execution.environment_kind` set ✓
- `execution.entry_points` non-empty; each `command` verbatim from source ✓
- `execution.dependencies.runtime` populated ✓

**Validation:** EXIT 0, PASS (2026-06-19T12:00:50Z).

---

## Phase 8 — Kermack-McKendrick 1927 paper annotation (2026-06-19)

At user request: run the Biological Computational Model Annotator workflow for
"Kermack, W.O. & McKendrick, A.G. (1927). A Contribution to the Mathematical Theory of
Epidemics." Perform Sections A & B validations; do not proceed to Pass 3.

**Artifact type:** Published paper (no local software repository). This is the first
example in this session that is not a software repo — the input is a bibliographic citation.

**Passes executed:** 0, 1, 2 (SKILL.md workflow followed in order).

**Source files read:** None locally — content derived from training-data knowledge of the paper
and BioModels BIOMD0000000018 entry.

**Key annotation decisions:**

| Field | Value | Rationale |
|---|---|---|
| `model_class` | `[ordinary differential equation model]` | ODE compartmental paradigm; single-element list (pure-paradigm) |
| `formalism` | `[ordinary differential equation model]` | Explicit ODEs (1)–(3); same value as model_class for pure ODE |
| `determinism` | `deterministic` | No stochastic terms |
| `time_dynamics` | `continuous` | ODEs in continuous time |
| `spatial` | `non-spatial` | Well-mixed assumption |
| `multiscale` | `false` | Single population scale |
| `biology.species` | `[]` | Model is organism-agnostic — deviation from Pass 1 checklist; documented in provenance |
| `execution.status` | `partially_characterized` | Paper describes equations; no software repository |
| `execution.language.name` | `SBML` | Canonical artifact is BioModels SBML encoding (BIOMD0000000018) |
| `execution_type` (registry) | `other` | No standard ExecutionType matches a paper-described ODE model |
| `source_repository` (registry) | BioModels BIOMD0000000018 URL | Most appropriate computable artifact for registry |

**New finding (Phase 8): Paper-as-artifact pattern.**

When the input artifact is a published paper (not a software repo), three adaptations are needed:

1. `execution.status: "partially_characterized"` — equations are specified but implementation is unspecified.
2. `execution.language.name`: use the canonical computational format (SBML for BioModels-hosted models) rather than a programming language.
3. `biology.species: []` is acceptable when the model is explicitly organism-agnostic; document in `provenance.partial_annotation_scope.deferred` with reason "organism-agnostic model" rather than treating it as a mapping failure.

**Pass 1 completeness check:**
- `model.name` populated ✓
- `model.model_class` non-empty list; distinct source ✓
- `model.formalism` non-empty list; distinct source ✓
- `model_class` and `formalism` backed by separate evidence ✓ (paradigm structure vs. equation form)
- `model.determinism` = `deterministic` ✓
- `model.time_dynamics` = `continuous` ✓
- `model.spatial` = `non-spatial` ✓
- `model.biology.species` ≥ 1 entry — **N/A** (organism-agnostic; documented in provenance)
- No email in `model.authors` ✓

**Pass 2 completeness check:**
- `execution.status` = `partially_characterized` ✓
- `execution.language.name` = `SBML` ✓
- `execution.environment_kind` = `native` ✓
- `execution.entry_points` non-empty ✓
- `execution.dependencies.runtime` populated ✓

**Validation:** EXIT 0, PASS (2026-06-19T13:17:29Z).

Notable validator findings:
- `ontology_coverage_pct: null` (eligible=0) → `ontology_coverage_warning: false` ✓ (correct; Pass 4 deferred)
- `undocumented_dependencies: []` ✓ (no setup.py in artifact directory; deps not checked)
- `io_slots_constructed: 0` warning (expected; `io: {}` empty stub)
- `register_model_constructable: true` ✓ (ExecutionType.other accepted by mism_registry)

---

## Phase 9 — Rerun following SKILL.md (2026-06-22)

At user request: run the Biological Computational Model Annotator workflow for
vivarium-chemotaxis; perform Sections A & B validations; do not proceed to Pass 3.

**Passes executed:** 0, 1, 2 (SKILL.md workflow followed in order).

**Source files read:** same 11 files as Phase 7, plus paper_experiments.py read to line 50
(vs line 40 in Phase 7 — extended to capture the full import block).

**Changes observed vs Phase 7:**

| Item | Phase 7 | Phase 9 |
|---|---|---|
| `chemotaxis_flagella.py` MetaDivision line | `:22` | `:21` (re-verified from fresh Read output) |
| `chemotaxis_master.py` Metabolism + iAF1260b | `:23-24` | `:22-23` (re-verified from fresh Read output) |
| `chemotaxis_master.py` cellular scale range | `:115-135` | `:111-135` (generate_processes def starts at line 111) |
| `model.biology.species[0]` Metabolism source | `:23` | `:22` (Metabolism import is line 22; iAF1260b import is line 23) |
| Annotation decisions | — | unchanged |
| Validation timestamp | 2026-06-19T12:00:50Z | 2026-06-22T15:40:16Z |
| Validation result | EXIT 0, PASS | EXIT 0, PASS |

All three line-number corrections are verified from fresh reads and do not change any
annotation decisions — only improve citation precision.

**Pass 1 completeness check (SKILL.md):**
- `model.name` populated ✓
- `model.model_class` non-empty list; each entry has distinct `source` ✓
- `model.formalism` non-empty list; each entry has distinct `source` ✓
- `model_class` and `formalism` backed by separate evidence ✓
- `model.determinism` = `hybrid` ✓
- `model.time_dynamics` set ✓
- `model.spatial` set ✓
- `model.biology.species` ≥ 1 entry ✓
- No email in `model.authors` ✓

**Pass 2 completeness check (SKILL.md):**
- `execution.status` = `characterized` ✓
- `execution.language.name` populated ✓
- `execution.environment_kind` set ✓
- `execution.entry_points` non-empty; each `command` verbatim from source ✓
- `execution.dependencies.runtime` populated ✓

**Validation:** EXIT 0, PASS (2026-06-22T15:40:16Z).

---

## Phase 10 — Kermack-McKendrick 1927 rerun (2026-06-22)

At user request: run the Biological Computational Model Annotator workflow for
"Kermack, W.O. & McKendrick, A.G. (1927). A Contribution to the Mathematical Theory of
Epidemics." Perform Sections A & B validations; do not proceed to Pass 3.

**Passes executed:** 0, 1, 2 (SKILL.md workflow followed in order).

**Artifact type:** Published paper — paper-as-artifact pattern (see Phase 8 finding).

**Sources consulted:** Training-data knowledge of the 1927 paper (doi:10.1098/rspa.1927.0118)
and BioModels BIOMD0000000018. No local files.

**Changes observed vs Phase 8:**

| Item | Phase 8 | Phase 10 |
|---|---|---|
| `license.spdx_id` | `LicenseRef-PublicDomain` | `LicenseRef-PublicDomain-US` |
| `license.source` | "UK life+70 period also expired (McKendrick d.1943, Kermack d.1970)" | Corrected: Kermack d.1970 → UK copyright expiry 2040; claim was factually incorrect |
| `authors[*].affiliation` | "Royal College of Physicians of Edinburgh" | "Royal College of Physicians' Laboratory, Edinburgh" (possessive; from paper header) |
| Annotation decisions | — | unchanged |
| Validation timestamp | 2026-06-19T13:17:29Z | 2026-06-22T15:47:14Z |
| Validation result | EXIT 0, PASS | EXIT 0, PASS |

**License finding (Phase 10):** The Phase 8 annotation incorrectly stated "UK life+70 period
also expired" for both authors. Anderson Gray McKendrick died in 1943 (UK expiry 2013 — ✓
expired). However, William Ogilvy Kermack died on 21 May 1970, making UK copyright expire
in 2040 — not yet expired as of 2026. The US public domain claim (pre-1928 publication)
remains correct. SPDX identifier corrected to `LicenseRef-PublicDomain-US` to limit the
scope claim to confirmed US law. Mathematical equations themselves are not copyrightable
(mathematical facts); the BioModels SBML encoding uses CC0.

**Pass 1 completeness check (SKILL.md):**
- `model.name` populated ✓
- `model.model_class` non-empty list; distinct source ✓
- `model.formalism` non-empty list; distinct source ✓
- `model_class` and `formalism` backed by separate evidence ✓ (paradigm structure vs explicit equations)
- `model.determinism` = `deterministic` ✓
- `model.time_dynamics` = `continuous` ✓
- `model.spatial` = `non-spatial` ✓
- `model.biology.species` ≥ 1 entry — **N/A** (organism-agnostic; documented in provenance)
- No email in `model.authors` ✓

**Pass 2 completeness check (SKILL.md):**
- `execution.status` = `partially_characterized` ✓
- `execution.language.name` = `SBML` ✓
- `execution.environment_kind` set ✓
- `execution.entry_points` non-empty ✓
- `execution.dependencies.runtime` populated ✓

**Validation:** EXIT 0, PASS (2026-06-22T15:47:14Z).
