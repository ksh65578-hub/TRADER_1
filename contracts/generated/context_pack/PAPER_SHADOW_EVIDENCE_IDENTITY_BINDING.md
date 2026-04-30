# PAPER_SHADOW_EVIDENCE_IDENTITY_BINDING

context_pack_id: PAPER_SHADOW_EVIDENCE_IDENTITY_BINDING
task_class: VALIDATOR_PATCH
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
created_at_utc: 2026-04-29T15:07:01Z

## Included Sections
- SECTION_STRATEGY_PROFITABILITY_EVIDENCE
- SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL
- SECTION_LIVE_FINAL_GUARD
- AGENTS_0G_VALIDATOR_IMPLEMENTATION_RULES

## Included Requirements
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-IDENTITY-BINDING
- REQ-MVP4-PATCH-RESULT-COVERAGE-INDEX-ENUM-HARDENING
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING
- REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-MATURITY
- REQ-MVP4-PATCH-RESULT-RUNTIME-SCHEMA-VALIDATION

## Acceptance Checklist
- paper and shadow source evidence IDs are unique.
- paper/shadow source evidence bindings include role, scope, session, artifact path, artifact hash, candidate, strategy, parameter hash, sample count, artifact age, and PASS identity status.
- supplemental source evidence IDs may remain unbound only when paper/shadow role bindings are complete.
- patch_result coverage_index_result is restricted to PASS, UNCHANGED_PASS, or UPDATED_PASS.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, and scale_up_allowed=false.

## Known Omissions By Design
- No live exchange/account/API calls.
- No live readiness, live order permission, live config mutation, or risk scale-up.
- External evidence remains blocked for MVP-5.

## Conflict Resolution Rule
TRADER_1.md remains highest authority. This context pack is a read cache only.
