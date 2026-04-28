# ── Stage 1: Builder ───────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev curl \
    && rm -rf /var/lib/apt/lists/*

# ── Stage 2: Final ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies for Playwright/Chromium and build tools needed for some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 libxkbcommon0 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
    fonts-liberation fonts-noto-color-emoji fonts-unifont \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies directly in final stage for stable PATHs
COPY requirements.txt requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Install Playwright Chromium
RUN playwright install chromium

# Copy source code
COPY . .

# Ensure uvicorn is in the PATH and available as a command
ENV PATH="/usr/local/bin:/home/app/.local/bin:${PATH}"
RUN ln -s /usr/local/bin/uvicorn /usr/bin/uvicorn || true

# Non-root user
RUN groupadd -r app && useradd -r -g app -m app
RUN chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

EXPOSE 8000
EXPOSE 10000

CMD ["sh", "-c", "PYTHONPATH=. python3 scripts/deployment_check.py && PYTHONPATH=. python3 -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2"]
