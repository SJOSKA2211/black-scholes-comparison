# ── Stage 1: dependency builder ─────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
 
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev curl \
    && rm -rf /var/lib/apt/lists/*
 
# CRITICAL layer-caching rule: requirements FIRST, source SECOND.
# pip install only reruns when requirements.txt changes, not on code edits.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt
 
# Install Playwright + Chromium (large layer — cached independently)
RUN pip install --no-cache-dir playwright==1.44.0 \
    && playwright install chromium --with-deps
 
# ── Stage 2: production runtime ─────────────────────────────────────────
FROM python:3.11-slim AS runtime
 
# Playwright runtime system libraries (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 libxkbcommon0 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 curl \
    && rm -rf /var/lib/apt/lists/*
 
# Copy installed Python packages from builder
COPY --from=builder /install /usr/local
 
# Copy Playwright browser binaries from builder
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright
 
# Non-root user — never run as root in production
RUN groupadd -r app && useradd -r -g app -m app
WORKDIR /app
COPY src/ ./src/
COPY scripts/ ./scripts/
RUN chown -R app:app /app
USER app
 
# Docker health check — Prometheus also uses this endpoint for liveness
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
 
EXPOSE 8000
 
# Standard uvicorn start — no Datadog agent wrapping needed
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
