FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt uvicorn[standard]

# Copy application code
COPY agent.py .
COPY __init__.py .
COPY main.py .
COPY frontend ./frontend

# Cloud Run sets the PORT env variable (default 8080)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
