#!/usr/bin/env bash
# Install NaarFind edge-agent as a systemd service on Raspberry Pi.
set -euo pipefail

AGENT_DIR="/home/pi/naarfind-cloud/edge-agent"
SERVICE_NAME="naarfind-agent"
SERVICE_SRC="${AGENT_DIR}/systemd/${SERVICE_NAME}.service"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"
VENV_PYTHON="${AGENT_DIR}/venv/bin/python"
ENV_FILE="${AGENT_DIR}/.env"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run as root: sudo bash scripts/install_service.sh"
  exit 1
fi

if [[ ! -d "${AGENT_DIR}" ]]; then
  echo "Expected directory not found: ${AGENT_DIR}"
  exit 1
fi

if [[ ! -x "${VENV_PYTHON}" ]]; then
  echo "Virtualenv not found. Create it first:"
  echo "  cd ${AGENT_DIR}"
  echo "  python3 -m venv venv"
  echo "  source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Warning: ${ENV_FILE} not found."
  echo "  cp ${AGENT_DIR}/.env.example ${ENV_FILE}"
  echo "  Then edit CLOUD_API_URL, DEVICE_UID, DEVICE_API_KEY, AGENT_VERSION"
  read -r -p "Continue without .env? [y/N] " reply
  if [[ "${reply}" != [yY] ]]; then
    exit 1
  fi
fi

if [[ ! -f "${SERVICE_SRC}" ]]; then
  echo "Service template missing: ${SERVICE_SRC}"
  exit 1
fi

cp "${SERVICE_SRC}" "${SERVICE_DEST}"
chmod 644 "${SERVICE_DEST}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo ""
echo "Installed and started ${SERVICE_NAME}."
echo "  sudo systemctl status ${SERVICE_NAME}"
echo "  journalctl -u ${SERVICE_NAME} -f"
