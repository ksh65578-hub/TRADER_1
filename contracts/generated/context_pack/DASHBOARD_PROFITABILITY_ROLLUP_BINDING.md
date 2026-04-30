# DASHBOARD_PROFITABILITY_ROLLUP_BINDING

context_pack_id: DASHBOARD_PROFITABILITY_ROLLUP_BINDING
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
created_at_utc: 2026-04-29T15:43:55Z

## Included Sections
- SECTION_DASHBOARD_OPERATOR_UX
- SECTION_STRATEGY_PROFITABILITY_EVIDENCE
- SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL
- SECTION_LIVE_FINAL_GUARD

## Included Requirement IDs
- REQ-MVP4-DASHBOARD-PROFITABILITY-ROLLUP-BINDING
- REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR
- REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT
- REQ-MVP4-DASHBOARD-PROFITABILITY-MATURITY-UX-HARDENING

## Acceptance Checklist
- Dashboard can load profitability_evidence_maturity_rollup.json for PAPER display.
- Dashboard treats the rollup as display truth only, never execution truth.
- Rollup projection shows 10/10 component coverage, 4 PAPER scorecard input components, and 6 remaining maturity gaps.
- Optimizer ranking remains blocked and all live/scale flags remain false.
- Rollup live flag drift or missing component count becomes BLOCKED/ERROR in the dashboard shell.
- Runtime dashboard_shell.json artifacts are regenerated after schema changes.

## Known Omissions By Design
- This context pack does not provide LIVE_READY evidence.
- This context pack does not permit live config mutation, real exchange calls, credential use, or risk scale-up.
- Long-run paper/shadow sample evidence remains required before any higher-stage review.

## Conflict Rule
TRADER_1.md active authority wins over this generated context pack.
