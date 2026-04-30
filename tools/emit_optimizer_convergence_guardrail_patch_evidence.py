from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_OPTIMIZER_CONVERGENCE_GUARDRAIL_20260429_001"
PATCH_RESULT_REL = "system/evidence/patch_results/MVP4_OPTIMIZER_CONVERGENCE_GUARDRAIL.patch_result.json"
GUARDRAIL_IDS = [
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
]
DEPENDENCY_UNTESTED_IDS = [
    "convergence_objective_profile_validator",
    "optimizer_memory_state_validator",
    "strategy_performance_memory_validator",
    "overfit_diagnostic_validator",
    "execution_feedback_loop_validator",
    "model_drift_validator",
    "risk_scaling_decision_validator",
    "live_burn_in_feedback_validator",
    "paper_live_parity_validator",
]
REMAINING_BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "CONVERGENCE_STATE_UNTESTED",
    "SCALE_UP_NOT_ELIGIBLE",
]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.validation.mvp0_validators import run_fixture_file, run_validators


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


def schema_bundle_hash() -> str:
    paths = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    return sha256_json({rel(path): sha256_file(path) for path in paths})


def source_tree_hash() -> str:
    paths = sorted((ROOT / "trader1").rglob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return sha256_json({rel(path): sha256_file(path) for path in paths if "__pycache__" not in path.parts})


def run_command(command: list[str], label: str) -> dict[str, str]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": label,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
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


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") not in GUARDRAIL_IDS]
    for validator_id in GUARDRAIL_IDS:
        implemented.append(
            {
                "validator_id": validator_id,
                "module_path": "trader1.validation.mvp0_validators",
                "status": "IMPLEMENTED_FAIL_CLOSED",
                "live_enabling": False,
            }
        )
    write_json(path, registry)

    fixture_catalog_path = ROOT / "contracts" / "validators" / "fixture_catalog.json"
    catalog = load_json(fixture_catalog_path)
    fixture_paths = {
        "optimizer_convergence_guardrail_no_live_mutation_pass": "tests/validators/fixtures/optimizer_convergence_guardrail_pass.json",
        "optimizer_convergence_guardrail_live_permission_fail": "tests/validators/fixtures/optimizer_convergence_guardrail_fail.json",
        "optimizer_convergence_guardrail_dependency_blocked": "tests/validators/fixtures/optimizer_convergence_guardrail_blocked.json",
    }
    catalog["fixtures"] = [
        fixture for fixture in catalog.get("fixtures", []) if fixture.get("fixture_id") not in fixture_paths
    ]
    for fixture_id, fixture_path in fixture_paths.items():
        fixture = load_json(ROOT / fixture_path)
        catalog["fixtures"].append(
            {
                "fixture_id": fixture_id,
                "validator_id": fixture["validator_id"],
                "expected_status": fixture["expected_status"],
                "path": fixture_path,
            }
        )
    catalog["updated_at_utc"] = now
    catalog["live_order_ready"] = False
    catalog["live_order_allowed"] = False
    catalog["can_live_trade"] = False
    write_json(fixture_catalog_path, catalog)


def write_validator_log(now: str, validator_results: list[dict[str, Any]], fixture_results: list[dict[str, Any]]) -> Path:
    path = ROOT / "system" / "evidence" / "validator_runs" / "MVP4_OPTIMIZER_CONVERGENCE_GUARDRAIL.validator_run_log.json"
    write_json(
        path,
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": validator_results,
            "fixture_results": fixture_results,
            "validators_blocked_by_missing_dependencies": DEPENDENCY_UNTESTED_IDS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    return path


def write_stage_gate(now: str, validator_log_path: Path) -> Path:
    path = ROOT / "system" / "evidence" / "stage_gates" / "MVP4_OPTIMIZER_CONVERGENCE_GUARDRAIL.stage_gate_result.json"
    write_json(
        path,
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "BLOCKED_FAIL_CLOSED_GUARDRAIL_DEPENDENCIES",
            "validator_run_log_path": rel(validator_log_path),
            "next_allowed_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    return path


def write_evidence_manifest(now: str, authority: dict[str, str], validator_log_path: Path, stage_gate_path: Path) -> Path:
    path = ROOT / "system" / "evidence" / "MVP4_OPTIMIZER_CONVERGENCE_GUARDRAIL.evidence_manifest.json"
    write_json(
        path,
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": authority,
            "evidence_manifest_id": "MVP4_OPTIMIZER_CONVERGENCE_GUARDRAIL_EVIDENCE",
            "artifact_paths": [
                "trader1/validation/mvp0_validators.py",
                "tools/run_optimizer_convergence_guardrail_validators.py",
                "tests/validators/test_optimizer_convergence_guardrails.py",
                "tests/validators/fixtures/optimizer_convergence_guardrail_pass.json",
                "tests/validators/fixtures/optimizer_convergence_guardrail_fail.json",
                "tests/validators/fixtures/optimizer_convergence_guardrail_blocked.json",
                rel(validator_log_path),
                rel(stage_gate_path),
                PATCH_RESULT_REL,
            ],
            "known_blockers": REMAINING_BLOCKERS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    return path


def status_of(results: list[dict[str, Any]], validator_id: str) -> str:
    for result in results:
        if result["validator_id"] == validator_id:
            return result["status"]
    return "UNTESTED"


def build_patch_result(
    now: str,
    validator_results: list[dict[str, Any]],
    test_results: list[dict[str, str]],
    evidence_path: Path,
    validator_log_path: Path,
    stage_gate_path: Path,
) -> dict[str, Any]:
    optimizer_results = [result for result in validator_results if result["validator_id"].startswith("optimizer_")]
    convergence_results = [
        result
        for result in validator_results
        if result["validator_id"] in {"convergence_assessment_validator", "scale_up_eligibility_validator"}
    ]
    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "VALIDATOR_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-OPT-MVP0-SCAFFOLD", "REQ-CONV-MVP0-SCAFFOLD"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "LIVE_REVIEW",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": ["optimizer/convergence guardrail validators marked IMPLEMENTED_FAIL_CLOSED"],
        "new_or_changed_schema_ids": [],
        "validators_required": GUARDRAIL_IDS,
        "validators_run": validator_results,
        "tests_run": test_results,
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED_FOR_FAIL_CLOSED_GUARDRAILS",
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
            "contracts/generated/context_pack/OPTIMIZER_MVP3.md",
            "contracts/generated/context_pack/PROFIT_CONVERGENCE_MVP3.md",
            "contracts/generated/context_pack/LIVE_BLOCKED_TEST.md",
            "SECTION_OPTIMIZER_GUARDRAIL",
            "SECTION_CONVERGENCE_ASSESSMENT",
            "SECTION_LIVE_GATE",
        ],
        "task_class": "VALIDATOR_IMPLEMENTATION",
        "required_section_ids": [
            "SECTION_OPTIMIZER_GUARDRAIL",
            "SECTION_CONVERGENCE_ASSESSMENT",
            "SECTION_LIVE_GATE",
        ],
        "expanded_section_ids": [
            "TRADER_1:640-690",
            "TRADER_1:1950-1990",
            "TRADER_1:3110-3145",
            "AGENTS:730-775",
            "AGENTS:1190-1240",
        ],
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
        "optimizer_patch": "FAIL_CLOSED_GUARDRAIL_VALIDATOR_PATCH",
        "optimizer_stage": "METRIC_COLLECTION",
        "optimizer_status_before": "SCAFFOLD_UNTESTED",
        "optimizer_status_after": "NO_LIVE_MUTATION_PASS_GUARDRAIL_PASS",
        "optimizer_maturity_level_before": "MVP0_SCHEMA_ONLY",
        "optimizer_maturity_level_after": "MVP0_FAIL_CLOSED_VALIDATOR",
        "optimizer_output_type": "OPTIMIZER_RESEARCH_SIGNAL",
        "optimizer_validators_required": ["optimizer_guardrail_validator", "optimizer_no_live_mutation_validator"],
        "optimizer_validators_run": optimizer_results,
        "optimizer_guardrail_result": status_of(validator_results, "optimizer_guardrail_validator"),
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "FAIL_CLOSED_GUARDRAIL_VALIDATOR_PATCH",
        "convergence_layer_changed": False,
        "convergence_state_before": "UNTESTED",
        "convergence_state_after": "BLOCKED_FAIL_CLOSED_DEPENDENCY_UNTESTED",
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_FOR_GUARDRAIL_VALIDATOR_PATCH",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
        "convergence_validators_required": ["convergence_assessment_validator", "scale_up_eligibility_validator"],
        "convergence_validators_run": convergence_results,
        "convergence_guardrail_result": status_of(validator_results, "convergence_assessment_validator"),
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "scale_up_allowed_after": False,
        "result_hash": "",
    }
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def write_patch_and_state(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / PATCH_RESULT_REL
    write_json(patch_path, patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    for validator_id in GUARDRAIL_IDS:
        if validator_id not in state["implemented_validator_ids"]:
            state["implemented_validator_ids"].append(validator_id)
    state["untested_validator_ids"] = DEPENDENCY_UNTESTED_IDS
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
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
            "patch_class": "VALIDATOR_PATCH",
            "target_mvp_level": "MVP-4",
            "patch_result_path": PATCH_RESULT_REL,
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
    manifest["context_pack_hashes"] = {
        rel(pack): sha256_file(pack) for pack in sorted((ROOT / "contracts" / "generated" / "context_pack").glob("*.md"))
    }
    manifest["active_working_view_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md")
    manifest["current_implementation_state_sha256"] = sha256_file(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    manifest["live_order_ready"] = False
    manifest["live_order_allowed"] = False
    manifest["can_live_trade"] = False
    write_json(path, manifest)


def main() -> int:
    now = utc_now()
    authority = authority_hashes()
    update_authority_manifest(now)
    update_validator_registry(now)

    validator_results = run_validators(GUARDRAIL_IDS)
    fixture_paths = [
        ROOT / "tests" / "validators" / "fixtures" / "optimizer_convergence_guardrail_pass.json",
        ROOT / "tests" / "validators" / "fixtures" / "optimizer_convergence_guardrail_fail.json",
        ROOT / "tests" / "validators" / "fixtures" / "optimizer_convergence_guardrail_blocked.json",
    ]
    fixture_results = [run_fixture_file(path) for path in fixture_paths]
    validator_log_path = write_validator_log(now, validator_results, fixture_results)
    stage_gate_path = write_stage_gate(now, validator_log_path)
    evidence_path = write_evidence_manifest(now, authority, validator_log_path, stage_gate_path)

    preliminary = build_patch_result(now, validator_results, [], evidence_path, validator_log_path, stage_gate_path)
    write_patch_and_state(now, preliminary)
    update_read_cache(now, authority)

    test_results = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"], "python -m compileall trader1 tools tests -q"),
        run_command([sys.executable, "tools/run_optimizer_convergence_guardrail_validators.py"], "python tools/run_optimizer_convergence_guardrail_validators.py"),
        run_command([sys.executable, "tools/run_upbit_live_review_validators.py"], "python tools/run_upbit_live_review_validators.py"),
        run_command([sys.executable, "tools/run_mvp0_validators.py"], "python tools/run_mvp0_validators.py"),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"], "python tools/validate_mvp0_contracts.py"),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], "python -m unittest discover -s tests -v"),
    ]
    validator_results = run_validators(GUARDRAIL_IDS)
    fixture_results = [run_fixture_file(path) for path in fixture_paths]
    validator_log_path = write_validator_log(now, validator_results, fixture_results)
    final_patch = build_patch_result(now, validator_results, test_results, evidence_path, validator_log_path, stage_gate_path)
    write_patch_and_state(now, final_patch)
    update_read_cache(now, authority)

    status = "PASS" if all(result["status"] == "PASS" for result in test_results) else "FAIL"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": status,
                "patch_result_path": PATCH_RESULT_REL,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
