/**
 * stream-output — pi-coding-agent extension for biomodel-annotator
 *
 * Provides two tools for reading and summarizing the assembled annotation
 * package (metadata-package/) during Assembly step 6:
 *
 *   stream_output_readPackage         — reads all three package files in one call
 *   stream_output_confidenceSummary   — counts confidence levels and lists fields needing review
 *
 * Both tools are called after the package is written and the validation gate
 * (uv run scripts/validate.py) has passed, so the agent can present a concise
 * summary to the user without making multiple sequential Read calls.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "@earendil-works/pi-ai";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

function readPackageFile(packageDir: string, filename: string): string | null {
	const filePath = join(packageDir, filename);
	return existsSync(filePath) ? readFileSync(filePath, "utf-8") : null;
}

interface ConfidenceCounts {
	confidence: { high: number; medium: number; inferred: number; none: number; total: number };
	mapping_confidence: { high: number; medium: number; low: number; none: number };
	fields_needing_review: string[];
}

function parseConfidences(yamlText: string): ConfidenceCounts {
	const conf = { high: 0, medium: 0, inferred: 0, none: 0, total: 0 };
	const mapping = { high: 0, medium: 0, low: 0, none: 0 };
	const fieldsNeedingReview: string[] = [];

	const lines = yamlText.split("\n");

	for (let i = 0; i < lines.length; i++) {
		const line = lines[i];

		// mapping_confidence must be checked before confidence to avoid double-counting.
		const mappingMatch = line.match(/mapping_confidence:\s*(\w+)/);
		if (mappingMatch) {
			const val = mappingMatch[1] as keyof typeof mapping;
			if (val in mapping) mapping[val]++;
			continue;
		}

		const confMatch = line.match(/\bconfidence:\s*(\w+)/);
		if (confMatch) {
			const val = confMatch[1] as keyof Omit<typeof conf, "total">;
			if (val in conf && val !== "total") {
				(conf[val] as number)++;
				conf.total++;

				if (val === "none") {
					// Walk back to find the parent field name, skipping known sibling keys
					// (value, source, iri, ontology_label, ontology, mapping_confidence, confidence).
					const SIBLING_KEYS = new Set([
						"value", "source", "iri", "ontology_label", "ontology",
						"confidence", "mapping_confidence",
					]);
					for (let j = i - 1; j >= Math.max(0, i - 6); j--) {
						const keyMatch = lines[j].match(/^\s*([\w_]+)\s*:/);
						if (keyMatch && !SIBLING_KEYS.has(keyMatch[1])) {
							const candidate = keyMatch[1];
							if (!fieldsNeedingReview.includes(candidate)) {
								fieldsNeedingReview.push(candidate);
							}
							break;
						}
					}
				}
			}
		}
	}

	return { confidence: conf, mapping_confidence: mapping, fields_needing_review: fieldsNeedingReview };
}

export default function (pi: ExtensionAPI) {
	// ── 1. readPackage ──────────────────────────────────────────────────────
	pi.registerTool({
		name: "stream_output_readPackage",
		label: "Read Annotation Package",
		description:
			"Reads all three files from a metadata-package/ directory " +
			"(metadata.yaml, execution.yaml, README.md) and returns their full contents " +
			"in a single response. Call this at the end of Assembly after the validation gate " +
			"passes to verify the written package before presenting it to the user.",
		promptSnippet:
			"Use stream_output_readPackage with the absolute path to metadata-package/ " +
			"after Assembly is complete and the validator exits 0. " +
			"It replaces three sequential Read calls with one tool call.",
		parameters: Type.Object({
			packageDir: Type.String({
				description: "Absolute path to the metadata-package/ directory (e.g. /workspace/mymodel/metadata-package)",
			}),
		}),
		async execute(_callId, params) {
			const filenames = ["metadata.yaml", "execution.yaml", "README.md"] as const;
			const files: Record<string, string | null> = {};
			const missing: string[] = [];

			for (const f of filenames) {
				const content = readPackageFile(params.packageDir, f);
				files[f] = content;
				if (content === null) missing.push(f);
			}

			const filesFound = filenames.filter((f) => files[f] !== null);

			return {
				content: [
					{
						type: "text" as const,
						text: JSON.stringify(
							{
								packageDir: params.packageDir,
								filesFound,
								filesMissing: missing,
								files,
							},
							null,
							2,
						),
					},
				],
				details: {
					filesFound: filesFound.length,
					filesMissing: missing,
				},
			};
		},
	});

	// ── 2. confidenceSummary ────────────────────────────────────────────────
	pi.registerTool({
		name: "stream_output_confidenceSummary",
		label: "Annotation Confidence Summary",
		description:
			"Parses metadata.yaml and execution.yaml from a metadata-package/ directory " +
			"and returns a breakdown of field confidence levels (high / medium / inferred / none) " +
			"and ontology mapping confidence (high / medium / low / none). " +
			"Also returns the names of fields adjacent to any 'confidence: none' lines " +
			"so the agent can tell the user which fields most need human review. " +
			"Call this during Assembly step 6 before summarizing the annotation.",
		promptSnippet:
			"Use stream_output_confidenceSummary after the validation gate passes to get a " +
			"confidence breakdown. Use the fields_needing_review list and mapping_confidence.none " +
			"count to highlight gaps in your Assembly step 6 summary to the user.",
		parameters: Type.Object({
			packageDir: Type.String({
				description: "Absolute path to the metadata-package/ directory",
			}),
		}),
		async execute(_callId, params) {
			const metadataYaml = readPackageFile(params.packageDir, "metadata.yaml") ?? "";
			const executionYaml = readPackageFile(params.packageDir, "execution.yaml") ?? "";

			if (!metadataYaml && !executionYaml) {
				return {
					content: [
						{
							type: "text" as const,
							text: JSON.stringify(
								{ error: `No YAML files found in ${params.packageDir}` },
								null,
								2,
							),
						},
					],
					details: { error: true },
				};
			}

			const result = parseConfidences(metadataYaml + "\n" + executionYaml);

			return {
				content: [
					{
						type: "text" as const,
						text: JSON.stringify(result, null, 2),
					},
				],
				details: {
					fieldsNone: result.confidence.none,
					mappingNone: result.mapping_confidence.none,
					reviewRequired: result.fields_needing_review,
				},
			};
		},
	});
}
