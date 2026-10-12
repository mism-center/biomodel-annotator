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

# Resolve the provider from the credential that is actually present. Failing here
# with a named variable beats pi failing several minutes into a build with a
# stream error that looks like a model problem.
provider="${AI_PROVIDER:-}"
model="${AI_MODEL:-}"
if [ -n "${AZURE_OPENAI_API_KEY:-}" ]; then
  : "${AZURE_OPENAI_BASE_URL:?AZURE_OPENAI_API_KEY is set but AZURE_OPENAI_BASE_URL is not}"
  # pi 1.0 renamed the provider id `azure-openai-responses` -> `azure`. Ask the
  # installed pi which one it knows rather than guessing from a version string.
  if [ -z "$provider" ]; then
    if pi --list-models 2>/dev/null | awk '{print $1}' | grep -qx azure; then
      provider=azure
    else
      provider=azure-openai-responses
    fi
  fi
  model="${model:-gpt-5.6-luna}"
elif [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  model="${model:-anthropic/claude-opus-4-5}"
else
  echo "envbuild: no model credential in the environment." >&2
  echo "  Azure    : export AZURE_OPENAI_BASE_URL and AZURE_OPENAI_API_KEY" >&2
  echo "  Anthropic: export ANTHROPIC_API_KEY" >&2
  echo "Export it on the host and pass it through; do not hardcode it." >&2
  exit 78                     # EX_CONFIG -- a setup fault, not a job failure
fi

PROVIDER_ARGS=()
[ -n "$provider" ] && PROVIDER_ARGS=(--provider "$provider")
echo "envbuild: provider=${provider:-<pi default>} model=${model}" >&2
# The driver stamps these onto every attempt/verdict row as `run.agent_model`
# and `run.agent_provider` -- so the RESOLVED values must be in the environment
# the agent's shell inherits, not just in this script's locals.
export AI_MODEL="$model" AI_PROVIDER="${provider:-pi-default}" AI_RUNTIME_VERSION="pi $(pi --version 2>/dev/null | head -1)"

run() {
  pi --approve --stream=all \
    ${model:+--model "$model"} \
    "${PROVIDER_ARGS[@]}" \
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
