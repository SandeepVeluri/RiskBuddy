FROM python:3.11-slim

# Install Node.js 20
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Install and build frontend
COPY frontend/package*.json frontend/
RUN npm --prefix frontend install --no-fund --no-audit

COPY frontend/ frontend/
RUN npm --prefix frontend run build

# Copy backend source
COPY backend/ backend/

EXPOSE 8080

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
