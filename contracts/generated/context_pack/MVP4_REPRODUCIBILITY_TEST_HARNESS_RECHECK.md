# MVP4_REPRODUCIBILITY_TEST_HARNESS_RECHECK

context_pack_id: MVP4_REPRODUCIBILITY_TEST_HARNESS_RECHECK
task_class: MVP4_REPRODUCIBILITY_TEST_HARNESS_RECHECK
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_TEST_REPRODUCIBILITY", "SECTION_RUNTIME_STABILITY", "SECTION_LIVE_FINAL_GUARD", "SECTION_SOURCE_BUNDLE_HYGIENE"]
included_requirement_ids: ["REQ-MVP4-REPRODUCIBILITY-TEST-HARNESS-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.safe_smoke_report.v1"]
included_validator_ids: ["patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "secret_scan_validator", "live_final_guard_validator"]
included_artifact_ids: ["tools/run_safe_smoke.py", "system/evidence/patch_results/MVP4_REPRODUCIBILITY_TEST_HARNESS_RECHECK.patch_result.json"]

acceptance_checklist:
- full unittest discover passes locally without live credentials
- safe smoke output uses shared atomic writer
- patch_result coverage_index_result uses closed PASS/UPDATED_PASS/UNCHANGED_PASS values
- source bundle excludes runtime/cache/pyc artifacts and contains no secrets
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live account read-only credential check
- no official API verification
- no manual order test
- no live burn-in

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is only a read cache.
generated_at_utc: 2026-04-29T11:51:59Z
