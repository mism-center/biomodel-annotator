# biomodel-annotator — Docker harness (Pi)

Runs the `biomodel-annotator` skill as a one-shot, headless container using the
[Pi](https://pi.dev) coding agent instead of Claude Code. Pi has no MCP support,
so the skill's `ols-ontology` MCP dependency is replaced by a small Pi extension
(`extensions/ols/`) that calls the public EBI **OLS4 REST API** directly.

## What's here

| Path | Role |
|---|---|
| `Dockerfile` | node:24 + Pi + skill + OLS extension. **Build from repo root.** |
| `extensions/ols/index.ts` | Registers `searchClasses`, `fetch`, `listEmbeddingModels`, `searchClassesWithEmbeddingModel` as native Pi tools over OLS4 REST. |
| `pi/settings.json` | Wires the skill + extension; no MCP. |
| `pi/APPEND_SYSTEM.md` | Tells the model the OLS tools are native (drop the `ols-ontology:` prefix). |
| `entrypoint.sh` | `pi --mode json -p "/skill:biomodel-annotator annotate <target>"`. |

The skill files (`SKILL.md`, `references/`) are **unchanged** — they're copied into
the image at build time.

## Build

```bash
# from the repo root (NOT from harness/)
docker build -t biomodel-annotator-pi -f harness/Dockerfile .
```

## Run (fire-and-forget)

Annotate a model that lives on the host. Mount it at `/workspace`; the output
`<slug>.annotation.yaml` is written back to that same host directory.

```bash
docker run --rm \
  -e ANTHROPIC_API_KEY \
  -v "/path/to/model:/workspace" \
  biomodel-annotator-pi
```

Annotate a GitHub URL instead of a mounted folder:

```bash
docker run --rm \
  -e ANTHROPIC_API_KEY \
  -e MODEL_INPUT="https://github.com/owner/repo" \
  -v "$PWD/out:/workspace" \
  biomodel-annotator-pi
```

- `ANTHROPIC_API_KEY` — passed through from the host env (Pi resolves it automatically).
- `MODEL_INPUT` — path inside the container (default `/workspace`) or a GitHub URL.
- stdout = full JSON event trace (`docker logs`); the YAML lands in the mounted dir.

## Egress

The container needs outbound HTTPS to `api.anthropic.com` (model) and
`www.ebi.ac.uk` (OLS4). No other network access required.

## Notes / limits

- **Lexical-only ontology mapping.** OLS4 REST has no embedding search, so
  `listEmbeddingModels` returns `[]` and the skill records
  `embedding_fallback_used: false`, mapping every eligible field via lexical
  search. The skill's reproducibility invariant still holds.
- **Model:** uses Pi's default model resolution. Set one explicitly by editing
  `entrypoint.sh` (e.g. `--model anthropic/claude-opus-4-8`).
- **Picking specific tools:** built-in `read`/`bash`/`edit`/`write` stay enabled
  so Passes 0–3 can read the repo; the four OLS tools auto-register on top.
