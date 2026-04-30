# PAPER_SHADOW_LONG_RUN_EVIDENCE_VISIBILITY

context_pack_id: PAPER_SHADOW_LONG_RUN_EVIDENCE_VISIBILITY
created_at_utc: 2026-04-29T15:54:53Z
task_class: MVP4_LONG_RUN_PAPER_SHADOW_REPRODUCIBILITY_AND_PROFITABILITY_EVIDENCE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

## Included Section IDs
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_STRATEGY_PROFITABILITY_EVIDENCE
- SECTION_LONG_RUN_STABILITY
- SECTION_OPTIMIZER_CONVERGENCE_GUARDRAIL
- SECTION_LIVE_FINAL_GUARD

## Requirement IDs
- REQ-MVP4-PAPER-SHADOW-LONG-RUN-EVIDENCE-VISIBILITY
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-IDENTITY-BINDING
- REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT

## Acceptance Checklist
- Paper/shadow source bindings remain exchange, market_type, mode, session, candidate, strategy, build, parameter, and hash scoped.
- scorecard_input_eligible may be true for PAPER ranking only.
- long_run_evidence_eligible is separate and must remain false unless minimum window and span evidence is met.
- A false long-run claim with short samples must BLOCK with SAMPLE_INSUFFICIENT.
- live_order_ready, live_order_allowed, can_live_trade, and scale_up_allowed remain false.

## Known Omissions By Design
- No real exchange account, API credential, read-only private stream, or live order evidence was used.
- MVP-5 live-enabling evidence remains external and blocked.
