# MVP4 Upbit PAPER Post-Rerun Reconciliation Recheck

created_at_utc: 2026-05-03T14:08:01Z
patch_id: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK_20260503_001

Finding:
- Post-rerun current-evidence closure recheck did not directly expose the supporting ledger runtime-depth binding fields.

Patch:
- Added persistent-loop/runtime-depth ledger fields to the post-rerun closure recheck schema and report.
- Required runtime-depth PASS, public data source/runtime hash equality, ledger-head cycle binding, and false live/scale linkage flags.
- Added negative tests and validator coverage for runtime-depth regression and live-linkage mutation.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
