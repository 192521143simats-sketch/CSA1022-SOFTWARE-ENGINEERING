#!/bin/sh
# Roll back the isolated stack to the previous known-good image.
# NOTE: this restores CODE only. If a destructive migration already ran, the DATA must be
# restored from a verified backup (scripts/recover.py) - an image rollback cannot undo it.
set -eu
PREV="${PREVIOUS_IMAGE:?set PREVIOUS_IMAGE=campus-backend:<known-good-sha>}"
docker compose -p campus-test down
GIT_SHA="${PREV#*:}" docker compose -p campus-test up -d --no-build
echo "rolled back to $PREV"
