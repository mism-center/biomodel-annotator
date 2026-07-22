---
name: biomodel-annotator
description: Annotate a biological/biomedical computational model (git repo, folder, or single model file) into a structured, MIRIAM-aligned YAML covering (1) what the model is — type, biology, authors, references; (2) how to execute it — language, dependencies, environment, compute; (3) inputs and outputs — parameters, formats, units. Each term gets an ontology IRI (MAMO, KISAO, GO, ChEBI, UO, NCBITaxon, CL, UBERON, SWO, SBO, EDAM) via the EBI OLS MCP. Use whenever a user asks to annotate, describe, catalog, document, characterize, or do a first pass on a biological model, simulation, or modeling repository — including SBML, CellML, SED-ML, NeuroML, COMBINE archives, BNGL, agent-based models, ODE/PDE systems, multi-scale frameworks (Vivarium, BioNetGen, MCell), and Python/Julia/R simulation code. Trigger even when the user does not literally use the word annotate — phrases like "what does this model do", "extract metadata from this repo", "make this model FAIR", or "help me describe this simulation" all qualify.
---

# Biological Computational Model Annotator

A first-pass annotation skill: point it at a model (repo, folder, or URL) and it produces a MIRIAM-aligned **annotation package** (a `metadata-package/` folder of YAML + a README) with ontology mappings already attached. The output is meant to be a starting point for a human curator — every field carries a `confidence` and `source` so the reviewer can see what was found verbatim versus inferred.

## What the skill produces

An **annotation package** — a folder named `metadata-package/`, written **inside the model's own directory** (the repo/folder being annotated) — containing three files:

1. **`metadata.yaml`** — `model` (Section A: identity, biology, authorship, references, licensing) plus the identity/ontology half of `provenance` (files inspected, ontology lookups, unmapped fields, deferred scope).
2. **`execution.yaml`** — `execution` (Section B: language, dependencies, environment, resources, entry points) and `io` (Section C: inputs/outputs with units and formats), plus the `validation` half of `provenance`.
3. **`README.md`** — a human-readable model-card summary of the package (not validated).

`provenance` is split across the two YAML files; a small run-stamp (date, source path, files inspected) is repeated in both so each file stands alone. The full field-by-field schema and the exact split live in `references/schema.md`. Read it before writing the package.

## When to use this skill

Trigger the workflow whenever the user references a model artifact and wants a structured description of it. Examples that should fire this skill:

- "Annotate the model at `<path or URL>`."
- "What does this repo do? Give me a summary I can put in a catalog."
- "Extract metadata from this simulation so we can index it."
- "Help me write a model card for this."
- "Do a first pass on this model — we'll review later."

If the user just wants a casual one-paragraph explanation of a model, answer directly — don't invoke the full annotation workflow.

## Inputs the skill accepts

- A **local folder path** (most common; explore with Filesystem MCP if available, otherwise bash).
- A **GitHub URL** (clone or fetch the README/key files).
- A **single model file** (e.g. one SBML or BNGL file) — in this case `execution` and `io` will be sparser.

If the user gives you nothing, ask once for one of these.

---

## Workflow

The workflow is four passes plus assembly. **Do not start writing the package until you finish all four passes** — earlier passes inform later ones (e.g. knowing the model is a stochastic ABM changes how you describe inputs).

**Extraction discipline (Passes 0–3).** These passes are extraction tasks, not creative generation. Copy values verbatim from source files wherever possible — do not paraphrase or rephrase. Prefer `confidence: high` over `confidence: inferred` whenever the source text is explicit. Only use `confidence: inferred` when you are reading between the lines of the source.

### Pass 0 — Inventory

Before reading anything in depth, get the lay of the land:

1. List the top-level files and directories. Note presence of any of: `README*`, `LICENSE*`, `CITATION*`, `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements*.txt`, `environment.yml`, `Pipfile`, `poetry.lock`, `Dockerfile`, `docker-compose.yml`, `Makefile`, `.python-version`, `package.json`, `Project.toml`, `Manifest.toml`, `DESCRIPTION`, `renv.lock`, `Snakefile`, `nextflow.config`, `CWL` files, `manifest.xml` (COMBINE), `*.sbml`, `*.xml`, `*.cellml`, `*.sedml`, `*.omex`, `*.bngl`, `*.nml`, `*.mod`, `*.hoc`, `*.ode`, notebooks, `tests/`, `examples/`, `docs/`, `data/`, `config*.yaml`, CI files.
2. Locate the entry point(s): scripts in `bin/`, `__main__.py`, `main.py`, `run*.py`, top-level notebooks, a `[project.scripts]` block, or `CMD`/`ENTRYPOINT` in a Dockerfile.
3. Note the rough size (number of source files, presence of compiled extensions).

Write a brief inventory note to yourself (mental or scratch). You'll cite specific files in the YAML's `source` fields.

**Framework dispatch.** After inventory, check the model against the table below. If a row's signal matches, **read that one reference file now and apply its framework-specific heuristics throughout Passes 1–3**. **Precedence: where the framework file and a generic pass instruction conflict, the framework file WINS** — it is more specific to the artifact in front of you. (Example: if the framework file says "enumerate every runnable module" and Pass 2's generic bullet says "copy the README's literal commands," you enumerate.) The one thing a framework file never overrides is `references/schema.md` — field names, envelopes, and required/optional status always come from the schema. If no row matches, skip this step entirely and do not read any framework file — the generic passes cover it.

| Framework | Signal (any) | Reference |
|---|---|---|
| Vivarium | dependency `vivarium`/`vivarium-core`; any import from `vivarium.core.*` | `references/vivarium-model-reference.md` |

(One row per supported framework. Match at most one; the generic entry-point / classification / I/O guidance in Passes 1–3 still applies for everything the framework file doesn't override.)

### Pass 1 — Model identity & biology (Section A)

Read the README first; it's where authors put the high-level pitch. Then skim the top of the main module / entry script. You're looking for:

- **Name**, **short description**, **long description**.
- **Model class(es)**: the modeling *approach* — use only values from the `model_class[]` closed vocabulary below. The field is a **list** — if the model genuinely combines paradigms (e.g. agent-based agents whose internal state evolves under ODEs), record both. The label "hybrid" by itself is not a class; emit the component classes and let the multi-element list speak for itself. Map to MAMO in Pass 4.
- **Formalism(s)**: the *mathematical machinery* the model uses — distinct from model_class (`model_class` is the approach; `formalism` is the math). Also a list; use only values from the `formalism[]` closed vocabulary below. For pure-paradigm models the list will have one element.
- **Biological scope**: organism(s), cell type(s), tissue/anatomy, biological process(es), molecules involved. Map to NCBITaxon, CL, UBERON, GO, ChEBI.
- **Spatial/temporal characteristics**: deterministic vs stochastic, continuous vs discrete time, dimensionality, spatial scale. Use only the values from the closed vocabularies below — do not invent synonyms or variant spellings.

  | Field | Allowed values |
  |---|---|
  | `model_class[]` | `agent-based model` \| `ordinary differential equation model` \| `partial differential equation model` \| `stochastic model` \| `constraint-based model` \| `Boolean network model` \| `rule-based model` \| `Markov chain model` \| `multi-scale model` |
  | `formalism[]` | `ODE` \| `SDE` \| `PDE` \| `Boolean` \| `Markov chain` \| `rule-based` \| `discrete-event` \| `stochastic` \| `agent-based` |
  | `determinism` | `deterministic` \| `stochastic` \| `hybrid` \| `unknown` |
  | `time_dynamics` | `continuous` \| `discrete` \| `event-driven` \| `static` \| `unknown` |
  | `spatial` | `non-spatial` \| `well-mixed` \| `compartmental` \| `1D` \| `2D` \| `3D` \| `lattice` \| `off-lattice` \| `unknown` |
  | `model_scales[]` | `molecular` \| `cellular` \| `tissue` \| `individual` \| `population` |

  **`time_dynamics` tiebreaker — `discrete` vs `event-driven`:** Use `discrete` when the framework advances by a fixed timestep (e.g. Vivarium, NetLogo, Mesa). Use `event-driven` only for true event-queue simulators that advance time to the next scheduled event (e.g. NEURON, SimPy, NEST). When in doubt for fixed-timestep frameworks, prefer `discrete`.

  **Fields that must always be emitted** — even when no evidence exists, use `null` for scalars and `[]` for lists: `model_class`, `formalism`, `determinism`, `time_dynamics`, `spatial`, `biology`. Do not omit these keys. A missing key is indistinguishable from a forgotten one.

  **Note on `multiscale`:** this is a bare `true`/`false`/`unknown` scalar — it does **not** use a `{value, source, confidence}` envelope. It is the only field in Section A that works this way.

  **Note on `model_scales` items:** even though the allowed values are a closed vocabulary (see table above), each list entry still uses the standard `{value, source, confidence}` envelope — not a bare string.

- **Authorship and contacts (two separate fields).** `authors` records who *created* the model (intellectual contribution): name, affiliation, ORCID, role. `contacts` records who to *reach* about the model now: corresponding author, current maintainer, support address. The two lists can overlap or not — don't conflate them. Put email addresses only in `contacts`, not `authors`. Sources to check, in order: `CITATION.cff` (has both fields explicitly), `pyproject.toml` / `setup.py` (authors and maintainers separately), README author/contact blocks, git log (last-resort fallback for maintainer only). **Only add an entry to `contacts` when you found the person's email address verbatim in a source file — do not construct or infer email addresses.**
- **License**: from `LICENSE` file or metadata config. Use SPDX identifiers.
- **Publications / references**: DOIs in README or `CITATION.cff`. Capture as PubMed/DOI identifiers.
- **Version**: from `__version__`, `pyproject.toml`, `package.json`, or git tags.

For every field, record the file you found it in. If you inferred it from context rather than reading it verbatim, set `confidence: inferred`. **For multi-element fields like `model_class` and `formalism`, each list entry must carry its own `source` pointing to distinct evidence** — don't reuse the README citation for every paradigm. If you claim a model is agent-based + ODE, one entry's source should point to where the agent-based framing comes from (often the README or framework name) and the other to where the ODE evidence comes from (a process file's rate equations, a solver import).

### Pass 2 — Execution environment (Section B)

You want a reviewer to be able to run this model after reading the YAML. Pull out:

- **Primary language and version**: from `.python-version`, `pyproject.toml` `requires-python`, `Project.toml`, shebangs, `DESCRIPTION`'s `Depends: R (>= ...)`.
- **Runtime environment kind**: native (just pip/conda/Julia Pkg), Docker, Singularity, Nextflow/Snakemake workflow, HPC job, Jupyter only, or web app. Look at the union of CI config, Dockerfiles, and entry-point docs.
- **Dependencies**: read `requirements*.txt`, `pyproject.toml [project] dependencies` and any optional-dependencies groups, `environment.yml`, `Pipfile`, `Project.toml`, `package.json`, `DESCRIPTION` Imports/Depends. Capture name + version constraint. Don't try to expand transitive deps.
- **System-level dependencies**: anything in `apt-get install` lines of the Dockerfile, README "Installation" prerequisites (compilers, BLAS, CUDA, MPI, GraphViz, Java).
- **Compute requirements**: GPU? Multi-core / MPI? Approximate memory and runtime if the README mentions them. Note "unknown" rather than guessing.
- **Entry points / how to run**: `[project.scripts]` / `console_scripts` first, then the commands in README "Usage" sections, then any additional runnable modules you can enumerate structurally (a `__main__` block, a `bin/` script, a notebook). **Decompose the command.** The `command` field is the **base invocation only** — interpreter + script/module, plus `<PLACEHOLDER>` tokens for required positionals. Never inline flags/options as free-text (no `[--foo]`, no `--config x`). Whenever an entry parses arguments (argparse, click, `sys.argv`, or documented console-script flags), enumerate every flag/option/positional into the structured **`arguments`** list — each with `name` (the canonical CLI token, not a doc label), `default`, `enums`, `data_type` (`"bool"` for presence flags), `position` (>=1 for positionals, unique per entry), and `user_can_override`. See `references/schema.md` for the exact field shape. Emit `arguments: []` only when the entry truly takes none. Each entry's **`source` is the file that makes it runnable** — the module path holding the `__main__` block, or the config that declares the script (`pyproject.toml` / `setup.py`) — **not** a README line reference; if the README also documents it you may append that, but the runnable file comes first. Each entry also carries a **`confidence`**: `high` for a declared console-script or a file you confirmed has a `__main__` / is otherwise runnable, `inferred` when you reconstructed the command without confirming the file runs. When an entry writes results to a known directory or file, record it in the optional **`default_output_location`** as a **repo-relative** path (never absolute); omit or null it when the entry produces no files or the location is undeterminable.

  **Completeness rule (mirrors the Pass 4 reproducibility invariant).** `entry_points` must be *exhaustive*, not a representative sample. The README's "Usage" section usually shows one command per way-of-running; the repo often exposes many more runnable modules than the README documents. Enumerate them structurally (e.g. `grep -rl "__main__"`, the `[project.scripts]` table, `bin/`) rather than copying only the README's examples — building the full list this way is high-confidence **structural** extraction, so it is not constrained by the "copy only what a source states verbatim" discipline that governs Passes 0–3. If you deliberately leave any runnable entry point out (e.g. a budget cap on a large repo), you MUST record the omitted scope in `provenance.partial_annotation_scope.deferred` — a non-empty `entry_points` list that silently drops runnable modules is not acceptable. (Framework reference files may refine *which* modules count as entry points; when one is loaded, it wins per the Pass 0 precedence rule.)
- **Tests**: presence and how to invoke them.

If the model is just a single file (e.g. an SBML file), execution metadata is mostly about the simulator it targets — capture that instead.

Sections A and B are validated against `references/schema.md` at the end, in Assembly — there is no mid-workflow checkpoint. Fill `model:` and `execution:` as completely as the sources allow now; you will run the structural gate once, on the finished file, before presenting it.

### Pass 3 — Inputs and outputs (Section C)

This is usually the section with the least explicit documentation; expect to read code, not just docs.

**Reading budget.** Open the primary entry point and at most 2–3 modules it directly imports — usually a config/parameters module, a top-level model class, and an output/writer module. If you can't find a field's value in those files, leave it with `confidence: none` and a brief curator note rather than doing a depth-first search of the whole codebase. A first-pass annotation is allowed to be incomplete; an over-budget one that stalls is not.

**Fast path — config-driven models.** If a config file governs the run (`config.yaml`, `params.json`, `settings.toml`, an `experiments/*.yaml`, or similar), treat it as the source of truth for `io.inputs.parameters` and derive the schema almost 1:1: each top-level key becomes a parameter entry with its value as `default_value`, and the file path goes in `source`. Still infer units and biological meaning from surrounding comments, docstrings, and variable names — the config file alone rarely tells you what the parameters *mean*, only what they're set to. If multiple config files exist (e.g. `experiments/chemotaxis_default.yaml`, `experiments/chemotaxis_long.yaml`), pick the one the README points to as canonical, or the one with `default` in its name, and note the alternatives in `notes`.

For **inputs**, distinguish three flavors:
- **Parameters** — scalar/array values that configure the model (rate constants, initial concentrations, agent counts). Capture name, default value, unit, biological meaning, source file.
- **Initial conditions / state files** — explicit starting states (e.g. a CSV of cell positions, an SBML species block).
- **Data inputs** — external files the model consumes (experimental data, parameter sweeps, network topology). Note file format.

For **outputs**:
- What's produced (timeseries, snapshots, fluxes, agent trajectories, fields, summary statistics).
- File format (CSV, HDF5, Parquet, plot images, custom binary).
- Units of each reported quantity.
- Where outputs are written (working dir, `output/`, configurable).

For every parameter and output, **capture units even when they aren't explicit** — infer from context and mark `confidence: inferred`. Units will be mapped to UO IRIs in Pass 4.

### Pass 4 — Ontology mapping via OLS

Now go back through every textual term you've filled in and try to attach an ontology IRI. Use the `ols-ontology` MCP tools. Detailed routing — which ontology to consult for which field — is in `references/ontologies.md`. **Read that file before doing the mapping pass.**

**Reproducibility invariant.** Every ontology-eligible field MUST be attempted. The output of this skill needs to be reproducible — two runs over the same input should produce the same `mapping_confidence` distribution. That means `mapping_confidence: none` strictly means "I tried lexical search (and embedding fallback if available) and got nothing acceptable" — it never means "I didn't try." If you genuinely can't attempt mapping for some scope (e.g. you can only annotate one of five process files for budget reasons), record the *whole skipped scope* in `provenance.partial_annotation_scope.deferred` rather than emitting partially-mapped entries.

**Step 0 — Probe the deployment once.** At the start of Pass 4, call `ols-ontology:listEmbeddingModels` to find out whether semantic fallback is available. Record the result in `provenance.ontology_lookups.embedding_models_available`. If at least one model has `can_embed: true`, pick that model id for use in step 3 below. If all models have `can_embed: false`, the embedding fallback is unavailable in this deployment — set `provenance.ontology_lookups.embedding_fallback_used: false`, and skip step 3 entirely (go directly from step 2's miss to step 4).

Strategy per term:
1. Pick the most likely ontology from `references/ontologies.md`.
2. Call `ols-ontology:searchClasses` with `ontologyId` set to that ontology.
3. If the top hit's label matches the term closely (case-insensitive, ignoring trailing punctuation), accept it. If not, and embedding fallback is available, fall back to `searchClassesWithEmbeddingModel` for a semantic search.
4. If you still don't have a confident hit, leave the `iri` field null, set `mapping_confidence: none`, and **append an entry to `provenance.unmapped_fields`** with: the field path in the YAML, every query attempted (ontology, query string, strategy, hit count, reason for not accepting). Do not invent IRIs.
5. For each accepted mapping, record `iri`, `label` (from OLS — the *canonical* label, not your input string), `ontology`, and `mapping_confidence` (`high` for exact label match, `medium` for close match requiring judgment, `low` for embedding-only).

Don't try to map purely structural fields (version strings, file paths, license SPDX codes — SPDX is already a controlled vocabulary).

Batch tip: group queries by ontology so you reuse the same `ontologyId` repeatedly. This keeps similar terms mapped consistently.

### Assembly

Once all four passes are done:

1. Render the content following `references/schema.md`. Use the BioModels/MIRIAM qualifier vocabulary where it applies (e.g. `bqbiol:is`, `bqbiol:hasTaxon`, `bqmodel:isDerivedFrom`).
2. Build the `provenance` content: timestamp, the path you annotated, the list of source files you actually read, the OLS lookups, `unmapped_fields`, `partial_annotation_scope`, a `validation` sub-block (see `references/schema.md`), and a `human_review_required: true` flag.
3. Write the **annotation package** as a folder `metadata-package/` **inside the model's own directory** (the repo/folder you annotated — not your cwd), with two YAML files:
   - `metadata-package/metadata.yaml` — `schema_version`, `model:`, and the identity/ontology half of `provenance:` (`files_inspected`, `ontology_lookups`, `unmapped_fields`, `partial_annotation_scope`).
   - `metadata-package/execution.yaml` — `schema_version`, `execution:`, `io:`, and the `validation` half of `provenance:`.
   - Repeat the run-stamp (`annotated_at`, `annotated_by`, `source_root`, `human_review_required`) in both files so each stands alone.
4. **Validation gate — mandatory, run on the package you just wrote. Do not present the annotation until this exits 0.** Run the bundled validator against the real package (`uv run` resolves the PyYAML dependency inline — no install step, no MCP server).

   **Locating the script.** `scripts/validate.py` ships *inside this skill's directory*, which is **not** your current working directory (your cwd is the model repo you are annotating). Resolve the path against the skill directory — the directory holding this `SKILL.md`. Your harness tells you where that is: it loads the skill with a `location=<.../SKILL.md>` attribute / a "References are relative to `<dir>`" line. Take that `<dir>` and run `<dir>/scripts/validate.py`. Do **not** run a bare `scripts/validate.py` (resolves against cwd and fails) and do **not** `find`/`rg` the filesystem for it — the path is already known from the skill location.

   ```bash
   # SKILL_DIR = the directory containing this SKILL.md (from the skill's location attribute)
   uv run "$SKILL_DIR/scripts/validate.py" --package <model-repo-root>/metadata-package --input-path <model-repo-root>
   ```

   (Important: Try `uv` first, if `uv` is unavailable, fall back to `python3 "$SKILL_DIR/scripts/validate.py" --package <model-repo-root>/metadata-package` with PyYAML installed.) It reconstructs the `model:` and `execution:` sections from the two files, checks them against the REQUIRED fields in `references/schema.md`, prints a JSON result to stdout, and sets its exit code:

   - **Exit 0 (`status: "pass"`):** overwrite `provenance.validation` **in `execution.yaml`** with `{method: "cli", status: "pass", flagged_fields: []}` — this must be a populated mapping, not an empty `{}`. Then proceed to step 5.
   - **Exit 1 (`status: "fail"`):** this is an instruction to go back and fix, not a reason to stop. The `missing_required_fields` and `empty_required_fields` lists name every field needing attention by path (e.g. `"model.name"` → `metadata.yaml`, `"execution.entry_points"` → `execution.yaml`). For each path: go back to the pass that owns it (Pass 1 for `model.*`, Pass 2 for `execution.*`), re-read the source files, and fill or correct the field in the written file — do not fabricate a value to satisfy the check; if a source truly lacks it, that is a `confidence: none` / `not_determined` value, which still resolves the structural gate. Record every path you touched in `execution.yaml`'s `provenance.validation.flagged_fields`, then re-run the validator. Repeat this fix-and-re-run loop until it exits 0. Never present a `status: "fail"` annotation.
   - **Exit 2:** usage error (missing file or unparseable YAML) — fix the invocation or the YAML and re-run.

   This is the only structural gate and it is not optional. Running it is the definition of "done" — an annotation that has not exited 0 is not finished, regardless of how complete it looks.
5. Write `metadata-package/README.md` — a model-card summary the curator reads first: model name + one-line type (`model_class` / `formalism`), organism/biology, a "Package contents" file list, what the annotation covers, what was deferred (passes/sections skipped, count of `mapping_confidence: none`), and the fields most needing human review (low/`none` confidence). Keep it skimmable — it mirrors the YAML, it doesn't replace it.
6. Briefly summarize for the user: what type of model it is, the most notable fields you filled, anything where confidence was low, and which sections need human review most. Then present the package.

---

## Conventions

### Confidence and source

Every leaf field that carries content (not structural keys) gets two siblings: `source` and `confidence`.

```yaml
name:
  value: "Vivarium Chemotaxis"
  source: "README.md:1"
  confidence: high
```

`confidence` is one of:
- `high` — found verbatim in an authoritative source (README, `pyproject.toml`, `CITATION.cff`).
- `medium` — derived from clear context (e.g. unit inferred from variable name plus comment).
- `inferred` — your best guess based on patterns; explicitly flag for review.
- `none` — couldn't determine; field present so the curator knows to fill it.

For ontology mappings, use `mapping_confidence` separately (see Pass 4).

### Missing information

Never silently omit a section. If you found no execution metadata, emit `execution:` with `status: not_determined` and a brief note explaining why (e.g. "single SBML file, no surrounding repo").

For **individual optional fields**: if a key is present in the schema but you found no evidence for it, emit it as `[]` (lists) or `null` (scalars). **Never omit a schema key from the output.** Omitting a key is indistinguishable from forgetting it — emit the key with an empty value so the curator knows the field was considered.

### Don't fabricate identifiers

If you can't find a DOI, ORCID, or ontology IRI, leave it null. Do not guess. The annotation is a substrate for human curation, not the final word.

### Keep it terse

YAML descriptions should be 1–3 sentences. The point is to make a reviewer able to skim. Long-form prose belongs in a separate README.

---

## Standards & vocabularies referenced

This skill aligns with conventions from:

- **MIRIAM** (Minimum Information Required In the Annotation of Models) and its BioModels.net qualifier vocabulary (`bqbiol:`, `bqmodel:`).
- **COMBINE archive** manifest semantics.
- **MIASE** (Minimum Information About a Simulation Experiment) for the `io` section's experiment description.
- **EDAM**, **MAMO**, **KISAO**, **TEDDY**, **GO**, **ChEBI**, **UO**, **NCBITaxon**, **CL**, **UBERON**, **SWO**, **SBO** — all queryable via OLS.

Pointers and per-field ontology choices are in `references/ontologies.md`.

---

## Reference files

- `references/schema.md` — full YAML schema with required/optional fields per section.
- `references/ontologies.md` — which ontology to consult for which field, with OLS query tips.

Read both before writing your final output.

**Framework reference files** (`references/<framework>-model-reference.md`, e.g. `vivarium-model-reference.md`) are **conditionally** loaded — read one only when the Pass 0 Framework dispatch table matches. They carry framework-specific extraction heuristics that **override the generic pass guidance on conflict** (see Pass 0 "Framework dispatch" precedence rule); they point back at `schema.md` for field shape and never redefine schema fields. Unlike `schema.md`/`ontologies.md`, they are not read on every run.

## Available scripts

- **`scripts/validate.py`** — Sections A & B structural check against `references/schema.md`. Run as the final validation gate in Assembly, on the written package. The script lives in this skill's directory, not your cwd — invoke it as `<skill-dir>/scripts/validate.py` (see the Assembly "Locating the script" note): `uv run "$SKILL_DIR/scripts/validate.py" --package <repo>/metadata-package --input-path <repo>`. Exits 0 pass / 1 fail / 2 usage error; prints a JSON result to stdout. See `--help` for details.
