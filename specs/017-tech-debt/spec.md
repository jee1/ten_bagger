# Specification: Tech Debt Remediation

Epic: #27

## Problem

Score v2(#16) 이후 스크리닝 엔진·일일 파이프라인 복잡도가 증가했으나, 통합 테스트·CI 복원력·모듈 구조가 따라가지 못함.

## Goals

- 일일 생성 파이프라인 회귀를 CI에서 포착
- CI push 충돌·외부 API 장애에 대한 복원력
- `screen.py` 모듈화로 유지보수성 확보
- 장기 콘텐츠 증가에 대한 빌드 스케일 대비

## Non-goals

- Score v3 알고리즘 변경
- 대체 데이터 소스 전면 교체 (Phase 3에서 검토만)
- 프론트엔드 E2E 테스트 (선택, 별도 논의)

## Acceptance criteria

- [x] Phase 1: #28–#32 완료
- [x] Phase 2: #33–#36 완료
- [ ] Phase 3: 필요 시 #37–#39 착수

## Issues

| # | Title | Phase |
|---|-------|-------|
| 28 | 일일 파이프라인 통합 테스트 | 1 |
| 29 | CI git push 재시도 | 1 |
| 30 | pre-commit CI 연동 | 1 |
| 31 | backtest_screen 스냅샷 | 1 |
| 32 | 스코어링 경계값 테스트 | 1 |
| 33 | screen.py 모듈 분리 | 2 |
| 34 | v1 스코어링 분리 | 2 |
| 35 | types.ts 단일화 | 2 |
| 36 | 실패 알림 | 2 |
| 37 | Content Collections | 3 |
| 38 | yfinance 회복력 | 3 |
| 39 | build_universe 테스트 | 3 |
