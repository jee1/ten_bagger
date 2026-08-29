# Glossary — Performance Loop

English definition · Korean gloss. Minimum set for docs gate (Q24).

| Term | English | 한국어 요지 |
|------|---------|------------|
| **pick** | A day the screener publishes a chosen symbol that met the score threshold. | 점수 기준을 통과해 종목이 선정·공개된 날 |
| **no_pick** | A day with no symbol recommendation (e.g. composite below threshold). | 기준 미달 등으로 종목 추천 없이 기록된 날 |
| **PIT** | Point-in-time: only information available at the decision timestamp may be used. | 의사결정 시점에 알 수 있었던 정보만 사용 (미래 정보 금지) |
| **OOS** | Out-of-sample: evaluation on data not used to fit the candidate rule/weights. | 적합에 쓰지 않은 구간으로 검증하는 표본 외 평가 |
| **GO/NO-GO** | Merge gate outcome for Score v3 (see ADR 0004). | Score v3 병합 허용(GO) / 거부(NO-GO) 판정 |
| **ledger** | Additive store of pick/performance events separate from daily pick JSON semantics. | 일별 pick JSON과 별도로 쌓는 측정·이벤트 원장 |
| **forward return** | Return from ADR 0002 entry price to horizon exit price. | 선정 후 진입가부터 목표 기간 청산가까지 수익률 |

Additional useful terms (non-mandatory):

| Term | English | 한국어 요지 |
|------|---------|------------|
| **walk-forward** | Rolling train/test (or evaluate) windows through time. | 시간을 밀어가며 검증하는 방식 |
| **benchmark** | Reference index return for excess-return comparison. | 초과수익 비교용 기준 지수 |
