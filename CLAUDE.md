# Perfect Stroke Project

A watercolor/painting brushstroke collection and charity project. The concept: every brushstroke represents "one human helping another." The collection has ~1,300 brushstrokes with ~800 photographed and uploaded.

## Architecture

### Active Repos (all in ~/www/)

| Repo | Purpose | Stack | Port |
|------|---------|-------|------|
| `perfect-stroke-project` | Backend API | Django 5.1, DRF, PostgreSQL, Cloudflare R2 | 8200 |
| `react-perfect-stroke` | Public website | React 18, Parcel, styled-components, Three.js | 1240 |
| `cms-react-psp` | Admin CMS | React 18, TypeScript, Parcel | 1239 |

### Archived/Deleted Repos (backed up on Bitbucket under teamhakomo)

- `api-perfect-stroke` — Old .NET Core 2.2 backend (2020), used AWS S3 + SQL Server
- `cms-perfect-stroke` — Old React 16 admin CMS (2020), used react-admin

## Deployment

**Server:** Contabo VPS (`ssh contabo`), root access, Ubuntu, IP: 62.171.136.238

| Component | URL | How it runs |
|-----------|-----|-------------|
| Django API | `api.perfectstrokeproject.com` | systemd `perfectstroke.service` → gunicorn on 127.0.0.1:8200 |
| Public site | `perfectstrokeproject.com` | nginx serves static files from `/var/www/perfect-stroke/frontend/` |
| R2 images | `dns.perfectstrokeproject.com` | Cloudflare R2 bucket `perfect-stroke-project` |

**Nginx config:** `/etc/nginx/sites-available/perfect-stroke`
**Systemd service:** `/etc/systemd/system/perfectstroke.service`
**Server project dir:** `/var/www/perfect-stroke/`

### Deploy process (manual)

- **API:** push to server, restart service (`systemctl restart perfectstroke`)
- **Frontend:** build locally (`cd ~/www/react-perfect-stroke && npm run build`), then `scp -r build/* contabo:/var/www/perfect-stroke/frontend/`
- **DNS/SSL:** managed through Cloudflare (origin certs at `/etc/ssl/perfectstroke/`)

## Backend (perfect-stroke-project)

### Key files
- `perfectstroke/settings.py` — Django settings, R2 config
- `api/models.py` — all models (Stroke, Paint, Paper, Tool, Brand, etc.)
- `api/views.py` — REST viewsets + custom frontend endpoints
- `api/serializers.py` — DRF serializers, R2 image URL construction
- `api/services/file_service.py` — R2 upload + image resize pipeline
- `r2_image_map.json` — maps stroke IDs to R2 file paths (798 entries)
- `import_data.py` — bulk import from legacy SQL Server CSV exports

### Models
Core: `Stroke`, `Paint`, `Paper`, `Tool`, `Brand`, `BrandModel`, `Color`, `Store`, `Pigment`, `File`
Supporting: `PaperMaterial`, `PaperSurface`, `ToolType`, `ToolShape`, `ToolSize`, `BrushHairType`
Many-to-many: `StrokePaint`, `StrokeTool`, `PigmentPaint`
All use UUID string primary keys.

### Image pipeline
- Images stored in Cloudflare R2 bucket
- 5 sizes per stroke: 100px, 600px, 1800px, 2500px, original
- Public URL pattern: `https://dns.perfectstrokeproject.com/stroke_photos/{stroke_id}/600x600/{file_id}_600x600.jpg`
- Frontend endpoints use `r2_image_map.json` to resolve image paths without DB joins

### Public API endpoints (no auth required)
- `GET /api/strokes/frontend/all/` — all strokes with R2 image URLs
- `GET /api/strokes/{id}/frontend/` — single stroke detail
- `GET /api/strokes/get-random/` — random stroke

### Auth
- JWT via djangorestframework-simplejwt (24h access, 30d refresh)
- Default admin: `admin` / `Pass@word1` (email: `p@hakomo.com`)

## Public Website (react-perfect-stroke)

### Key pages
- `/` — Home (splash image, text about the project)
- `/paper-collection` — Stroke gallery (3D perspective card grid on desktop, Three.js on mobile)
- `/stroke/:id` — Individual stroke detail page
- `/about`, `/get-involved`, `/experimental-projects`, `/subscribe`

### Image display logic (App.tsx)
- Desktop (width > 600): `StrokePlain` component — CSS 3D perspective card grid
- Mobile (width <= 600): `Image` component — Three.js WebGL gallery
- Controlled by `showStrokePlain` context state (set per-page in useEffect)

### Known issues
- Firebase Auth is still wired into `AuthContext.js` and `RequireAuth.tsx` — needs migration to Django JWT to fully remove Firebase
- `react-perfect-stroke/.env*` still has Firebase config for `thank-you-project` Firebase project
- Images not rendering on Firefox (under investigation — may be CSS 3D transform issue or JS error)

## Admin CMS (cms-react-psp)

- All CRUD goes through Django API (Firebase was fully removed)
- Auth uses Django JWT tokens
- `.env.production` points to `https://api.perfectstrokeproject.com`
- Dev runs on `http://localhost:8200/api`

## Data history

The project migrated through several backends:
1. **2020:** .NET Core + SQL Server + AWS S3
2. **2022:** Firebase Firestore (CMS rewrite)
3. **2026:** Django + PostgreSQL + Cloudflare R2 (current)

~10,000 stroke records exist in the DB (imported from SQL Server), but only ~800 have images in R2. The rest were never photographed — this is expected.

## External services
- **Cloudflare R2** — image storage (S3-compatible, via boto3)
- **Cloudflare** — DNS, SSL (origin certs), CDN proxy
- **SendGrid** — transactional email
- **PostgreSQL 14** — database (on Contabo server)
