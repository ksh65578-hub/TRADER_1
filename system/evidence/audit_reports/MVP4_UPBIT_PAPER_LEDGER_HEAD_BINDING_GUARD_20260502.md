# MVP4 Upbit PAPER Ledger Head Binding Guard

created_at_utc: 2026-05-01T19:25:11Z
patch_id: MVP4_UPBIT_PAPER_LEDGER_HEAD_BINDING_GUARD_20260502_001

Finding:
- PAPER session-cycle ledger rollup needed explicit proof that the rolled-up ledger source matched latest_paper_ledger_head.json.
- Explicit scoped repair/rerun rollups needed to remain terminal-ledger evidence without falsely claiming the current latest head.

Patch:
- Added ledger-head binding fields to paper_ledger_rollup_report.
- Added ledger_input_scope to separate SESSION_CYCLE_GLOB from EXPLICIT_SCOPED_PATHS evidence.
- Blocked duplicate explicit ledger_paths.
- Blocked missing or mismatched latest ledger head reports for session-cycle rollups.
- Kept explicit scoped rollups NOT_APPLICABLE for latest-head binding while retaining ledger-chain validation.
- Added negative tests and validator coverage.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential use
- no exchange private API call
- no live order path enabled
