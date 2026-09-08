/**
 * paper-fetch — pi-coding-agent extension
 *
 * Gives the biomodel-annotator skill the ability to read a paper it has already
 * found in a model's files. pi's built-in tools are bash/read/edit/write only,
 * so without this the agent can locate a DOI or paper URL but never see what is
 * at it. (Under Claude Code the host's own web-fetch tool covers this; the
 * extension exists for the container harness.)
 *
 *   registered name → paper_fetch
 *
 * Scope: transport and format conversion, nothing else. It does not decide
 * which fields of a record matter, does not classify sections, and does not
 * summarise — records are passed through whole and full text is converted to
 * readable text with its headings and tables intact, for the agent to read.
 *
 * Fetching the publisher page directly is not a reliable route to a paper's
 * contents: MDPI, Elsevier and Springer return 403 to non-browser clients
 * (MDPI blocks at the CDN edge, so no User-Agent gets through), and a doi.org
 * link redirects onto the same wall. The scholarly APIs are not gated, so
 * resolution goes:
 *
 *   1. doi.org content negotiation  → the CSL record, passed through whole
 *   2. Europe PMC                   → the article record, passed through whole
 *   3. Europe PMC fullTextXML       → full text, open-access subset only
 *   4. direct HTTP                  → fallback for non-hostile hosts
 *
 * Names use underscores only (no dashes): the OpenAI Responses API requires
 * ^[a-zA-Z0-9_]+$ for tool names.
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "@earendil-works/pi-ai";

const DOI_RESOLVER = "https://doi.org";
const EUROPEPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest";
const FETCH_TIMEOUT_MS = 20000;
const DEFAULT_LIMIT = 60000;
const USER_AGENT = "biomodel-annotator/0.1 (+https://github.com/mism-center/biomodel-annotator)";

// In-session cache: a paper cited in both README and CITATION.cff is otherwise
// fetched twice in one annotation run.
const paperCache = new Map<string, unknown>();

type FetchAttempt = { service: string; url: string; ok: boolean; detail?: string };

async function httpGet(url: string, accept: string) {
	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
	try {
		const resp = await fetch(url, {
			headers: { Accept: accept, "User-Agent": USER_AGENT },
			redirect: "follow",
			signal: controller.signal,
		});
		return { body: resp.ok ? await resp.text() : "", status: resp.status };
	} finally {
		clearTimeout(timer);
	}
}

async function httpGetRetrying(url: string, accept: string) {
	try {
		return await httpGet(url, accept);
	} catch (err) {
		if (err instanceof Error && (err.name === "AbortError" || err.name === "TypeError")) {
			return await httpGet(url, accept);
		}
		throw err;
	}
}

/** Reduce any DOI spelling to its bare, lowercase form. */
function normalizeDoi(raw: string): string {
	let s = (raw ?? "").trim().replace(/^[([{<"'\s]+/, "");
	s = s.replace(/^(?:https?:\/\/)?(?:dx\.|www\.)?doi\.org\//i, "").replace(/^doi:/i, "");
	s = s.replace(/[>"']+$/, "").replace(/[.,;:]+$/, "");
	while (s.endsWith(")") && (s.match(/\(/g)?.length ?? 0) < (s.match(/\)/g)?.length ?? 0)) {
		s = s.slice(0, -1).replace(/[.,;:]+$/, "");
	}
	// A DOI-badge image URL otherwise yields a second, non-resolving DOI.
	s = s.replace(/\.(?:svg|png|jpe?g|gif|webp)$/i, "");
	return s.toLowerCase();
}

function extractDoi(input: string): string {
	const direct = normalizeDoi(input);
	if (/^10\.\d{4,9}\/\S+$/.test(direct)) return direct;
	const embedded = input.match(/10\.\d{4,9}\/[^\s"'<>{}|\\^\]]+/);
	return embedded ? normalizeDoi(embedded[0]) : "";
}

function decodeEntities(s: string): string {
	return s
		.replace(/&(?:nbsp|#160);/g, " ")
		.replace(/&lt;/g, "<")
		.replace(/&gt;/g, ">")
		.replace(/&quot;/g, '"')
		.replace(/&#39;|&apos;/g, "'")
		.replace(/&amp;/g, "&");
}

/**
 * Convert JATS/HTML to readable text, preserving the document's structure.
 *
 * Headings become `## `-prefixed lines and table rows keep their cells, so the
 * agent can navigate the paper and read parameter tables. Only non-content
 * elements are dropped — nothing is summarised or classified here.
 */
function markupToText(markup: string): string {
	return (
		decodeEntities(
			markup
				.replace(/<!--[\s\S]*?-->/g, " ")
				.replace(/<\?[\s\S]*?\?>/g, " ")
				.replace(/<(script|style|noscript|svg)\b[^>]*>[\s\S]*?<\/\1>/gi, " ")
				.replace(/<(?:title|article-title|h[1-6])\b[^>]*>/gi, "\n\n## ")
				.replace(/<\/(?:title|article-title|h[1-6])>/gi, "\n")
				.replace(/<\/(?:p|sec|abstract|list-item|li|div|caption)>/gi, "\n")
				.replace(/<\/(?:tr|table-row)>/gi, "\n")
				.replace(/<(?:td|th|table-cell)\b[^>]*>/gi, " | ")
				.replace(/<[^>]+>/g, " "),
		)
			// Collapse runs of spaces/tabs but keep paragraph breaks.
			.replace(/[ \t ]+/g, " ")
			.replace(/ *\n */g, "\n")
			.replace(/\n{3,}/g, "\n\n")
			.trim()
	);
}

function jsonOrNull(body: string): unknown {
	try {
		return JSON.parse(body);
	} catch {
		return null;
	}
}

export default function (pi: ExtensionAPI) {
	pi.registerTool({
		name: "paper_fetch",
		label: "Fetch Paper",
		description:
			"Retrieve a journal paper, preprint or report that you have already found referenced " +
			"in the model's files, so you can read it. Accepts a DOI ('10.3390/e22101101'), a " +
			"doi.org link, or any paper URL (publisher landing page, PubMed, arXiv, bioRxiv).\n\n" +
			"Returns the bibliographic records verbatim (the CSL record from doi.org and the " +
			"Europe PMC article record, both passed through unabridged) and, with " +
			"include='fulltext', the paper's full text as readable text with headings and " +
			"tables preserved. It does not interpret or summarise anything — read the returned " +
			"content and extract what you need yourself. Funding, acknowledgements, methods and " +
			"parameter tables are all in the full text; the abstract alone will not contain them.\n\n" +
			"Publisher pages often refuse non-browser clients (HTTP 403); when that happens the " +
			"result says so in `attempts` and still returns whatever the scholarly APIs supplied. " +
			"Pass `title` whenever the source prints one — for a URL with no DOI it is the only " +
			"thing that will resolve the paper.",
		promptSnippet:
			"Use paper_fetch to read any paper cited in the model's files. Pass the DOI or URL as " +
			"printed, plus `title` if the source gives one, and include='fulltext' when you need " +
			"anything beyond the abstract (funding, methods, parameter values). Read the returned " +
			"text yourself rather than expecting pre-extracted fields.",
		parameters: Type.Object({
			url: Type.String({
				description:
					"A DOI, doi.org link, or paper URL exactly as it appears in the model's files.",
			}),
			title: Type.Optional(
				Type.String({
					description:
						"The paper's title as printed in the model's files. Supply it whenever the " +
						"source gives one: for a landing-page URL with no DOI it is the only route " +
						"to the paper, and it costs nothing since you have already read it.",
				}),
			),
			include: Type.Optional(
				Type.String({
					description:
						"'metadata' (default) returns the bibliographic records only. 'fulltext' also " +
						"returns the paper's body text, available for open-access papers.",
				}),
			),
			offset: Type.Optional(
				Type.Number({ description: "Character offset into the full text (default 0)." }),
			),
			limit: Type.Optional(
				Type.Number({
					description:
						`Characters of full text to return (default ${DEFAULT_LIMIT}). The response ` +
						"always reports total_chars and next_offset, so nothing is lost silently — " +
						"page through with offset if the paper is longer than one call.",
				}),
			),
		}),
		async execute(_id, params) {
			const wantFullText = (params.include ?? "metadata").toLowerCase() === "fulltext";
			const offset = Math.max(0, params.offset ?? 0);
			const limit = Math.max(1, params.limit ?? DEFAULT_LIMIT);
			const cacheKey = `${params.url}::${params.title ?? ""}::${wantFullText}::${offset}::${limit}`;

			const cached = paperCache.get(cacheKey);
			if (cached) {
				return {
					content: [{ type: "text" as const, text: JSON.stringify({ ...cached, cached: true }, null, 2) }],
					details: { url: params.url, cached: true },
				};
			}

			const attempts: FetchAttempt[] = [];
			let doi = extractDoi(params.url);
			let csl: unknown = null;
			let europepmc: Record<string, unknown> | null = null;
			let candidates: Record<string, unknown>[] = [];

			// A landing-page URL carrying no DOI is the common case, and the page
			// itself is often edge-blocked, so look the paper up by its title. The
			// candidates are returned for the agent to judge; only an unambiguous
			// single hit is followed automatically.
			if (!doi && params.title) {
				const url =
					`${EUROPEPMC}/search?query=${encodeURIComponent(`TITLE:"${params.title}"`)}` +
					`&format=json&resultType=core&pageSize=5`;
				try {
					const resp = await httpGetRetrying(url, "application/json");
					const hits = ((jsonOrNull(resp.body) as Record<string, any>)?.resultList?.result ??
						[]) as Record<string, unknown>[];
					candidates = hits;
					if (hits.length === 1) {
						europepmc = hits[0];
						doi = normalizeDoi(String(hits[0].doi ?? ""));
					}
					attempts.push({
						service: "europepmc/title",
						url,
						ok: hits.length > 0,
						detail:
							hits.length === 1
								? "one unambiguous hit, used"
								: hits.length > 1
									? `${hits.length} candidates returned in title_search_candidates — ` +
										"pick one and re-call with its DOI"
									: "no record",
					});
				} catch (err) {
					attempts.push({ service: "europepmc/title", url, ok: false, detail: String(err) });
				}
			}

			if (doi) {
				const url = `${DOI_RESOLVER}/${doi}`;
				try {
					const resp = await httpGetRetrying(url, "application/vnd.citationstyles.csl+json");
					if (resp.status === 200) {
						csl = jsonOrNull(resp.body);
						attempts.push({ service: "doi.org", url, ok: csl !== null });
					} else {
						attempts.push({
							service: "doi.org",
							url,
							ok: false,
							detail:
								resp.status === 404
									? "DOI is not registered — check it was transcribed correctly"
									: `HTTP ${resp.status}`,
						});
					}
				} catch (err) {
					attempts.push({ service: "doi.org", url, ok: false, detail: String(err) });
				}
			}

			// The Europe PMC record carries the PMID/PMCID crosswalk, which is what
			// gates full-text availability, plus an abstract when the DOI record
			// lacks one.
			if (doi && !europepmc) {
				const url =
					`${EUROPEPMC}/search?query=${encodeURIComponent(`DOI:"${doi}"`)}` +
					`&format=json&resultType=core&pageSize=1`;
				try {
					const resp = await httpGetRetrying(url, "application/json");
					const hit = ((jsonOrNull(resp.body) as Record<string, any>)?.resultList?.result ??
						[])[0] as Record<string, unknown> | undefined;
					europepmc = hit ?? null;
					attempts.push({ service: "europepmc", url, ok: Boolean(hit), detail: hit ? undefined : "no record" });
				} catch (err) {
					attempts.push({ service: "europepmc", url, ok: false, detail: String(err) });
				}
			}

			const pmcid = String(europepmc?.pmcid ?? "");
			const openAccess = String(europepmc?.isOpenAccess ?? "") === "Y";

			let fullText: string | null = null;
			let totalChars = 0;
			if (wantFullText && pmcid && openAccess) {
				const url = `${EUROPEPMC}/${pmcid}/fullTextXML`;
				try {
					const resp = await httpGetRetrying(url, "application/xml");
					if (resp.status === 200 && resp.body) {
						const text = markupToText(resp.body);
						totalChars = text.length;
						fullText = text.slice(offset, offset + limit);
						attempts.push({ service: "europepmc/fullTextXML", url, ok: true });
					} else {
						attempts.push({ service: "europepmc/fullTextXML", url, ok: false, detail: `HTTP ${resp.status}` });
					}
				} catch (err) {
					attempts.push({ service: "europepmc/fullTextXML", url, ok: false, detail: String(err) });
				}
			} else if (wantFullText) {
				attempts.push({
					service: "europepmc/fullTextXML",
					url: "",
					ok: false,
					detail: pmcid
						? "not in the open-access subset; full text is unavailable"
						: "no PMCID; full text is unavailable",
				});
			}

			// Last resort for a URL the scholarly APIs could not account for.
			if (!csl && !europepmc && /^https?:\/\//i.test(params.url)) {
				try {
					const resp = await httpGetRetrying(params.url, "text/html");
					if (resp.status === 200 && resp.body) {
						const text = markupToText(resp.body);
						totalChars = text.length;
						fullText = text.slice(offset, offset + limit);
						attempts.push({ service: "direct", url: params.url, ok: true });
					} else {
						attempts.push({
							service: "direct",
							url: params.url,
							ok: false,
							detail:
								resp.status === 403
									? "publisher refused a non-browser client (403); use the DOI or pass title"
									: `HTTP ${resp.status}`,
						});
					}
				} catch (err) {
					attempts.push({ service: "direct", url: params.url, ok: false, detail: String(err) });
				}
			}

			const nextOffset = offset + (fullText?.length ?? 0);
			const result = {
				status: csl || europepmc || fullText ? "ok" : "unavailable",
				requested: params.url,
				doi: doi || null,
				pmid: String(europepmc?.pmid ?? "") || null,
				pmcid: pmcid || null,
				open_access: openAccess,
				full_text_available: Boolean(pmcid && openAccess),
				csl,
				europepmc,
				title_search_candidates: candidates.length > 1 ? candidates : undefined,
				full_text: fullText,
				full_text_chars_returned: fullText?.length ?? 0,
				full_text_total_chars: totalChars,
				full_text_next_offset: totalChars > nextOffset ? nextOffset : null,
				attempts,
			};

			paperCache.set(cacheKey, result);
			return {
				content: [{ type: "text" as const, text: JSON.stringify(result, null, 2) }],
				details: {
					url: params.url,
					doi: result.doi,
					status: result.status,
					full_text_chars: result.full_text_chars_returned,
				},
			};
		},
	});
}
