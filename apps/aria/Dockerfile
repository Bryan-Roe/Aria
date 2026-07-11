# =============================================================================
# Aria Web Server — Dockerfile
# =============================================================================
# Builds the standalone Aria web UI and API server.
#
# Build:
#   docker build -f apps/aria/Dockerfile -t aria-server:local .
#   (run from repo root so the build context includes shared/ etc.)
#
# Run:
#   docker run -p 8080:8080 aria-server:local
# =============================================================================

FROM python:3.11-slim@sha256:e031123e3d85762b141ad1cbc56452ba69c6e722ebf2f042cc0dc86c47c0d8b3

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ARIA_PORT=8080

WORKDIR /app

# Install OS-level dependencies (keep the image slim)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only the files needed to install Python dependencies first
# (layer-cache friendly — rebuilds only when deps change)
COPY requirements.txt ./

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application source
COPY shared/ ./shared/
COPY apps/aria/ ./apps/aria/

# Expose the HTTP port
EXPOSE 8080

# Health check — polls the Aria state endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${ARIA_PORT}/api/aria/state')" \
    || exit 1

# Run the Aria web server
CMD ["python", "apps/aria/server.py"]
