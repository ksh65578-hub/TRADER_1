# MVP4 Upbit Public REST Continuity Evidence Audit

created_at_utc: 2026-04-30T12:06:43Z
patch_id: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE_20260430_001

Findings:
- Hidden issue: a single public REST PASS sample did not prove market data continuity.
- Hidden issue: repeated calls inside the same candle could be mistaken for progress unless latest event timestamps are compared.
- Hidden issue: data continuity needed its own operator-visible BLOCKED state, distinct from live readiness.

Patch:
- Added strict public REST continuity schema, runtime builder, validator, tests, and CLI tool.
- Repeated latest candle timestamps now block continuity with DATA_QUALITY_INSUFFICIENT.
- Continuity evidence is PAPER-only and cannot create live readiness, live order permission, or scale-up.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
