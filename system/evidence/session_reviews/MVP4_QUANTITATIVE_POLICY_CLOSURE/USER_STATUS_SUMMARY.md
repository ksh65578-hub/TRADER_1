# USER_STATUS_SUMMARY

generated_at_utc: 2026-05-05T15:25:52Z

현재 상태: 정량 판단 규칙은 더 닫혔지만, 실거래는 아직 차단입니다.

사용자가 지금 보면 되는 것:
- PAPER 실행: 가능하지만 이번 세션은 실제 PAPER 런을 새로 돌린 것이 아니라 정책/검증 코드를 고도화했습니다.
- 대시보드 확인: LIVE 가능 여부는 `BLOCKED`로 나와야 합니다.
- LIVE_READY 확인: 현재는 `LIVE_READY_MISSING`입니다.
- MICRO_LIVE/LIVE 전환: 금지입니다.
- STOP: 런타임 실행 중이면 사용자가 종료할 수 있습니다.

핵심 이유:
- LIVE_READY snapshot 없음
- official API/read-only burn-in/operator approval 증거 없음
- Binance spot/futures는 정책 후보 표면만 강화했고 runtime 주문 경로는 아직 surface-only입니다.

live_order_ready=false
live_order_allowed=false
can_live_trade=false
scale_up_allowed=false
