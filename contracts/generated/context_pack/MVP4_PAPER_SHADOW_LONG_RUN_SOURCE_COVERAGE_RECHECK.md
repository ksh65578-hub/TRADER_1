# MVP4_PAPER_SHADOW_LONG_RUN_SOURCE_COVERAGE_RECHECK

context_pack_id: MVP4_PAPER_SHADOW_LONG_RUN_SOURCE_COVERAGE_RECHECK
task_class: MVP4_PAPER_SHADOW_LONG_RUN_SOURCE_COVERAGE_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

## Included Sections
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_LONG_RUN_OPERATION
- SECTION_PARTIAL_WRITE_RECOVERY
- SECTION_LIVE_FINAL_GUARD

## Included Requirement IDs
- REQ-MVP4-PAPER-SHADOW-LONG-RUN-SOURCE-COVERAGE-RECHECK
- REQ-MVP4-PAPER-SHADOW-LONG-RUN-EVIDENCE-VISIBILITY
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-IDENTITY-BINDING
- REQ-MVP4-PROFITABILITY-ROLLUP-SCORECARD-LONG-RUN-SPLIT

## Acceptance Checklist
- Long-run PAPER/SHADOW evidence cannot become eligible from aggregate window/span fields alone.
- A long-run claim must include enough paired per-window PAPER and SHADOW supporting source ids.
- Short-window claims remain SAMPLE_INSUFFICIENT so the operator sees the primary maturity blocker first.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

## Known Omissions By Design
- No live order, credential, real exchange account, read-only account, official API, manual order, or burn-in evidence was used.
- Retained archive was not read because no omitted-detail or conflict-resolution trigger was present.
- Full compileall bytecode generation was blocked by a Windows __pycache__ file lock; test imports and full regression passed with bytecode writes disabled.

## Conflict Resolution
TRADER_1.md active authority overrides generated context pack content. This pack is read cache only.
