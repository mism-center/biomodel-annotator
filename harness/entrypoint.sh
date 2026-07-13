#!/usr/bin/env bash
# Fire-and-forget annotation run.
# MODEL_INPUT: path inside the container (default /workspace) or a GitHub URL.
# The skill writes <slug>.annotation.yaml into the working directory (/workspace),
# which is bind-mounted to the host. Full JSON event trace goes to stdout (= docker logs).
set -euo pipefail

TARGET="${MODEL_INPUT:-/workspace}"

exec pi --mode json --approve --model ${AI_MODEL} --stream=all \
  --provider azure-openai-response \
  --append-system-prompt "$(cat /opt/pi/APPEND_SYSTEM.md)" \
  -p "/skill:biomodel-annotator annotate ${TARGET}, ${PROMPT}"
