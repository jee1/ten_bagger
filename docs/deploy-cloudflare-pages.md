# Cloudflare Pages 배포 (FINA-29)

프로덕션: `https://tenbagger.finnaut.com`

`finnaut-box`, `finnaut-www`와 동일하게 **Cloudflare Pages**가 `main` push마다 Astro 정적 사이트를 빌드·서빙한다. GitHub Actions `daily.yml` / `ledger.yml`은 콘텐츠 생성·검증만 담당하고, Pages 아티팩트 업로드·`deploy-pages`는 컷오버 후 제거한다.

## Cloudflare Pages 빌드 설정 (finnaut-box와 동일 패턴)

| 항목 | 값 |
|------|-----|
| Production branch | `main` |
| Build command | `npm ci && npm run check && npm run build` |
| Build output directory | `dist` |
| Root directory | `/` (저장소 루트) |
| Node | `NODE_VERSION=22` (CI·`package.json` engines와 동일; box는 24) |

Astro는 빌드 시 환경 변수를 읽는다 (`astro.config.mjs`):

| 변수 | 프로덕션 값 | 비고 |
|------|-------------|------|
| `SITE_URL` | `https://tenbagger.finnaut.com` | sitemap·canonical |
| `BASE_PATH` | `/` | 커스텀 도메인 root |

## Pages 환경 변수 (Production)

GitHub Actions secret 이름 → Cloudflare **Production** 변수 이름. 값은 GitHub **Settings → Secrets and variables → Actions**에서 복사한다 (코멘트·PR에 값 금지).

| Cloudflare 변수 | GitHub Actions secret (원본) | 필수 |
|-----------------|------------------------------|------|
| `PUBLIC_CF_WEB_ANALYTICS_TOKEN` | `PUBLIC_CF_WEB_ANALYTICS_TOKEN_TENBAGGER` | 권장 |
| `PUBLIC_GOOGLE_SITE_VERIFICATION` | `PUBLIC_GOOGLE_SITE_VERIFICATION_TENBAGGER` | 선택 |
| `PUBLIC_NAVER_SITE_VERIFICATION` | `PUBLIC_NAVER_SITE_VERIFICATION_TENBAGGER` | 선택 |
| `SITE_URL` | (고정값) | 예 |
| `BASE_PATH` | (고정값 `/`) | 예 |
| `NODE_VERSION` | `22` | 예 |

`PUBLIC_GOATCOUNTER_CODE`는 코드 기본값 `tenbagger`가 있어 secret 없어도 동작한다. 오버라이드할 때만 Pages에 추가한다.

뉴스레터용 `PUBLIC_*`는 **ten_bagger 저장소에 없음** (2026-11-03 기준). 추가 integration 시 동일 표로 Pages 변수만 확장한다.

로컬·CI 검증: `.env.example` 참고.

## 컷오버 절차 (끊김 없음)

순서를 바꾸지 않는다. GitHub Pages를 DNS 전환 전에 끄지 않는다.

### 1. Cloudflare Pages 프로젝트 생성

1. Cloudflare Dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. GitHub 앱으로 `jee1/ten_bagger` 연결.
3. 위 빌드 표대로 설정 후 **Save and Deploy**.
4. 첫 빌드 green 확인. Preview URL은 프로젝트 이름에 따라 `*.pages.dev` 호스트가 정해진다 (예: `ten-bagger.pages.dev`는 **다른 계정/프로젝트**가 이미 쓸 수 있음). Cloudflare가 할당한 **실제 Preview URL**을 프로젝트 Overview에서 확인한 뒤 검증한다.

### 2. 측정·SEO 확인 (Pages 빌드)

1. Web Analytics: `tenbagger.finnaut.com` 사이트가 이미 대시보드에 있으면 토큰이 `PUBLIC_CF_WEB_ANALYTICS_TOKEN`과 일치하는지 확인.
2. View Source on `*.pages.dev`: CF beacon / verification meta 존재 확인 (변수 누락 시 HTML에 태그 없음).

### 3. 커스텀 도메인 전환

**전:** DNS `tenbagger.finnaut.com` → GitHub Pages (`CNAME` → `jee1.github.io` 등, 현재 프로덕션).

1. Pages 프로젝트 → **Custom domains** → `tenbagger.finnaut.com` 추가.
2. Cloudflare가 제시하는 DNS 레코드로 **같은 호스트명**을 Cloudflare Pages 대상으로 변경 (zone이 Cloudflare에 있으면 CNAME/flattened A 자동).
3. Pages SSL **Active** 대기.
4. 검증:

```bash
curl -sI https://tenbagger.finnaut.com | rg -i '^server:|^cf-ray:'
# 기대: server: cloudflare, cf-ray: ...
```

GitHub Pages였을 때: `server: GitHub.com`.

5. `main`에 빈 커밋 또는 문서만 push 후 Pages 배포 완료 시각을 이슈에 기록.

### 4. GitHub Pages 배포 중단 (프로덕션이 CF일 때만)

DNS 전환 후 `server: cloudflare` 확인 **전에는** `daily.yml` / `ledger.yml`의 deploy job을 제거하는 PR을 **머지하지 않는다** (머지 시 GitHub Pages 갱신만 멈춤).

1. **머지:** 별도 PR로 workflow에서 `upload-pages-artifact`·`deploy` job 제거 (`docs/plans/fina-29-cutover-workflows.patch.md` 참고).
2. GitHub **Settings → Pages**: custom domain 해제 또는 Pages 비활성화 (선택, DNS가 CF면 트래픽 없음).
3. `public/CNAME`은 Astro root 배포에 불필요. CF 전용이면 후속 PR에서 제거 검토 (GitHub Pages 복귀 계획 없을 때).

### 5. 롤백

DNS를 다시 GitHub Pages 대상으로 되돌리고, workflow의 `deploy-pages` job이 있는 커밋으로 revert. GitHub Pages custom domain 재연결.

## GitHub Actions와의 역할 분담 (컷오버 후)

| Workflow | 역할 |
|----------|------|
| `ci.yml` | PR·push 검증 (빌드 only) |
| `daily.yml` | universe·daily JSON·push; **로컬 `npm run build`는 검증용** |
| `ledger.yml` | ledger regenerate·push; 동일 |

프로덕션 HTML은 **push → Cloudflare Pages** 한 경로만 사용한다.

## 참고

- 측정 상세: [site-measurement.md](./site-measurement.md)
- box 배포 README: `finnaut-box` 저장소 README § Cloudflare Pages
