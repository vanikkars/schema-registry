FROM python:3.11-slim

WORKDIR /app

COPY requirements-iceberg.txt .
RUN pip install --no-cache-dir -r requirements-iceberg.txt

COPY iceberg_creation_service/ ./iceberg_creation_service/

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "iceberg_creation_service.main:app", "--host", "0.0.0.0", "--port", "8001"]