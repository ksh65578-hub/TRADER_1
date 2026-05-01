# MVP4 Upbit PAPER Verified Portfolio Ledger Bootstrap Audit

created_at_utc: 2026-05-01T21:41:16Z
patch_id: MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP_20260502_001

Finding:
- Session-cycle PAPER rollup selected the final source by filename order, so a valid latest_paper_ledger_head.json could mismatch the rollup head when older or differently named cycle files sorted later.

Patch:
- Session-cycle rollup now processes the scoped ledger named by latest_paper_ledger_head.json as the provenance tail when that file exists in the session ledger namespace.
- Existing missing, invalid, escaped, or mismatched latest-head cases still block.
- The dashboard now receives a fresh VERIFIED simulated PAPER portfolio only after the rollup validates PASS.

Runtime evidence:
- rollup_status=PASS
- ledger_head_match_status=PASS
- ledger_head_cycle_id=mvp4-upbit-paper-ledger-head-binding-guard-cycle-2
- portfolio_status=VERIFIED

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- post-rerun and long-run blockers remain open
