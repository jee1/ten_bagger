# Local daily runner (main PC / systemd)

GitHub Actions 스케줄 지연을 피하려고 메인 PC 에서 평일 06:07 KST 에 daily JSON 을 만들고, 이어 ledger, performance, exports 를 다시 만들어 `content/` 를 push 합니다. 이 타이머가 주 실행입니다. `daily.yml` 은 스케줄 없이 수동 실행(workflow_dispatch)만 남겼습니다. 사이트 빌드와 배포는 Cloudflare Pages 가 main push 를 받아 합니다.

## 경로 (기본값)

| 용도 | 경로 |
|------|------|
| Git clone | `~/git/ten_bagger-daily` |
| yfinance 디스크 캐시 (clone 밖) | `~/.cache/ten_bagger/yfinance` |
| 시크릿 env (chmod **600**) | `~/.config/ten_bagger/daily.env` |
| Python venv (자동 생성) | `~/.local/share/ten_bagger/venv` |

`daily.env` 예시는 [`env.example`](env.example)를 복사합니다. **`OPENDART_API_KEY`**, **`PIT_DATA_TOKEN`** 값은 이슈 댓글이 아니라 보드가 호스트 파일에 직접 넣습니다.

## 1. Clone

```bash
git clone https://github.com/jee1/ten_bagger.git ~/git/ten_bagger-daily
cd ~/git/ten_bagger-daily
git pull origin main   # PR 머지 후 최신 main
chmod +x ops/local-daily/ten-bagger-daily.sh
```

## 2. env 파일

```bash
mkdir -p ~/.config/ten_bagger
cp ops/local-daily/env.example ~/.config/ten_bagger/daily.env
chmod 600 ~/.config/ten_bagger/daily.env
# 편집기로 OPENDART_API_KEY, PIT_DATA_TOKEN 입력 (보드)
```

`PIT_DATA_TOKEN`이 비어 있으면 `pit_snapshot.py` push만 건너뛰고 daily JSON 생성은 계속합니다.

## 3. 수동 1회 실행 (PR 머지 전 검증)

```bash
~/git/ten_bagger-daily/ops/local-daily/ten-bagger-daily.sh
# 또는 특정 날짜 (gate 우회 없음 — origin/main에 파일 있으면 skip). 주말에는 날짜를 꼭 넘깁니다:
# TEN_BAGGER_FORCE=1 ~/git/ten_bagger-daily/ops/local-daily/ten-bagger-daily.sh 2026-10-30
```

로그는 stderr의 `ten-bagger-daily:` 접두사로 journal/systemd와 동일합니다.

## 4. Gate (CI와 동일)

스크립트는 **오늘(KST) `content/daily/<날짜>.json`이 이미 `origin/main`에 있으면** daily 생성을 건너뜁니다. `.github/workflows/daily.yml`의 `gate` job과 같은 조건입니다.

확인:

```bash
TARGET=$(TZ=Asia/Seoul date +%F)
cd ~/git/ten_bagger-daily && git fetch origin main
git cat-file -e "origin/main:content/daily/${TARGET}.json" && echo "would skip" || echo "would run"
```

daily 가 이미 있어도 ledger 단계는 따로 판단합니다(아래 7).

## 5. systemd user timer (PR 머지 후 활성화)

```bash
mkdir -p ~/.config/systemd/user
cp ~/git/ten_bagger-daily/ops/local-daily/systemd/ten-bagger-daily.service ~/.config/systemd/user/
cp ~/git/ten_bagger-daily/ops/local-daily/systemd/ten-bagger-daily.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now ten-bagger-daily.timer
systemctl --user list-timers ten-bagger-daily.timer
```

`Persistent=true`라 호스트가 꺼져 있던 구간은 다음 기동 후 한 번 catch-up 합니다 (gate가 이미 push된 날은 skip).

## 6. 실패 조사

```bash
journalctl --user -u ten-bagger-daily.service -n 80 --no-pager
```

`git pull --rebase` 또는 `git push` 실패 시 서비스는 non-zero로 종료합니다.

## 7. push 흐름

1. `git fetch`, `git pull --ff-only origin main`
2. daily 가 없으면 `build_universe.py`, `generate_daily.py`, (선택) `pit_snapshot.py`, manifest/validate, `content/` commit
3. 앞선 commit 을 `git pull --rebase` 후 push. ledger 가 실패해도 daily 는 먼저 나갑니다.
4. ledger: `content/ledger/{KR,US}.json` 중 오래된 `asOfDate` 가 이번 asOfDate(기본은 대상 날짜)보다 오래됐을 때만 `regenerate_ledger.py`, manifest/validate, `export_picks.py` 를 돌리고 `content/ledger`, `content/performance`, `content/exports` 를 commit, push 합니다.
   - 오래된 날짜로 backfill 해도 ledger 를 과거로 되돌리지 않습니다(2026-11-05 에 10-30 backfill 이 ledger 를 되돌린 일).
   - 같은 날짜로 다시 만들려면 `TEN_BAGGER_FORCE_LEDGER=1`, 날짜를 정하려면 `TEN_BAGGER_AS_OF=YYYY-MM-DD`.
   - 금요일 edge baseline(`edge_baseline.py`)은 돌리지 않습니다. 필요하면 `ledger.yml` 을 수동 실행합니다.

## 8. 실패 알림

0 이 아닌 코드로 끝나면 `orca orchestration send --to bot:오르카 --type status --subject 'ten_bagger 매일 실행 실패'` 를 보냅니다. 본문은 대상 날짜, 단계(sync, deps, daily, push, ledger), 종료 코드, 스크립트의 오류 문구뿐입니다. env 값은 넣지 않습니다. CLI 경로는 `TEN_BAGGER_ORCA_BIN`, 보내는 이는 `TEN_BAGGER_NOTIFY_FROM`(기본 `bot:ten-bagger-daily`)으로 바꿉니다.

GitHub push 권한은 호스트에 설정된 `git`/`gh` 자격(예: SSH 또는 credential helper)에 의존합니다.
