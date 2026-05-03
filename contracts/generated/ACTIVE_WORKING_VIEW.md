# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-05-03T13:22:09Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_DEPTH_RECHECK_20260503_001
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Upbit PAPER ledger idempotency runtime evidence now fails closed unless the ledger head cycle is present in the current persistent-loop PASS cycle_results and carries public input hash, canonical depth, feature, regime, and strategy/regime/cost linkage evidence. This is PAPER-only evidence and does not create live readiness or scale-up permission.

## Next Safe Task

MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK
