# MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_DASHBOARD_VISIBILITY

context_pack_id: MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_DASHBOARD_VISIBILITY
task_class: DASHBOARD_UX
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-DASHBOARD-VISIBILITY"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "upbit_paper_ledger_idempotency_runtime_evidence_validator", "read_only_dashboard_validator", "dashboard_visual_layout_validator", "runtime_schema_instance_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py", "contracts/schema/read_only_dashboard_shell.schema.json", "tests/dashboard/test_read_only_dashboard.py", "tools/emit_upbit_paper_ledger_idempotency_dashboard_visibility_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_DASHBOARD_VISIBILITY.md", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json", "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html", "system/runtime/upbit/krw_spot/paper/dashboard/index.html", "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard_shell.json", "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json", "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard_shell.json"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Read-only dashboard loads scoped Upbit PAPER ledger idempotency runtime evidence.
- Ledger Safety panel displays idempotency evidence status, validator status, reconciliation status, portfolio provenance, source ledger count, recomputed event count, duplicate counts, and count mismatch count.
- Dashboard source artifacts include PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE when the report is loaded.
- Any blocked, stale, invalid, or live-mutated idempotency evidence remains display-only and cannot create live or scale-up permission.

known_omissions_by_design:
- This patch does not resolve post-rerun operator reconciliation guidance.
- This patch does not create long-run evidence, LIVE_READY, live config, credentials, orders, or scale-up permission.
- Binance spot/futures remain surface/scaffold gaps.

runtime_summary:
- dashboard_reconciliation_status: BLOCKED
- ledger_idempotency_runtime_evidence_status: PASS
- ledger_idempotency_runtime_validation_status: PASS
- source_ledger_jsonl_count: 28
- recomputed_ledger_event_count: 168
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-05-01T22:15:24Z
