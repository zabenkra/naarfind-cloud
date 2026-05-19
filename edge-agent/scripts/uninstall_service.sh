#!/usr/bin/env bash
# Remove NaarFind edge-agent systemd service.
set -euo pipefail

SERVICE_NAME="naarfind-agent"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/uninstall_service.sh"
  exit 1
fi

if systemctl is-active --quiet "${SERVICE_NAME}" 2>/dev/null; then
  systemctl stop "${SERVICE_NAME}"
fi

if systemctl is-enabled --quiet "${SERVICE_NAME}" 2>/dev/null; then
  systemctl disable "${SERVICE_NAME}"
fi

if [[ -f "${SERVICE_DEST}" ]]; then
  rm -f "${SERVICE_DEST}"
fi

systemctl daemon-reload
systemctl reset-failed "${SERVICE_NAME}" 2>/dev/null || true

echo "Uninstalled ${SERVICE_NAME}."
echo "Agent code and venv in /home/pi/naarfind-cloud/edge-agent were not deleted."
