FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy
WORKDIR /app
COPY requirements.txt requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt
# Browsers are already installed in this image, but we can ensure chromium is there
RUN playwright install chromium
COPY . .
ENV PATH="/usr/local/bin:/home/app/.local/bin:${PATH}"
RUN groupadd -r app && useradd -r -g app -m app
RUN chown -R app:app /app
USER app
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
EXPOSE 8000
CMD ["sh", "-c", "PYTHONPATH=. python3 scripts/deployment_check.py && PYTHONPATH=. uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2"]
