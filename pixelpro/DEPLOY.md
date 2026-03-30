# PixelPro — Deployment Guide

**Stack:** Next.js frontend → **Vercel** (free) | FastAPI backend → **Railway** (~$5/mo) | PostgreSQL → **Railway add-on**

---

## 1. Push to GitHub

```bash
# Create a new repo at https://github.com/new  (name: pixelpro)
git remote set-url origin https://github.com/YOUR_USERNAME/pixelpro.git
git add .
git commit -m "feat: production-ready deployment config"
git push -u origin main
```

---

## 2. Deploy Backend on Railway

1. Go to **https://railway.app** → New Project → Deploy from GitHub
2. Select your `pixelpro` repo → choose the **`backend`** directory
3. Railway will auto-detect `Dockerfile.prod` ✅

### Add PostgreSQL add-on
- Railway dashboard → **+ New** → **Database** → **PostgreSQL**
- Copy the `DATABASE_URL` from the PostgreSQL service

### Add Redis add-on
- Railway dashboard → **+ New** → **Database** → **Redis**
- Copy the `REDIS_URL`

### Set Environment Variables (Railway → Variables tab)
```
DEBUG=false
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
DATABASE_URL=<from Railway PostgreSQL>
REDIS_URL=<from Railway Redis>
CELERY_BROKER_URL=<same as REDIS_URL>/0
CELERY_RESULT_BACKEND=<same as REDIS_URL>/1
AWS_ACCESS_KEY_ID=dev
LOCAL_STORAGE_DIR=/app/local_storage
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
FREE_MONTHLY_CREDITS=500
PRO_MONTHLY_CREDITS=500
MAX_IMAGE_SIZE_MB=20
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
FAL_KEY=                    (optional — get free at fal.ai/dashboard/keys)
HF_TOKEN=                   (optional — get free at huggingface.co/settings/tokens)
```

> **Storage note:** For production with many users, switch from local storage to **Cloudflare R2** (free 10GB):
> Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_ENDPOINT_URL=https://ACCOUNT.r2.cloudflarestorage.com`

### Run migrations
```bash
# Via Railway CLI
railway run alembic upgrade head
```

---

## 3. Deploy Frontend on Vercel

1. Go to **https://vercel.com** → New Project → Import from GitHub
2. Select your `pixelpro` repo → set **Root Directory** to `frontend`
3. Framework: **Next.js** (auto-detected)

### Set Environment Variables (Vercel → Settings → Environment Variables)
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app/api/v1
NEXT_PUBLIC_APP_URL=https://yourdomain.com
```

4. Click **Deploy** ✅

---

## 4. Connect Your Domain

### Vercel (frontend)
- Vercel dashboard → Settings → Domains → Add `yourdomain.com` and `www.yourdomain.com`
- Point DNS: add CNAME `@` → `cname.vercel-dns.com`

### Railway (backend / API)
- Railway dashboard → Settings → Domains → Add `api.yourdomain.com`
- Point DNS: CNAME `api` → provided by Railway

Then update `ALLOWED_ORIGINS` in Railway to include your domain.

---

## 5. Stripe Webhooks

1. Go to **https://dashboard.stripe.com/webhooks** → Add endpoint
2. URL: `https://api.yourdomain.com/api/v1/stripe/webhook`
3. Events to listen: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`
4. Copy the signing secret → set as `STRIPE_WEBHOOK_SECRET` in Railway

---

## Quick Checklist

- [ ] GitHub repo created and code pushed
- [ ] Railway backend deployed and healthy (`/health` returns 200)
- [ ] Railway PostgreSQL connected, migrations run
- [ ] Vercel frontend deployed
- [ ] Custom domain connected (or using `.vercel.app` / `.railway.app` for now)
- [ ] `ALLOWED_ORIGINS` updated in Railway with your domain
- [ ] `NEXT_PUBLIC_API_URL` set in Vercel pointing to Railway URL
- [ ] Stripe webhook configured
- [ ] Test: register → login → upload image → AI edit works

---

## Cost Estimate

| Service | Cost |
|---------|------|
| Vercel (frontend) | **Free** |
| Railway (backend + PostgreSQL + Redis) | ~$5–10/month |
| Cloudflare R2 storage | Free for 10GB |
| Domain | $1–2/year |
| **Total** | **~$5–10/month** |
