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

## Production run (heartbeat + AI detection)

```bash
source venv/bin/activate
python agent.py --run
```

This will:

- Run **heartbeat in a background thread** every 30s
- Run **YOLO fire/smoke detection** in a separate thread (CSI camera + temporal filter)
- Send alerts to cloud + optional R2 snapshot upload

See **[README_DETECTION.md](./README_DETECTION.md)** for model setup, camera test, and tuning.

### systemd service (recommended)

See **[README_SYSTEMD.md](./README_SYSTEMD.md)** for install scripts and exact commands:

```bash
cd /home/pi/naarfind-cloud/edge-agent
sudo bash scripts/install_service.sh
sudo systemctl status naarfind-agent
journalctl -u naarfind-agent -f
```

## CLI modes

| Flag | Description |
|------|-------------|
| `--camera-test` | CSI/OpenCV → `snapshots/camera_test.jpg` |
| `--detect` | Detection + heartbeat (no GUI) |
| `--detect-debug` | Verbose logs; GUI only if `ENABLE_DEBUG_WINDOW=true` |
| `--run` | Production: heartbeat + detection |
| `--heartbeat-test` | Send one heartbeat |
| `--test` | Send one test fire event |
| `--r2-test` | Upload sample image to R2 |
| `--image` / `--video` | Media paths (with `--test` only) |

List all modes: `python agent.py --help`

## Test on Raspberry Pi

```bash
cd /home/pi/naarfind-cloud/edge-agent
source venv/bin/activate
pip install -r requirements-pi.txt

# 1) Camera
python agent.py --camera-test

# 2) Detection (no GUI)
python agent.py --detect

# 3) Detection debug (GUI only if ENABLE_DEBUG_WINDOW=true)
ENABLE_DEBUG_WINDOW=true python agent.py --detect-debug

# 4) Production
python agent.py --run
```

## Test locally

**Heartbeat** (backend must be running):

```bash
cd edge-agent
source venv/bin/activate
python agent.py --heartbeat-test
```

Expected output:

```
Sending heartbeat...
Heartbeat success
```

**Fire event test:**

```bash
python agent.py --test
```

**Fire event with R2 media:**

```bash
python agent.py --test --image ./samples/test-fire.png --video ./samples/clip.mp4
```

**R2 upload test:**

```bash
python agent.py --r2-test
```

**Production loop (manual):**

```bash
python agent.py --run
```

## Fire/smoke AI detection

Place YOLO model in `models/` (see `models/README.md`). Configure thresholds in `.env`:

```
MODEL_PATH=./models/fire_smoke_yolov8n_ncnn_model
FIRE_THRESHOLD=0.55
SMOKE_THRESHOLD=0.65
```

Detection uses temporal confirmation and 30s cooldown to limit false alarms.

## Offline queue

Failed fire events are stored in `edge-agent/data/pending_fire_events.json` and replayed after the next successful heartbeat.

## Docker (dev only)

From project root:

```bash
docker compose --profile edge run --rm edge-agent
```
