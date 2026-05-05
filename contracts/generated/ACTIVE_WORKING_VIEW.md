# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-05-05T22:10:19Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT_20260506_002
next_allowed_task_class: MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Audited UPBIT PAPER current evidence writer artifacts exist and are bound to the PAPER portfolio snapshot. Dashboard and summary logic now distinguish three operator states:

1. VERIFIED: fresh audited PAPER ledger display truth.
2. STALE: last verified audited PAPER ledger display truth that requires PAPER rerun before review.
3. UNVERIFIED: missing, invalid, or unbound current truth.

None of these states creates LIVE_READY, live order permission, or scale-up permission.
