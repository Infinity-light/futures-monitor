# Futures Monitor single-service Dockerfile
# role: Build Vue assets and run FastAPI as one deploy-setup compatible service
# depends: node:20-alpine, python:3.11-slim, requirements.txt, web/package.json
# exports: Single image serving frontend, API, and WebSocket traffic
# status: VERIFIED

FROM node:20-alpine AS web-builder
WORKDIR /build/web
COPY web/package*.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=web-builder /build/web/dist ./web_dist

RUN mkdir -p /app/.data

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

CMD ["python", "-X", "utf8", "-m", "futures_monitor.server", "--host", "0.0.0.0", "--port", "8000"]
