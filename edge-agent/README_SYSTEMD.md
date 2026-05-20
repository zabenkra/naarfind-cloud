# NaarFind Edge Agent — systemd (Raspberry Pi)

**Install path:** `/home/pi/naarfind-cloud/edge-agent`

---

## 0. Sync code (required for detection CLI)

If you see:
```
agent.py: error: one of the arguments --test --heartbeat-test --run --r2-test is required
```

Your `agent.py` is outdated. Fix:

```bash
cd /home/pi/naarfind-cloud
git pull
cd edge-agent
bash scripts/verify_cli.sh
python agent.py --version
# Must show: NaarFind edge-agent 2.1.0
python agent.py --help
# Must list: --camera-test --detect --detect-debug
```

---

## 1. One-time setup

```bash
cd /home/pi/naarfind-cloud/edge-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-pi.txt
cp .env.example .env
```

Edit `.env`:

```env
CLOUD_API_URL=https://your-api.up.railway.app
DEVICE_UID=pi-001
DEVICE_API_KEY=your-secret-key
AGENT_VERSION=1.0.0
MODEL_PATH=./models/fire_smoke_yolov8n_ncnn_model
ENABLE_DEBUG_WINDOW=false
```

---

## 2. Test before systemd

```bash
source venv/bin/activate

# API
python agent.py --heartbeat-test

# Camera → snapshots/camera_test.jpg
python agent.py --camera-test

# Detection (needs model in models/)
python agent.py --detect-debug

# Full production (manual)
python agent.py --run
```

---

## 3. Install service

```bash
sudo bash scripts/install_service.sh
sudo systemctl status naarfind-agent
```

Runs: `python agent.py --run` (heartbeat + detection; heartbeat only if no model).

---

## 4. Logs

```bash
journalctl -u naarfind-agent -f
```

Look for:
- `camera initialized`
- `model loaded` or `model missing`
- `Heartbeat OK`
- `processed_fps=... infer=...ms`
- `ALERT` / `Alert sent`

---

## 5. Commands reference

| Command | Use |
|---------|-----|
| `python agent.py --camera-test` | Verify CSI camera |
| `python agent.py --detect-debug` | Test AI + logs before production |
| `python agent.py --detect` | Headless detection test |
| `python agent.py --run` | Production (same as systemd) |
| `python agent.py --heartbeat-test` | Cloud API check |

---

## 6. Uninstall

```bash
sudo bash scripts/uninstall_service.sh
```
