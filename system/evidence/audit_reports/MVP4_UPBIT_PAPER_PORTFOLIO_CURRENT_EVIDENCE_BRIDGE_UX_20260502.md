# MVP4 Upbit PAPER Portfolio Current-Evidence Bridge UX Audit

created_at_utc: 2026-05-01T23:04:14Z
patch_id: MVP4_UPBIT_PAPER_PORTFOLIO_CURRENT_EVIDENCE_BRIDGE_UX_20260502_001

Patch:
- Made the portfolio cards explain that configured PAPER capital is visible but not verified current cash/equity.
- Bound the post-rerun closure recheck bridge blocker into the portfolio snapshot and operation status.
- Kept ledger provenance PASS as support-only while POST_RERUN_RECONCILIATION_REQUIRED remains active.

Runtime evidence:
- portfolio_status=UNVERIFIED
- source_snapshot_status=BLOCKED
- portfolio_blocking_reason=POST_RERUN_RECONCILIATION_REQUIRED
- current_evidence_bridge_status=BLOCKED_BY_POST_RERUN_CLOSURE

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no current evidence writer or live config mutation added
