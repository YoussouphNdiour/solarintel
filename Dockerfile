# ─── SolarIntel — Docker image ─────────────────────────────────────────────
# Base: Python 3.11 slim (avoids heavy image; pvlib/reportlab compile fine)
FROM python:3.11-slim

# System deps: Python libs + Node.js LTS (for solarintel-3d build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all sources (solarintel-3d/dist is pre-built and committed)
COPY . .

# Expose port (Render/Cloud Run inject $PORT at runtime)
EXPOSE 8000

# Start FastAPI — use $PORT injected by Render (default 8000 for local docker run)
CMD ["sh", "-c", "uvicorn solarintel.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
