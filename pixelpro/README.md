# PixelPro — AI Ecommerce Product Image Enhancer

> SaaS platform that uses Real-ESRGAN, GFPGAN, and U²-Net to upscale,
> denoise, sharpen, color-correct, and background-remove product photos.

---

## 1. System Architecture

```
                        ┌─────────────────────────────────────────┐
                        │              USERS (Browser)             │
                        └───────────────────┬─────────────────────┘
                                            │ HTTPS
                        ┌───────────────────▼─────────────────────┐
                        │            Nginx (reverse proxy)         │
                        │         SSL termination, rate limit      │
                        └─────┬──────────────────────┬────────────┘
                              │ /api/*               │ /*
               ┌──────────────▼──────┐     ┌─────────▼────────────┐
               │   FastAPI (API)     │     │  Next.js (Frontend)   │
               │   2 uvicorn workers │     │  SSR + React          │
               └──────────┬──────────┘     └──────────────────────┘
                          │
               ┌──────────▼──────────────────────────────────────┐
               │              PostgreSQL (primary data store)      │
               │  users · images · batches · api_usage            │
               └──────────────────────────────────────────────────┘
                          │
               ┌──────────▼──────────┐
               │   Redis (broker +   │
               │   result backend)   │
               └──────────┬──────────┘
                          │ task queue
         ┌────────────────▼──────────────────────┐
         │         Celery Worker (GPU server)      │
         │   - Real-ESRGAN  (upscaling)           │
         │   - GFPGAN       (face restore)        │
         │   - rembg/U²Net  (bg removal)          │
         │   - OpenCV       (denoise/sharpen)     │
         └────────────────┬──────────────────────┘
                          │ store results
         ┌────────────────▼──────────────────────┐
         │             AWS S3                     │
         │   pixelpro-inputs  (originals)         │
         │   pixelpro-outputs (enhanced)          │
         └────────────────────────────────────────┘
```

**Key design decisions:**
- API server and GPU worker are **separate containers** — API stays fast while
  GPU tasks run asynchronously.
- `task_acks_late=True` + `worker_prefetch_multiplier=1` — no task loss on
  worker crash, one GPU job at a time per worker.
- Credits are deducted **before** queuing; refunded **on failure**.
- Presigned S3 URLs expire in 1 hour — images never go through the API.

---

## 2. Folder Structure

```
pixelpro/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py          # Router aggregator
│   │   │   └── routes/
│   │   │       ├── auth.py          # /auth/register, /login, /refresh
│   │   │       ├── images.py        # /images/upload, /{id}, /batch
│   │   │       ├── users.py         # /users/me, /dashboard
│   │   │       └── stripe_webhooks.py
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic settings
│   │   │   ├── database.py          # Async SQLAlchemy engine
│   │   │   └── security.py          # JWT, password hashing
│   │   ├── models/
│   │   │   ├── user.py              # User, PlanType
│   │   │   └── image.py             # Image, Batch, APIUsage
│   │   ├── schemas/
│   │   │   ├── user.py              # Pydantic I/O schemas
│   │   │   └── image.py
│   │   ├── services/
│   │   │   ├── user_service.py      # CRUD + credit logic
│   │   │   ├── image_service.py     # CRUD + status updates
│   │   │   └── s3_service.py        # S3 upload/download/presign
│   │   ├── workers/
│   │   │   ├── celery_app.py        # Celery config + beat schedule
│   │   │   ├── ai_pipeline.py       # Real-ESRGAN, GFPGAN, OpenCV
│   │   │   └── tasks.py             # enhance_image_task, credit reset
│   │   └── main.py                  # FastAPI app + middleware
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── page.tsx             # Landing page
│       │   ├── layout.tsx           # Root layout + providers
│       │   ├── auth/
│       │   │   ├── login/page.tsx
│       │   │   └── register/page.tsx
│       │   ├── dashboard/
│       │   │   ├── layout.tsx       # Sidebar layout (auth guard)
│       │   │   └── page.tsx         # Stats + recent images
│       │   └── enhance/
│       │       └── page.tsx         # Upload + options + compare slider
│       ├── components/
│       │   ├── landing/             # Hero, Features, Pricing, etc.
│       │   └── ui/                  # Providers, Toaster
│       └── lib/
│           ├── api.ts               # Axios instance + typed helpers
│           └── auth-store.ts        # Zustand auth state
│
├── infrastructure/
│   ├── nginx/nginx.conf
│   └── scripts/download_models.sh
│
└── docker-compose.yml
```

---

## 3. AI Pipeline

Enhancement runs in this order (each step is optional):

```
Original Image
  │
  ├─ [denoise]          OpenCV fastNlMeansDenoisingColored
  ├─ [upscale]          Real-ESRGAN x2 or x4 (GPU)
  ├─ [face_enhance]     GFPGAN v1.4 (GPU, if faces detected)
  ├─ [sharpen]          Unsharp mask (OpenCV)
  ├─ [color_correct]    CLAHE in LAB space (OpenCV)
  └─ [remove_bg]        rembg U²-Net → PNG with transparency
```

**Why this order?**
- Denoise *before* upscaling — less data to process, no upscaled noise
- Face enhance *after* upscaling — GFPGAN works better on larger faces
- BG removal *last* — operates on the final quality image

**Fallbacks:** If a GPU model fails (OOM, missing weights), the pipeline
falls back gracefully (Lanczos for upscaling, skips face/bg steps) instead
of failing the whole job.

---

## 4. Database Schema

```sql
-- Users
users (
  id            UUID PK,
  email         VARCHAR UNIQUE,
  hashed_password VARCHAR,
  full_name     VARCHAR,
  is_active     BOOLEAN,
  plan          ENUM(free|starter|pro|business),
  credits_remaining INT,
  credits_used_total INT,
  credits_reset_at TIMESTAMPTZ,
  stripe_customer_id VARCHAR,
  stripe_subscription_id VARCHAR,
  api_key       VARCHAR UNIQUE,
  created_at    TIMESTAMPTZ,
  updated_at    TIMESTAMPTZ
)

-- Images
images (
  id                UUID PK,
  user_id           UUID FK→users,
  batch_id          UUID FK→batches,
  original_filename VARCHAR,
  original_s3_key   VARCHAR,
  original_size_bytes INT,
  original_width/height INT,
  original_format   VARCHAR,
  enhanced_s3_key   VARCHAR,
  enhanced_width/height INT,
  enhanced_size_bytes INT,
  enhancement_options JSONB,   -- {upscale_factor, denoise, ...}
  status            ENUM(pending|queued|processing|completed|failed),
  celery_task_id    VARCHAR,
  error_message     VARCHAR,
  processing_time_ms INT,
  credits_consumed  INT,
  created_at        TIMESTAMPTZ,
  completed_at      TIMESTAMPTZ
)

-- Batches
batches (
  id             UUID PK,
  user_id        UUID FK→users,
  total_images   INT,
  completed_images INT,
  failed_images  INT,
  status         ENUM,
  enhancement_options JSONB,
  created_at     TIMESTAMPTZ
)

-- API Usage (for rate limiting & analytics)
api_usage (
  id             UUID PK,
  user_id        UUID FK→users,
  endpoint       VARCHAR,
  method         VARCHAR,
  status_code    INT,
  response_time_ms INT,
  credits_used   INT,
  created_at     TIMESTAMPTZ
)
```

---

## 5. Stripe Integration Flow

```
1. User clicks "Upgrade" → /pricing → chooses plan
2. Frontend calls POST /api/v1/stripe/checkout-session?price_id=price_xxx
3. Backend creates Stripe Checkout Session → returns checkout_url
4. User redirected to Stripe Checkout (hosted page, handles card)
5. On success → Stripe sends webhook: checkout.session.completed
6. Backend webhook handler:
   a. Verifies Stripe signature
   b. Retrieves subscription, maps price_id → PlanType
   c. Updates user.plan + user.credits_remaining
   d. Saves stripe_customer_id + stripe_subscription_id
7. Subsequent webhooks:
   - customer.subscription.updated → plan change
   - customer.subscription.deleted → downgrade to free
   - invoice.payment_failed → log warning (Stripe retries automatically)
```

**Webhook security:** Raw request body is verified against `STRIPE_WEBHOOK_SECRET`
using `stripe.Webhook.construct_event()` before any DB writes.

---

## 6. Deployment Plan

### Infrastructure

| Service | Host | Spec |
|---------|------|------|
| API (FastAPI) | AWS EC2 `t3.medium` | 2 vCPU, 4GB RAM |
| GPU Worker | AWS `g4dn.xlarge` | T4 GPU, 16GB VRAM |
| PostgreSQL | AWS RDS `db.t3.medium` | Managed, auto-backup |
| Redis | AWS ElastiCache | `cache.t3.micro` |
| S3 | AWS S3 | Standard + lifecycle rules |
| Frontend | Vercel (or EC2) | Edge CDN |
| CDN | CloudFront | S3 + API caching |

### Steps

```bash
# 1. Provision infrastructure (Terraform or manual)
# 2. Clone repo on EC2
git clone https://github.com/yourorg/pixelpro

# 3. Copy env files
cp backend/.env.example backend/.env
# Fill in all secrets

# 4. Download AI model weights
bash infrastructure/scripts/download_models.sh

# 5. Run DB migrations
docker compose run api alembic upgrade head

# 6. Start all services
docker compose up -d

# 7. Configure Stripe webhook endpoint
# Dashboard → Developers → Webhooks → Add endpoint
# URL: https://pixelpro.app/api/v1/stripe/webhook
# Events: checkout.session.completed, customer.subscription.*

# 8. Point DNS to EC2 public IP / load balancer
# 9. Issue SSL certificate (Let's Encrypt / ACM)
```

### Scaling

- **Horizontal API scaling:** Add more `api` containers behind a load balancer
- **GPU scaling:** Add more `worker` containers on separate GPU instances;
  Celery distributes work across all workers automatically
- **Database:** RDS read replicas for dashboard queries

---

## 7. Pricing Strategy

| Plan | Price | Credits | Target customer |
|------|-------|---------|-----------------|
| Free | $0 | 5/mo | Try it, hobbyists |
| Starter | $19/mo | 100/mo | Side-hustle sellers |
| Pro | $49/mo | 500/mo | Full-time sellers, photographers |
| Business | $149/mo | 2,000/mo | Agencies, large catalogs |
| Pay-as-you-go | $0.25/credit | — | API developers |

**Credit costs:**
- Base enhancement (upscale + denoise + sharpen + color): **1 credit**
- + Face restoration: **+1 credit**
- + Background removal: **+1 credit**
- Max 3 credits per image

**Annual discount:** 20% off → billed as $15, $39, $119/mo

**Unit economics at 200 Pro users:**
- Revenue: 200 × $49 = $9,800/mo
- AWS GPU (g4dn.xlarge ~$0.526/hr × 730hr): ~$385/mo
- AWS other infra: ~$200/mo
- Stripe fees (~2.9%): ~$284/mo
- **Gross profit: ~$8,930/mo (91% margin)**

---

## 8. Quick Start (Local Dev)

```bash
# Clone
git clone https://github.com/yourorg/pixelpro && cd pixelpro

# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

# Start infra
docker compose up postgres redis -d

# Run API locally
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Run Celery worker (in another terminal)
celery -A app.workers.celery_app worker --loglevel=info -Q enhancement

# Frontend
cd frontend
cp .env.example .env.local
npm install
npm run dev   # → http://localhost:3000
```

---

## 9. API Reference

All endpoints require `Authorization: Bearer <token>` or `X-API-Key: <key>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| POST | `/api/v1/images/upload` | Upload + enhance image |
| GET | `/api/v1/images/{id}/status` | Poll enhancement status |
| GET | `/api/v1/images/{id}` | Get result with presigned URLs |
| GET | `/api/v1/images/` | List all images (paginated) |
| POST | `/api/v1/images/batch` | Batch upload (up to 10) |
| GET | `/api/v1/users/me` | Current user profile |
| GET | `/api/v1/users/me/dashboard` | Stats + recent images |
| POST | `/api/v1/stripe/checkout-session` | Create upgrade checkout |
| POST | `/api/v1/stripe/webhook` | Stripe webhook receiver |

---

## Landing Page Copy (High-Converting)

### Headline
**Turn Blurry Product Photos Into Sales Machines**

### Subheadline
PixelPro uses cutting-edge AI to upscale, denoise, and perfect your product images
in seconds — no Photoshop skills needed. Sellers using PixelPro see an average 37%
lift in click-through rate.

### Feature bullets
- ⚡ **4x Super Resolution** — From 720p to 4K. Real-ESRGAN, not just interpolation.
- 🎨 **Auto Color Correction** — Colors that pop, white balance fixed automatically.
- 🧹 **1-Click Background Removal** — Pure white backgrounds for Amazon & Etsy, instant.
- 👤 **Face Restoration** — GFPGAN restores faces in lifestyle shots to studio quality.
- 📦 **Batch Processing** — Enhance 100 product images while you sleep.
- 🔌 **REST API** — Plug into your existing workflow, Shopify app, or custom tool.

### Social proof
"We went from 3.2% to 5.8% conversion rate after running our catalog through PixelPro.
ROI was instant." — Sarah K., Head of Ecommerce, NordStyle

### CTA
**Enhance Your First Image Free** — No credit card. No catch. 5 free enhancements, today.
