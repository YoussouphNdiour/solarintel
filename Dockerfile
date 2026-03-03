# ─── SolarIntel — Docker image ─────────────────────────────────────────────
# Base: Python 3.11 slim (avoids heavy image; pvlib/reportlab compile fine)
FROM python:3.11-slim

# System deps for ReportLab (Pillow/freetype) and pvlib (numpy/scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project sources
COPY . .

# Expose port (Render/Cloud Run inject $PORT at runtime)
EXPOSE 8000

# Start FastAPI with uvicorn
CMD ["uvicorn", "solarintel.api:app", "--host", "0.0.0.0", "--port", "8000"]
