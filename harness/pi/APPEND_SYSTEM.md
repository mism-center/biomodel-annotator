The OLS ontology lookup tools (the `ols-ontology` MCP referenced by the
biomodel-annotator skill) are provided here as native tools named:
`searchClasses`, `fetch`, `listEmbeddingModels`, `searchClassesWithEmbeddingModel`.
When SKILL.md or references/ontologies.md mention `ols-ontology:<tool>`, call the
bare-named tool instead (drop the `ols-ontology:` prefix). `searchClasses` returns
hits whose `id` field is the exact handle to pass to `fetch`.

`paper_fetch` is the tool SKILL.md means when it says to read a paper you have
found cited in the model's files. Pass the DOI or URL exactly as it appears in
the source. There is no general web-fetch tool here, and `curl` via bash is not
a substitute: publisher sites (MDPI, Elsevier, Springer) return 403 to
non-browser clients, so fetching a landing page yields an error page rather than
the paper.

`uv` is preconfigured (UV_PYTHON_INSTALL_DIR and UV_CACHE_DIR point to an
exec-safe location baked into the image). Run the validation gate exactly as
SKILL.md shows — `uv run <skill-dir>/scripts/validate.py ...`. Do NOT set
UV_CACHE_DIR or UV_PYTHON_INSTALL_DIR yourself; pointing them at /tmp fails
because /tmp is mounted noexec.
