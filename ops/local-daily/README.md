# Local daily runner (Paperclip / systemd)

GitHub Actions 스케줄 지연을 피하려고 **Paperclip 호스트**에서 평일 06:07 KST에 `generate_daily.py`만 돌리고 `content/`만 push합니다. Astro 빌드와 Pages 배포는 저장소의 `daily.yml`이 담당합니다.

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
# 또는 특정 날짜 (gate 우회 없음 — origin/main에 파일 있으면 skip):
# TEN_BAGGER_FORCE=1 ~/git/ten_bagger-daily/ops/local-daily/ten-bagger-daily.sh 2026-10-30
```

로그는 stderr의 `ten-bagger-daily:` 접두사로 journal/systemd와 동일합니다.

## 4. Gate (CI와 동일)

스크립트는 **오늘(KST) `content/daily/<날짜>.json`이 이미 `origin/main`에 있으면** 생성·push 없이 exit 0 합니다. `.github/workflows/daily.yml`의 `gate` job과 같은 조건입니다.

확인:

```bash
TARGET=$(TZ=Asia/Seoul date +%F)
cd ~/git/ten_bagger-daily && git fetch origin main
git cat-file -e "origin/main:content/daily/${TARGET}.json" && echo "would skip" || echo "would run"
```

저장소 cron(06:07 KST fallback)은 그대로 두면, systemd가 먼저 push한 날에는 Actions `gate`가 skip 합니다.

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

1. `git fetch` 후 gate 검사  
2. `git pull --ff-only origin main`  
3. `build_universe.py` → `generate_daily.py` → (선택) `pit_snapshot.py` → manifest/validate  
4. `content/` commit  
5. **`git pull --rebase origin main`** — 실패 시 종료  
6. `git push origin main`

GitHub push 권한은 호스트에 설정된 `git`/`gh` 자격(예: Paperclip runner용 SSH 또는 credential helper)에 의존합니다.
