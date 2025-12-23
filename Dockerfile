# Backend Dockerfile for Django Application
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy supervisor configuration first (before copying project)
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy project
COPY . .

# Set permissions for entrypoint script
RUN chmod +x /app/docker-entrypoint.sh

# Create directories for supervisor and static files
RUN mkdir -p /var/log/supervisor /app/staticfiles

# Expose port
EXPOSE 8000

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; resp = urllib.request.urlopen('http://localhost:8000/', timeout=5); exit(0 if resp.getcode() < 500 else 1)" || exit 1

# Use entrypoint script to run migrations, then start supervisor
ENTRYPOINT ["/app/docker-entrypoint.sh"]

