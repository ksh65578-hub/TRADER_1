# UPBIT_PAPER_SCORECARD_DASHBOARD_VISIBILITY

context_pack_id: UPBIT_PAPER_SCORECARD_DASHBOARD_VISIBILITY
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

## Included Sections

- SECTION_TOKEN_NAVIGATION
- SECTION_PROFIT_CONVERGENCE_REINFORCEMENT
- SECTION_PROFITABILITY_OPTIMIZER
- SECTION_DASHBOARD_SHELL
- SECTION_LIVE_FINAL_GUARD
- SECTION_UPBIT_PAPER_RUNTIME

## Requirement IDs

- REQ-MVP4-UPBIT-PAPER-SCORECARD-DASHBOARD-VISIBILITY
- REQ-MVP4-UPBIT-PAPER-RUNTIME-SCORECARD-BRIDGE
- REQ-MVP4-PAPER-RUNTIME-CANDIDATE-NET-EV-AFTER-COST
- REQ-MVP4-SCORECARD-NOT-LIVE-READY-UX-GUARD
- REQ-MVP4-DASHBOARD-PROFITABILITY-ACTUAL-RUNTIME-SOURCE-VISIBILITY

## Acceptance Checklist

- Dashboard loads scoped Upbit KRW spot PAPER candidate_scorecard.json when present.
- Candidate scorecard is display truth only and cannot become execution truth.
- Cross-scope, stale, or live-flag-drift scorecards are shown as blocked.
- Net EV after cost, candidate id, strategy id, symbol, and ranking blocker are visible to the operator.
- Source artifact table includes CANDIDATE_SCORECARD when projected.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

## Known Omissions By Design

- This patch does not create LIVE_READY evidence.
- This patch does not create OOS, walk-forward, bootstrap, live burn-in, official API verification, or operator approval evidence.
- Candidate ranking remains PAPER review only and blocked when robustness evidence is missing.

## Conflict Resolution

TRADER_1.md wins over this context pack. This context pack is a read cache, not authority.
