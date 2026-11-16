# ==============================================================================
# Personalised Learning Buddy - application image
# Base: python:3.12-slim, linux/amd64, CPU only (no GPU, no model weights). Well under 5 GB.
# ==============================================================================
FROM --platform=linux/amd64 python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    LITELLM_LOCAL_MODEL_COST_MAP=True \
    LITELLM_TELEMETRY=False

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app
COPY web /app/web
COPY data /app/data
COPY scripts /app/scripts
COPY docker /app/docker
COPY tests /app/tests
COPY pyproject.toml /app/pyproject.toml
# Career-track knowledge bases (generated CSVs only; the source workbooks stay out of the image)
COPY sde/output /app/sde/output
COPY da/output /app/da/output
COPY aiml/output /app/aiml/output

RUN chmod +x /app/docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
