# NaarFind Production Deployment

Deploy NaarFind using:

| Component | Platform | Config |
|-----------|----------|--------|
| Backend API | Render Web Service | `DATABASE_URL`, `PORT`, `JWT_*`, `FRONTEND_URL`, R2 vars |
| PostgreSQL | Render Managed PostgreSQL | Linked as `DATABASE_URL` |
| Frontend | Vercel | `VITE_API_URL`, `VITE_WS_URL` |
| Media | Cloudflare R2 | Edge agent + backend env |
| Devices | Raspberry Pi | `CLOUD_API_URL` → Render backend URL |

**Local development only:** `docker compose up --build` (see bottom).

---

## Architecture

```
Vercel (React)  --HTTPS-->  Render (FastAPI)
       |                           |
       +-------- wss:// ------------+
                                   |
                            Render PostgreSQL
                                   |
Raspberry Pi ----HTTPS POST--------+
       |
Cloudflare R2 (images/videos)
```

---

## 1. Push to GitHub

```bash
git add .
git commit -m "Prepare production deployment"
git push origin main
```

Never commit `.env` — only `.env.example` and `frontend/.env.example`.

---

## 2. Render PostgreSQL

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **PostgreSQL**
2. Name: `naarfind-db`
3. Same region as backend
4. Create → copy **Internal Database URL**

Render may use `postgres://` — the backend converts it to `postgresql://` automatically.

---

## 3. Render Backend Web Service

1. **New +** → **Web Service** → connect GitHub repo
2. Settings:

| Field | Value |
|-------|--------|
| **Root Directory** | `backend` |
| **Runtime** | Docker |
| **Dockerfile Path** | `Dockerfile` |
| **Instance Type** | Starter or higher |

3. **Start Command** (auto from Docker, or set manually):

```bash
./start.sh
```

Equivalent to:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render injects `PORT` automatically — do not hardcode it.

---

## 4. Render environment variables

Web Service → **Environment** → add:

| Variable | Value | Required |
|----------|--------|----------|
| `ENVIRONMENT` | `production` | Yes |
| `DATABASE_URL` | Render Postgres **Internal** URL | Yes |
| `JWT_SECRET_KEY` | `openssl rand -hex 32` | Yes |
| `JWT_ALGORITHM` | `HS256` | Yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Yes |
| `FRONTEND_URL` | `https://your-app.vercel.app` | Yes |
| `R2_ACCOUNT_ID` | Cloudflare account ID | If using R2 |
| `R2_ACCESS_KEY_ID` | R2 token access key | If using R2 |
| `R2_SECRET_ACCESS_KEY` | R2 token secret | If using R2 |
| `R2_BUCKET` | e.g. `naarfind-media` | If using R2 |
| `R2_PUBLIC_URL` | e.g. `https://pub-xxx.r2.dev` | If using R2 |
| `ALLOWED_MEDIA_URL_PREFIXES` | Same as `R2_PUBLIC_URL` | Optional |

Do **not** set `PORT` — Render provides it.

### CORS

The backend reads `FRONTEND_URL` and allows:

- `http://localhost:5173` (local dev)
- Your `FRONTEND_URL` (production Vercel app)

Set `FRONTEND_URL` to the **exact** Vercel URL including `https://`.

---

## 5. Deploy backend & verify

1. Click **Deploy** on Render
2. Wait for build to complete
3. Test health:

```bash
curl https://YOUR-SERVICE.onrender.com/health
```

Expected:

```json
{"status":"healthy","database":"connected"}
```

4. Create super admin (one-time):

```bash
# Render Shell, or locally with External DATABASE_URL
cd backend
export ENVIRONMENT=production
export DATABASE_URL="your-render-postgres-url"
export JWT_SECRET_KEY="same-as-render-env"
python scripts/create_super_admin.py \
  --email admin@yourdomain.com \
  --password 'YourSecurePass123!' \
  --name 'Platform Admin'
```

---

## 6. Vercel frontend

1. [vercel.com](https://vercel.com) → **Add New** → **Project**
2. Import GitHub repo
3. Settings:

| Field | Value |
|-------|--------|
| **Root Directory** | `frontend` |
| **Framework Preset** | Vite |
| **Build Command** | `npm run build` |
| **Output Directory** | `dist` |

`vercel.json` is included for React Router SPA routing.

---

## 7. Vercel environment variables

Project → **Settings** → **Environment Variables**:

| Variable | Production value |
|----------|------------------|
| `VITE_API_URL` | `https://YOUR-SERVICE.onrender.com` |
| `VITE_WS_URL` | `wss://YOUR-SERVICE.onrender.com/ws/events` |

Use **wss://** (not `ws://`) for production WebSocket.

Redeploy after adding variables.

---

## 8. Deploy frontend & test

1. Deploy on Vercel
2. Open `https://your-app.vercel.app`
3. Register or log in
4. Confirm dashboard loads
5. DevTools → Network → WS → should show `101` on `wss://.../ws/events?token=...`

---

## 9. Custom domain (optional)

### Vercel (frontend)

1. Vercel → Domains → add `app.yourdomain.com`
2. Cloudflare DNS: CNAME → Vercel
3. Update Render `FRONTEND_URL=https://app.yourdomain.com`
4. Redeploy backend

### Render (API)

1. Render → Custom Domains → `api.yourdomain.com`
2. Update Vercel env:
   - `VITE_API_URL=https://api.yourdomain.com`
   - `VITE_WS_URL=wss://api.yourdomain.com/ws/events`

---

## 10. Raspberry Pi (production)

`edge-agent/.env`:

```env
CLOUD_API_URL=https://YOUR-SERVICE.onrender.com
DEVICE_UID=pi-001
DEVICE_API_KEY=your-device-key
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=naarfind-media
R2_PUBLIC_URL=https://pub-xxx.r2.dev
```

Register device in production DB (assign to a site under your org):

```sql
INSERT INTO devices (site_id, name, device_uid, api_key, is_online)
VALUES (
  (SELECT id FROM sites WHERE organization_id = 1 LIMIT 1),
  'Pi 001', 'pi-001', 'YOUR_DEVICE_API_KEY', false
);
```

Test:

```bash
cd edge-agent && python agent.py --test
```

---

## Local development (docker-compose only)

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local   # optional

docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

Local `.env` provides `DATABASE_URL` for the compose Postgres service.

---

## Environment variable reference

### Backend (Render)

```
ENVIRONMENT=production
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
FRONTEND_URL=https://your-app.vercel.app
PORT                    # auto-set by Render
```

### Frontend (Vercel)

```
VITE_API_URL=https://your-api.onrender.com
VITE_WS_URL=wss://your-api.onrender.com/ws/events
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CORS error | `FRONTEND_URL` on Render must match Vercel URL exactly |
| WebSocket fails | Use `wss://` in `VITE_WS_URL` |
| 503 on `/health` | Use Render Postgres **Internal** `DATABASE_URL` |
| Registration 500 | Check `JWT_SECRET_KEY` is set on Render |
| Empty dashboard | Assign devices to a site in your organization |
| WS auth failed | Log in again after deploy; same `JWT_SECRET_KEY` everywhere |

---

## Security checklist

- [ ] Strong `JWT_SECRET_KEY` (32+ random bytes)
- [ ] `ENVIRONMENT=production` on Render
- [ ] `FRONTEND_URL` = production Vercel URL
- [ ] R2 keys only on backend + Pi — never in frontend
- [ ] Device API keys only on Pi
- [ ] `.env` not committed to git
