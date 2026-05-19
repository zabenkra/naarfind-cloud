# NaarFind Edge Agent (Raspberry Pi)

Production agent for a **single device** (`pi-001`). Sends heartbeats every 30 seconds and fire events when detection runs.

## Prerequisites

- Raspberry Pi with Python 3.10+
- Device registered in NaarFind Cloud (`device_uid` + `api_key`, site = Main Site)
- Production API URL (Railway / Render)

## Environment variables

| Variable | Required | Example |
|----------|----------|---------|
| `CLOUD_API_URL` | Yes | `https://your-api.railway.app` |
| `DEVICE_UID` | Yes | `pi-001` |
| `DEVICE_API_KEY` | Yes | (matches DB, never expose in frontend) |
| `AGENT_VERSION` | Yes | `1.0.0` |
| `HEARTBEAT_INTERVAL_SECONDS` | No | `30` (default) |
| R2 vars | For media uploads | See root `.env.example` |

Copy `edge-agent/.env.example` to `edge-agent/.env` or set vars in `/home/pi/naarfind/.env` at project root.

## Register device (one-time)

If `pi-001` is not in the database yet:

```bash
cd backend
export DATABASE_URL="your-postgres-url"
export DEVICE_API_KEY="your-secret-key"
python scripts/seed_pi_device.py
```

Or via SQL (assign to Main Site):

```sql
INSERT INTO devices (site_id, name, device_uid, api_key, is_online)
SELECT s.id, 'Raspberry Pi 01', 'pi-001', 'YOUR_API_KEY', false
FROM sites s WHERE s.name = 'Main Site' LIMIT 1;
```

## Install on Raspberry Pi

```bash
cd /home/pi/naarfind-cloud/edge-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # CLOUD_API_URL, DEVICE_API_KEY, AGENT_VERSION
```

## Production run (heartbeat loop)

```bash
source .venv/bin/activate
python agent.py --run
```

This will:

- `POST /api/device/heartbeat` every 30s (CPU temp, RAM, disk, camera, agent version)
- Call `check_fire_detection()` each cycle — implement your ML/camera logic there
- Queue fire events to `data/pending_fire_events.json` if the API is down, replay when back

### systemd service (recommended)

See **[README_SYSTEMD.md](./README_SYSTEMD.md)** for install scripts and exact commands:

```bash
cd /home/pi/naarfind-cloud/edge-agent
sudo bash scripts/install_service.sh
sudo systemctl status naarfind-agent
journalctl -u naarfind-agent -f
```

## Test locally

**Heartbeat** (backend must be running):

```bash
curl -X POST http://localhost:8000/api/device/heartbeat \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: SUPER_SECRET_KEY_123" \
  -d '{
    "device_uid": "pi-001",
    "cpu_temp": 52.1,
    "ram_usage": 41.2,
    "disk_usage": 28.5,
    "camera_status": "ok",
    "agent_version": "1.0.0"
  }'
```

**Fire event test:**

```bash
python agent.py --test
```

**R2 upload test:**

```bash
python agent.py --r2-test
```

## Plug in fire detection

Edit `check_fire_detection()` in `agent.py`:

```python
def check_fire_detection() -> bool:
    # return True when your model detects fire
    return my_detector.poll()
```

When `True`, the agent calls `send_fire_event()` automatically.

## Offline queue

Failed fire events are stored in `edge-agent/data/pending_fire_events.json` and replayed after the next successful heartbeat.

## Docker (dev only)

From project root:

```bash
docker compose --profile edge run --rm edge-agent
```
