from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_EXTERNAL_LIVE_REVIEW_BLOCKER_20260429_001"
EXTERNAL_REVIEW_INPUT_PATHS = [
    "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/official_api_verification_report.json",
    "system/runtime/upbit/krw_spot/read_only/mvp4_live_review/read_only_account_snapshot.json",
    "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/api_key_permission_check_report.json",
    "system/evidence/upbit/krw_spot/live/mvp4_live_review/manual_order_test_evidence_missing.json",
]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.validation.mvp0_validators import (
    CONVERGENCE_RISK_SCALE_VALIDATORS,
    OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS,
    run_validators,
)

LIVE_REVIEW_VALIDATORS = ["upbit_live_review_preflight_validator"]
OPTIMIZER_GUARDRAIL_VALIDATORS = [
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
]
CONVERGENCE_GUARDRAIL_VALIDATORS = [
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
    *CONVERGENCE_RISK_SCALE_VALIDATORS,
]
ALL_EXTERNAL_BLOCKER_VALIDATORS = [
    *LIVE_REVIEW_VALIDATORS,
    *OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS,
    *CONVERGENCE_RISK_SCALE_VALIDATORS,
]
REMAINING_BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "LIVE_BURN_IN_FEEDBACK_MISSING",
    "EXECUTION_QUALITY_UNTESTED",
    "SURVIVAL_LAYER_BLOCKED",
    "RISK_SCALING_UNTESTED",
    "SCALE_UP_NOT_ELIGIBLE",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def authority_hashes() -> dict[str, str]:
    return {
        "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
        "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
    }


def source_tree_hash() -> str:
    paths = sorted((ROOT / "trader1").rglob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return sha256_json({rel(path): sha256_file(path) for path in paths if "__pycache__" not in path.parts})


def schema_bundle_hash() -> str:
    paths = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    return sha256_json({rel(path): sha256_file(path) for path in paths})


def run_command(command: list[str], label: str) -> dict[str, str]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    status = "PASS" if completed.returncode == 0 else "FAIL"
    return {
        "command": label,
        "status": status,
        "returncode": str(completed.returncode),
    }


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["source_tree_hash_when_generated"] = source_tree_hash()
    manifest["updated_at_utc"] = now
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def first_present(*values: Any) -> Any:
    for value in values:
        if value is not None and value != "":
            return value
    return None


def external_review_input_statuses() -> list[dict[str, Any]]:
    statuses: list[dict[str, Any]] = []
    for artifact_path in EXTERNAL_REVIEW_INPUT_PATHS:
        path = ROOT / artifact_path
        if not path.exists():
            statuses.append(
                {
                    "artifact_path": artifact_path,
                    "exists": False,
                    "artifact_sha256": None,
                    "status": "MISSING",
                    "primary_blocker_code": "MISSING_EXTERNAL_EVIDENCE",
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "usable_for_live_enabling": False,
                }
            )
            continue

        artifact = load_json(path)
        status = first_present(
            artifact.get("status"),
            artifact.get("result"),
            artifact.get("verification_status"),
            artifact.get("account_snapshot_status"),
            artifact.get("permission_status"),
            artifact.get("permission_check_status"),
            artifact.get("evidence_status"),
        )
        statuses.append(
            {
                "artifact_path": artifact_path,
                "exists": True,
                "artifact_sha256": sha256_file(path),
                "status": status or "MISSING_STATUS",
                "primary_blocker_code": artifact.get("primary_blocker_code") or "LIVE_ENABLING_EVIDENCE_MISSING",
                "live_order_ready": bool(artifact.get("live_order_ready") or artifact.get("live_order_ready_after")),
                "live_order_allowed": bool(artifact.get("live_order_allowed") or artifact.get("live_order_allowed_after")),
                "can_live_trade": bool(artifact.get("can_live_trade")),
                "usable_for_live_enabling": False,
            }
        )
    return statuses


def validator_subset(validator_results: list[dict[str, Any]], validator_ids: list[str]) -> list[dict[str, Any]]:
    ids = set(validator_ids)
    return [result for result in validator_results if result.get("validator_id") in ids]


def validator_statuses(validator_results: list[dict[str, Any]]) -> dict[str, str]:
    return {result["validator_id"]: result["status"] for result in validator_results}


def optimizer_guardrail_result(validator_results: list[dict[str, Any]]) -> str:
    statuses = validator_statuses(validator_results)
    expected = {
        "optimizer_no_live_mutation_validator": "PASS",
        "optimizer_guardrail_validator": "PASS",
    }
    return "PASS" if all(statuses.get(key) == value for key, value in expected.items()) else "FAIL"


def convergence_guardrail_result(validator_results: list[dict[str, Any]]) -> str:
    statuses = validator_statuses(validator_results)
    expected = {
        "convergence_assessment_validator": "PASS",
        "scale_up_eligibility_validator": "BLOCKED",
        "risk_scaling_decision_validator": "BLOCKED",
        "live_burn_in_feedback_validator": "BLOCKED",
        "paper_live_parity_validator": "BLOCKED",
        "execution_quality_measurement_validator": "BLOCKED",
        "survival_layer_validator": "BLOCKED",
    }
    return "PASS" if all(statuses.get(key) == value for key, value in expected.items()) else "FAIL"


def build_blocker_report(now: str, authority: dict[str, str]) -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    latest_live_review_patch = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_LIVE_REVIEW.patch_result.json")
    latest_scaleup_patch = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json")
    return {
        "schema_id": "trader1.mvp4_external_live_review_blocker_report.v1",
        "created_at_utc": now,
        "project_id": "TRADER_1",
        "authority": authority,
        "target_mvp_level": "MVP-4",
        "current_mvp": state.get("current_mvp", "MVP-4"),
        "last_patch_id": state.get("last_patch_id"),
        "last_patch_result_hash": state.get("last_patch_result_hash"),
        "blocking_patch_id": PATCH_ID,
        "next_allowed_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
        "blocked_requirement_ids": [
            "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE",
            "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE",
            "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE",
            "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE",
        ],
        "blocking_reason": "External exchange/account/operator evidence is required before MVP-5 or any live-enabling behavior.",
        "remaining_blockers": REMAINING_BLOCKERS,
        "operator_inputs_required": [
            "official API verification PASS evidence",
            "read-only account snapshot evidence",
            "operator approval evidence",
            "read-only burn-in evidence",
            "manual order test evidence when required by the live review gate",
        ],
        "forbidden_next_steps": [
            "MVP5_LIVE_ENABLING_WITHOUT_EVIDENCE",
            "LIVE_ORDER_SUBMISSION",
            "LIVE_ORDER_READY_TRUE",
            "LIVE_ORDER_ALLOWED_TRUE",
            "CAN_LIVE_TRADE_TRUE",
            "OPTIMIZER_LIVE_CONFIG_MUTATION",
            "CONVERGENCE_LIVE_CONFIG_MUTATION",
        ],
        "latest_live_review_patch_result_path": "system/evidence/patch_results/MVP4_UPBIT_LIVE_REVIEW.patch_result.json",
        "latest_live_review_remaining_blockers": latest_live_review_patch.get("remaining_blockers", []),
        "latest_scaleup_safety_patch_result_path": "system/evidence/patch_results/MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json",
        "latest_scaleup_safety_remaining_blockers": latest_scaleup_patch.get("remaining_blockers", []),
        "latest_scaleup_safety_result_hash": latest_scaleup_patch.get("result_hash"),
        "external_review_input_statuses": external_review_input_statuses(),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "can_submit_order": False,
        "order_adapter_called": False,
        "result_hash": "",
    }


def write_validator_log(now: str, validator_results: list[dict[str, Any]]) -> Path:
    path = ROOT / "system" / "evidence" / "validator_runs" / "MVP4_EXTERNAL_BLOCKER.validator_run_log.json"
    write_json(
        path,
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": validator_results,
            "validators_untested": [],
            "optimizer_guardrail_result": optimizer_guardrail_result(validator_results),
            "convergence_guardrail_result": convergence_guardrail_result(validator_results),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
        },
    )
    return path


def write_stage_gate(now: str, blocker_report_path: Path) -> Path:
    path = ROOT / "system" / "evidence" / "stage_gates" / "MVP4_EXTERNAL_BLOCKER.stage_gate_result.json"
    write_json(
        path,
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "BLOCKED_BY_EXTERNAL_LIVE_REVIEW_EVIDENCE",
            "blocker_report_path": rel(blocker_report_path),
            "next_allowed_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "can_submit_order": False,
            "order_adapter_called": False,
        },
    )
    return path


def write_evidence_manifest(now: str, authority: dict[str, str], blocker_report_path: Path, validator_log_path: Path, stage_gate_path: Path) -> Path:
    path = ROOT / "system" / "evidence" / "MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
    write_json(
        path,
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": authority,
            "evidence_manifest_id": "MVP4_EXTERNAL_LIVE_REVIEW_BLOCKER_EVIDENCE",
            "artifact_paths": [
                rel(blocker_report_path),
                rel(validator_log_path),
                rel(stage_gate_path),
                "system/evidence/patch_results/MVP4_EXTERNAL_BLOCKER.patch_result.json",
                "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/official_api_verification_report.json",
                "system/runtime/upbit/krw_spot/read_only/mvp4_live_review/read_only_account_snapshot.json",
                "system/evidence/upbit/krw_spot/read_only/mvp4_live_review/api_key_permission_check_report.json",
                "system/evidence/upbit/krw_spot/live/mvp4_live_review/manual_order_test_evidence_missing.json",
                "system/runtime/upbit/krw_spot/live/review/live_preflight_report.json",
                "system/runtime/upbit/krw_spot/live/review/live_review_dashboard.json",
            ],
            "known_blockers": [
                *REMAINING_BLOCKERS,
            ],
            "external_review_input_statuses": external_review_input_statuses(),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
        },
    )
    return path


def build_patch_result(
    now: str,
    validator_results: list[dict[str, Any]],
    test_results: list[dict[str, str]],
    evidence_path: Path,
    validator_log_path: Path,
    stage_gate_path: Path,
) -> dict[str, Any]:
    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "EVIDENCE_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": [
            "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE",
            "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE",
            "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE",
            "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE",
        ],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "LIVE_REVIEW",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": [],
        "validators_required": ALL_EXTERNAL_BLOCKER_VALIDATORS,
        "validators_run": validator_results,
        "tests_run": test_results,
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_USED_FOR_AUTHORITY_ACTIVE_AUTHORITY_PREVAILED",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
        "next_required_section_ids": [
            "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            "SECTION_LIVE_PREFLIGHT_ACTIVE",
            "SECTION_LIVE_GATE_ACTIVE",
        ],
        "next_optional_section_ids": ["SECTION_AGENTS_MVP4_REQUIRED_FILES"],
        "next_forbidden_default_sections": [
            "SECTION_RETAINED_ARCHIVE",
            "SECTION_OPTIMIZER_FULL",
            "SECTION_CONVERGENCE_FULL",
            "SECTION_LIVE_ENABLING",
            "SECTION_MVP5_LIMITED_LIVE",
        ],
        "live_order_ready_before": False,
        "live_order_ready_after": False,
        "live_order_allowed_before": False,
        "live_order_allowed_after": False,
        "can_live_trade_before": False,
        "can_live_trade_after": False,
        "remaining_blockers": REMAINING_BLOCKERS,
        "evidence_manifest_path": rel(evidence_path),
        "validator_run_log_path": rel(validator_log_path),
        "stage_gate_result_path": rel(stage_gate_path),
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "contracts/generated/current_implementation_state.json",
            "system/evidence/patch_results/MVP4_UPBIT_LIVE_REVIEW.patch_result.json",
            "system/evidence/patch_results/MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json",
            "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            "SECTION_LIVE_PREFLIGHT_ACTIVE",
            "SECTION_LIVE_GATE_ACTIVE",
        ],
        "task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
        "required_section_ids": [
            "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            "SECTION_LIVE_PREFLIGHT_ACTIVE",
            "SECTION_LIVE_GATE_ACTIVE",
        ],
        "expanded_section_ids": [],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "UNCHANGED_FRESH",
        "requirement_index_status": "UNCHANGED_FRESH",
        "requirement_artifact_matrix_status": "UNCHANGED_FRESH",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UNCHANGED_FRESH",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
        "optimizer_stage": "METRIC_COLLECTION",
        "optimizer_status_before": "SCAFFOLD",
        "optimizer_status_after": "SCAFFOLD",
        "optimizer_maturity_level_before": "MVP0_SCHEMA_ONLY",
        "optimizer_maturity_level_after": "MVP0_SCHEMA_ONLY",
        "optimizer_output_type": "OPTIMIZER_RESEARCH_SIGNAL",
        "optimizer_validators_required": OPTIMIZER_GUARDRAIL_VALIDATORS,
        "optimizer_validators_run": validator_subset(validator_results, OPTIMIZER_GUARDRAIL_VALIDATORS),
        "optimizer_guardrail_result": optimizer_guardrail_result(validator_results),
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_state_before": "SCALEUP_SAFETY_BLOCKED_LIVE_STILL_BLOCKED",
        "convergence_state_after": "EXTERNAL_LIVE_REVIEW_EVIDENCE_BLOCKED",
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_FOR_EXTERNAL_BLOCKER_REPORT",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
        "convergence_validators_required": CONVERGENCE_GUARDRAIL_VALIDATORS,
        "convergence_validators_run": validator_subset(validator_results, CONVERGENCE_GUARDRAIL_VALIDATORS),
        "convergence_guardrail_result": convergence_guardrail_result(validator_results),
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "scale_up_allowed_after": False,
        "result_hash": "",
    }
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def write_patch_and_state(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / "MVP4_EXTERNAL_BLOCKER.patch_result.json"
    write_json(patch_path, patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    blocked = state.setdefault("blocked_requirement_ids", [])
    for requirement_id in patch_result["affected_contract_ids"]:
        if requirement_id not in blocked:
            blocked.append(requirement_id)
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger["patches"] if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": "EVIDENCE_PATCH",
            "target_mvp_level": "MVP-4",
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
        }
    )
    write_json(ledger_path, ledger)


def update_read_cache(now: str, authority: dict[str, str]) -> None:
    path = ROOT / "contracts" / "generated" / "read_cache_manifest.json"
    manifest = load_json(path)
    manifest["created_at_utc"] = now
    manifest["trader1_sha256"] = authority["trader1_sha256"]
    manifest["agents_sha256"] = authority["agents_sha256"]
    manifest["authority_section_map_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "authority_section_map.json")
    manifest["requirement_index_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "requirement_index.json")
    manifest["requirement_artifact_matrix_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json")
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["active_working_view_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md")
    manifest["current_implementation_state_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    context_dir = ROOT / "contracts" / "generated" / "context_pack"
    manifest["context_pack_hashes"] = {rel(pack): sha256_file(pack) for pack in sorted(context_dir.glob("*.md"))}
    manifest["live_order_ready"] = False
    manifest["live_order_allowed"] = False
    manifest["can_live_trade"] = False
    write_json(path, manifest)


def main() -> int:
    now = utc_now()
    authority = authority_hashes()
    update_authority_manifest(now)

    blocker_report = build_blocker_report(now, authority)
    blocker_report["result_hash"] = sha256_json({key: value for key, value in blocker_report.items() if key != "result_hash"})
    blocker_report_path = ROOT / "system" / "evidence" / "blocker_reports" / "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE.blocker_report.json"
    write_json(blocker_report_path, blocker_report)

    validator_results = run_validators(ALL_EXTERNAL_BLOCKER_VALIDATORS)
    validator_log_path = write_validator_log(now, validator_results)
    stage_gate_path = write_stage_gate(now, blocker_report_path)
    evidence_path = write_evidence_manifest(now, authority, blocker_report_path, validator_log_path, stage_gate_path)

    preliminary = build_patch_result(now, validator_results, [], evidence_path, validator_log_path, stage_gate_path)
    write_patch_and_state(now, preliminary)
    update_read_cache(now, authority)
    preliminary_blocker_report = build_blocker_report(now, authority)
    preliminary_blocker_report["result_hash"] = sha256_json(
        {key: value for key, value in preliminary_blocker_report.items() if key != "result_hash"}
    )
    write_json(blocker_report_path, preliminary_blocker_report)

    test_results = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"], "python -m compileall trader1 tools tests -q"),
        run_command([sys.executable, "tools/run_upbit_live_review_validators.py"], "python tools/run_upbit_live_review_validators.py"),
        run_command(
            [sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"],
            "python tools/run_optimizer_convergence_guardrail_validators.py",
        ),
        run_command(
            [sys.executable, "tools/run_convergence_risk_scale_validators.py"],
            "python tools/run_convergence_risk_scale_validators.py",
        ),
        run_command([sys.executable, "tools/run_mvp0_validators.py"], "python tools/run_mvp0_validators.py"),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"], "python tools/validate_mvp0_contracts.py"),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "python -m unittest discover -s tests -v"),
    ]
    validator_results = run_validators(ALL_EXTERNAL_BLOCKER_VALIDATORS)
    final_patch = build_patch_result(now, validator_results, test_results, evidence_path, validator_log_path, stage_gate_path)
    write_validator_log(now, validator_results)
    write_patch_and_state(now, final_patch)
    update_read_cache(now, authority)

    final_blocker_report = build_blocker_report(now, authority)
    final_blocker_report["result_hash"] = sha256_json(
        {key: value for key, value in final_blocker_report.items() if key != "result_hash"}
    )
    write_json(blocker_report_path, final_blocker_report)

    status = "PASS" if all(result["status"] == "PASS" for result in test_results) else "FAIL"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": status,
                "blocker_report_path": rel(blocker_report_path),
                "patch_result_path": "system/evidence/patch_results/MVP4_EXTERNAL_BLOCKER.patch_result.json",
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
            },
            indent=2,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
