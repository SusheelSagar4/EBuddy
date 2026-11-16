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

COPY requirements.txt constraints.txt ./
# constraints.txt pins every package to the versions the image was tested with, so rebuilds are reproducible
RUN pip install --no-cache-dir -r requirements.txt -c constraints.txt

COPY app /app/app
COPY web /app/web
COPY data /app/data
COPY scripts /app/scripts
COPY docker /app/docker
COPY tests /app/tests
COPY pyproject.toml /app/pyproject.toml
# Configuration files checked by tests/test_db_free.py, so the suite runs complete inside the image (no secrets:
# .env itself stays excluded by .dockerignore)
COPY .env.example .gitignore .dockerignore docker-compose.yml /app/
# Career-track knowledge bases (generated CSVs only; the source workbooks stay out of the image)
COPY sde/output /app/sde/output
COPY da/output /app/da/output
COPY aiml/output /app/aiml/output

RUN chmod +x /app/docker/entrypoint.sh

# Run as an unprivileged user. The code stays root-owned (read-only to the app); the only runtime write is the
# seed loader's data-quality report, so /app/docs is the one directory the user owns.
RUN useradd --system --uid 10001 --home-dir /app --shell /usr/sbin/nologin ebuddy \
    && mkdir -p /app/docs \
    && chown ebuddy:ebuddy /app/docs
USER ebuddy

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
