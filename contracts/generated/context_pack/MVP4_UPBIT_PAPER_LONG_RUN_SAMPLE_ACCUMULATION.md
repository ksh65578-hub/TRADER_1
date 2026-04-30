# MVP4_UPBIT_PAPER_LONG_RUN_SAMPLE_ACCUMULATION

context_pack_id: MVP4_UPBIT_PAPER_LONG_RUN_SAMPLE_ACCUMULATION
task_class: MVP4_UPBIT_PAPER_LONG_RUN_RUNTIME_SAMPLE_HISTORY
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP4-UPBIT-PAPER-LONG-RUN-SAMPLE-ACCUMULATION-SPAN-PROVENANCE"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: ["schema_validator", "registry_validator", "paper_shadow_evidence_accumulation_validator", "runtime_schema_instance_validator", "patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator", "source_bundle_hygiene_validator", "shipped_package_hygiene_validator", "secret_scan_validator", "coverage_index_validator", "live_final_guard_validator"]
included_artifact_ids: ["contracts/schema/paper_shadow_evidence_accumulation_report.schema.json", "trader1/research/shadow/shadow_runner.py", "trader1/research/shadow/evidence_accumulator.py", "trader1/validation/mvp0_validators.py", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "tests/research/test_paper_shadow_evidence_accumulator.py", "tests/validators/fixtures/paper_shadow_evidence_accumulation_pass.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_insufficient_sample_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_stale_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_missing_reason_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_live_flag_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_identity_mismatch_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_identity_stale_fail.json", "tests/validators/fixtures/paper_shadow_evidence_accumulation_false_long_run_claim_fail.json", "contracts/security/source_bundle_manifest.json", "tools/emit_upbit_paper_long_run_sample_accumulation_patch_evidence.py", "contracts/generated/context_pack/MVP4_UPBIT_PAPER_LONG_RUN_SAMPLE_ACCUMULATION.md"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- paper/shadow evidence reports expose evidence_span_source and evidence_span_source_status
- operation-report accumulation marks missing span provenance as NOT_PROVIDED/MISSING with evidence_span_hours=0
- supporting_source_window_count is hash-covered and must match paired PAPER/SHADOW supporting source ids
- long-run eligibility remains blocked unless sample, window, span provenance, supporting windows, and actual runtime source evidence all pass
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- this patch does not create long-run evidence
- this patch does not run private exchange/account/API calls and does not use credentials
- MVP-5 remains blocked on external live-review evidence and operator approval

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: 2026-04-30T23:45:21Z
