# NaarFind Edge Agent — systemd (Raspberry Pi)

Run `python agent.py --run` automatically on boot with automatic restarts and journal logs.

**Install path:** `/home/pi/naarfind-cloud/edge-agent`

---

## 1. One-time setup

```bash
cd /home/pi/naarfind-cloud/edge-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with production values:

```env
CLOUD_API_URL=https://your-api.example.com
DEVICE_UID=pi-001
DEVICE_API_KEY=your-secret-key
AGENT_VERSION=1.0.0
```

Use simple `KEY=value` lines (no `export`). systemd reads this file via `EnvironmentFile=`.

---

## 2. Install the service

```bash
cd /home/pi/naarfind-cloud/edge-agent
sudo bash scripts/install_service.sh
```

This copies `systemd/naarfind-agent.service` to `/etc/systemd/system/`, enables it on boot, and starts it now.

---

## 3. Check status

```bash
sudo systemctl status naarfind-agent
```

Expected: `Active: active (running)`.

---

## 4. View logs (live)

```bash
journalctl -u naarfind-agent -f
```

Recent logs without follow:

```bash
journalctl -u naarfind-agent -n 100 --no-pager
```

Since last boot:

```bash
journalctl -u naarfind-agent -b
```

---

## 5. Service controls

```bash
sudo systemctl restart naarfind-agent
sudo systemctl stop naarfind-agent
sudo systemctl start naarfind-agent
```

---

## 6. Uninstall

```bash
cd /home/pi/naarfind-cloud/edge-agent
sudo bash scripts/uninstall_service.sh
```

Stops and disables the service and removes `/etc/systemd/system/naarfind-agent.service`. Your code, `venv`, and `.env` stay on disk.

---

## Service details

| Setting | Value |
|---------|--------|
| Unit file | `systemd/naarfind-agent.service` |
| After | `network-online.target` |
| Command | `venv/bin/python agent.py --run` |
| Env | `/home/pi/naarfind-cloud/edge-agent/.env` |
| Restart | `always` (5s delay) |
| User | `pi` |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `venv/bin/python: No such file` | Run `python3 -m venv venv` in `edge-agent` |
| Heartbeat 401 | `DEVICE_API_KEY` in `.env` must match database |
| Service exits immediately | `journalctl -u naarfind-agent -n 50` |
| `.env` ignored | No spaces around `=`; restart after edits: `sudo systemctl restart naarfind-agent` |
| Wrong API URL | Set `CLOUD_API_URL` in `.env`, then restart |

---

## Different install path

If the repo is not under `/home/pi/naarfind-cloud/edge-agent`, edit paths in `systemd/naarfind-agent.service` before running `install_service.sh`.
