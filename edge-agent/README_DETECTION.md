# NaarFind Edge Agent — Fire/Smoke AI Detection

YOLO-based fire and smoke detection for Raspberry Pi 4 with CSI camera. Heartbeat runs in a **separate thread** so detection never blocks cloud connectivity.

## Raspberry Pi install

```bash
cd /home/pi/naarfind-cloud/edge-agent
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-pi.txt
cp .env.example .env
nano .env
```

## Where to put the model

**Production (NCNN — fastest on Pi 4):**

```
/home/pi/naarfind-cloud/edge-agent/models/fire_smoke_yolov8n_ncnn_model/
```

Export on a desktop machine:

```bash
pip install ultralytics
yolo export model=fire_smoke_yolov8n.pt format=ncnn imgsz=416
# Copy the generated fire_smoke_yolov8n_ncnn_model/ folder to the Pi
```

**Fallback (.pt for testing):**

```
/home/pi/naarfind-cloud/edge-agent/models/fire_smoke_yolov8n.pt
```

See `models/README.md` for details.

## Test camera

```bash
source venv/bin/activate
python agent.py --camera-test
```

Expected: `Camera OK — backend=picamera2` (or `opencv` on laptop).

## Test detection

```bash
# With debug window (Pi desktop or X11)
ENABLE_DEBUG_WINDOW=true python agent.py --detect-debug

# Headless production-style
python agent.py --detect
```

Logs show inference time, processed FPS, and alerts.

## Test heartbeat + API

```bash
python agent.py --heartbeat-test
python agent.py --test
```

## Production run

```bash
python agent.py --run
```

- Heartbeat thread: every 30s
- Detection thread: camera + YOLO + temporal filter + cooldown
- Alerts: snapshot → R2 (if configured) → `POST /api/device/events/fire`

## systemd (boot)

```bash
sudo bash scripts/install_service.sh
sudo systemctl status naarfind-agent
journalctl -u naarfind-agent -f
```

Ensure `.env` has `CLOUD_API_URL`, model path, and R2 vars. The service runs `python agent.py --run`.

To use detection under systemd, the unit already runs `--run` (heartbeat + detection).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No YOLO model found` | Copy NCNN folder or `.pt` to `models/`; check `MODEL_PATH` |
| `picamera2 unavailable` | `sudo apt install -y python3-picamera2`; or uses OpenCV index 0 |
| Camera test fails | Enable camera in `raspi-config`; check CSI ribbon |
| Heartbeat failed | Check `CLOUD_API_URL`, `DEVICE_API_KEY`, device in DB |
| R2 upload skipped | Set `R2_*` env vars or `UPLOAD_SNAPSHOTS=false` |
| False alarms | Raise `FIRE_THRESHOLD` / `SMOKE_THRESHOLD`; increase temporal windows |
| Slow inference | Use NCNN model; increase `PROCESS_EVERY_N_FRAMES`; lower `MODEL_IMG_SIZE` |
| 403 / 404 API | Use `POST` heartbeat; correct Railway URL |

## Performance tips (Pi 4)

- `MODEL_PATH` → NCNN export (not `.pt` in production)
- `MODEL_IMG_SIZE=416` (default)
- `PROCESS_EVERY_N_FRAMES=3` → process ~7 FPS if camera is 20 FPS
- `ENABLE_DEBUG_WINDOW=false` in production
- No GUI under systemd

## Detection pipeline

1. Capture frame (picamera2 or OpenCV)
2. Every Nth frame → YOLO inference
3. Temporal filter + **instant dual confirm** (fire+smoke same frame)
4. Cooldown 30s between cloud alerts
5. Snapshot with boxes → R2 → `POST /api/device/events/fire`

Debug temporal state on Pi:
```env
TEMPORAL_DEBUG=true
```

Logs on alert:
```
FIRE_SMOKE CONFIRMED
sending alert | type=fire_smoke fire=0.77 smoke=0.69
snapshot saved path=...
snapshot uploaded url=...
event sent successfully event_id=...
```

Pending (before confirm):
```
confirmation pending | fire 2/3 (hist=110) smoke 3/4 (hist=1110) both 1/2 (hist=10)
```
