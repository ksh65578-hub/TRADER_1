# MVP4_PROFITABILITY_ROLLUP_SCORECARD_LONG_RUN_SPLIT

context_pack_id: MVP4_PROFITABILITY_ROLLUP_SCORECARD_LONG_RUN_SPLIT
task_class: MVP4_PROFITABILITY_ROLLUP_SCORECARD_LONG_RUN_SPLIT
created_at_utc: 2026-04-29T16:07:53Z
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

## Purpose

Separate PAPER scorecard input eligibility from long-run paper/shadow evidence maturity so dashboards and validators do not treat scorecard input as LIVE_READY, and do not hide long-run blockers.

## Included Requirement IDs

- REQ-MVP4-PROFITABILITY-ROLLUP-SCORECARD-LONG-RUN-SPLIT
- REQ-MVP4-PAPER-SHADOW-LONG-RUN-EVIDENCE-VISIBILITY
- REQ-MVP4-DASHBOARD-PROFITABILITY-ROLLUP-BINDING
- REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR

## Acceptance Checklist

- `paper_scorecard_input_eligible` is explicit for each maturity component.
- `long_run_evidence_eligible` is explicit for each maturity component.
- `long_run_blocker_code` stays visible when long-run maturity is missing.
- Dashboard counts scorecard input using the explicit field, not only maturity_status.
- Runtime dashboard artifacts validate after schema changes.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

## Known Omissions By Design

- No live order path is enabled.
- No official API, credential, read-only account snapshot, burn-in, manual order test, or operator approval evidence is created.
- Long-run profitability evidence remains blocked until real PAPER/SHADOW operational evidence exists.
