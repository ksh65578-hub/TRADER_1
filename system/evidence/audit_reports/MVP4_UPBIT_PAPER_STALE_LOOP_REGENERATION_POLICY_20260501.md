# MVP4 Upbit PAPER Stale Loop Regeneration Policy Audit

created_at_utc: 2026-05-01T00:40:57Z
patch_id: MVP4_UPBIT_PAPER_STALE_LOOP_REGENERATION_POLICY_20260501_001

Finding:
- Stale loop reconciliation identified legacy schema-drift loop reports, but the next action was not represented as a source-preserving regeneration plan.
- Without an explicit plan, a future patch could accidentally overwrite/delete legacy evidence or treat planned regeneration as actual long-run runtime evidence.
- A RECONCILIATION_REQUIRED source also needed a clear operator-review path to avoid silent or ambiguous handling.

Patch:
- Added strict stale loop regeneration plan schema, runtime builder/writer/validator, registry entry, runtime artifact, and negative tests.
- The plan maps legacy schema-drift reports to new PAPER-only replacement paths.
- The plan excludes current accepted evidence and maps RECONCILIATION_REQUIRED sources to operator review.
- The patch performs no regeneration, no deletion, no overwrite, no private exchange/account/API call, no live order, no long-run evidence creation, no promotion, and no scale-up.

Runtime plan summary:
- plan_status: READY_FOR_SAFE_PAPER_REGENERATION
- regeneration_item_count: 16
- operator_review_item_count: 0
- duplicate_replacement_path_count: 0
- actual_regeneration_performed: false

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
