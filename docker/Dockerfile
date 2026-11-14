# ==============================================================================
# Slim Dockerfile for Adobe Personalised Learning Buddy
# Base: python:3.12-slim (linux/amd64, Total Footprint < 500 MB)
# ==============================================================================

FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY web /app/web
COPY data /app/data
COPY scripts /app/scripts
COPY docker /app/docker

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
