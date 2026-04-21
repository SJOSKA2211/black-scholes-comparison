# Stage 1: dependency builder
FROM python:3.11-slim AS builder
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev curl \
    && rm -rf /var/lib/apt/lists/*

# requirements FIRST, source SECOND
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: production runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Non-root user
RUN groupadd -r app && useradd -r -g app -m app
WORKDIR /app
COPY src/ ./src/
COPY scripts/ ./scripts/
RUN chown -R app:app /app
USER app

EXPOSE 8000

# Standard uvicorn start
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
