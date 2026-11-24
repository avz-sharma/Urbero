# ==============================================================================
# Multi-Stage Dockerfile for Urbero: Urban Air Quality Assistant (Challenge 6)
# Target: Google Cloud Run (min-instances=1 during judging; non-root user)
# ==============================================================================

# Stage 1: Build Frontend Assets
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
COPY docs/openapi.json ../docs/openapi.json
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.12-slim AS runtime

# Security hardening: Create non-root user
RUN groupadd -r urbero && useradd -r -g urbero -d /app -s /sbin/nologin urbero

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    ENVIRONMENT=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend /app/backend
COPY docs /app/docs

# Copy compiled frontend static assets from builder stage
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Switch to non-root user
USER urbero

# Cloud Run Container Health Check
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Launch uvicorn
CMD ["sh", "-c", "uvicorn backend.app.api.routes:app --host 0.0.0.0 --port ${PORT} --no-access-log"]
