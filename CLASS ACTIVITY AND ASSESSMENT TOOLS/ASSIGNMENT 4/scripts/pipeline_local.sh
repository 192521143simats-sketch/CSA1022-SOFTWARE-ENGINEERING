#!/usr/bin/env bash
# Local runner that executes the SAME commands as .github/workflows/ci.yml, in the same
# order and with the same gates. Used where GitHub-hosted runners / a Docker registry are
# not reachable. It is NOT a GitHub Actions run and does not replace one.
#   usage: scripts/pipeline_local.sh            (exit 0 = released to isolated test env)
set -u
cd "$(dirname "$0")/.."
PORT="${PORT:-18081}"
SHA="$(git rev-parse HEAD)"; SHORT="${SHA:0:12}"
VERSION="$(git describe --tags --always)"
export SECRET_KEY="${SECRET_KEY:-$(python -c 'import secrets;print(secrets.token_hex(16))')}"  # ephemeral secret, never written to a file
SERVER_PID=""
trap '[ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null' EXIT

echo "PIPELINE START  commit=$SHA  version=$VERSION  $(date -u +%FT%TZ)"
stage() {
  local name="$1"; shift; local t0=$SECONDS
  echo; echo "=== STAGE: $name"
  if "$@"; then echo "--- [PASS] $name ($((SECONDS-t0))s)"
  else
    echo "--- [FAIL] $name"
    echo "!!! QUALITY GATE FAILED at '$name' -> package + deploy stages SKIPPED; previous release stays live"
    echo "PIPELINE RESULT: BLOCKED  commit=$SHORT"
    exit 1
  fi
}

s_checkout() { echo "tracked-file changes: $(git status --short -- . ':!evidence' | wc -l)"; git log -1 --format='commit %H%nauthor %an%nsubject %s'; }
s_deps()     { [ -d .venv ] || python -m venv .venv; . .venv/bin/activate; pip install -q --disable-pip-version-check -r requirements-dev.txt 2>&1 | tail -2; python -m pip check; python --version; }
s_compile()  { python -m compileall -q campus scripts; }
s_unit()     { python -m pytest -m unit -q; }
s_integ()    { python -m pytest -m integration -q; }
s_regress()  { python -m pytest -m regression -q; }
s_security() { python -m pytest -m security -q; }
s_migrate()  { python -m pytest -m migration -q; }
s_rehearse() { python scripts/migration_rehearsal.py | tail -4; return "${PIPESTATUS[0]}"; }
s_cov()      { python -m pytest -q --cov=campus --cov-fail-under=80 | tail -14; return "${PIPESTATUS[0]}"; }
s_bandit()   { bandit -q -r campus -ll; }
s_audit()    { pip-audit -r requirements.txt; }
s_secrets()  { python scripts/secret_scan.py; }
s_package() {
  mkdir -p dist
  if docker info >/dev/null 2>&1 && docker build -q --build-arg GIT_SHA="$SHA" -t "campus-backend:$SHORT" . ; then
    docker image inspect "campus-backend:$SHORT" --format 'image {{.Id}}'
  else
    echo "NOTE: Docker registry unreachable here -> building a release bundle from the commit instead of an image"
    git archive --format=tar.gz -o "dist/campus-backend-$SHORT.tar.gz" HEAD campus migrations scripts requirements.txt Dockerfile
    (cd dist && sha256sum "campus-backend-$SHORT.tar.gz" | tee "campus-backend-$SHORT.sha256")
  fi
}
s_deploy() {
  DEP="$(mktemp -d)"; mkdir -p "$DEP/data"
  tar xzf "dist/campus-backend-$SHORT.tar.gz" -C "$DEP"
  ( cd "$DEP" && DB_PATH="$DEP/data/campus.db" python -m campus.db ) || return 1
  ( cd "$DEP" && DB_PATH="$DEP/data/campus.db" GIT_SHA="$SHA" APP_VERSION="$VERSION" TRACKER_MODE=ok \
      exec python -m gunicorn -b 127.0.0.1:$PORT -w 2 --threads 4 "campus.app:create_app()" >"$DEP/server.log" 2>&1 ) &
  SERVER_PID=$!
  BASE_URL="http://127.0.0.1:$PORT" EXPECT_COMMIT="$SHA" SMOKE_V2="${SMOKE_V2:-}" python scripts/smoke_test.py
  local rc=$?; [ $rc -ne 0 ] && tail -20 "$DEP/server.log"; return $rc
}

stage "1 checkout"                     s_checkout
stage "2 dependency setup"             s_deps
stage "3 compile / lint"               s_compile
stage "4a unit tests"                  s_unit
stage "4b integration tests"           s_integ
stage "4c regression tests"            s_regress
stage "4d security tests"              s_security
stage "4e migration + recovery tests"  s_migrate
stage "4f migration rehearsal on synthetic v1 data (gate)" s_rehearse
stage "5 coverage gate (>=80%)"        s_cov
stage "6a static analysis (bandit)"    s_bandit
stage "6b dependency audit (pip-audit)" s_audit
stage "6c secret scan"                 s_secrets
stage "7 package (commit-tagged)"      s_package
stage "8 deploy to isolated env + smoke" s_deploy
echo; echo "PIPELINE RESULT: SUCCESS  commit=$SHORT  version=$VERSION"
