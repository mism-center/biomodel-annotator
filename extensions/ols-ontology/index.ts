/**
 * ols-ontology — pi-coding-agent extension
 *
 * Wraps the EBI OLS4 REST API to expose the four tool calls that
 * biomodel-annotator SKILL.md expects from the ols-ontology MCP server
 * during Pass 4 (ontology mapping).
 *
 * pi-coding-agent has no native MCP client, so this extension provides
 * equivalent tools under Anthropic-API-valid names (underscores instead
 * of the MCP colon separator):
 *
 *   SKILL.md expects                               → registered name
 *   ols-ontology:listEmbeddingModels              → ols_ontology_listEmbeddingModels
 *   ols-ontology:searchClasses                    → ols_ontology_searchClasses
 *   ols-ontology:searchClassesWithEmbeddingModel  → ols_ontology_searchClassesWithEmbeddingModel
 *   ols-ontology:fetch                            → ols_ontology_fetch
 *
 * Names use underscores only (no dashes) because the OpenAI Responses API
 * requires ^[a-zA-Z0-9_]+$ for tool names — dashes are rejected.
 * Each tool description includes the SKILL.md name so the LLM maps correctly.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "@earendil-works/pi-ai";

const OLS4_BASE = "https://www.ebi.ac.uk/ols4/api";

async function olsGet(path: string): Promise<unknown> {
	const resp = await fetch(`${OLS4_BASE}${path}`, {
		headers: { Accept: "application/json" },
	});
	if (!resp.ok) {
		throw new Error(`OLS4 request failed: ${resp.status} ${resp.statusText} — ${OLS4_BASE}${path}`);
	}
	return resp.json();
}

export default function (pi: ExtensionAPI) {
	// ── 1. listEmbeddingModels ──────────────────────────────────────────────
	pi.registerTool({
		name: "ols_ontology_listEmbeddingModels",
		label: "OLS: List Embedding Models",
		description:
			"Equivalent to ols-ontology:listEmbeddingModels. " +
			"Probes whether semantic embedding search is available in this OLS deployment. " +
			"Call once at the very start of Pass 4 before any searchClasses calls. " +
			"In REST-proxy mode, embedding models are never available (can_embed: false).",
		promptSnippet:
			"Use ols_ontology_listEmbeddingModels in place of ols-ontology:listEmbeddingModels " +
			"at the start of Pass 4.",
		parameters: Type.Object({}),
		async execute() {
			// The EBI OLS4 REST API does not expose embedding models.
			// Report can_embed: false so Pass 4 skips the embedding fallback step.
			const models = [{ model: "rest-api-proxy", can_embed: false }];
			return {
				content: [{ type: "text" as const, text: JSON.stringify(models, null, 2) }],
				details: { models },
			};
		},
	});

	// ── 2. searchClasses ────────────────────────────────────────────────────
	pi.registerTool({
		name: "ols_ontology_searchClasses",
		label: "OLS: Search Classes",
		description:
			"Equivalent to ols-ontology:searchClasses. " +
			"Lexical search for ontology classes in EBI OLS4. " +
			"Use for every mappable term in Pass 4. " +
			"Provide the term as query and the target ontology as ontologyId. " +
			"ontologyId values: mamo, go, chebi, ncbitaxon, swo, uo, sbo, edam, sio, cl, uberon, kisao.",
		promptSnippet:
			"Use ols_ontology_searchClasses in place of ols-ontology:searchClasses during Pass 4 " +
			"ontology mapping. Always set ontologyId from references/ontologies.md.",
		parameters: Type.Object({
			query: Type.String({
				description: "Term to search (e.g. 'agent-based model', 'Escherichia coli', 'second')",
			}),
			ontologyId: Type.String({
				description:
					"OLS ontology ID to scope the search (e.g. 'mamo', 'go', 'chebi', 'ncbitaxon', 'uo')",
			}),
			pageSize: Type.Optional(
				Type.Number({ description: "Max results to return (default 5)" }),
			),
		}),
		async execute(_id, params) {
			const rows = params.pageSize ?? 5;
			const qs = new URLSearchParams({
				q: params.query,
				ontology: params.ontologyId,
				rows: String(rows),
				fieldList: "label,iri,obo_id,description,synonym,is_obsolete",
				type: "class",
			});
			const data = (await olsGet(`/search?${qs}`)) as {
				response?: { numFound?: number; docs?: unknown[] };
			};
			const docs = data?.response?.docs ?? [];
			const numFound = data?.response?.numFound ?? 0;
			return {
				content: [
					{
						type: "text" as const,
						text: JSON.stringify({ numFound, docs }, null, 2),
					},
				],
				details: { numFound, returned: docs.length, query: params.query, ontologyId: params.ontologyId },
			};
		},
	});

	// ── 3. searchClassesWithEmbeddingModel ──────────────────────────────────
	pi.registerTool({
		name: "ols_ontology_searchClassesWithEmbeddingModel",
		label: "OLS: Semantic Search (Embedding)",
		description:
			"Equivalent to ols-ontology:searchClassesWithEmbeddingModel. " +
			"Semantic embedding search — NOT available via OLS4 REST API. " +
			"Always returns empty results. " +
			"Only call if listEmbeddingModels returned can_embed: true (it never will in this deployment). " +
			"When this returns empty, proceed directly to step 4: set mapping_confidence: none and record the attempt.",
		parameters: Type.Object({
			query: Type.String({ description: "Semantic search query" }),
			model: Type.String({ description: "Embedding model ID from listEmbeddingModels" }),
			ontologyId: Type.String({ description: "OLS ontology ID" }),
		}),
		async execute() {
			return {
				content: [
					{
						type: "text" as const,
						text: JSON.stringify(
							{
								docs: [],
								message:
									"Embedding search is unavailable in REST-proxy mode. " +
									"Proceed to step 4: leave iri: null, set mapping_confidence: none, " +
									"and record the attempt in provenance.unmapped_fields.",
							},
							null,
							2,
						),
					},
				],
				details: { available: false },
			};
		},
	});

	// ── 4. fetch ────────────────────────────────────────────────────────────
	pi.registerTool({
		name: "ols_ontology_fetch",
		label: "OLS: Fetch Term",
		description:
			"Equivalent to ols-ontology:fetch. " +
			"Retrieves full details for a single OLS term. " +
			"id format: 'ontologyId+IRI' (e.g. 'mamo+http://identifiers.org/mamo/MAMO_0000028') " +
			"or a plain IRI string.",
		parameters: Type.Object({
			id: Type.String({
				description:
					"Compound OLS ID in the form 'ontologyId+IRI' " +
					"(e.g. 'mamo+http://identifiers.org/mamo/MAMO_0000028') or a plain IRI.",
			}),
		}),
		async execute(_callId, params) {
			const plusIdx = params.id.indexOf("+");
			let ontologyId: string | null = null;
			let iri = params.id;

			if (plusIdx > 0) {
				ontologyId = params.id.slice(0, plusIdx);
				iri = params.id.slice(plusIdx + 1);
			}

			// OLS4 terms endpoint accepts IRI as a single-encoded query parameter.
			const encodedIri = encodeURIComponent(iri);
			const path = ontologyId
				? `/ontologies/${ontologyId}/terms?iri=${encodedIri}`
				: `/terms?iri=${encodedIri}`;

			const data = await olsGet(path);
			return {
				content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
				details: { iri, ontologyId },
			};
		},
	});
}
