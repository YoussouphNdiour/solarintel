# ─── SolarIntel — Docker image ─────────────────────────────────────────────
# Base: Python 3.11 slim (avoids heavy image; pvlib/reportlab compile fine)
FROM python:3.11-slim

# System deps: Python libs + Node.js LTS (for solarintel-3d build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    libpng-dev \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Build the 3D viewer — copy package files first for cache efficiency
COPY solarintel-3d/package.json solarintel-3d/package-lock.json* ./solarintel-3d/
RUN cd solarintel-3d && npm install --prefer-offline

COPY solarintel-3d/ ./solarintel-3d/
RUN cd solarintel-3d && npm run build

# Copy remaining project sources
COPY . .

# Expose port (Render/Cloud Run inject $PORT at runtime)
EXPOSE 8000

# Start FastAPI — use $PORT injected by Render (default 8000 for local docker run)
CMD ["sh", "-c", "uvicorn solarintel.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
