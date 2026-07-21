# Self-check for the entry_points `arguments` structural rule added to
# Validator._check_section_b. No framework: run `python scripts/test_validate_arguments.py`.
from pathlib import Path

from validate import Validator


def _empties(entry_points):
    """Return the `empty` field paths _check_section_b reports for these entry_points."""
    v = Validator(input_path=Path("."))
    ann = {"execution": {"entry_points": entry_points}}
    return v._check_section_b(ann)["empty"]


def main() -> None:
    # Valid: decomposed command + well-formed arguments (unique positions).
    ok = [{
        "command": "python run.py <config>", "purpose": "run", "source": "run.py",
        "confidence": "high",
        "arguments": [
            {"name": "config", "position": 1, "data_type": "path"},
            {"name": "--topology", "position": 0, "data_type": "bool", "default": False},
        ],
    }]
    assert not any("arguments" in e for e in _empties(ok)), _empties(ok)

    # Duplicate positions must be flagged.
    dup = [{
        "command": "python run.py <a> <b>", "purpose": "run", "source": "run.py",
        "confidence": "high",
        "arguments": [
            {"name": "a", "position": 1},
            {"name": "b", "position": 1},
        ],
    }]
    assert any("duplicate positions" in e for e in _empties(dup)), _empties(dup)

    # Missing arg name must be flagged.
    noname = [{
        "command": "python run.py", "purpose": "run", "source": "run.py",
        "confidence": "high",
        "arguments": [{"description": "no name here"}],
    }]
    assert any(e.endswith("arguments[0].name") for e in _empties(noname)), _empties(noname)

    print("ok")


if __name__ == "__main__":
    main()
