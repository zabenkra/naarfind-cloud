#!/usr/bin/env bash
# Verify agent.py on this machine supports detection CLI (run on Raspberry Pi).
set -euo pipefail

AGENT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_PY="${AGENT_DIR}/agent.py"

echo "Checking ${AGENT_PY}..."

for flag in camera-test detect detect-debug; do
  if ! grep -q "\"--${flag}\"" "${AGENT_PY}" 2>/dev/null && ! grep -q "'--${flag}'" "${AGENT_PY}" 2>/dev/null; then
    echo "OUTDATED: missing --${flag} in agent.py"
    echo "Run: cd ~/naarfind-cloud && git pull"
    exit 1
  fi
done

if [[ ! -d "${AGENT_DIR}/detector" ]]; then
  echo "OUTDATED: missing detector/ package"
  exit 1
fi

echo "OK: agent.py supports --camera-test --detect --detect-debug"
echo "Run: python agent.py --version"
python3 "${AGENT_PY}" --version 2>/dev/null || true
