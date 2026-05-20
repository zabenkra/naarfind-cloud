# NaarFind Edge Agent (Raspberry Pi)

Production agent for **pi-001**: heartbeat, YOLO fire/smoke detection, cloud alerts.

## Quick start (Raspberry Pi)

```bash
cd /home/pi/naarfind-cloud
git pull

cd edge-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-pi.txt
cp .env.example .env
nano .env

# Verify CLI is up to date (must print 2.1.0+)
bash scripts/verify_cli.sh
python agent.py --version
python agent.py --help
```

If `--help` only lists `--test --heartbeat-test --run --r2-test`, your `agent.py` is **outdated** — run `git pull` from the project root.

---

## CLI commands

| Command | Description |
|---------|-------------|
| `python agent.py --camera-test` | One frame → `snapshots/camera_test.jpg` |
| `python agent.py --detect` | Detection + heartbeat (no GUI) |
| `python agent.py --detect-debug` | Verbose logs; GUI only if `ENABLE_DEBUG_WINDOW=true` |
| `python agent.py --run` | Production: heartbeat + detection |
| `python agent.py --heartbeat-test` | One heartbeat to cloud |
| `python agent.py --test` | One test fire event |
| `python agent.py --r2-test` | Test R2 upload |
| `python agent.py --version` | Show CLI version (2.1.0 = detection support) |

---

## Test camera

```bash
source venv/bin/activate
python agent.py --camera-test
```

**Expected:**
```
SUCCESS: Camera test passed
  backend=picamera2
  saved=/home/pi/naarfind-cloud/edge-agent/snapshots/camera_test.jpg
```

---

## Test detection

**1. Place model** in `models/` (see `models/README.md`).

**2. Headless detection + heartbeat:**
```bash
python agent.py --detect
```

**3. Debug mode (verbose logs):**
```bash
python agent.py --detect-debug
```

**4. With live preview** (Pi desktop / X11 only):
```bash
# In .env: ENABLE_DEBUG_WINDOW=true
python agent.py --detect-debug
```

**If model missing:** heartbeat keeps running; logs `model missing`.

---

## Production mode

```bash
python agent.py --run
```

Or use systemd: **[README_SYSTEMD.md](./README_SYSTEMD.md)**

```bash
sudo bash scripts/install_service.sh
journalctl -u naarfind-agent -f
```

---

## Environment

Copy `edge-agent/.env.example` → `.env`. Key vars:

```env
CLOUD_API_URL=https://your-api.up.railway.app
DEVICE_UID=pi-001
DEVICE_API_KEY=your-key
MODEL_PATH=./models/fire_smoke_yolov8n_ncnn_model
MODEL_FALLBACK_PATH=./models/fire_smoke_yolov8n.pt
ENABLE_DEBUG_WINDOW=false
```

See **[README_DETECTION.md](./README_DETECTION.md)** for model export and tuning.

---

## Package layout

```
edge-agent/
  agent.py              # CLI entry
  detector/
    camera.py           # picamera2 + OpenCV
    inference.py        # YOLOFireSmokeInference
    fire_detector.py    # detection loop
    temporal_filter.py
    utils.py
  models/               # place .pt or NCNN folder here
  snapshots/            # camera_test + alerts
```
