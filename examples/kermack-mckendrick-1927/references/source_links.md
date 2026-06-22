# Source Links — Kermack-McKendrick SIR (1927)

Sources consulted during Passes 0–2 (Phase 10 rerun, 2026-06-22).
All content derived from training-data knowledge (paper not locally available).
Line/equation citations follow the original paper structure.

## Primary sources

| Source | Type | Accessed via | Key content extracted |
|---|---|---|---|
| Kermack & McKendrick (1927) | Published paper | Training-data knowledge | Full model equations, authors, institution, abstract |
| BioModels BIOMD0000000018 | SBML model entry | Training-data knowledge | SBML format, version, simulator compatibility |

## Paper structure references

| Citation | Content | Used for |
|---|---|---|
| Paper title | "A Contribution to the Mathematical Theory of Epidemics" | `model.name`, `model.publications` |
| Paper header | Author names, affiliation | `model.authors` |
| pp. 700–701, Abstract | Model description and epidemic threshold | `model.short_description`, `model.long_description` |
| pp. 700–702 | Introduction of S/I/R compartmental structure | `model.model_class` source |
| Equations (1)–(3) | dS/dt = -kSI, dI/dt = kSI − lI, dR/dt = lI | `model.formalism` source |
| Equations (1)–(34), Sections I–IV | Full mathematical development | `model.long_description` |
| Equation (1), −kSI term | Transmission rate term | `biology.biological_processes[0]` |
| Equation (3), lI term | Removal/recovery rate term | `biology.biological_processes[1]` |

## Ontology mapping status (Pass 4 deferred)

| Field | Planned ontology | Status |
|---|---|---|
| `model.model_class[0]` | MAMO | Deferred — `ols-ontology` MCP not connected |
| `model.formalism[0]` | MAMO | Deferred |
| `model.biology.health_condition[0]` | MONDO | Deferred |
| `model.biology.topic_category[0]` | EDAM | Deferred |
| `model.biology.biological_processes[0]` | GO | Deferred |
| `model.biology.biological_processes[1]` | GO | Deferred |
| `execution.language` | EDAM | Deferred |

## Registry fields

| Field | Value | Source |
|---|---|---|
| `name` | `kermack-mckendrick-sir-1927` | Assigned (slug) |
| `source_repository` | `https://www.ebi.ac.uk/biomodels/BIOMD0000000018` | BioModels database |
| `execution_type` | `other` | No standard execution type matches paper-described ODE model |

## Phase 10 corrections vs Phase 8

| Item | Phase 8 | Phase 10 |
|---|---|---|
| `license.spdx_id` | `LicenseRef-PublicDomain` | `LicenseRef-PublicDomain-US` |
| `license.source` | "UK life+70 period also expired (McKendrick d.1943, Kermack d.1970)" — incorrect for Kermack | Corrected: Kermack d.1970 → UK copyright expiry 2040; US public domain (pre-1928) only confirmed |
| `authors[*].affiliation` | "Royal College of Physicians of Edinburgh" | "Royal College of Physicians' Laboratory, Edinburgh" (possessive; matches paper header) |
