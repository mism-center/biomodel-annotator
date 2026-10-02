"""
Tests for scripts/validate.py

Run with:
    pytest tests/test_validate.py
or:
    uv run pytest tests/test_validate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

# Make scripts/ importable without an install step.
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate import (  # noqa: E402
    Validator,
    _count_needs_review,
    _extract_dep_names,
    _find_non_numeric_leaves,
    _iter_io_slots,
)

# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


def _minimal_section_a() -> dict:
    """Minimal valid model dict that passes Section A structural check."""
    return {
        "name": {"value": "Test Model", "source": "README.md", "confidence": "high"},
        "short_description": {"value": "A test model.", "source": "README.md", "confidence": "high"},
        "long_description": {"value": "A longer description.", "source": "README.md", "confidence": "high"},
        "version": {"value": "1.0.0", "source": "setup.py", "confidence": "high"},
        "external_identifier": {"scheme": "url", "value": "https://example.com", "source": "README.md"},
        "multiscale": {"value": False, "source": "README.md", "confidence": "high"},
        "model_scales": [{"value": "cellular", "source": "README.md", "confidence": "high"}],
        "authors": [{"name": "Alice", "affiliation": "Uni", "source": "setup.py"}],
        "contacts": [{"name": "Alice", "role": "corresponding author", "email": "a@example.com",
                      "affiliation": "Uni", "source": "setup.py"}],
        "license": {"spdx_id": "MIT", "source": "LICENSE", "confidence": "high"},
        "publications": [{"title": "A Paper", "url": "https://doi.org/10.1", "source": "README.md"}],
    }


def _minimal_section_b() -> dict:
    """Minimal valid execution dict that passes Section B structural check."""
    return {
        "status": "characterized",
        "language": {"name": "Python", "source": "README.md"},
        "environment_kind": {"value": "pip", "source": "README.md"},
        "entry_points": [{"command": "python run.py", "purpose": "Run", "source": "README.md"}],
    }


def _make_annotation(model: dict | None = None, execution: dict | None = None) -> dict:
    return {
        "model": model if model is not None else _minimal_section_a(),
        "execution": execution if execution is not None else _minimal_section_b(),
        "io": {},
        "provenance": {},
    }


# ---------------------------------------------------------------------------
# Structural validation — Section A
# ---------------------------------------------------------------------------


class TestSectionA:
    def _validator(self, tmp_path: Path) -> Validator:
        return Validator(input_path=tmp_path)

    def test_pass_all_required(self, tmp_path):
        v = self._validator(tmp_path)
        result = v._check_section_a(_make_annotation())
        assert result["missing"] == []
        assert result["empty"] == []

    def test_missing_name(self, tmp_path):
        model = _minimal_section_a()
        del model["name"]
        v = self._validator(tmp_path)
        result = v._check_section_a(_make_annotation(model=model))
        assert "model.name" in result["missing"]

    def test_empty_name_value(self, tmp_path):
        model = _minimal_section_a()
        model["name"] = {"value": "", "source": "README.md", "confidence": "high"}
        v = self._validator(tmp_path)
        result = v._check_section_a(_make_annotation(model=model))
        assert "model.name" in result["empty"]

    def test_empty_authors_list(self, tmp_path):
        model = _minimal_section_a()
        model["authors"] = []
        v = self._validator(tmp_path)
        result = v._check_section_a(_make_annotation(model=model))
        assert "model.authors" in result["empty"]

    def test_missing_external_identifier_value(self, tmp_path):
        model = _minimal_section_a()
        model["external_identifier"] = {"scheme": "url", "source": "README.md"}  # no value key
        v = self._validator(tmp_path)
        result = v._check_section_a(_make_annotation(model=model))
        assert "model.external_identifier.value" in result["empty"]

    def test_empty_model_scales(self, tmp_path):
        model = _minimal_section_a()
        model["model_scales"] = []
        v = self._validator(tmp_path)
        result = v._check_section_a(_make_annotation(model=model))
        assert "model.model_scales" in result["empty"]


# ---------------------------------------------------------------------------
# Structural validation — Section B
# ---------------------------------------------------------------------------


class TestSectionB:
    def _validator(self, tmp_path: Path) -> Validator:
        return Validator(input_path=tmp_path)

    def test_pass_all_required(self, tmp_path):
        v = self._validator(tmp_path)
        result = v._check_section_b(_make_annotation())
        assert result["missing"] == []
        assert result["empty"] == []

    def test_missing_entry_points(self, tmp_path):
        execution = _minimal_section_b()
        del execution["entry_points"]
        v = self._validator(tmp_path)
        result = v._check_section_b(_make_annotation(execution=execution))
        assert "execution.entry_points" in result["missing"]

    def test_empty_entry_points(self, tmp_path):
        execution = _minimal_section_b()
        execution["entry_points"] = []
        v = self._validator(tmp_path)
        result = v._check_section_b(_make_annotation(execution=execution))
        assert "execution.entry_points" in result["empty"]

    def test_missing_language(self, tmp_path):
        execution = _minimal_section_b()
        del execution["language"]
        v = self._validator(tmp_path)
        result = v._check_section_b(_make_annotation(execution=execution))
        assert "execution.language" in result["missing"]

    def test_language_missing_name_subkey(self, tmp_path):
        execution = _minimal_section_b()
        execution["language"] = {"version_constraint": ">=3.8"}  # no name key
        v = self._validator(tmp_path)
        result = v._check_section_b(_make_annotation(execution=execution))
        assert "execution.language.name" in result["empty"]


# ---------------------------------------------------------------------------
# _extract_dep_names
# ---------------------------------------------------------------------------


class TestExtractDepNames:
    def test_nested_schema_format(self):
        execution = {
            "dependencies": {
                "runtime": [
                    {"name": "vivarium-core", "version_constraint": "==0.0.34"},
                    {"name": "pymunk", "version_constraint": "==5.6.0"},
                ],
                "optional": [{"name": "matplotlib"}],
                "system": [{"name": "mongodb"}],
            }
        }
        names = _extract_dep_names(execution)
        assert "vivarium-core" in names
        assert "pymunk" in names
        assert "matplotlib" in names
        assert "mongodb" in names

    def test_flat_list_legacy(self):
        execution = {
            "dependencies": [
                {"name": "numpy"},
                {"name": "scipy"},
            ]
        }
        names = _extract_dep_names(execution)
        assert "numpy" in names
        assert "scipy" in names

    def test_flat_string_style(self):
        execution = {
            "dependencies": ["numpy>=1.24", "scipy==1.10"]
        }
        names = _extract_dep_names(execution)
        assert "numpy" in names
        assert "scipy" in names

    def test_empty_deps(self):
        assert _extract_dep_names({}) == []
        assert _extract_dep_names({"dependencies": []}) == []
        assert _extract_dep_names({"dependencies": {}}) == []

    def test_partial_nested_keys(self):
        execution = {
            "dependencies": {
                "runtime": [{"name": "vivarium-cell"}],
                # optional and system absent
            }
        }
        names = _extract_dep_names(execution)
        assert names == ["vivarium-cell"]


# ---------------------------------------------------------------------------
# _iter_io_slots
# ---------------------------------------------------------------------------


class TestIterIOSlots:
    def test_parameters_and_outputs(self):
        annotation = {
            "io": {
                "inputs": {
                    "parameters": [{"name": "k_run", "default_value": 1.0}],
                    "initial_conditions": [{"name": "agent_count", "value": 100}],
                    "data_inputs": [],
                },
                "outputs": [{"name": "trajectories", "description": "Agent paths"}],
            }
        }
        slots = list(_iter_io_slots(annotation))
        names = [s["name"] for s in slots]
        assert "k_run" in names
        assert "agent_count" in names
        assert "trajectories" in names

    def test_flat_inputs_list(self):
        annotation = {
            "io": {
                "inputs": [{"name": "param_a"}],
                "outputs": [{"name": "out_b"}],
            }
        }
        slots = list(_iter_io_slots(annotation))
        names = [s["name"] for s in slots]
        assert "param_a" in names
        assert "out_b" in names

    def test_empty_io(self):
        assert list(_iter_io_slots({})) == []
        assert list(_iter_io_slots({"io": {}})) == []

    def test_does_not_read_from_metadata_top_level(self):
        # metadata.yaml has no "io" key — should yield nothing
        metadata_like = {
            "model": {"name": {"value": "X"}},
            "inputs": [{"name": "should_not_appear"}],  # wrong place
        }
        assert list(_iter_io_slots(metadata_like)) == []


# ---------------------------------------------------------------------------
# _count_needs_review
# ---------------------------------------------------------------------------


class TestCountNeedsReview:
    def test_flat_dict(self):
        obj = {"a": "needs_review", "b": "ok", "c": "needs_review"}
        assert _count_needs_review(obj) == 2

    def test_nested_dict(self):
        obj = {"outer": {"inner": "needs_review"}, "x": "fine"}
        assert _count_needs_review(obj) == 1

    def test_list_of_strings(self):
        obj = ["needs_review", "ok", "needs_review"]
        assert _count_needs_review(obj) == 2

    def test_mixed_nesting(self):
        obj = {
            "model": {
                "name": "needs_review",
                "scales": ["cellular", "needs_review"],
            },
            "execution": {"status": "characterized"},
        }
        assert _count_needs_review(obj) == 2

    def test_no_needs_review(self):
        obj = {"a": "high", "b": ["x", "y"]}
        assert _count_needs_review(obj) == 0

    def test_non_string_values_ignored(self):
        obj = {"count": 5, "flag": True, "nothing": None}
        assert _count_needs_review(obj) == 0

    def test_substring_does_not_match(self):
        # "not_needs_review" should NOT be counted
        obj = {"a": "not_needs_review", "b": "needs_review_extra"}
        assert _count_needs_review(obj) == 0


# ---------------------------------------------------------------------------
# Semantic validation — entry-point path check
# ---------------------------------------------------------------------------


class TestSemanticEntryPoints:
    def test_existing_command_path(self, tmp_path):
        # Create the script so the path check passes
        script = tmp_path / "run.py"
        script.write_text("# run script")

        execution = {
            **_minimal_section_b(),
            "entry_points": [{"command": "python run.py", "purpose": "Run"}],
        }
        v = Validator(input_path=tmp_path)
        result = v._check_semantic(None, execution, None)
        assert result["execution_command_verified"] is True
        assert result["execution_command_path"] == "run.py"

    def test_missing_command_path(self, tmp_path):
        execution = {
            **_minimal_section_b(),
            "entry_points": [{"command": "python does_not_exist.py", "purpose": "Run"}],
        }
        v = Validator(input_path=tmp_path)
        result = v._check_semantic(None, execution, None)
        assert result["execution_command_verified"] is False

    def test_no_entry_points_is_not_a_failure(self, tmp_path):
        execution = {**_minimal_section_b(), "entry_points": []}
        v = Validator(input_path=tmp_path)
        result = v._check_semantic(None, execution, None)
        assert result["execution_command_verified"] is True

    def test_legacy_execution_command_field_is_ignored(self, tmp_path):
        # A top-level execution_command key (not in schema) should not be
        # used for path verification.
        execution = {
            **_minimal_section_b(),
            "execution_command": "python does_not_exist_either.py",
            "entry_points": [],  # no valid entry point
        }
        v = Validator(input_path=tmp_path)
        result = v._check_semantic(None, execution, None)
        # No failure from the legacy field
        assert result["execution_command_verified"] is True


# ---------------------------------------------------------------------------
# Registry check — correct schema paths
# ---------------------------------------------------------------------------


class TestRegistryCheck:
    def test_correct_paths_resolve_name_and_uri(self, tmp_path):
        metadata = {
            "model": {
                "name": {"value": "My Model", "source": "README.md", "confidence": "high"},
                "external_identifier": {"scheme": "url", "value": "https://example.com", "source": "README.md"},
            }
        }
        v = Validator(input_path=tmp_path)
        # If mism_registry is not installed the check is skipped optimistically.
        # Either way, it should not crash and should not report name/uri as missing.
        result = v._check_registry(metadata)
        assert "name (model.name.value)" not in result.get("missing_registry_fields", [])
        assert "location_uri (model.external_identifier.value)" not in result.get("missing_registry_fields", [])

    def test_flat_metadata_no_model_key(self, tmp_path):
        # When mism_registry is not installed, the check is skipped optimistically.
        # When it IS installed, an empty model dict should report missing fields.
        v = Validator(input_path=tmp_path)
        result = v._check_registry({})
        # Either the check was skipped (mism_registry absent) or fields were reported missing.
        # In both cases the function must not crash and must return a dict.
        assert isinstance(result, dict)
        warnings = result.get("warnings", [])
        missing = result.get("missing_registry_fields", [])
        # If mism_registry is installed, the correct paths must be flagged.
        # If not installed, a skip warning must be present.
        assert (
            ("mism_registry not installed" in " ".join(warnings))
            or ("name (model.name.value)" in missing)
        )


# ---------------------------------------------------------------------------
# Numeric range/prose rejection — warning-only CLI field
# ---------------------------------------------------------------------------


class TestFindNonNumericLeaves:
    def test_clean_numeric_annotation_reports_nothing(self):
        annotation = {
            "execution": {"compute": {"cpu_cores": {"value": 4}, "memory_gb": {"value": 8.0}}},
            "io": {"experiment_protocol": {"timestep": {"value": 0.01}, "duration": {"value": 500}}},
        }
        assert _find_non_numeric_leaves(annotation) == []

    def test_missing_fields_report_nothing(self):
        # Absent/None is "not characterized" — not a defect this check should flag.
        assert _find_non_numeric_leaves({}) == []
        assert _find_non_numeric_leaves({"execution": {"compute": {}}}) == []

    def test_prose_value_is_flagged(self):
        annotation = {
            "execution": {
                "compute": {"typical_runtime": {"value": "~30 minutes for the larger efficacy simulation"}}
            }
        }
        flagged = _find_non_numeric_leaves(annotation)
        assert flagged == [
            {
                "field_path": "execution.compute.typical_runtime",
                "value": "~30 minutes for the larger efficacy simulation",
            }
        ]

    def test_range_string_is_flagged(self):
        annotation = {
            "io": {
                "experiment_protocol": {
                    "duration": {"value": "300-700 ticks in canonical studies; 1500 ticks at scale"}
                }
            }
        }
        flagged = _find_non_numeric_leaves(annotation)
        assert flagged == [
            {
                "field_path": "io.experiment_protocol.duration",
                "value": "300-700 ticks in canonical studies; 1500 ticks at scale",
            }
        ]

    def test_numeric_ish_string_is_not_flagged_for_float_fields(self):
        annotation = {"execution": {"compute": {"memory_gb": {"value": "8.0"}}}}
        assert _find_non_numeric_leaves(annotation) == []

    def test_numeric_ish_string_is_not_flagged_for_cpu_cores(self):
        # Aligns with ingest's _num() helper (metadata_package.py): cpu_cores
        # goes through float() first, so "4.0" is accepted here too — the
        # same value must not be treated inconsistently by the two layers.
        annotation = {"execution": {"compute": {"cpu_cores": {"value": "4.0"}}}}
        assert _find_non_numeric_leaves(annotation) == []
