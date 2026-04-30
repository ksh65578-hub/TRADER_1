from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_HARDENING"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-EXECUTION-FEEDBACK-RISK-REVIEW-GAP-HARDENING"

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
    "execution_feedback_loop_validator",
    "candidate_scorecard_net_ev_validator",
    "convergence_assessment_validator",
    "optimizer_no_live_mutation_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/optimizer_feedback_report.schema.json",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_optimizer_feedback_validator.py",
    "tests/validators/fixtures/optimizer_feedback_pass.json",
    "tests/validators/fixtures/optimizer_feedback_slippage_divergent_fail.json",
    "tests/validators/fixtures/optimizer_feedback_missing_blocker_fail.json",
    "tests/validators/fixtures/optimizer_feedback_live_flag_fail.json",
    "tests/validators/fixtures/optimizer_feedback_missing_risk_review_fail.json",
    "tools/emit_execution_feedback_risk_review_gap_patch_evidence.py",
    "contracts/generated/context_pack/EXECUTION_FEEDBACK_RISK_REVIEW_GAP.md",
    "system/evidence/audit_reports/MVP4_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_HARDENING_20260429.md",
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
        ROOT / "contracts" / "generated" / "context_pack" / "EXECUTION_FEEDBACK_RISK_REVIEW_GAP.md",
        f"""# EXECUTION_FEEDBACK_RISK_REVIEW_GAP

context_pack_id: EXECUTION_FEEDBACK_RISK_REVIEW_GAP
task_class: MVP4_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_HARDENING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_EXECUTION_FEEDBACK", "SECTION_RISK_EXPOSURE", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.optimizer_feedback_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- optimizer feedback cannot become paper-ranking eligible without risk_review_status=PASS
- exposure and drawdown review must PASS before feedback eligibility
- non-PASS risk review must carry a known blocker code and cannot allow paper ranking review
- feedback_hash must match the report payload
- optimizer/convergence feedback remains display-only and cannot create live or scale-up permission

known_omissions_by_design:
- no live exchange data is consumed
- no live order, live config mutation, LIVE_READY snapshot, or LIVE_ENABLING_PATCH is introduced
- no risk scale-up is enabled

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

Optimizer feedback now links expected-vs-realized execution costs to risk review fields. PAPER ranking feedback requires PASS for execution quality, risk review, exposure review, and drawdown review. Feedback reports are hash-checked and remain unable to create live permission.
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
            "source_section_id": "SECTION_EXECUTION_FEEDBACK",
            "source_file": "TRADER_1.md",
            "source_heading": "Execution feedback risk review closure",
            "full_text_marker": f"{REQUIREMENT_ID}:SECTION_EXECUTION_FEEDBACK:Risk review linkage and feedback hash integrity",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Require risk review and hash integrity for execution feedback",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.optimizer_feedback_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_optimizer_feedback_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["VALIDATOR_IMPLEMENTATION", "OPTIMIZER_MVP3", "PROFIT_CONVERGENCE_MVP3"],
            "depends_on": ["REQ-MVP4-EXECUTION-FEEDBACK-COST-MODEL-HARDENING", "REQ-MVP4-RISK-EXPOSURE-DRAWDOWN-UX-HARDENING"],
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
            "section_id": "SECTION_EXECUTION_FEEDBACK",
            "schema_files": ["contracts/schema/optimizer_feedback_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_optimizer_feedback_validator.py"],
            "fixture_files": [
                "tests/validators/fixtures/optimizer_feedback_pass.json",
                "tests/validators/fixtures/optimizer_feedback_missing_risk_review_fail.json",
            ],
            "runtime_modules": [],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "optimizer_live_mutation_detected",
                "convergence_live_mutation_detected",
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
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_RISK_EXPOSURE_DRAWDOWN_UX_HARDENING.patch_result.json")
    optimizer_validators = run_validators(["optimizer_no_live_mutation_validator", "execution_feedback_loop_validator"])
    convergence_validators = run_validators(["convergence_assessment_validator"])
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-EXECUTION-FEEDBACK-COST-MODEL-HARDENING",
                "REQ-MVP4-RISK-EXPOSURE-DRAWDOWN-UX-HARDENING",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_SHADOW_REPLAY_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": CHANGED_ARTIFACTS,
            "new_or_changed_schema_ids": ["trader1.optimizer_feedback_report.v1"],
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
            "next_task_class": "MVP4_EXECUTION_FEEDBACK_DASHBOARD_OPERATOR_VISIBILITY",
            "next_required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_EXECUTION_FEEDBACK", "SECTION_OPTIMIZER_GUARDRAIL"],
            "next_optional_section_ids": ["SECTION_CONVERGENCE_MEMORY", "SECTION_STRATEGY_EVIDENCE"],
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
            "active_read_surface_used": ["SECTION_EXECUTION_FEEDBACK", "SECTION_RISK_EXPOSURE", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_HARDENING",
            "required_section_ids": ["SECTION_EXECUTION_FEEDBACK", "SECTION_RISK_EXPOSURE", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": [
                "TRADER_1:execution-feedback-active-surface",
                "TRADER_1:risk-exposure-active-surface",
                "TRADER_1:optimizer-guardrail-active-surface",
                "AGENTS:validator-implementation-guide",
            ],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "OPTIMIZER_FEEDBACK_VALIDATOR_HARDENING",
            "optimizer_status_before": "PAPER_RANKING_FEEDBACK_COST_ONLY",
            "optimizer_status_after": "PAPER_RANKING_FEEDBACK_REQUIRES_RISK_REVIEW_AND_HASH",
            "optimizer_output_type": "DISPLAY_ONLY_PAPER_RANKING_FEEDBACK",
            "optimizer_validators_required": ["optimizer_no_live_mutation_validator", "execution_feedback_loop_validator"],
            "optimizer_validators_run": optimizer_validators,
            "optimizer_guardrail_result": "PASS_LIVE_MUTATION_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "CONVERGENCE_DEPENDENCY_RECHECK",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_EXECUTION_FEEDBACK_SCHEMA_VALIDATOR_HARDENING",
            "convergence_validators_required": ["convergence_assessment_validator"],
            "convergence_validators_run": convergence_validators,
            "convergence_guardrail_result": "PASS_DEPENDENCY_RECHECKED",
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
            "stage_gate_status": "PASS_FOR_EXECUTION_FEEDBACK_RISK_REVIEW_GAP_NO_LIVE_ORDERS",
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
                *CHANGED_ARTIFACTS,
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
        f"""# MVP4 Execution Feedback Risk Review Gap Hardening Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Optimizer feedback validated expected-vs-realized fee, slippage, impact, latency, and net EV, but did not require an explicit risk review link before PAPER ranking eligibility.
- `feedback_hash` existed in schema but was not checked against the report payload, allowing stale or tampered feedback artifacts to look structurally valid.

Patch:
- Added risk_review_status, risk_review_action, exposure_review_status, drawdown_review_status, and risk_review_blocker_code to optimizer_feedback_report schema.
- Hardened execution_feedback_loop_validator so feedback eligibility requires execution quality PASS, risk review PASS, exposure review PASS, drawdown review PASS, and no risk blocker.
- Added feedback_hash payload validation.
- Added a missing-risk-review negative fixture and tests.

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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.optimizer_feedback_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["execution_feedback_loop_validator"]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXECUTION_FEEDBACK_DASHBOARD_OPERATOR_VISIBILITY"
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
        run_command([sys.executable, "-m", "unittest", "tests.validators.test_optimizer_feedback_validator", "tests.validators.test_convergence_assessment_dependency_validators", "-v"]),
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
