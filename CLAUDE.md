# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code **skill** plus a small Python support layer. The skill itself is three Markdown files that Claude Code loads at invocation time:

- `SKILL.md` — frontmatter (`name`, `description`) + the full operating procedure for the `biomodel-annotator` skill.
- `references/schema.md` — the YAML schema the skill must emit.
- `references/ontologies.md` — per-field routing to OLS ontologies + query strategy.

The Python support layer lives in `src/` and ships with the skill in every release zip:

- `src/validator.py` — structural validation of Section A (`model:`) and Section B (`execution:`) against the required fields in `references/schema.md`.
- `src/mcp_server.py` — FastMCP stdio server that exposes `validator.py` as the `biomodel-validator` MCP tool, called by the skill at the validation checkpoint between Pass 2 and Pass 3.

**When editing Markdown skill content** (the three `.md` files), no Python tools are needed. **When editing `src/`**, standard Python applies: `pip install fastmcp pyyaml`, and run `python src/mcp_server.py` to start the server locally for testing.

Note: a parent `CLAUDE.md` at `../.claude/CLAUDE.md` describes a generic Python/PowerShell workflow. Treat it as out of scope when editing skill or `src/` content here — there is no venv at this directory level and no PyLint target to run.

## What the skill does (architecture)

The skill turns a biological model artifact (repo, folder, single SBML/CellML/BNGL/etc. file, or GitHub URL) into one MIRIAM-aligned YAML file: `<model-name>.annotation.yaml`. The YAML has four top-level sections: `model` (identity/biology), `execution` (how to run), `io` (inputs/outputs), `provenance` (run metadata).

Execution is a strict **four-pass workflow plus assembly**, and the passes are not independent — earlier passes feed later ones, so the YAML must not be written until all four have run:

1. **Pass 0 — Inventory.** Enumerate top-level files; locate entry points.
2. **Pass 1 — Identity/biology.** README-first; fill Section A.
3. **Pass 2 — Execution.** Dependencies, language, container, entry points; Section B.
4. **Pass 3 — I/O.** Parameters, initial conditions, data inputs, outputs; Section C. Bounded reading budget: entry point + 2–3 directly-imported modules.
5. **Pass 4 — Ontology mapping** via the external `ols-ontology` MCP. Probe `listEmbeddingModels` once at the start; lexical `searchClasses` first, embedding fallback only if a `can_embed=true` model exists.
6. **Assembly.** Render YAML per `references/schema.md`, write `provenance`, emit `<slug>.annotation.yaml`.

The skill depends on the `ols-ontology` MCP server being connected at runtime. Without it, Pass 4 cannot run and every ontology-mapped field will end up `mapping_confidence: none`.

## Invariants when editing the skill

Three rules in `SKILL.md` are load-bearing for downstream consumers. Preserve them when editing:

- **Reproducibility invariant (Pass 4).** `mapping_confidence: none` strictly means "tried and failed." Fields not attempted must instead go into `provenance.partial_annotation_scope.deferred`. Two runs over the same input must produce the same `mapping_confidence` distribution. Any edit that loosens this breaks the contract `references/schema.md` documents.
- **`model_class` vs `formalism`.** Both are lists. `model_class` = modeling approach (agent-based, constraint-based); `formalism` = math (ODE, SDE, Markov chain). They are intentionally separate — a single agent-based ODE model has one entry in each. Don't merge them, and require distinct `source` evidence per list entry.
- **`authors` vs `contacts`.** Authors = intellectual creators; contacts = who to email now. Email addresses belong only in `contacts`. Don't conflate.

Every leaf value field in the schema carries `value` + `source` + `confidence`. Ontology-mapped fields additionally carry `iri`, `ontology_label`, `ontology`, `mapping_confidence`. When extending the schema, follow the same shape.

## Cross-file consistency

`SKILL.md`, `references/schema.md`, and `references/ontologies.md` must agree on:

- Field names and nesting (schema is authoritative).
- The four `mapping_confidence` values and their exact meanings (schema's "Strict definitions" table is authoritative).
- The Pass 4 lexical-then-embedding strategy (`ontologies.md` and `SKILL.md` describe the same procedure — keep them in sync).
- Provenance shape, especially `unmapped_fields` and `partial_annotation_scope`.

When changing one of these three files, check the other two.
