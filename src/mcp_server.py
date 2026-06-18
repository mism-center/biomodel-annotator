"""
biomodel-validator MCP server

Exposes validator.py's Section A + B structural check as a single MCP tool,
``validate_sections``. The skill calls this tool at the validation checkpoint
between Pass 2 and Pass 3.

Usage (stdio transport — required by Claude Code):
    python src/mcp_server.py

Register with Claude Code:
    claude mcp add --transport stdio biomodel-validator python /path/to/src/mcp_server.py

Or in .mcp.json / ~/.claude.json:
    {
      "mcpServers": {
        "biomodel-validator": {
          "type": "stdio",
          "command": "python",
          "args": ["/path/to/biomodel-annotator/src/mcp_server.py"]
        }
      }
    }
"""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from validator import Validator, _safe_parse_yaml

mcp = FastMCP(
    name="biomodel-validator",
    instructions=(
        "Validates Section A (model) and Section B (execution) of a partial "
        "biomodel annotation YAML against the required field list defined in "
        "references/schema.md. Call validate_sections after completing Pass 1 "
        "and Pass 2, before starting Pass 3."
    ),
)


@mcp.tool()
def validate_sections(
    annotation_yaml: str,
    input_path: str = ".",
) -> dict:
    """
    Validate Section A (model) and Section B (execution) of a partial annotation YAML.

    Parameters
    ----------
    annotation_yaml:
        The full YAML string built so far — ``model:`` and ``execution:`` filled,
        ``io: {}`` and ``provenance: {}`` as empty stubs.
    input_path:
        Root directory of the model repo being annotated. Used for future
        execution-command path checks. Defaults to the current working directory.

    Returns
    -------
    A dict with three keys:

    - ``status``: ``"pass"`` or ``"fail"``
    - ``missing_required_fields``: list of field paths that are absent entirely
      (e.g. ``["model.name", "execution.entry_points"]``)
    - ``empty_required_fields``: list of field paths that are present but empty
      or null
    """
    v = Validator(input_path=Path(input_path))
    annotation = _safe_parse_yaml(annotation_yaml, "annotation")
    return v._check_structural(None, None, annotation)


if __name__ == "__main__":
    mcp.run(transport="stdio")
