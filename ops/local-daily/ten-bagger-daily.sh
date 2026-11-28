#!/usr/bin/env bash
# Generate today's daily JSON, regenerate ledger/performance/exports, and push content/ to origin/main.
# See ops/local-daily/README.md for install and env layout.
set -euo pipefail

log() {
  echo "ten-bagger-daily: $*" >&2
}

STAGE=init
FAIL_REASON=""
TARGET=""

fail() {
  FAIL_REASON="$*"
  log "ERROR: $*"
  exit 1
}

# Body carries only stage, date, and our own fail() text, never env values.
notify_failure() {
  local rc=$?
  [[ $rc -eq 0 ]] && return 0
  local orca="${TEN_BAGGER_ORCA_BIN:-${HOME}/.config/orca/linux-orca-cli-shim/orca}"
  local body="target=${TARGET:-?} stage=${STAGE} rc=${rc}: ${FAIL_REASON:-journalctl --user -u ten-bagger-daily}"
  if [[ -x "$orca" ]]; then
    timeout 60 "$orca" orchestration send --from "${TEN_BAGGER_NOTIFY_FROM:-bot:ten-bagger-daily}" --to "bot:오르카" \
      --type status --subject "ten_bagger 매일 실행 실패" --body "$body" >/dev/null 2>&1 \
      || log "failure notify failed"
  else
    log "orca CLI not found at $orca; failure not notified"
  fi
  return 0
}
trap notify_failure EXIT

push_if_ahead() {
  STAGE=push
  if [[ -z "$(git rev-list origin/main..HEAD)" ]]; then
    log "nothing to push"
    return 0
  fi
  if ! git pull --rebase origin main; then
    git rebase --abort 2>/dev/null || true
    fail "git pull --rebase origin main failed before push"
  fi
  git push origin main || fail "git push origin main failed"
  log "push succeeded: $(git log -1 --format=%s)"
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

AS_OF="${TEN_BAGGER_AS_OF:-$TARGET}"

[[ -d "$REPO_DIR/.git" ]] || fail "repo not found at $REPO_DIR (clone first)"

mkdir -p "$YF_CACHE_DIR"
export TEN_BAGGER_YF_CACHE_DIR="$YF_CACHE_DIR"

cd "$REPO_DIR"
STAGE=sync
git fetch origin main
git checkout -q main
# Drop leftovers of a failed run so they never ride along in today's commit.
git restore --staged --worktree .
git clean -fdq content/
git pull --ff-only origin main || fail "git pull --ff-only origin main failed; fix repo state manually"

if [[ -n "$PYTHON" ]]; then
  PY="$PYTHON"
elif [[ -x "${VENV_DIR}/bin/python" ]]; then
  PY="${VENV_DIR}/bin/python"
else
  PY="python3"
fi

if ! "$PY" -c 'import yfinance' 2>/dev/null; then
  STAGE=deps
  log "installing Python deps into ${VENV_DIR}"
  python3 -m venv "$VENV_DIR"
  "${VENV_DIR}/bin/pip" install -q -r scripts/requirements.txt
  PY="${VENV_DIR}/bin/python"
fi

STAGE=daily
if [[ -z "$FORCE" ]] && git cat-file -e "origin/main:content/daily/${TARGET}.json" 2>/dev/null; then
  log "skip daily: content/daily/${TARGET}.json already on origin/main"
else
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
  else
    git commit -q -m "chore: daily report ${TARGET}"
  fi
fi
# Publish the daily before the ledger so a ledger failure never holds back the pick.
push_if_ahead

# Never move the ledger back in time: a backfill TARGET older than the ledger is skipped (2026-11-05 regress).
STAGE=ledger
CURRENT_AS_OF="$("$PY" -c 'import json,sys; print(min(json.load(open(f)).get("asOfDate","") for f in sys.argv[1:]))' content/ledger/KR.json content/ledger/US.json 2>/dev/null || true)"
if [[ -z "${TEN_BAGGER_FORCE_LEDGER:-}" ]] && [[ -n "$CURRENT_AS_OF" ]] && [[ ! "$AS_OF" > "$CURRENT_AS_OF" ]]; then
  log "skip ledger: asOfDate ${CURRENT_AS_OF} is not older than ${AS_OF}"
else
  log "ledger asOfDate ${CURRENT_AS_OF:-none} -> ${AS_OF}"
  (
    cd scripts
    "$PY" regenerate_ledger.py --as-of-date "$AS_OF"
    "$PY" sync_manifest.py
    "$PY" validate_content.py
    "$PY" export_picks.py
  )
  git add content/ledger/ content/performance/ content/exports/
  if git diff --staged --quiet; then
    log "no ledger changes"
  else
    git commit -q -m "chore: ledger regenerate asOfDate=${AS_OF}"
  fi
  # sync/validate may leave tracked dirt; rebase refuses with unstaged changes (#96).
  git restore .
fi

push_if_ahead
log "done target=${TARGET}"
