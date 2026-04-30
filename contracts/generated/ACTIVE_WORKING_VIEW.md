# ACTIVE_WORKING_VIEW

generated_at_utc: 2026-04-30T14:44:41Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: MVP4_UPBIT_PAPER_SCORECARD_DASHBOARD_VISIBILITY_20260430_001
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Upbit PAPER runtime now writes candidate_scorecard.json and the read-only dashboard projects it as display truth. The first screen can show the PAPER scorecard candidate, symbol, net EV after cost, and ranking blocker while preserving live order blocks.

## Latest Hidden Defect Closed

The generated PAPER scorecard existed but was not loaded by the launcher dashboard path, so the operator could not see the actual candidate quality or robustness blocker. The dashboard now refuses stale, cross-scope, or live-flag-drift scorecards and keeps LIVE_READY false.

## Next Safe Task

MVP4_UPBIT_PAPER_SCORECARD_ROBUSTNESS_FIXTURES_CONTINUE
