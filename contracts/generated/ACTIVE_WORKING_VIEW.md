# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-05-01T19:25:11Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD_20260502_001
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Upbit PAPER session-cycle ledger rollup now proves the rolled-up source cycle is bound to latest_paper_ledger_head.json before portfolio truth can PASS. Explicit scoped repair/rerun rollups stay terminal-ledger evidence only and cannot claim latest-head binding. Missing, mismatched, or duplicated ledger inputs block review and keep all live/scaling flags false.

## Next Safe Task

MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_EVIDENCE
