#!/usr/bin/env bash
# Fire-and-forget annotation run.
# MODEL_INPUT: path inside the container (default /workspace) or a GitHub URL.
# The skill writes the metadata-package/ (metadata.yaml, execution.yaml, README.md)
# into the working directory (/workspace), which is bind-mounted to the host.
# Full JSON event trace goes to stdout (= docker logs).
#
# Retry loop: the Azure Responses API can drop the SSE stream mid-turn (usually
# the final, largest turn), which pi reports as a terminal error with
# willRetry:false. The session is saved (no --no-session), so on nonzero exit we
# resume with --continue to finish the package instead of losing a 90%-done run.
set -euo pipefail

TARGET="${MODEL_INPUT:-/workspace}"
ATTEMPTS="${MAX_ATTEMPTS:-3}"

run() {
  pi --mode json --approve --model "${AI_MODEL}" --stream=all \
    --provider azure-openai-responses \
    --append-system-prompt "$(cat /opt/pi/APPEND_SYSTEM.md)" "$@"
}

# Attempt 1: full annotation.
if run -p "/skill:biomodel-annotator annotate ${TARGET}, ${PROMPT}"; then
  exit 0
fi

# Attempts 2..N: resume the saved session and finish whatever is left.
for i in $(seq 2 "${ATTEMPTS}"); do
  echo "pi exited nonzero — resume attempt ${i}/${ATTEMPTS} via --continue" >&2
  if run -c -p "Continue. Finish the annotation package: write README.md, then present the confidence summary."; then
    exit 0
  fi
done

exit 1
