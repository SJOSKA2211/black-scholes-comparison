# Stage 1: dependency builder
FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev curl && rm -rf /var/lib/apt/lists/*

# CRITICAL: copy requirements BEFORE source — cached pip layer
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt
COPY requirements-dev.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements-dev.txt

# Playwright browsers (large cached layer)
RUN pip install --no-cache-dir playwright==1.44.0 \
    && playwright install chromium --with-deps

# Stage 2: production runtime
FROM python:3.11-slim AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libdbus-1-3 libexpat1 libxcb1 libxkbcommon0 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /install /usr/local
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright
RUN groupadd -r app && useradd -r -g app -m app
WORKDIR /app
COPY src/ ./src/
COPY scripts/ ./scripts/
RUN chown -R app:app /app
USER app
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
