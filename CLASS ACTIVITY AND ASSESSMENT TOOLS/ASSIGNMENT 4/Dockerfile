# Campus Facility Platform - container image (non-root, no secrets baked in)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN useradd --system --uid 10001 app && mkdir /data /backups && chown app /data /backups

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY campus campus
COPY migrations migrations
COPY scripts/entrypoint.sh scripts/entrypoint.sh

# Traceable identity of what is running (set by the pipeline: --build-arg GIT_SHA=$GITHUB_SHA)
ARG GIT_SHA=dev
ARG APP_VERSION=1.0.0
ENV GIT_SHA=$GIT_SHA APP_VERSION=$APP_VERSION DB_PATH=/data/campus.db
LABEL org.opencontainers.image.revision=$GIT_SHA org.opencontainers.image.version=$APP_VERSION

USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/ready')"
ENTRYPOINT ["sh", "scripts/entrypoint.sh"]
