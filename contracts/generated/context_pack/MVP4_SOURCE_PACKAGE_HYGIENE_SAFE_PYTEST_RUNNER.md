# MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER

context_pack_id: MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER
task_class: MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-SOURCE-PACKAGE-HYGIENE-SAFE-PYTEST-RUNNER"]
included_schema_ids: ["trader1.hygiene_safe_pytest_report.v1", "trader1.patch_result.v1"]
included_validator_ids: ["schema_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "bytecode_free_syntax_validator", "live_final_guard_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
included_artifact_ids: ["pyproject.toml", "contracts/schema/hygiene_safe_pytest_report.schema.json", "tools/run_hygiene_safe_pytest.py", "tools/emit_source_package_hygiene_safe_pytest_runner_patch_evidence.py", "tests/runtime/test_bytecode_free_syntax_check.py", "tests/security/test_source_bundle_security.py", "contracts/security/source_bundle_manifest.json", "contracts/generated/context_pack/MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Use tools/run_hygiene_safe_pytest.py for repo pytest proof runs that must leave no __pycache__, .pytest_cache, .pyc, or .pyo artifacts.
- pyproject disables pytest cacheprovider by default.
- The hygiene-safe pytest report is schema-valid and keeps live flags false.
- Source/shipped package hygiene remains PASS after the test runner executes.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- cache_artifact_count: 0
- shipped_forbidden_count: 0
- safe_pytest_report_status: PASS
- safe_pytest_post_run_cache_artifact_count: 0

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: 2026-05-02T02:26:57Z
