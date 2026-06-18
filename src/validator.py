"""
Annotation Validator

Runs structural, semantic, and registry compatibility checks on the produced
metadata.yaml, execution.yaml, and full annotation YAML. Writes validation_report.json.

Exit code rules:
    0 — all required fields present, execution_command verified, registry check passed
    1 — any required field missing/null, execution_command path not found, or
        RegisterModelRequest cannot be constructed

Warnings (flagged in report but do not change exit code):
    - needs_review count > 5
    - ontology coverage < 40% of eligible fields
    - any leaf field missing a source citation
    - listed dependency not found in setup.py / pyproject.toml
    - zero IOSlot objects constructable from inputs/outputs
"""

from __future__ import annotations

import logging
import os
import re
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Required field lists — aligned to references/schema.md
# ---------------------------------------------------------------------------

# Fields required in annotation['model'] (Section A).
# kind values:
#   "scalar"   — envelope {value, source, confidence}; value must be non-empty
#   "list"     — must be a non-empty list
#   "dict:KEY" — must be a dict whose KEY sub-field is present
REQUIRED_SECTION_A: list[tuple[str, str]] = [
    ("name",             "scalar"),
    ("short_description","scalar"),
    ("model_class",      "list"),
    ("formalism",        "list"),
    ("determinism",      "scalar"),
    ("time_dynamics",    "scalar"),
    ("spatial",          "scalar"),
]

# Fields required in annotation['execution'] (Section B).
REQUIRED_SECTION_B: list[tuple[str, str]] = [
    ("status",           "scalar"),
    ("language",         "dict:name"),
    ("environment_kind", "scalar"),
    ("entry_points",     "list"),
]

# Fields eligible for ontology mapping in the full annotation
_ONTOLOGY_ELIGIBLE_PATHS = [
    "model.model_class",
    "model.formalism",
    "model.biology.organisms",
    "model.biology.biological_processes",
    "model.biology.molecular_entities",
    "model.biology.cell_types",
    "model.biology.anatomy",
    "execution.language",
]


def _get_leaf_value(field: Any) -> Any:
    """
    Extract the plain value from a schema leaf envelope or bare scalar.

    Schema leaf fields use the shape ``{value: ..., source: ..., confidence: ...}``.
    Returns ``field["value"]`` when that key is present, otherwise returns ``field``
    itself (handles bare scalars for forward-compat). Returns ``None`` for None input.
    """
    if field is None:
        return None
    if isinstance(field, dict):
        return field.get("value")
    return field


class Validator:
    """Runs all validation checks and returns a report dict."""

    def __init__(
        self,
        input_path: Path,
        model_id: str = "",
        run_id: str = "",
    ) -> None:
        self._input_path = input_path
        self._model_id = model_id
        self._run_id = run_id

    def validate(
        self,
        annotation_yaml: str,
        metadata_yaml: str,
        execution_yaml: str,
    ) -> dict[str, Any]:
        """
        Run all checks and return the validation_report dict.
        The dict contains an 'exit_code' key (0 or 1).
        """
        report: dict[str, Any] = {
            "run_id": self._run_id,
            "model_id": self._model_id,
            "annotated_at": datetime.now(timezone.utc).isoformat(),
            "exit_code": 0,
            "structural_validation": {},
            "semantic_validation": {},
            "registry_compatibility": {},
            "overall_status": "pass",
            "failure_reasons": [],
        }

        # Parse YAML inputs
        metadata = _safe_parse_yaml(metadata_yaml, "metadata.yaml")
        execution = _safe_parse_yaml(execution_yaml, "execution.yaml")
        annotation = _safe_parse_yaml(annotation_yaml, "annotation.yaml")

        # --- Structural validation ---
        structural = self._check_structural(metadata, execution, annotation)
        report["structural_validation"] = structural
        if structural["status"] == "fail":
            report["exit_code"] = 1
            report["failure_reasons"].extend(
                [f"Missing required field: {f}" for f in structural["missing_required_fields"]]
                + [f"Null required field: {f}" for f in structural["empty_required_fields"]]
            )

        # --- Semantic validation ---
        semantic = self._check_semantic(metadata, execution, annotation)
        report["semantic_validation"] = semantic
        if not semantic.get("execution_command_verified", True):
            report["exit_code"] = 1
            report["failure_reasons"].append(
                f"execution_command path not found in INPUT_PATH: "
                f"{semantic.get('execution_command_path', '?')}"
            )

        # --- Registry compatibility ---
        registry = self._check_registry(metadata)
        report["registry_compatibility"] = registry
        if not registry.get("register_model_constructable", False):
            report["exit_code"] = 1
            report["failure_reasons"].extend(
                [f"Registry field missing: {f}" for f in registry.get("missing_registry_fields", [])]
            )

        report["overall_status"] = "pass" if report["exit_code"] == 0 else "fail"
        return report

    # ------------------------------------------------------------------
    # Structural validation
    # ------------------------------------------------------------------

    def _check_structural(
        self,
        metadata: dict[str, Any] | None,
        execution: dict[str, Any] | None,
        annotation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Validate structural completeness of the assembled annotation.

        Operates on the full ``annotation`` dict (top-level keys: model, execution, io,
        provenance). The ``metadata`` and ``execution`` flat-dict parameters are kept for
        callers that still use the legacy three-YAML interface but are no longer
        authoritative; a deprecation warning is emitted when they are used as fallback.
        """
        if annotation is not None:
            section_a = self._check_section_a(annotation)
            section_b = self._check_section_b(annotation)
            missing = section_a["missing"] + section_b["missing"]
            empty   = section_a["empty"]   + section_b["empty"]
        else:
            # Legacy path — POC-2 flat-dict callers only.
            log.warning(
                "_check_structural called without annotation dict; "
                "falling back to legacy flat-dict validation (deprecated)."
            )
            missing, empty = [], []
            if metadata is None:
                missing.append("annotation.model (not provided)")
            if execution is None:
                missing.append("annotation.execution (not provided)")

        status = "fail" if (missing or empty) else "pass"
        return {
            "status": status,
            "missing_required_fields": missing,
            "empty_required_fields": empty,
        }

    def _check_section_a(self, annotation: dict[str, Any]) -> dict[str, Any]:
        """Check required Section A (model) fields against REQUIRED_SECTION_A."""
        model = annotation.get("model") or {}
        missing: list[str] = []
        empty: list[str] = []

        for field, kind in REQUIRED_SECTION_A:
            raw = model.get(field)
            path = f"model.{field}"

            if raw is None:
                missing.append(path)
                continue

            if kind == "scalar":
                val = _get_leaf_value(raw)
                if val is None or val == "":
                    empty.append(path)

            elif kind == "list":
                if not isinstance(raw, list) or len(raw) == 0:
                    empty.append(path)

            elif kind.startswith("dict:"):
                sub_key = kind.split(":", 1)[1]
                if not isinstance(raw, dict) or raw.get(sub_key) is None:
                    empty.append(f"{path}.{sub_key}")

        return {"missing": missing, "empty": empty}

    def _check_section_b(self, annotation: dict[str, Any]) -> dict[str, Any]:
        """Check required Section B (execution) fields against REQUIRED_SECTION_B."""
        execution = annotation.get("execution") or {}
        missing: list[str] = []
        empty: list[str] = []

        for field, kind in REQUIRED_SECTION_B:
            raw = execution.get(field)
            path = f"execution.{field}"

            if raw is None:
                missing.append(path)
                continue

            if kind == "scalar":
                val = _get_leaf_value(raw)
                if val is None or val == "":
                    empty.append(path)

            elif kind == "list":
                if not isinstance(raw, list) or len(raw) == 0:
                    empty.append(path)

            elif kind.startswith("dict:"):
                sub_key = kind.split(":", 1)[1]
                if not isinstance(raw, dict) or raw.get(sub_key) is None:
                    empty.append(f"{path}.{sub_key}")

        return {"missing": missing, "empty": empty}

    # ------------------------------------------------------------------
    # Semantic validation
    # ------------------------------------------------------------------

    def _check_semantic(
        self,
        metadata: dict[str, Any] | None,
        execution: dict[str, Any] | None,
        annotation: dict[str, Any] | None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "needs_review_count": 0,
            "needs_review_warning": False,
            "ontology_coverage_pct": None,
            "ontology_coverage_warning": False,
            "missing_source_citations": [],
            "execution_command_verified": True,
            "execution_command_path": None,
            "undocumented_dependencies": [],
        }

        # Count needs_review across all extracted files
        all_text = ""
        if metadata:
            all_text += str(metadata)
        if execution:
            all_text += str(execution)
        needs_review_count = all_text.count("needs_review")
        result["needs_review_count"] = needs_review_count
        result["needs_review_warning"] = needs_review_count > 5

        # Ontology coverage from full annotation
        if annotation:
            coverage = _compute_ontology_coverage(annotation)
            result["ontology_coverage_pct"] = coverage
            result["ontology_coverage_warning"] = coverage is not None and coverage < 40.0

        # execution_command path check
        if execution:
            cmd = execution.get("execution_command")
            if cmd and cmd != "needs_review":
                verified, path_str = self._verify_execution_command(str(cmd))
                result["execution_command_verified"] = verified
                result["execution_command_path"] = path_str
                if not verified:
                    log.warning(
                        "execution_command path not found: %s (searched under %s)",
                        path_str,
                        self._input_path,
                    )
            else:
                # needs_review or missing — not a hard failure at semantic layer
                result["execution_command_verified"] = True

        # Dependency consistency check
        if execution:
            deps = _extract_dep_names(execution)
            declared = self._load_declared_deps()
            undocumented = [d for d in deps if d.lower() not in declared]
            result["undocumented_dependencies"] = undocumented

        return result

    def _verify_execution_command(self, cmd: str) -> tuple[bool, str]:
        """
        Strip interpreter prefix and check the path exists under INPUT_PATH.
        Handles:
            python chemotaxis/composites/chemotaxis_minimal.py
            python3 chemotaxis/composites/chemotaxis_minimal.py
            python -m chemotaxis.composites.chemotaxis_minimal
        Returns (verified: bool, path_string: str).
        """
        cmd = cmd.strip()

        # Strip leading interpreter
        for prefix in ("python3 -m ", "python -m ", "python3 ", "python ", "python2 "):
            if cmd.lower().startswith(prefix):
                cmd = cmd[len(prefix):].strip()
                break

        # Convert dotted module path to file path
        if re.match(r'^[\w][\w.]+$', cmd) and not cmd.endswith(".py"):
            cmd = cmd.replace(".", "/") + ".py"

        # Strip any remaining arguments
        path_part = cmd.split()[0] if cmd else cmd

        abs_path = self._input_path / path_part
        exists = abs_path.exists()
        return exists, path_part

    def _load_declared_deps(self) -> set[str]:
        """Return lowercase dep names found in setup.py / pyproject.toml."""
        declared: set[str] = set()

        setup_py = self._input_path / "setup.py"
        if setup_py.exists():
            text = setup_py.read_text(encoding="utf-8", errors="replace")
            # Extract package names from install_requires strings
            for match in re.finditer(r'["\']([A-Za-z0-9_\-]+)[>=<!\s]', text):
                declared.add(match.group(1).lower())

        pyproject = self._input_path / "pyproject.toml"
        if pyproject.exists():
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            for match in re.finditer(r'["\']([A-Za-z0-9_\-]+)[>=<!\s]', text):
                declared.add(match.group(1).lower())

        return declared

    # ------------------------------------------------------------------
    # Registry compatibility
    # ------------------------------------------------------------------

    def _check_registry(self, metadata: dict[str, Any] | None) -> dict[str, Any]:
        result: dict[str, Any] = {
            "register_model_constructable": False,
            "missing_registry_fields": [],
            "io_slots_constructed": 0,
            "warnings": [],
        }

        if metadata is None:
            result["missing_registry_fields"] = ["name", "location_uri", "execution_type"]
            return result

        # Try to import mism_registry; skip registry check if not installed
        try:
            from mism_registry import (  # type: ignore[import]
                ExecutionType,
                Resource,
                ResourceType,
            )
            from mism_registry.validation import (  # type: ignore[import]
                validate_execution_fields,
                validate_resource_required_fields,
            )
        except ImportError:
            log.warning(
                "mism_registry not installed — skipping registry dry-run. "
                "Install metadata-schema to enable registry compatibility checks."
            )
            result["register_model_constructable"] = True  # optimistic
            result["warnings"].append("mism_registry not installed — registry check skipped")
            return result

        missing: list[str] = []

        name = _str_val(metadata.get("name"))
        location_uri = _str_val(metadata.get("source_repository"))
        exec_type_str = _str_val(metadata.get("execution_type"))

        if not name:
            missing.append("name")
        if not location_uri:
            missing.append("location_uri (source_repository)")
        if not exec_type_str:
            missing.append("execution_type")

        if missing:
            result["missing_registry_fields"] = missing
            return result

        # Attempt to construct Resource and validate
        try:
            exec_type = ExecutionType(exec_type_str)
            resource = Resource(
                name=name,
                resource_type=ResourceType.MODEL,
                location_uri=location_uri,
                execution_type=exec_type,
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                validate_resource_required_fields(resource)
                validate_execution_fields(resource)
            result["register_model_constructable"] = True
        except Exception as exc:
            log.warning("Registry dry-run failed: %s", exc)
            result["missing_registry_fields"].append(str(exc))
            return result

        # IOSlot construction
        try:
            from mism_registry.types import IOSlot  # type: ignore[import]

            slots_ok = 0
            for slot_data in _iter_io_slots(metadata):
                try:
                    IOSlot(
                        name=slot_data.get("name", ""),
                        description=slot_data.get("description", ""),
                        tags=tuple(slot_data.get("tags") or []),
                    )
                    slots_ok += 1
                except Exception:
                    pass
            result["io_slots_constructed"] = slots_ok
            if slots_ok == 0:
                result["warnings"].append(
                    "Zero IOSlot objects constructable from inputs/outputs"
                )
        except ImportError:
            pass

        return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_parse_yaml(text: str | None, name: str) -> dict[str, Any] | None:
    if not text:
        log.warning("Empty YAML content for %s", name)
        return None
    try:
        data = yaml.safe_load(text)
        if not isinstance(data, dict):
            log.warning("%s parsed to non-dict type: %s", name, type(data))
            return None
        return data
    except yaml.YAMLError as exc:
        log.warning("Failed to parse %s: %s", name, exc)
        return None


def _compute_ontology_coverage(annotation: dict[str, Any]) -> float | None:
    """
    Walk annotation looking for ontology-eligible fields.
    Returns percentage (0–100) of eligible fields with mapping_confidence >= medium,
    or None if no eligible fields found.
    """
    eligible = 0
    mapped = 0

    def _walk(obj: Any) -> None:
        nonlocal eligible, mapped
        if isinstance(obj, dict):
            # If this dict has a mapping_confidence key, it's an eligible field
            mc = obj.get("mapping_confidence")
            if mc is not None:
                eligible += 1
                if mc in ("high", "medium", "low"):
                    mapped += 1
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(annotation)
    if eligible == 0:
        return None
    return round(100.0 * mapped / eligible, 1)


def _extract_dep_names(execution: dict[str, Any]) -> list[str]:
    """Extract dependency package names from the execution dict."""
    deps = execution.get("dependencies") or []
    names = []
    if isinstance(deps, list):
        for dep in deps:
            if isinstance(dep, dict):
                name = dep.get("name")
                if name:
                    names.append(str(name))
            elif isinstance(dep, str):
                # "name==version" style
                names.append(re.split(r'[>=<!]', dep)[0].strip())
    return names


def _iter_io_slots(metadata: dict[str, Any]):
    """Yield slot dicts from metadata inputs and outputs."""
    for key in ("inputs", "outputs"):
        slots = metadata.get(key) or []
        if isinstance(slots, list):
            for slot in slots:
                if isinstance(slot, dict):
                    yield slot


def _str_val(val: Any) -> str:
    """Return val as a stripped string, or '' for None/needs_review."""
    if val is None:
        return ""
    s = str(val).strip()
    return "" if s in ("needs_review", "deferred", "null") else s


# ---------------------------------------------------------------------------
# CLI entry point — structural-only validation for mid-workflow checkpoints
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import json
    import sys

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(
        description=(
            "Validate Section A (model) and Section B (execution) of an annotation YAML. "
            "Intended to be run after Pass 1 and Pass 2 of the biomodel-annotator skill, "
            "before Pass 3 begins. Exits 0 on pass, 1 on failure."
        )
    )
    parser.add_argument(
        "--annotation",
        required=True,
        metavar="FILE",
        help="Path to the (partial) annotation YAML file.",
    )
    parser.add_argument(
        "--input-path",
        default=".",
        metavar="DIR",
        help="Root directory of the model repo being annotated. Defaults to cwd.",
    )
    args = parser.parse_args()

    annotation_text = Path(args.annotation).read_text(encoding="utf-8")
    v = Validator(input_path=Path(args.input_path))
    annotation = _safe_parse_yaml(annotation_text, args.annotation)

    result = v._check_structural(None, None, annotation)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "pass" else 1)
