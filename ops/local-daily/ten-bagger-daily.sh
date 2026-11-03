#!/usr/bin/env bash
# Generate today's daily JSON on the Paperclip host and push content/ to origin/main.
# See ops/local-daily/README.md for install and env layout.
set -euo pipefail

log() {
  echo "ten-bagger-daily: $*" >&2
}

fail() {
  log "ERROR: $*"
  exit 1
}

ENV_FILE="${TEN_BAGGER_ENV_FILE:-${HOME}/.config/ten_bagger/daily.env}"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
else
  log "env file missing ($ENV_FILE); OPENDART/PIT secrets must be set elsewhere"
fi

REPO_DIR="${TEN_BAGGER_REPO:-${HOME}/git/ten_bagger-daily}"
YF_CACHE_DIR="${TEN_BAGGER_YF_CACHE_DIR:-${HOME}/.cache/ten_bagger/yfinance}"
VENV_DIR="${TEN_BAGGER_VENV:-${HOME}/.local/share/ten_bagger/venv}"
PYTHON="${TEN_BAGGER_PYTHON:-}"

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  TARGET="$(TZ=Asia/Seoul date +%F)"
fi
FORCE="${TEN_BAGGER_FORCE:-}"

[[ -d "$REPO_DIR/.git" ]] || fail "repo not found at $REPO_DIR (clone first)"

mkdir -p "$YF_CACHE_DIR"
export TEN_BAGGER_YF_CACHE_DIR="$YF_CACHE_DIR"

cd "$REPO_DIR"
git fetch origin main

if [[ -z "$FORCE" ]] && git cat-file -e "origin/main:content/daily/${TARGET}.json" 2>/dev/null; then
  log "skip: content/daily/${TARGET}.json already on origin/main (gate parity with CI)"
  exit 0
fi

git checkout -q main
if ! git pull --ff-only origin main; then
  fail "git pull --ff-only origin main failed; fix repo state manually"
fi

if [[ -n "$PYTHON" ]]; then
  PY="$PYTHON"
elif [[ -x "${VENV_DIR}/bin/python" ]]; then
  PY="${VENV_DIR}/bin/python"
else
  PY="python3"
fi

if ! "$PY" -c 'import yfinance' 2>/dev/null; then
  log "installing Python deps into ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
  "${VENV_DIR}/bin/pip" install -q -r scripts/requirements.txt
  PY="${VENV_DIR}/bin/python"
fi

log "target=${TARGET} yf_cache=${YF_CACHE_DIR}"
(
  cd scripts
  "$PY" build_universe.py
  "$PY" generate_daily.py "$TARGET"
  if [[ -n "${PIT_DATA_TOKEN:-}" ]]; then
    PIT_TARGET_DATE="$TARGET" "$PY" pit_snapshot.py
  else
    log "PIT_DATA_TOKEN unset; skipping pit_snapshot push"
  fi
  "$PY" sync_manifest.py
  "$PY" validate_content.py
)

git add content/
if git diff --staged --quiet; then
  log "no content changes after generate"
  exit 0
fi

git commit -m "chore: daily report ${TARGET}"

if ! git pull --rebase origin main; then
  fail "git pull --rebase origin main failed before push"
fi

if ! git push origin main; then
  fail "git push origin main failed"
fi

log "push succeeded for ${TARGET}"
