# biomodel-annotator

A Claude Code **skill** that turns a biological/biomedical computational model — a repo, a folder, a single SBML/CellML/BNGL/etc. file, or a GitHub URL — into a single MIRIAM-aligned YAML annotation with ontology IRIs already attached.

The output is a starting point for a human curator: every field carries a `confidence` and `source`, and every ontology-eligible term carries `mapping_confidence` plus the queries that were tried.

See [`SKILL.md`](SKILL.md) for the full workflow and [`references/schema.md`](references/schema.md) for the YAML schema this skill emits.

---

## Prerequisites

### 1. Claude Code

You need [Claude Code](https://claude.com/claude-code) installed. Skills are loaded from either:

- `~/.claude/skills/<skill-name>/` — user-level (available in every session), or
- `<project>/.claude/skills/<skill-name>/` — project-level (only in that repo).

Each skill is a directory whose root contains a `SKILL.md` file.

### 2. OLS MCP server (required for Pass 4 — ontology mapping)

Pass 4 of the workflow attaches ontology IRIs to every mappable term via the **EBI Ontology Lookup Service**. The skill calls these tools through a Model Context Protocol server it expects to find under the namespace `ols-ontology`:

- `ols-ontology:listEmbeddingModels`
- `ols-ontology:searchClasses`
- `ols-ontology:searchClassesWithEmbeddingModel`
- `ols-ontology:fetch`

Without this MCP server, the skill will still run — but every ontology-eligible field will end up `mapping_confidence: none`, and the resulting annotation will need much more human work.

**Endpoint.** EBI hosts the OLS MCP server. No local install needed.

- URL: `https://www.ebi.ac.uk/ols4/api/mcp`
- Transport: **Streamable HTTP** (not legacy SSE).

**Registering the MCP server.** Add it to your Claude Code MCP configuration *before* invoking the skill. **The registered server name must be `ols-ontology`** — that is the namespace `SKILL.md` and `references/ontologies.md` call into.

Via the Claude Code CLI:

```bash
claude mcp add --transport http ols-ontology https://www.ebi.ac.uk/ols4/api/mcp
```

Or by editing the config directly:

```jsonc
// ~/.claude.json  (user-level) or <project>/.mcp.json (project-level)
{
  "mcpServers": {
    "ols-ontology": {
      "type": "http",
      "url": "https://www.ebi.ac.uk/ols4/api/mcp"
    }
  }
}
```

Verify the server is connected before running the skill:

```bash
claude mcp list
# expect: ols-ontology  ✓ connected
```

---

## Installing the skill

Pull a release zip from the Releases page (the CI workflow in this repo publishes one on every push to `main`), and extract it into your skills directory.

### User-level install

```bash
mkdir -p ~/.claude/skills
cd ~/.claude/skills
unzip /path/to/biomodel-annotator-vX.Y.Z.zip
# Result: ~/.claude/skills/biomodel-annotator/SKILL.md
#         ~/.claude/skills/biomodel-annotator/references/{schema,ontologies}.md
```

### Project-level install

```bash
mkdir -p .claude/skills
cd .claude/skills
unzip /path/to/biomodel-annotator-vX.Y.Z.zip
```

Restart your Claude Code session (or open a new one) so the skill is picked up. The release zip contains **only** `SKILL.md` and the two `references/*.md` files — nothing else — so it will not bloat the agent context with unrelated repo files.

---

## Using the skill

Once installed and the MCP server is connected, just ask Claude Code:

```
Annotate the model at /path/to/some/model-repo.
```

Other phrasings that trigger the skill:

- "What does this repo do? Give me a catalog entry."
- "Extract metadata from this simulation."
- "Help me write a model card for this."
- "Do a first pass on this model — we'll review later."

Inputs accepted: a local folder path, a GitHub URL, or a single model file (e.g. one `.sbml` / `.cellml` / `.bngl` / `.sedml`).

### Output

One file, written to the working directory:

```
<model-slug>.annotation.yaml
```

Top-level sections:

| Section | Contents |
|---|---|
| `model` | Identity, biology, authors, contacts, license, references |
| `execution` | Language, deps, container, compute, entry points, tests |
| `io` | Parameters, initial conditions, data inputs, outputs |
| `provenance` | Annotation run metadata, OLS lookups, unmapped fields, deferred scope |

Every leaf field carries `value` + `source` + `confidence`. Ontology-mapped fields additionally carry `iri`, `ontology_label`, `ontology`, `mapping_confidence`. See [`references/schema.md`](references/schema.md) for the full schema and [`references/ontologies.md`](references/ontologies.md) for the per-field ontology routing.

---

## Releases

This repo ships releases via GitHub Actions on every push to `main`:

- Workflow: [`.github/workflows/release.yml`](.github/workflows/release.yml)
- Versioning: semver, auto-incremented from the latest `v*` tag. Default bump is **patch**. Include `#minor` or `#major` in the commit message to override.
- Asset: `biomodel-annotator-vX.Y.Z.zip` — strict allowlist of `SKILL.md` + `references/*.md` only. The workflow fails the build if anything else slips in.

To consume a specific version, download the corresponding asset from the Releases page and reinstall as above.

---

## Development

`src/validator.py` is a post-hoc validation utility for the annotation YAML the skill produces. It is **not** part of the installed skill and is excluded from release zips.

```python
from pathlib import Path
from src.validator import Validator

v = Validator(input_path=Path("/path/to/model-repo"))
report = v.validate(
    annotation_yaml=open("mymodel.annotation.yaml").read(),
    metadata_yaml="",   # legacy; pass empty string when using annotation_yaml
    execution_yaml="",
)
print(report["overall_status"])  # "pass" or "fail"
print(report["structural_validation"])
```

Exit code rules and warning thresholds are documented in the module docstring.

---

## License

See [`LICENSE`](LICENSE).
