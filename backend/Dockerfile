FROM python:3.11-slim

WORKDIR /app

# System deps for PyTorch / arch / numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ build-essential libgfortran5 \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy ML core (src/) and backend code
COPY src/ /app/src/
COPY backend/ /app/backend/
COPY config/ /app/config/

# Checkpoints and data cache dirs
RUN mkdir -p /app/checkpoints /app/data/cache /app/logs

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
