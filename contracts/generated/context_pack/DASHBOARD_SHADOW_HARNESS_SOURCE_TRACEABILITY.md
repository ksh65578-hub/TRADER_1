# DASHBOARD_SHADOW_HARNESS_SOURCE_TRACEABILITY

context_pack_id: DASHBOARD_SHADOW_HARNESS_SOURCE_TRACEABILITY
task_class: MVP4_DASHBOARD_SHADOW_HARNESS_SOURCE_TRACEABILITY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D

This generated context pack is a read cache only. TRADER_1.md remains the highest authority and AGENTS.md remains the implementation guide.

Included section ids:
- SECTION_DASHBOARD_OPERATOR_VISIBILITY
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_LIVE_FINAL_GUARD
- SECTION_LONG_RUN_OPERATION

Included requirement ids:
- REQ-MVP4-DASHBOARD-SHADOW-HARNESS-SOURCE-TRACEABILITY
- REQ-MVP4-DASHBOARD-SHADOW-HARNESS-STATUS-BINDING
- REQ-MVP4-SHADOW-OBSERVATION-ACTUAL-RUNTIME-HARNESS

Acceptance checklist:
- Dashboard shadow_runtime_harness_status and Source Artifacts must agree.
- If shadow_runtime_harness_status.source is actual_runtime_harness_report.json, Source Artifacts must include SHADOW_RUNTIME_HARNESS with the same filename.
- If no harness report is loaded, Source Artifacts must not claim SHADOW_RUNTIME_HARNESS.
- The actual runtime filename is actual_runtime_harness_report.json.
- Stale samples may overlap degraded samples; long-run validation must not double-count stale and degraded samples as disjoint sets.
- Dashboard remains display truth only; execution truth, ledger truth, and exchange truth stay separate.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

Known omissions by design:
- No real exchange account call.
- No credential loading.
- No live order path enabling.
- No long-run evidence claim from the short-window harness.

Conflict resolution rule:
- If this context pack conflicts with TRADER_1.md, TRADER_1.md wins.
