# MVP4 Long-Run Operator Summary Hardening Audit

created_at_utc: 2026-04-29T02:53:34Z
patch_id: MVP4_LONG_RUN_OPERATOR_SUMMARY_HARDENING_20260429_001

Findings:
- The dashboard exposed stability details, but did not provide a compact first-screen answer to whether the program is running normally now.
- Current healthy heartbeat status could be confused with validated long-run stability, creating false-safe operator UX risk.
- A future dashboard mutation could hide available stability history or display stale samples as stable without an explicit validator check.

Patch:
- Added long_run_operator_summary to the read-only dashboard shell and schema.
- Rendered a first-screen Long-Run Operation panel with normal blue/green, warning yellow, and error red status semantics.
- Added validator checks that separate RUNNING_NOW from VALIDATED_STABLE and block stale/degraded history from being shown as stable.
- Added negative tests for false validated history, live permission drift, hidden validated history, and stale sample masking.
- Regenerated root launcher dashboard artifacts for UPBIT/BINANCE PAPER/LIVE safe-mode sessions.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
