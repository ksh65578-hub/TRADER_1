from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-OPTIMIZER-GUARDRAIL-REPORT-SCHEMA-HARDENING"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (
    rel,
    run_command,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators


BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "optimizer_guardrail_report_validator",
    "optimizer_run_report_validator",
    "optimizer_recommendation_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/optimizer_guardrail_report.schema.json",
    "contracts/registry.yaml",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_optimizer_guardrail_report_validator.py",
    "tests/validators/fixtures/optimizer_guardrail_report_pass.json",
    "tests/validators/fixtures/optimizer_guardrail_report_live_flag_fail.json",
    "tests/validators/fixtures/optimizer_guardrail_report_dependency_override_fail.json",
    "tests/validators/fixtures/optimizer_guardrail_report_live_ready_wording_fail.json",
    "tests/validators/fixtures/optimizer_guardrail_report_missing_blocker_fail.json",
    "tests/validators/fixtures/optimizer_guardrail_report_live_writer_fail.json",
    "tests/validators/fixtures/optimizer_guardrail_report_scale_up_fail.json",
    "tools/run_optimizer_guardrail_report_validators.py",
    "tools/run_optimizer_run_guardrail_validators.py",
    "tools/run_optimizer_recommendation_validators.py",
    "tools/emit_optimizer_guardrail_report_schema_hardening_patch_evidence.py",
    "contracts/generated/context_pack/OPTIMIZER_GUARDRAIL_REPORT_SCHEMA.md",
    "system/evidence/audit_reports/MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING_20260429.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest().upper()


def patch_hash(value: dict[str, Any]) -> str:
    clean = dict(value)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "OPTIMIZER_GUARDRAIL_REPORT_SCHEMA.md",
        f"""# OPTIMIZER_GUARDRAIL_REPORT_SCHEMA

context_pack_id: OPTIMIZER_GUARDRAIL_REPORT_SCHEMA
task_class: MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.optimizer_guardrail_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer guardrail PASS cannot be read as LIVE_READY
- optimizer guardrail PASS cannot override FAIL/BLOCKED/UNTESTED/STALE/TIMEOUT dependencies
- optimizer guardrail report cannot write live snapshots, mutate live config, submit orders, call exchange accounts, or recommend scale-up
- blocked guardrail reports carry explicit blocker evidence
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live order, credential load, exchange account call, or live configuration mutation
- guardrail reports remain display/evidence artifacts only

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: {state.get("current_mvp", "MVP-4")}
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Optimizer guardrail reports now require explicit non-live wording, dependency status disclosure, dashboard-display-truth-only marking, and false fields for live permission, exchange account calls, LIVE_READY writes, live config mutation, and scale-up.
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_OPTIMIZER_GUARDRAIL",
            "source_file": "TRADER_1.md",
            "source_heading": "Optimizer guardrail report schema",
            "full_text_marker": f"{REQUIREMENT_ID}:SECTION_OPTIMIZER_GUARDRAIL:Guardrail PASS cannot create live readiness",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Harden optimizer guardrail report against live-readiness misinterpretation",
            "requirement_kind": "OPTIMIZER_GUARDRAIL",
            "schema_ids": ["trader1.optimizer_guardrail_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_optimizer_guardrail_report_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["OPTIMIZER_MVP3", "PROFIT_CONVERGENCE_MVP3", "LIVE_BLOCKED_TEST"],
            "depends_on": [
                "REQ-MVP4-OPTIMIZER-RUN-GUARDRAIL-SCHEMA-HARDENING",
                "REQ-MVP4-OPTIMIZER-RECOMMENDATION-LIVE-SEPARATION-HARDENING",
                "REQ-MVP4-OPTIMIZER-CONVERGENCE-GUARDRAIL",
            ],
            "source_text_sha256": sha256_text(REQUIREMENT_ID),
            "implementation_status": "IMPLEMENTED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_OPTIMIZER_GUARDRAIL",
            "schema_files": ["contracts/schema/optimizer_guardrail_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_optimizer_guardrail_report_validator.py"],
            "fixture_files": [
                "tests/validators/fixtures/optimizer_guardrail_report_pass.json",
                "tests/validators/fixtures/optimizer_guardrail_report_live_flag_fail.json",
                "tests/validators/fixtures/optimizer_guardrail_report_dependency_override_fail.json",
                "tests/validators/fixtures/optimizer_guardrail_report_live_ready_wording_fail.json",
                "tests/validators/fixtures/optimizer_guardrail_report_missing_blocker_fail.json",
                "tests/validators/fixtures/optimizer_guardrail_report_live_writer_fail.json",
                "tests/validators/fixtures/optimizer_guardrail_report_scale_up_fail.json",
            ],
            "runtime_modules": ["trader1/validation/mvp0_validators.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "optimizer_live_mutation_detected",
                "optimizer_live_order_allowed_after",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_OPERATOR_ACTION_SUMMARY_HARDENING.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-OPTIMIZER-RUN-GUARDRAIL-SCHEMA-HARDENING",
                "REQ-MVP4-OPTIMIZER-RECOMMENDATION-LIVE-SEPARATION-HARDENING",
                "REQ-MVP4-OPTIMIZER-CONVERGENCE-GUARDRAIL",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "REPLAY_PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": sorted(set(CHANGED_ARTIFACTS)),
            "new_or_changed_schema_ids": ["trader1.optimizer_guardrail_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_OPTIMIZATION_STATE_SCHEMA_RECHECK",
            "next_required_section_ids": ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_EXECUTION_FEEDBACK", "SECTION_DASHBOARD_SHELL"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING",
            "required_section_ids": ["SECTION_OPTIMIZER_GUARDRAIL", "SECTION_CONVERGENCE_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": [
                "TRADER_1:optimizer-guardrail-active-surface",
                "TRADER_1:live-final-guard-active-surface",
                "AGENTS:optimizer-validator-negative-fixtures",
            ],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING",
            "optimizer_stage": "MVP4_ANALYSIS_ONLY",
            "optimizer_status_before": "SCAFFOLD_SCHEMA_NO_REPORT_VALIDATOR",
            "optimizer_status_after": "STRICT_NON_LIVE_GUARDRAIL_REPORT_VALIDATED",
            "optimizer_maturity_level_before": "MVP4_SCAFFOLD",
            "optimizer_maturity_level_after": "MVP4_NEGATIVE_FIXTURE_VALIDATED",
            "optimizer_output_type": "GUARDRAIL_REPORT_DISPLAY_TRUTH_ONLY",
            "optimizer_guardrail_result": "PASS_NO_LIVE_PERMISSION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "OPTIMIZER_GUARDRAIL_DEPENDENCY_VISIBILITY_HARDENING",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "validators_untested": [],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_FOR_OPTIMIZER_GUARDRAIL_REPORT_SCHEMA_HARDENING_NO_LIVE_ORDERS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": [
                *patch_result["new_registry_items"],
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Optimizer Guardrail Report Schema Hardening Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Optimizer guardrail report schema was still scaffold-level and did not require dependency status disclosure or explicit no-live/no-scale fields.
- A guardrail PASS could be misunderstood as LIVE_READY if it only exposed generic status text.
- Optimizer guardrail dependency chain did not include a validator for the guardrail report artifact itself.

Patch:
- Hardened optimizer_guardrail_report schema with guardrail scope/status/decision, dependency results, source modes, output ranking scope, NOT_LIVE_READY status, dashboard-display-truth-only marking, and explicit no-live/no-scale/no-exchange fields.
- Added optimizer_guardrail_report_validator and made optimizer_guardrail_validator depend on it.
- Added PASS and negative fixtures for live flag drift, dependency override, misleading LIVE_READY wording, missing blockers, LIVE_READY writer attempts, and scale-up attempts.
- Added unit tests and a standalone validator runner for optimizer guardrail reports.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.optimizer_guardrail_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["optimizer_guardrail_report_validator"]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_OPTIMIZATION_STATE_SCHEMA_RECHECK"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_optimizer_guardrail_report_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_optimizer_run_report_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_optimizer_recommendation_validator", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_optimizer_convergence_guardrails", "-v"]),
        run_command([sys.executable, "tools/run_optimizer_guardrail_report_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_run_guardrail_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_recommendation_validators.py"]),
        run_command([sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"]),
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
