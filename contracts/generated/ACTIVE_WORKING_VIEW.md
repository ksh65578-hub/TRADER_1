# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-05-02T04:42:52Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE_20260502_001
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

The Upbit PAPER dashboard can now display verified simulated portfolio values when a fresh summary portfolio snapshot is bound to matching ledger idempotency runtime evidence. Reconciliation blockers remain visible and still block current-evidence writes, trading review, live orders, and risk scale-up.

Current dashboard display: portfolio_status=VERIFIED, cash=845,923 KRW, equity=999,923 KRW, blocker=STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED.

## Next Safe Task

MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE
