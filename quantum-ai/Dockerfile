FROM python:3.10-slim

LABEL maintainer="Quantum AI Team"
LABEL description="Quantum ML Fraud Detection API"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copy application files
COPY fraud_detection_api.py wsgi.py ./
COPY src/ ./src/
COPY results/ ./results/

# Create non-root user
RUN useradd -m -u 1000 apiuser && \
    chown -R apiuser:apiuser /app
USER apiuser

# Expose port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# Run with gunicorn
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5050", "wsgi:app"]
