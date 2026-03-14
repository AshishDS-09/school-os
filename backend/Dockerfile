# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached separately from code)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend code
COPY . .

# Default command (overridden by docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]