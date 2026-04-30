# MVP4_OPERATIONAL_PAPER_EVIDENCE_COUNT_BINDING

context_pack_id: MVP4_OPERATIONAL_PAPER_EVIDENCE_COUNT_BINDING
task_class: MVP4_OPERATIONAL_PAPER_EVIDENCE_COUNT_BINDING
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
created_at_utc: 2026-04-29T16:19:53Z

## Scope

This context pack records the MVP-4 safe hardening patch that binds operational PAPER evidence counts to actual generated paper artifacts instead of default maturity-sized sample counts.

## Included Section IDs

- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_STRATEGY_PROFITABILITY_EVIDENCE
- SECTION_DASHBOARD_OPERATOR_UX
- SECTION_LIVE_FINAL_GUARD
- AGENTS_0F_CONVERGENCE_VALIDATOR_RULES
- AGENTS_0G_IMPLEMENTATION_DEPTH_ENFORCEMENT

## Included Requirement IDs

- REQ-MVP4-OPERATIONAL-PAPER-EVIDENCE-COUNT-BINDING
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING
- REQ-MVP4-DASHBOARD-PROFITABILITY-ROLLUP-BINDING
- REQ-MVP4-LONG-RUN-PAPER-SHADOW-OPERATIONAL-EVIDENCE-COLLECTION
- REQ-MVP4-SCHEMA-RUNTIME-INSTANCE-VALIDATION

## Acceptance Checklist

- A single PAPER operational cycle must not fabricate minimum PAPER/SHADOW sample counts.
- PAPER evidence sample count must be derived from the actual dry-run report.
- SHADOW sample count must remain zero unless a scoped shadow artifact exists.
- Optimizer ranking must remain BLOCK_RANKING when evidence maturity is insufficient.
- Dashboard maturity must show COLLECTING/IN_PROGRESS rather than SCORECARD_INPUT_READY for a one-cycle PAPER report.
- Live flags and scale-up flag remain false.

## Known Omissions By Design

- No live account read-only evidence is collected.
- No exchange credential, API key, or real account call is used.
- No LIVE_READY snapshot is written.
- No optimizer/convergence output can mutate live config.

## Conflict Resolution Rule

TRADER_1.md remains the highest authority. This generated context pack is navigation-only and cannot create live permission.
