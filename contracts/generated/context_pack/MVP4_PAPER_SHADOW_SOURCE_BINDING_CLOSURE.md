# MVP4_PAPER_SHADOW_SOURCE_BINDING_CLOSURE

context_pack_id: MVP4_PAPER_SHADOW_SOURCE_BINDING_CLOSURE
task_class: MVP4_PAPER_SHADOW_SOURCE_BINDING_CLOSURE
source_trader1_sha256: FF6C3046FD64C3B16E874F3770CCB57E04B1E1E75775125382F285F33BD0052B
source_agents_sha256: 21F059ED68723E632704422C2E4DE94EA4093E49D4C3C5963A821B0C0953941D
included_section_ids:
- SECTION_PAPER_SHADOW_EVIDENCE
- SECTION_OPTIMIZER_OBJECTIVE
- SECTION_CONVERGENCE_MEMORY
- SECTION_LIVE_FINAL_GUARD
included_requirement_ids:
- REQ-MVP4-PAPER-SHADOW-SOURCE-BINDING-CLOSURE
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING
- REQ-MVP4-PAPER-SHADOW-EVIDENCE-IDENTITY-BINDING
included_schema_ids:
- trader1.paper_shadow_evidence_accumulation_report.v1
included_validator_ids:
- paper_shadow_evidence_accumulation_validator
- runtime_schema_instance_validator
- read_only_dashboard_validator
- live_final_guard_validator
included_artifact_ids:
- trader1/research/shadow/shadow_runner.py
- trader1/validation/mvp0_validators.py
- contracts/schema/paper_shadow_evidence_accumulation_report.schema.json
- tests/research/test_paper_shadow_evidence_accumulator.py
- tests/validators/test_paper_shadow_evidence_accumulation_validator.py
source_section_hashes:
- SECTION_PAPER_SHADOW_EVIDENCE: 2C828EDB7BB8D0DDE460C36FA61FE4D7C4BD36F22C91BA3AF276374D9698551B
- SECTION_OPTIMIZER_OBJECTIVE: FB8353ECDF5D8C67FB6B6CB8646C33AB39B34290CEBF49C338D49DA01F6119C9
- SECTION_CONVERGENCE_MEMORY: D4679EA2578F4756C759497EEA73173F23737DE6994A32E7B99A10A4D2796883
- SECTION_LIVE_FINAL_GUARD: CB6BA4D75140E551611EC16BB3EE9950E3CEAB8E181BF446B8317E80A4EC3761
acceptance_checklist:
- Bound paper/shadow source_evidence_ids must exactly match source_evidence_bindings.
- Supporting source ids must be separate and cannot duplicate bound source ids.
- Unbound source evidence must BLOCK scorecard input and remain live-blocked.
- Dashboard remains display truth only and cannot create live permission.
known_omissions_by_design:
- Does not create long-run paper/shadow profitability evidence.
- Does not use credentials, live account data, or order-capable exchange endpoints.
conflict_resolution_rule: TRADER_1.md overrides this generated context pack.
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false
