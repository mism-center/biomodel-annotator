The OLS ontology lookup tools (the `ols-ontology` MCP referenced by the
biomodel-annotator skill) are provided here as native tools named:
`searchClasses`, `fetch`, `listEmbeddingModels`, `searchClassesWithEmbeddingModel`.
When SKILL.md or references/ontologies.md mention `ols-ontology:<tool>`, call the
bare-named tool instead (drop the `ols-ontology:` prefix). `searchClasses` returns
hits whose `id` field is the exact handle to pass to `fetch`.
