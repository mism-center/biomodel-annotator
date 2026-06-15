# Annotation YAML Schema

The output of the `biomodel-annotator` skill. Every leaf value field carries `value`, `source`, and `confidence` siblings unless noted. Ontology-mapped fields additionally carry `iri`, `ontology_label`, `ontology`, and `mapping_confidence`.

## Top-level structure

```yaml
schema_version: "0.1"
model: { ... }       # Section A
execution: { ... }   # Section B
io: { ... }          # Section C
provenance: { ... }  # Run metadata
```

## Section A — `model`

```yaml
model:
  name: { value, source, confidence } #REQUIRED
  short_description: { value, source, confidence } #REQUIRED
  long_description: { value, source, confidence } #REQUIRED
  version: { value, source, confidence } #REQUIRED. probably auto generate
  doi: {value, source, confidence}     #Optional. We will need DOIs in the future, but may not for POC2.
  identifier:                          #REQUIRED. Should auto-generate identifier.
    scheme: "biomodels", "doi", "url", "other"
    value: ...
    source: ...
  model_class:                         #Optional. list, ontology-mapped to MAMO. Length 1 for pure-paradigm models, ≥2 for hybrids (e.g. agent-based + ODE).
    - value: "agent-based model"
      iri: "http://identifiers.org/mamo/MAMO_0000028"
      ontology_label: "agent-based model"
      ontology: "mamo"
      mapping_confidence: high
      source: ...
      confidence: ...
  formalism:                           # Optional. list, ontology-mapped to MAMO/KISAO. Each formalism the model uses (ODE, SDE, Boolean, Markov chain, ...). Length 1 for single-paradigm models, ≥2 for hybrids. Paired conceptually with model_class but kept separate because model_class is the modeling *approach* (agent-based, constraint-based) while formalism is the *mathematical machinery* (ODE, SDE). 
    - value: ...
      iri: ...
      ontology_label: ...
      ontology: "mamo", "kisao"
      mapping_confidence: ...
      source: ...
      confidence: ...
  determinism: "deterministic", "stochastic", "hybrid", "unknown" #Optional.
  time_dynamics: "continuous", "discrete", "event-driven", "static", "unknown" #Optional.
  spatial: "non-spatial", "well-mixed", "compartmental", "1D", "2D", "3D", "lattice", "off-lattice", "unknown" #Optional.
  multiscale: true | false | unknown #REQUIRED
  model_scales:                      #REQUIRED. the scale(s) of the model (e.g., "molecular", "cellular", "tissue", "individual", "population"). list
    - { ... }
  biology:
    species:                         #Optional. Host or model organism (e.g., "SARS-CoV-2", "HIV-1", "Homo sapiens"). list, ontology-mapped to NCBITaxon
      - { value, iri, ontology_label, ontology, mapping_confidence, source, confidence }
    infectious_agent:                #Optional. pathogen or organism of study. list, ontology-mapped to NCBI Taxonomy IDs
      - { value, iri, ontology_label, ontology, mapping_confidence, source, confidence }
    health_condition:                 #Optional. mapped to disease or clinical indication. list, ontology mapped to Mondo Disease Ontology (MONDO), Human Phenotype Ontology (HPO), or and Disease Ontology (DOID)
      - { value, iri, ontology_label, ontology, mapping_confidence, source, confidence }
    topic_category:                    #Optional. domain-level filtering and support topic-based navigation. list, mapped to EDAM Ontology
      - { value, iri, ontology_label, ontology, mapping_confidence, source, confidence }
    cell_types:                        #Optional. list, ontology-mapped to CL
      - { ... }
    anatomy:                           #Optional. list, ontology-mapped to UBERON
      - { ... }
    biological_processes:              #Optional. list, ontology-mapped to GO
      - { ... }
    molecular_entities:                #Optional. list, ontology-mapped to ChEBI; small molecules, ions, drugs
      - { ... }
    proteins_genes:                    #Optional. list, free-text + UniProt / Ensembl identifiers when available
      - { value, identifier: { scheme, value }, source, confidence }
  authors:                              # who created the model (intellectual authorship). Author identity is separate from how to reach a current maintainer; do not put email here unless the user has no separate contacts block.
    - name: ... #REQUIRED
      affiliation: ... #REQUIRED
      orcid: ...                     #Optional.  # full ORCID URL
      role: "author", "co-author", "principal investigator", "developer", null #Optional.
      source: ...            
  contacts:                             # how to reach someone about the model now — may overlap with authors, may not. Keeps "who wrote it" separate from "who to email about it".
    - name: ... #REQUIRED
      role: "corresponding author", "maintainer", "support", "submitter", null #REQUIRED
      email: ... #REQUIRED
      affiliation: ... #Optional.
      source: ...
  license:
    spdx_id: "MIT", "Apache-2.0", "GPL-3.0-or-later" , ... #REQUIRED
    source: ...
    confidence: ...
  publications:                          # papers, preprints
    - title: ...
      doi: ...
      pmid: ...
      url: ...
      source: ...
  related_resources:                   # data, prior models the curators want linked
    - qualifier: "bqmodel:isDerivedFrom", "bqbiol:isVersionOf", ...
      identifier: { scheme, value }
      source: ...
  funding:                             #Grant numbers or funding acknowledgments (e.g., "NIAID U19 AI123456").
    -acknowledgement: ...
  
  
```

## Section B — `execution`

```yaml
execution:
  status: "characterized" | "partially_characterized" | "not_determined"
  language:                            # ontology-mapped to SWO if possible
    name: "Python" | "Julia" | "R" | "MATLAB" | "C++" | ...
    version_constraint: ">=3.10,<3.13"
    iri: ...
    ontology: "swo"
    source: ...
  environment_kind:                    # ontology-mapped to EDAM operation/format where it fits, else free
    value: "conda" | "pip" | "docker" | "singularity" | "nextflow" | "snakemake" | "jupyter" | "native"
    source: ...
  dependencies:
    runtime:                           # Python pip / Julia / R / etc.
      - name: "numpy"
        version_constraint: ">=1.24"
        source: "pyproject.toml:42"
    optional:
      - { name, version_constraint, group, source }
    system:                            # apt-get, brew, OS-level libs (BLAS, MPI, CUDA toolkit)
      - { name, version_constraint, source }
  containers:
    - kind: "docker" | "singularity"
      file: "Dockerfile" | "container.def"
      image_name: ...
      source: ...
  compute:
    cpu_cores: { value, source, confidence }      # use null if not stated
    memory_gb: { value, source, confidence }
    gpu_required: { value, source, confidence }   # boolean
    parallelism: "single" | "multi-thread" | "multi-process" | "MPI" | "GPU" | "distributed"
    typical_runtime: { value, unit, source, confidence }  # e.g. "minutes", "hours"
  entry_points:                        # one entry per command the user might invoke
    - command: "python -m vivarium_chemotaxis.experiments.run_chemotaxis"
      purpose: "Run the main chemotaxis experiment"
      arguments:                       # capture if README documents them
        - name: "--duration"
          description: "Simulation duration in seconds"
          default: 10.0
      source: "README.md:120"
  tests:
    framework: "pytest" | "unittest" | "Test.jl" | ...
    invocation: "pytest tests/"
    source: ...
  notes: ...                           # free text for anything that doesn't fit
```

## Section C — `io`

```yaml
io:
  inputs:
    parameters:                        # scalar/array configuration values
      - name: "k_run"
        description: "Run-mode tumble rate"
        default_value: 1.0
        unit:                          # ontology-mapped to UO
          value: "per second"
          iri: "http://purl.obolibrary.org/obo/UO_0000106"
          ontology_label: "per second"
          ontology: "uo"
          mapping_confidence: high
        biological_meaning:            # ontology-mapped to GO/SBO when applicable
          value: "rotational diffusion rate"
          iri: ...
        source: ...
        confidence: ...
    initial_conditions:                # populations, fields, state files
      - name: "initial_agent_count"
        value: 100
        unit: { ... }
        source: ...
    data_inputs:                       # external files
      - name: "ligand_field.csv"
        purpose: ...
        format:                        # ontology-mapped to EDAM:format
          value: "CSV"
          iri: "http://edamontology.org/format_3752"
          ontology_label: "Comma-separated values"
          ontology: "edam"
        required: true | false
        source: ...
  outputs:
    - name: "agent_trajectories"
      description: "Position over time for each agent"
      quantity_kind:                   # ontology-mapped to GO/SBO/SIO
        value: "spatial position"
        iri: ...
      unit: { ... }                    # UO
      format: { ... }                  # EDAM:format
      destination: "output/<timestamp>/"
      source: ...
  experiment_protocol:                 # MIASE-style: how a typical run is set up
    description: ...
    timestep: { value, unit, source, confidence }
    duration: { value, unit, source, confidence }
    observables: [ ... ]
    source: ...
```

## `provenance`

```yaml
provenance:
  annotated_at: "2026-05-13T12:00:00Z"
  annotated_by: "biomodel-annotator/0.1 via Claude"
  source_root: "/path/or/url"
  files_inspected:
    - "README.md"
    - "pyproject.toml"
    - "vivarium_chemotaxis/experiments/run_chemotaxis.py"
  ontology_lookups:
    service: "EBI OLS via ols-ontology MCP"
    embedding_models_available: ["llama-embed-nemotron-8b_pca512", "..."]  # what listEmbeddingModels returned this run
    embedding_fallback_used: true | false        # were any mapping_confidence: low results produced via embedding search?
  unmapped_fields:                       # required for reproducibility — every ontology-eligible field that ended with `iri: null` lands here, with the queries tried. Empty list means full coverage.
    - field_path: "model.biology.molecular_entities[0]"
      attempted_queries:
        - { ontology: "chebi", query: "methylaspartate", strategy: "lexical", hits: 5, accepted: false, reason: "all hits were stereoisomers; no canonical alpha-methyl-DL-aspartate match" }
        - { ontology: "chebi", query: "alpha-methylaspartate", strategy: "lexical", hits: 0, accepted: false, reason: "no hits" }
        - { ontology: "chebi", query: "...", strategy: "embedding", hits: 0, accepted: false, reason: "embedding fallback unavailable (no can_embed=true model)" }
  partial_annotation_scope:              # if the run intentionally annotated a subset (e.g. only one of several processes in a multi-process repo), state what was IN scope. Empty/null means full coverage.
    in_scope: ["chemotaxis/processes/chemoreceptor_cluster.py"]
    deferred:
      - path: "chemotaxis/processes/flagella_motor.py"
        reason: "same Vivarium 'defaults' pattern as chemoreceptor_cluster; deferred for token budget"
      - path: "chemotaxis/processes/coarse_motor.py"
        reason: "same pattern; deferred"
  human_review_required: true
  notes: ...
```

## Conventions reminder

- Every leaf with a `value` should also have `source` (file:line or file) and `confidence`.
- Ontology-mapped fields additionally have `iri`, `ontology_label`, `ontology`, `mapping_confidence`.
- Lists may be empty (`[]`) — emit them empty rather than omitting.
- If a whole section is determinable, set its `status` to `not_determined` and explain in `notes`.
- Use null, not empty strings, for unknown values.

## Strict definitions for `mapping_confidence` (reproducibility-critical)

Every ontology-eligible value MUST be attempted. The four values have *exact* meanings — they are not interchangeable:

| value | meaning |
|---|---|
| `high` | OLS returned a hit whose canonical label matches the input term exactly (case-insensitive, ignoring trailing punctuation). |
| `medium` | OLS returned a close match (lexical) requiring a judgment call — e.g. plural vs singular, hyphenation, near-synonym. |
| `low` | Hit came from the embedding fallback (`searchClassesWithEmbeddingModel`), not lexical. |
| `none` | Lexical search was attempted (and, if available, embedding fallback was attempted), and no acceptable hit was found. The `unmapped_fields` block in provenance MUST record this attempt with at least one query. |

**`mapping_confidence: none` does NOT mean "I didn't try."** If a field was not attempted (e.g. due to budget), it must not appear in the output at all — instead, the containing scope (process, section, file) must be listed in `provenance.partial_annotation_scope.deferred` with a reason. This separation makes the output reproducible: two runs over the same input must produce the same `mapping_confidence` distribution, modulo OLS service changes.
