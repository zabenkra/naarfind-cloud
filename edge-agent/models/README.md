# Fire/Smoke YOLO Models

Place your trained model here.

## Production (Raspberry Pi 4 — NCNN)

Export from Ultralytics:

```bash
yolo export model=fire_smoke_yolov8n.pt format=ncnn imgsz=416
```

Copy the exported folder to:

```
edge-agent/models/fire_smoke_yolov8n_ncnn_model/
```

Set in `.env`:

```
MODEL_PATH=./models/fire_smoke_yolov8n_ncnn_model
```

## Fallback / testing (.pt)

```
edge-agent/models/fire_smoke_yolov8n.pt
```

```
MODEL_FALLBACK_PATH=./models/fire_smoke_yolov8n.pt
```

## Classes

The model must detect:

- `fire` (class 0)
- `smoke` (class 1)

Names are read from `model.names` or default to fire/smoke by index.
