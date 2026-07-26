FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file from registry_api subdirectory
COPY registry_api/requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy entire project (excluding things in .dockerignore)
COPY . .

# Set Python path to include working directory so registry_api can be imported
ENV PYTHONPATH=/app

# Ensure we're in the right directory
WORKDIR /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Expose port
EXPOSE 8000

# Run the application using python -m to properly resolve module paths
CMD ["python", "-m", "uvicorn", "registry_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]