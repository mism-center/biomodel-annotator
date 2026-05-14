# Ontology Routing Guide

For each ontology-mappable field in the annotation schema, this file specifies the canonical ontology to consult via the EBI OLS (`ols-ontology` MCP) and offers query tips. Use `ols-ontology:searchClasses` with the `ontologyId` filter for the targeted searches; fall back to `searchClassesWithEmbeddingModel` when the lexical search misses.

## How to query OLS via MCP

**Run this once at the start of Pass 4** to find out whether the embedding fallback is available in your deployment:

```
ols-ontology:listEmbeddingModels()
# Returns e.g. [{model: "...", can_embed: true|false}, ...]
```

If at least one model has `can_embed: true`, the embedding fallback is available — note the model id and use it in `searchClassesWithEmbeddingModel`. If all models report `can_embed: false`, embedding fallback is unavailable in this deployment; record this in `provenance.ontology_lookups.embedding_fallback_used: false`, and skip the embedding step (go straight from "lexical missed" to "leave null, `mapping_confidence: none`, record the attempt in `provenance.unmapped_fields`"). Either way, record what `listEmbeddingModels` returned in `provenance.ontology_lookups.embedding_models_available`.

```
# Targeted lexical search inside one ontology
ols-ontology:searchClasses(query="agent-based model", ontologyId="mamo", pageSize=5)

# Semantic / embedding fallback (only if a can_embed=true model exists)
ols-ontology:searchClassesWithEmbeddingModel(query="...", model="<can_embed_true_model>", ontologyId="mamo")

# Get full details for a hit
ols-ontology:fetch(id="mamo+http://identifiers.org/mamo/MAMO_0000028")
```

Accept the top hit only when its label matches the input term closely (case-insensitive, ignoring trailing punctuation and plurals). Otherwise inspect the top 3–5 results and pick the best, or fall back to embedding search if available. If still unconfident, leave `iri: null` and `mapping_confidence: none`, and **record the attempt in `provenance.unmapped_fields`** (with the queries you tried). Do not invent IRIs.

## Per-field ontology routing

### Section A — model

| Field | Ontology | OLS `ontologyId` | Notes |
|---|---|---|---|
| `model_class` | MAMO — Mathematical Modelling Ontology | `mamo` | "agent-based model", "ordinary differential equation model", "constraint-based model", "Boolean network model", "stochastic model". |
| `formalism` | MAMO + KISAO | `mamo`, `kisao` | KISAO is mostly *algorithms* (Gillespie, CVODE) but also includes formalisms. Try MAMO first for the formalism, KISAO for the solver. |
| `biology.organisms` | NCBI Taxonomy | `ncbitaxon` | Use scientific name when possible ("Escherichia coli", not "E. coli"). |
| `biology.cell_types` | Cell Ontology | `cl` | E.g. "neuron", "hepatocyte". |
| `biology.anatomy` | Uberon | `uberon` | Tissues, organs, anatomical regions. |
| `biology.biological_processes` | Gene Ontology — Biological Process | `go` | "chemotaxis", "signal transduction", "glycolysis". Filter to BP namespace if the search returns molecular function or cellular component instead. |
| `biology.molecular_entities` | ChEBI | `chebi` | Small molecules, ions, drugs. For proteins use UniProt accessions instead. |
| `biology.proteins_genes.identifier` | UniProt / Ensembl / HGNC | (external, not OLS) | These are not OLS-hosted; record the accession directly. |
| `biology` overall qualifier | SBO — Systems Biology Ontology | `sbo` | When the field is a *role* (e.g. "modifier", "product"), SBO is the right home. |

### Section B — execution

| Field | Ontology | OLS `ontologyId` | Notes |
|---|---|---|---|
| `language.name` | Software Ontology | `swo` | Search for "Python language", "R programming language", "Julia". SWO has both languages and tools. |
| `dependencies.runtime[].name` | Software Ontology | `swo` | Map well-known libraries (NumPy, SciPy, COBRApy) where they exist in SWO; many small libs won't be in any ontology — leave `iri: null` and that's fine. |
| `environment_kind` | EDAM (operation/format) + SWO | `edam`, `swo` | "Docker" / "Singularity" are in SWO. Pipeline systems (Nextflow, Snakemake) are in SWO too. |
| `compute.parallelism` | EDAM topic / NCIT | `edam`, `ncit` | Often not worth mapping — leave free-text if no good hit. |

### Section C — io

| Field | Ontology | OLS `ontologyId` | Notes |
|---|---|---|---|
| `inputs.parameters[].unit`, all `unit` fields | Units of Measurement | `uo` | Search for the human-readable unit ("per second", "molar", "millimolar"). Compound units (e.g. "m^3 / s") may not have an exact UO term — use the closest component and flag `mapping_confidence: low`. |
| `inputs.parameters[].biological_meaning` | GO / SBO / SIO | `go`, `sbo`, `sio` | "rate constant", "binding affinity", "concentration" — SBO has parameter roles, GO has biological processes. |
| `inputs.data_inputs[].format`, `outputs[].format` | EDAM format | `edam` | Use the `format_` subtree. "CSV" → format_3752, "HDF5" → format_3590, "SBML" → format_2585. |
| `outputs[].quantity_kind` | SIO / GO / SBO | `sio`, `go`, `sbo` | "concentration", "spatial position", "reaction flux". SIO covers generic scientific quantities well. |

### Section A — references qualifiers

When recording `related_resources`, use BioModels/MIRIAM qualifiers (these are not OLS-hosted but are a fixed controlled vocabulary):

- `bqbiol:is`, `bqbiol:hasPart`, `bqbiol:isPartOf`, `bqbiol:isVersionOf`, `bqbiol:hasVersion`, `bqbiol:isHomologTo`, `bqbiol:isDescribedBy`, `bqbiol:isEncodedBy`, `bqbiol:encodes`, `bqbiol:occursIn`, `bqbiol:hasProperty`, `bqbiol:isPropertyOf`, `bqbiol:hasTaxon`.
- `bqmodel:is`, `bqmodel:isDescribedBy`, `bqmodel:isDerivedFrom`, `bqmodel:isInstanceOf`, `bqmodel:hasInstance`.

Reference: https://co.mbine.org/standards/qualifiers

## Tips and gotchas

- **Don't over-map.** Software dependency names, license SPDX codes, file paths, version strings, command-line strings — these don't need IRIs.
- **Prefer specific over generic.** "Chemotaxis to cAMP" (GO:0043327) is better than "chemotaxis" (GO:0006935) when the model is specifically about a known chemoattractant. Read the OLS hit's definition before accepting it — don't accept ancestors like "taxis" (GO:0042330) when a more specific descendant exists.
- **Watch for obsolete entries.** OLS marks them; skip them and pick the active replacement.
- **Compound concepts.** A field like "tumble rate of E. coli during chemotaxis" needs decomposition: map "tumble" to GO if available, "E. coli" to NCBITaxon, "chemotaxis" to GO separately. The schema accommodates lists.
- **Embedding fallback.** When lexical search returns nothing useful, `searchClassesWithEmbeddingModel` will often find the right concept under a different name (e.g. "agent-based simulation" → "agent-based model"). First call `listEmbeddingModels` and pick one with `can_embed=true`.
- **Batch by ontology.** Resolve all NCBITaxon hits in a row, then all ChEBI, etc. Keeps the workflow tidy and avoids repeated MCP overhead.
