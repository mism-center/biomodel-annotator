The OLS ontology lookup tools (the `ols-ontology` MCP referenced by the
biomodel-annotator skill) are provided here as native tools named:
`searchClasses`, `fetch`, `listEmbeddingModels`, `searchClassesWithEmbeddingModel`.
When SKILL.md or references/ontologies.md mention `ols-ontology:<tool>`, call the
bare-named tool instead (drop the `ols-ontology:` prefix). `searchClasses` returns
hits whose `id` field is the exact handle to pass to `fetch`.

`uv` is preconfigured (UV_PYTHON_INSTALL_DIR and UV_CACHE_DIR point to an
exec-safe location baked into the image). Run the validation gate exactly as
SKILL.md shows — `uv run <skill-dir>/scripts/validate.py ...`. Do NOT set
UV_CACHE_DIR or UV_PYTHON_INSTALL_DIR yourself; pointing them at /tmp fails
because /tmp is mounted noexec.
