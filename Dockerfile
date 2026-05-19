# ─────────────────────────────────────────────────────────────
# Portfolio MLOps — Production Dockerfile
# ─────────────────────────────────────────────────────────────

FROM python:3.11-slim

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/       src/
COPY config/    config/
COPY train.py   .
COPY predict.py .

# Create writable directories (mounted as volumes in docker-compose)
RUN mkdir -p data/cache checkpoints metrics logs outputs \
    && chown -R appuser:appgroup /app

USER appuser

# Default: train spt_model. Override via docker-compose or CLI args.
CMD ["python", "train.py", "--model", "spt_model"]
