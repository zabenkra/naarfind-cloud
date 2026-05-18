# NaarFind Edge Agent

Python edge agent for Raspberry Pi that uploads fire media to **Cloudflare R2** and reports events to NaarFind Cloud.

## Prerequisites

- Python 3.10+
- NaarFind Cloud API running
- Cloudflare R2 bucket with public access (custom domain or `r2.dev` URL)
- Device registered in database (`device_uid` + `api_key`)

## Setup

```bash
cd edge-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit credentials in the **project root** `.env` (recommended) or `edge-agent/.env` for overrides.  
`env_loader.py` loads both automatically. Never commit `.env`.

### Environment loading order

1. Process environment (Docker `env_file`, shell exports)
2. `<project-root>/.env`
3. `edge-agent/.env` (overrides)

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DEVICE_UID` | Yes | e.g. `pi-001` |
| `DEVICE_API_KEY` | Yes | Matches cloud DB |
| `CLOUD_API_URL` | Yes | e.g. `http://192.168.1.100:8000` |
| `R2_ACCOUNT_ID` | For uploads | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | For uploads | R2 API token access key |
| `R2_SECRET_ACCESS_KEY` | For uploads | R2 API token secret |
| `R2_BUCKET` | For uploads | Bucket name |
| `R2_PUBLIC_URL` | For uploads | Public base URL (no trailing slash) |

## Test without files (URLs only)

```bash
python agent.py --test
```

## Test R2 upload only (sample image → public URL)

```bash
python test_r2_upload.py
# or
python agent.py --r2-test
```

Creates `samples/test-fire.png` if missing, uploads to R2, prints the public URL.

## Test with R2 upload + fire event

```bash
python agent.py --test --image ./samples/test-fire.png --video ./samples/clip.mp4
```

## Docker (uses root `.env`)

```bash
cd ..   # project root
docker compose --profile edge run --rm edge-agent
```

Upload paths in R2:

- `images/YYYY/MM/DD/{device_uid}_{timestamp}.jpg`
- `videos/YYYY/MM/DD/{device_uid}_{timestamp}.mp4`

## Use in detection code

```python
from agent import send_fire_event_with_media

send_fire_event_with_media(
    confidence=0.91,
    temperature=48.0,
    image_path="/tmp/snapshot.jpg",
    video_path="/tmp/clip.mp4",
)
```

Or upload separately:

```python
from storage.r2_uploader import R2Uploader
from agent import send_fire_event

uploader = R2Uploader()
image_url = uploader.upload_image("/tmp/snapshot.jpg")
video_url = uploader.upload_video("/tmp/clip.mp4")

send_fire_event(confidence=0.91, image_url=image_url, video_url=video_url)
```

## Register device (one-time)

```bash
docker exec -it naarfind_db psql -U naarfind -d naarfind -c "
INSERT INTO devices (site_id, name, device_uid, api_key, is_online)
VALUES (NULL, 'Pi Sensor 001', 'pi-001', 'SUPER_SECRET_KEY_123', false)
ON CONFLICT (device_uid) DO NOTHING;
"
```
