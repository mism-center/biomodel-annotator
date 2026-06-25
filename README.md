# biomodel-annotator

A Claude Code **skill** that turns a biological/biomedical computational model — a repo, a folder, a single SBML/CellML/BNGL/etc. file, or a GitHub URL — into a MIRIAM-aligned **annotation package** (a `metadata-package/` folder of YAML + a README) with ontology IRIs already attached.

The output is a starting point for a human curator: every field carries a `confidence` and `source`, and every ontology-eligible term carries `mapping_confidence` plus the queries that were tried.

See [`SKILL.md`](SKILL.md) for the full workflow and [`references/schema.md`](references/schema.md) for the package schema this skill emits.

---

## Prerequisites

### 1. Claude Code

You need [Claude Code](https://claude.com/claude-code) installed. Skills are loaded from either:

- `~/.claude/skills/<skill-name>/` — user-level (available in every session), or
- `<project>/.claude/skills/<skill-name>/` — project-level (only in that repo).

Each skill is a directory whose root contains a `SKILL.md` file.

### 2. Validator script (required for the Sections A & B validation gate)

As the final step before presenting the annotation, the skill runs the bundled script `scripts/validate.py` on the written package (the `metadata-package/` dir), checking the `model:` and `execution:` sections — reconstructed from `metadata.yaml` + `execution.yaml` — against the REQUIRED fields for Sections A and B in `references/schema.md`. No MCP server, no install step.

The script declares its one dependency (PyYAML) inline via [PEP 723](https://peps.python.org/pep-0723/), so [`uv`](https://docs.astral.sh/uv/) resolves it at run time:

```bash
uv run scripts/validate.py --package <model-repo-root>/metadata-package-na1-nx3-nx2-nx1 --input-path <model-repo-root>
```

It prints a JSON result to stdout and sets its exit code: `0` pass, `1` fail (with the offending field paths), `2` usage error. This is a hard gate — on exit 1 the skill goes back, fixes the flagged fields from the sources, and re-runs until it exits 0; it never presents a failing annotation.

If `uv` is unavailable, run it on any Python 3.9+ interpreter that has PyYAML installed:

```bash
pip install pyyaml
python3 scripts/validate.py --package <model-repo-root>/metadata-package-na1-nx3-nx2-nx1
```

### 3. OLS MCP server (required for Pass 4 — ontology mapping)

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

Restart your Claude Code session (or open a new one) so the skill is picked up. The release zip contains `SKILL.md`, the two `references/*.md` files, and `scripts/validate.py` (the bundled structural validator). Nothing else ships.

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

An **annotation package** — a directory named `metadata-package/`, written **inside the model's own directory** (not the working directory) — containing three files:

```
<model-dir>/
  metadata-package/
    metadata.yaml    # model identity, biology, authorship, references + provenance (ontology half)
    execution.yaml   # execution environment, IO, validation result + provenance (validation half)
    README.md        # human-readable model-card summary
```

The four logical sections are split across the two YAML files:

| Section | File | Contents |
|---|---|---|
| `model` | `metadata.yaml` | Identity, biology, authors, contacts, license, references |
| `execution` | `execution.yaml` | Language, deps, container, compute, entry points, tests |
| `io` | `execution.yaml` | Parameters, initial conditions, data inputs, outputs |
| `provenance` | both (split) | Annotation run metadata, OLS lookups, unmapped fields, validation result |

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

`scripts/validate.py` is the bundled validator. It ships with the skill and the skill runs it as the final Sections A & B validation gate (see Prerequisite 2). The same file also exposes a `Validator` class for richer post-hoc use — the full `validate()` adds semantic checks (execution-command path verification, dependency cross-check against `setup.py`/`pyproject.toml`) and a registry-compatibility dry-run on top of the structural check the CLI runs.

```python
import sys
from pathlib import Path

sys.path.insert(0, "scripts")        # validate.py lives in scripts/
from validate import Validator

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
