# Cloudflare R2 Setup for NaarFind

## 1. Create a bucket

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. Go to **R2 Object Storage** → **Create bucket**
3. Name it e.g. `naarfind-media`
4. Choose a location close to your devices

## 2. Enable public access

**Option A — R2.dev subdomain (quick)**

1. Open the bucket → **Settings**
2. Under **Public access**, enable **Allow Access** / **R2.dev subdomain**
3. Copy the public URL, e.g. `https://pub-xxxxxxxx.r2.dev`

**Option B — Custom domain (production)**

1. Connect a domain (e.g. `media.yourdomain.com`) under bucket settings
2. Use `https://media.yourdomain.com` as `R2_PUBLIC_URL`

## 3. Create API token

1. **R2** → **Manage R2 API Tokens** → **Create API Token**
2. Permissions: **Object Read & Write** on your bucket
3. Save **Access Key ID** and **Secret Access Key**
4. Note your **Account ID** (R2 overview page)

## 4. Configure edge-agent `.env`

```env
R2_ACCOUNT_ID=your_account_id
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET=naarfind-media
R2_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev
```

## 5. Configure backend `.env` (root)

Restrict accepted media URLs to your public R2 host:

```env
R2_PUBLIC_URL=https://pub-xxxxxxxx.r2.dev
```

Restart backend: `docker compose up --build`

## 6. CORS (if videos/images fail in browser)

In bucket **Settings** → **CORS policy**, add:

```json
[
  {
    "AllowedOrigins": ["http://localhost:5173", "https://your-frontend.com"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }
]
```

## 7. Test upload

```bash
cd edge-agent
source .venv/bin/activate
python agent.py --test --image ./fire.jpg --video ./clip.mp4
```

Check the Fire Events page for thumbnails and video playback.
