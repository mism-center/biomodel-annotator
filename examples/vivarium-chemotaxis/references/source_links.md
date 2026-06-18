# Source References

All source files read to produce `outputs/annotation.yaml` for vivarium-chemotaxis.
Passes executed: 0 (Inventory), 1 (Identity/biology), 2 (Execution environment).
Passes deferred: 3 (I/O), 4 (Ontology mapping — ols-ontology MCP not connected).

---

## Pass 0 — Inventory

**Enumeration method:** directory tree, 53 files (excluding .git, __pycache__)

| File | Present | Notes |
|---|---|---|
| `README.md` | Yes | Primary documentation |
| `setup.py` | Yes | Package metadata and dependencies |
| `requirements.txt` | Yes | `-e .` only |
| `pytest.ini` | Yes | Test configuration |
| `LICENSE` | Yes | MIT, Copyright 2020 Vivarium Collective |
| `doc/references.bib` | Yes | BibTeX bibliography |
| `chemotaxis/data/fasta/` | Yes | E. coli K-12 MG1655 FASTA (confirms strain) |
| `CITATION.cff` | No | — |
| `pyproject.toml` | No | — |
| `Dockerfile` | No | — |
| `*.sbml / *.cellml` | No | Python-only; no exchange format files |

---

## Pass 1 — Files Read (Model Identity / Biology)

| File | Lines read | Key findings |
|---|---|---|
| `README.md` | Full (82 lines) | Name (L1), description (L2-4), Python (L29), pip (L37), entry points (L49-50, L55, L63, L68-72) |
| `setup.py` | Full (31 lines) | version='0.0.2' (L13), author (L19), author_email (L20), url (L21), license='MIT' (L22), install_requires (L27-30) |
| `LICENSE` | Full | MIT, Copyright 2020 Vivarium Collective |
| `chemotaxis/processes/chemoreceptor_cluster.py` | 1-139 | ReceptorCluster (L49), MWC model (L54-60), DEFAULT_LIGAND='MeAsp' (L26), CheR=0.00016/CheB=0.00028 (L103-104) |
| `chemotaxis/processes/flagella_motor.py` | 1-110 | FlagellaMotor (L30), stochastic model/Sneddon 2012 (L44-46), expected_pmf=-140 (L50), expected_flagella=4 (L51), k_y=100/k_z=30 (L57-58) |
| `chemotaxis/processes/coarse_motor.py` | 1-100 | MotorActivity (L27), time_step=0.1 (L49), mb_0=0.65 (L60), n_motors=5 (L61) |
| `chemotaxis/processes/membrane_potential.py` | 1-100 | MembranePotential (L27), GHK equations, scipy.constants (L10) |
| `chemotaxis/composites/chemotaxis_master.py` | 1-100 | ChemotaxisMaster (L74), iAF1260b import confirming E. coli K-12 (L23) |

---

## Pass 2 — Files Read (Execution Environment)

| File | Lines read | Key findings |
|---|---|---|
| `setup.py` | Reused from Pass 1 | vivarium-cell==0.0.23 (L27), vivarium-core==0.0.34 (L28), pymunk==5.6.0 (L29), numpy (L30) |
| `requirements.txt` | Full (1 line) | `-e .` — editable install only |
| `pytest.ini` | Full (6 lines) | pytest framework (L1), addopts=--doctest-modules --strict-markers (L3), testpaths=chemotaxis (L5), slow marker (L6) |
| `chemotaxis/composites/chemotaxis_minimal.py` | 1-90 | ChemotaxisMinimal (L27), ReceptorCluster + MotorActivity, time_step=0.1, test_chemotaxis_minimal total_time=10 |

---

## README.md Entry Points (verbatim)

The following commands appear in `README.md`. Commands are recorded verbatim, including typos.

| Line | Command | Notes |
|---|---|---|
| L49-50 | `python chemotaxis/processes/chemoreptor_cluster.py` | Typo: 'chemoreptor' — correct filename is chemoreceptor_cluster.py |
| L55 | `python chemotaxis/processes/flagella_motor.py` | — |
| L63 | `python chemotaxis/composites/chemotaxis_minimal.py` | Primary annotation scope |
| L68/L72 | `pytest` / `pytest -m 'not slow'` | pytest.ini testpaths=chemotaxis |

---

## Primary Publication

| Field | Value |
|---|---|
| Title | A Multi-Scale Approach to Modeling E. coli Chemotaxis |
| Authors | Agmon, E.; Spangler, R.K. |
| Journal | Entropy |
| Year | 2020 |
| Volume/Issue/Article | 22(10):1101 |
| DOI | 10.3390/e22101101 |
| Source in repo | setup.py:21 (url field) |

---

## Ontology Mapping Status

**Pass 4 was not executed.** The ols-ontology MCP server was not connected in this session.

All `iri:` fields in `outputs/annotation.yaml` are `null`. No OLS queries were attempted.
Fields requiring ontology lookup are listed in `provenance.partial_annotation_scope.deferred`,
not in `provenance.unmapped_fields` (which would imply failed attempts).

| Field | Target ontology | Status |
|---|---|---|
| model.model_class[0] | MAMO | Deferred (Pass 4) |
| model.formalism[0] | MAMO | Deferred (Pass 4) |
| model.formalism[1] | MAMO | Deferred (Pass 4) |
| model.biology.species[0] | NCBITaxon | Deferred (Pass 4) |
| model.biology.biological_processes[0-3] | GO | Deferred (Pass 4) |
| model.biology.cell_types[0] | CL | Deferred (Pass 4) |
| model.biology.proteins_genes | UniProt | Deferred (Pass 4) |
| execution.language | SWO | Deferred (Pass 4) |

---

## Process-Level Citations (from source files)

These citations appear within the source code and were identified during Pass 1 reading.
They are not verified against external sources in this session.

| Process file | Citation found | Location |
|---|---|---|
| `chemoreceptor_cluster.py` | Endres & Wingreen (2006), PNAS — MWC receptor model | Docstring |
| `flagella_motor.py` | Kollmann et al. (2005), Nature — CheY phosphorylation | L57-58 comments |
| `flagella_motor.py` | Sneddon et al. (2012) — stochastic motor model | L44-46 |
| `flagella_motor.py` | Mears et al. (2014), eLife — veto model | L44-46 |
| `flagella_motor.py` | Berg (2004), E. coli in Motion — PMF reference | L50 comment |
| `coarse_motor.py` | Vladimirov et al. (2008) — gradient sensitivity | Comments |
| `coarse_motor.py` | Scharf et al. (1998), PNAS — motor switching | Comments |
| `coarse_motor.py` | Cluzel et al. (2000), Science — steady-state bias 0.65 | L60 (mb_0=0.65) |
