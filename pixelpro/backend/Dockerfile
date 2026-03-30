# ── Stage 1: Builder ───────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev libgl1 libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip wheel --no-deps --wheel-dir /wheels -r requirements.txt

# ── Stage 2: GPU runtime ──────────────────────────────────────────────────────
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 AS gpu-runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3-pip \
    libpq5 libgl1 libglib2.0-0 ffmpeg && \
    ln -s /usr/bin/python3.11 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt

# Download model weights at build time (optional — can also mount volume)
RUN mkdir -p /app/models
# COPY scripts/download_models.sh /app/models/
# RUN bash /app/models/download_models.sh

COPY app/ ./app/

# ── API server ─────────────────────────────────────────────────────────────────
FROM gpu-runtime AS api
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ── Celery worker ──────────────────────────────────────────────────────────────
FROM gpu-runtime AS worker
CMD ["celery", "-A", "app.workers.celery_app", "worker", \
     "--loglevel=info", "--queues=enhancement", "--concurrency=1"]

# ── Celery beat scheduler ──────────────────────────────────────────────────────
FROM gpu-runtime AS beat
CMD ["celery", "-A", "app.workers.celery_app", "beat", "--loglevel=info"]
