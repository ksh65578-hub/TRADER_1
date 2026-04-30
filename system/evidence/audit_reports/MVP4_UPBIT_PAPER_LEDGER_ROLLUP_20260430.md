# MVP4 Upbit PAPER Ledger Rollup Audit

created_at_utc: 2026-04-30T13:23:32Z
patch_id: MVP4_UPBIT_PAPER_LEDGER_ROLLUP_20260430_001

Finding:
- PAPER runtime wrote cycle-scoped ledger JSONL, but dashboard portfolio values could still be sourced from a single latest cycle instead of a cumulative session rollup.
- Minimal intent event IDs were session-scoped and could collide across repeated PAPER cycles.

Patch:
- Intent event IDs now include intent_id.
- Added paper_ledger_rollup_report schema, runtime builder, validator, and negative tests.
- Persistent loop writes a canonical PAPER ledger rollup artifact.
- Launcher dashboard prefers the fresh scoped rollup portfolio for display-only portfolio values.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
Remaining blocker: this is simulated PAPER ledger truth only, not exchange reconciliation or LIVE_READY evidence.
