# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=300

# Install dependencies first (cached separately from code)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --retries 10 --timeout 300 -r requirements.txt

# Copy all backend code
COPY . .

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
