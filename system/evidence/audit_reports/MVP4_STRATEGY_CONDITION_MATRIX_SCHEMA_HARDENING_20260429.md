# MVP4 Strategy Condition Matrix Schema Hardening

created_at_utc: 2026-04-29T00:55:15Z
patch_id: MVP4_STRATEGY_CONDITION_MATRIX_SCHEMA_HARDENING_20260429_001

Findings:
- Strategy review had no strict condition matrix requiring entry, exit, no-trade, regime, and risk-off traceability.
- A strategy family could appear operator-visible without proving why entries were allowed, why exits occur, or why risk-off blocks entry.
- The issue did not create live permission, but it weakened strategy diagnosis and user-facing explanation quality.

Patch:
- Added strategy_condition_matrix schema.
- Added strategy_condition_matrix_validator.
- Added PASS and negative fixtures for missing risk-off coverage, live flag drift, and missing no-trade blockers.
- Updated profitability maturity audit while keeping the broader contract_gap open.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
