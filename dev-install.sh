#!/usr/bin/env bash
# dev-install.sh — copy the skill into a Claude Code skills dir for local testing,
# mirroring exactly what .github/workflows/release.yml packages (the ship allowlist:
# SKILL.md, references/*.md, scripts/validate.py). Test the skill without cutting a release.
#
# Usage:
#   ./dev-install.sh                 # -> ~/.claude/skills/biomodel-annotator   (user-level)
#   ./dev-install.sh <skills-dir>    # -> <skills-dir>/biomodel-annotator        (e.g. project .claude/skills)
#
# Re-run after editing any skill file; restart/open a new Claude Code session to pick it up.
set -euo pipefail

name="biomodel-annotator"
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # repo root = this script's own dir

# Destination skills dir (default user-level); the skill lands in <skills-dir>/<name>.
skills_dir="${1:-$HOME/.claude/skills}"
dest="$skills_dir/$name"

# Source sanity — the same three allowlisted paths the release build requires.
test -f "$src/SKILL.md"            || { echo "SKILL.md missing in $src";            exit 1; }
test -d "$src/references"          || { echo "references/ missing in $src";          exit 1; }
test -f "$src/scripts/validate.py" || { echo "scripts/validate.py missing in $src";  exit 1; }

# Clear only the skill's own targets (not the whole dest dir) so renamed/removed files
# don't linger, then copy the allowlist — nothing else ships, matching release.yml.
rm -rf "$dest/SKILL.md" "$dest/references" "$dest/scripts"
mkdir -p "$dest/references" "$dest/scripts"
cp "$src/SKILL.md"            "$dest/SKILL.md"
cp "$src"/references/*.md     "$dest/references/"   # only .md, like the release
cp "$src/scripts/validate.py" "$dest/scripts/validate.py"

echo "Installed $name -> $dest"
find "$dest" -type f | sort   # show exactly what landed (dev mirror of release `unzip -l`)
