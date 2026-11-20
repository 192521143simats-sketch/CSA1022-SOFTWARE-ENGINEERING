#!/bin/sh
# Container start: apply pending migrations (transactional), then serve.
set -eu
: "${SECRET_KEY:?SECRET_KEY must be provided at runtime (never committed)}"
python -m campus.db            # migrate to latest; aborts start-up if a migration fails
exec gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 4 --access-logfile - "campus.app:create_app()"
