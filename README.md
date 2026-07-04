# Ten Bagger Daily

매일 하나의 **텐베거(5년 10배) 후보**를 규칙 기반으로 선정해 공개하는 정적 사이트입니다.

- **DB 없음**: `content/daily/YYYY-MM-DD.json`이 기록의 원천
- **매일 06:00 KST**: GitHub Actions가 스크리닝 → JSON 커밋 → Astro 빌드 → GitHub Pages 배포
- **한·미 교대**: 날짜(일) 홀수=한국, 짝수=미국
- **없음 표시**: 복합 점수 70 미만이면 해당 일 `no_pick`
- **30일 중복 금지**: 최근 30일 내 추천 종목 제외
- **한국어·영어 병기**

## 로컬 개발

```bash
npm install
npm run dev
```

GitHub Pages와 동일한 base path로 미리보기:

```bash
BASE_PATH=/ten_bagger npm run dev
npm run build
BASE_PATH=/ten_bagger npm run preview
```

## 일일 리포트 수동 생성

```bash
pip install -r scripts/requirements.txt
npm run generate:daily -- 2026-07-05
```

## 배포 (GitHub Pages)

1. GitHub 저장소 생성 후 push
2. **Settings → Pages → Source**: GitHub Actions
3. `.github/workflows/daily.yml`이 매일 06:00 KST에 실행됩니다
4. `workflow_dispatch`로 날짜 지정 수동 실행도 가능합니다

저장소 이름이 `ten_bagger`가 아니면 `astro.config.mjs`의 `SITE_URL` / `BASE_PATH`와 workflow의 env를 맞춰 주세요.

## 구조

```
content/daily/     # 일별 JSON (pick | no_pick)
content/manifest.json
scripts/           # Python 스크리닝 엔진
src/               # Astro 페이지
```

선정 방법은 사이트의 **Methodology / 선정 방법** 페이지를 참고하세요.

## 면책

본 프로젝트는 투자 권유가 아닙니다. 모든 투자 결정과 손실은 본인 책임입니다.
