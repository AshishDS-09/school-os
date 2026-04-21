# # backend/Dockerfile

# FROM python:3.11-slim

# WORKDIR /app

# ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
#     PIP_DEFAULT_TIMEOUT=300

# # Install dependencies first (cached separately from code)
# COPY requirements.txt .
# RUN pip install --upgrade pip && \
#     pip install --no-cache-dir --retries 10 --timeout 300 -r requirements.txt

# # Copy all backend code
# COPY . .

# # Default command (overridden by docker-compose)
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# backend/Dockerfile  — final production version

FROM python:3.11-slim

# Set environment to production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ENVIRONMENT=production

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Only enforce the HTTP healthcheck for the web process. Worker-style services
# share this image but do not expose an HTTP endpoint.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD sh -c 'if [ "${PROCESS_TYPE:-web}" = "web" ]; then python -c "import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")"; else exit 0; fi'

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["web"]
