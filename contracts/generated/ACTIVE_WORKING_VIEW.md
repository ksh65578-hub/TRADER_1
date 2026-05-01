# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-05-01T00:40:57Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_POLICY_20260501_001
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Upbit PAPER stale loop regeneration is planned but not executed. Legacy schema-drift reports have PAPER-only replacement paths, while deletion, overwrite, live orders, long-run evidence, promotion, and scale-up remain blocked.

## Current Regeneration Plan

- status: READY_FOR_SAFE_PAPER_REGENERATION
- planned PAPER replacements: 16
- operator-review items: 0
- duplicate replacement paths: 0
- actual regeneration performed: false

## Next Safe Task

MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_EXECUTION_GUARD
