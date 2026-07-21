# Dockerized biomodel-annotator: Pi harness + skill + extensions.
# Build from the REPO ROOT so SKILL.md/references/ are in the build context:
#   docker build -t biomodel-annotator-pi -f harness/Dockerfile .
FROM node:24-bookworm-slim

# Runtime tools Pi's built-in tools expect. curl for debugging.
RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates git ripgrep curl \
  && rm -rf /var/lib/apt/lists/*

# uv: required at runtime by the skill's validation gate (`uv run scripts/validate.py`,
# which resolves PyYAML + a managed Python via PEP 723 inline deps). Static binary,
# no curl/pip. Pinned for reproducibility.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /usr/local/bin/

# Install pi coding agent globally (still as root). Extensions import
# @earendil-works/* from this global install — no per-extension npm install.
RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent

# Pi reads global config (settings, extensions, APPEND_SYSTEM.md) from this dir.
ENV PI_CODING_AGENT_DIR=/opt/pi

# The skill itself (frozen — copied verbatim from the repo). Same allowlist as
# dev-install.sh / release.yml: SKILL.md + references/*.md + scripts/validate.py.
# validate.py is the skill's Assembly validation gate (run via `uv run`).
COPY SKILL.md /opt/skills/biomodel-annotator/SKILL.md
COPY references/ /opt/skills/biomodel-annotator/references/
COPY scripts/validate.py /opt/skills/biomodel-annotator/scripts/validate.py

# Harness wiring: all extensions, settings, system-prompt bridge.
# Every dir under harness/extensions/ is installed; settings.json enables them.
COPY harness/extensions/ /opt/pi/extensions/
COPY harness/pi/settings.json /opt/pi/settings.json
COPY harness/pi/APPEND_SYSTEM.md /opt/pi/APPEND_SYSTEM.md

COPY harness/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# uv writable state (managed Python + wheel cache) baked at BUILD time into an
# exec-safe, world-writable dir. At runtime /tmp is a small tmpfs mounted
# noexec, so uv's fallback of downloading CPython there fails to exec it
# (EACCES). /opt is exec-safe and 0777 makes it usable under any --user.
# ENV points uv here so the plain `uv run` in SKILL.md needs no /tmp override.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    UV_CACHE_DIR=/opt/uv/cache
RUN mkdir -p /opt/uv/python /opt/uv/cache \
  && uv python install 3.13 \
  && uv run /opt/skills/biomodel-annotator/scripts/validate.py --help >/dev/null 2>&1 || true \
  && chmod -R 0777 /opt/uv

# Run non-root as `app`. UID/GID pinned to 995 to match the owner of the
# iRODS-mounted files at /workspace — `useradd --system` otherwise picks the
# first free UID (drifted 995→999), leaving /workspace unreadable.
RUN groupadd --system --gid 995 app && useradd --system --uid 995 --gid app --no-create-home app \
  && mkdir -p /workspace && chown -R app:app /workspace /opt/pi /opt/skills
USER app

WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
