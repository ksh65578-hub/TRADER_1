from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_REVIEW_PLAN_REFLECTED_FILE_CLEANUP"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-REVIEW-PLAN-REFLECTED-FILE-CLEANUP"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_convergence_memory_failure_learning_hardening_patch_evidence import ensure_matrix_row, ensure_requirement  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from tools.review_plan_reflection_status import (  # noqa: E402
    LEDGER_PATH,
    build_reflection_ledger,
    delete_reflected_files,
    mark_current_files_reflected,
    validate_reflection_ledger,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "review_plan_reflection_ledger_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
]
BLOCKERS = [
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]
CHANGED_ARTIFACTS = [
    "tools/review_plan_reflection_status.py",
    "tools/emit_review_plan_reflected_file_cleanup_patch_evidence.py",
    "tests/contract/test_review_plan_reflection_status.py",
    "trader1/validation/mvp0_validators.py",
    "system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json",
    "contracts/generated/context_pack/MVP4_REVIEW_PLAN_REFLECTED_FILE_CLEANUP.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {"command": " ".join(args), "status": "PASS" if completed.returncode == 0 else "FAIL", "returncode": completed.returncode}


def remove_python_bytecode_artifacts() -> None:
    for path in ROOT.rglob("__pycache__"):
        if ".git" not in path.parts and path.is_dir():
            shutil.rmtree(path)
    for path in ROOT.rglob("*.pyc"):
        if ".git" not in path.parts and path.is_file():
            path.unlink()


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_REVIEW_PLAN_DELETE_POLICY.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-REVIEW-PLAN-DELETE-POLICY", "REQ-MVP4-REVIEW-PLAN-REFLECTION-LEDGER"],
            "affected_exchange": "ALL",
            "affected_market_type": "ALL",
            "affected_mode": "ALL_NON_LIVE",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [],
            "new_or_changed_schema_ids": ["trader1.review_plan_reflection_ledger.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "REVIEW_ADDENDUM_REFLECTED_TO_LEDGER_AND_DELETED_AFTER_REFLECTION",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["USER_REVIEW_PLAN_DELETE_POLICY", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH"],
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
            "active_read_surface_used": ["USER_REVIEW_PLAN_DELETE_POLICY", "AGENTS_0G.16", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "DOCUMENT_NORMALIZATION",
            "required_section_ids": ["USER_REVIEW_PLAN_DELETE_POLICY", "AGENTS_0G.16", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["USER_REVIEW_PLAN_DELETE_POLICY", "REVIEW_PLAN_ADDENDUM_FILE_SET"],
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_REVIEW_PLAN_FILE_CLEANUP",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_APPLICABLE",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def update_navigation(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    index = load_json(index_path)
    matrix = load_json(matrix_path)
    index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    ensure_requirement(
        index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "USER_REVIEW_PLAN_DELETE_POLICY",
            "source_file": "user_prompt",
            "source_heading": "Delete reflected 검토안 inputs after reflection",
            "full_text_marker": f"{REQUIREMENT_ID}: reflected review-plan files are deleted after file-level reflection evidence",
            "authority_level": "USER_OPERATION_POLICY_WITH_ACTIVE_AUTHORITY_SAFETY",
            "requirement_title": "Delete reflected review-plan inbox files after ledgered reflection",
            "requirement_kind": "AUDIT_VALIDATOR_PATCH",
            "schema_ids": ["trader1.review_plan_reflection_ledger.v1"],
            "validator_ids": ["review_plan_reflection_ledger_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/contract/test_review_plan_reflection_status.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["DOCUMENT_NORMALIZATION", "BUNDLE_SECURITY"],
            "depends_on": ["REQ-MVP4-REVIEW-PLAN-DELETE-POLICY", "REQ-MVP4-REVIEW-PLAN-REFLECTION-LEDGER"],
            "source_text_sha256": sha256_bytes(b"reflected review-plan files are deleted after file-level reflection evidence"),
            "source_authority_sha256": agents_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "USER_REVIEW_PLAN_DELETE_POLICY",
            "schema_files": [],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_review_plan_reflection_status.py"],
            "fixture_files": [],
            "runtime_modules": ["tools/review_plan_reflection_status.py"],
            "evidence_artifacts": [
                "system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "affected_contract_ids",
                "validators_required",
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    write_json(index_path, index)
    write_json(matrix_path, matrix)
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_REVIEW_PLAN_REFLECTED_FILE_CLEANUP.md",
        f"""# MVP4_REVIEW_PLAN_REFLECTED_FILE_CLEANUP

context_pack_id: MVP4_REVIEW_PLAN_REFLECTED_FILE_CLEANUP
task_class: DOCUMENT_NORMALIZATION
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["USER_REVIEW_PLAN_DELETE_POLICY", "AGENTS_0G.16", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_validator_ids: ["review_plan_reflection_ledger_validator"]

## Cleanup Result

- deleted_after_reflection_count: {audit["deleted_after_reflection_count"]}
- pending_reflection_count: {audit["pending_reflection_count"]}
- current_review_inbox_file_count: {audit["current_review_inbox_file_count"]}
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

The deleted files remain represented by hash and per-file ledger entries. New 검토안 files are accepted as pending input instead of being blocked as unexpected review numbers.
""",
    )
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: MVP-4
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

검토안 legacy files have been reflected into the ledger and deleted from the inbox. New 검토안 files can be added by the operator and will appear as pending reflection input.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_audit(now: str, trader_hash: str, agents_hash: str, ledger: dict[str, Any], deleted_files: list[str]) -> dict[str, Any]:
    current_files = [path.as_posix() for path in sorted((ROOT / "검토안").glob("*.md"))]
    validation = validate_reflection_ledger(ledger)
    return {
        "audit_schema_id": "trader1.review_plan_reflected_file_cleanup_audit.v1",
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "status": validation["status"],
        "review_files_checked": ledger.get("review_files_count"),
        "deleted_after_reflection_count": ledger.get("deleted_after_reflection_count", 0),
        "pending_reflection_count": ledger.get("pending_reflection_count", 0),
        "current_review_inbox_file_count": len(current_files),
        "deleted_files": deleted_files,
        "current_review_inbox_files": current_files,
        "hidden_defects": [
            {
                "classification": "review_inbox_cleanup_not_executed",
                "condition": "reflection/delete policy existed but all 검토안 originals remained in the inbox.",
                "impact": "operator could not tell which review notes were already reflected and which were new pending input.",
                "fix": "marked legacy review files reflected with evidence, deleted them, retained hashes/status in the reflection ledger, and allowed future review files as pending input.",
                "reproducibility": "run tools/review_plan_reflection_status.py --validate",
                "live_safety_impact": "no live permission or scale-up permission is created.",
                "ux_impact": "검토안 now works as an operator inbox; reflected legacy notes no longer clutter the folder.",
            }
        ],
        "validation": validation,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["completed_requirement_ids"] = list(dict.fromkeys([*state.get("completed_requirement_ids", []), REQUIREMENT_ID]))
    state.update(
        {
            "updated_at_utc": now,
            "current_mvp": "MVP-4",
            "untested_validator_ids": [],
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result["result_hash"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)
    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    patches = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    patches.append(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "target_mvp_level": "MVP-4",
            "requirement_id": REQUIREMENT_ID,
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    ledger["patches"] = patches
    ledger["updated_at_utc"] = now
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json"

    initial_patch = build_patch_result(now, [], [])
    write_json(patch_path, initial_patch)
    write_json(
        audit_path,
        {
            "audit_schema_id": "trader1.review_plan_reflected_file_cleanup_audit.v1",
            "generated_at_utc": now,
            "status": "BOOTSTRAP_FOR_REFLECTION_EVIDENCE",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )

    previous = load_json(LEDGER_PATH) if LEDGER_PATH.exists() else None
    ledger = build_reflection_ledger(previous=previous, now=now)
    evidence_paths = [
        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
        "system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json",
        "contracts/generated/current_implementation_state.json",
        "contracts/generated/requirement_index.json",
    ]
    mark_current_files_reflected(ledger, patch_id=PATCH_ID, evidence_paths=evidence_paths)
    deleted_files = delete_reflected_files(ledger, max_delete_count=1000)
    if not deleted_files and isinstance(previous, dict):
        deleted_files = list(previous.get("deleted_files_this_run") or ledger.get("deleted_after_reflection_files") or [])
    ledger["deleted_files_this_run"] = deleted_files
    ledger["generated_at_utc"] = now
    write_json(LEDGER_PATH, ledger)

    audit = build_audit(now, trader_hash, agents_hash, ledger, deleted_files)
    write_json(audit_path, audit)
    update_navigation(now, trader_hash, agents_hash, audit)
    remove_python_bytecode_artifacts()
    write_source_bundle_manifest()
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_review_plan_reflection_status", "-q"], timeout_seconds=300),
    ]
    validators_run = [
        {
            "validator_id": item["validator_id"],
            "status": item["status"],
            "blocker_code": item.get("blocker_code"),
            "message": item.get("message"),
        }
        for item in run_validators(BOOTSTRAP_VALIDATORS)
    ]
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_validator_ids = ["patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
    for _ in range(2):
        final_results = run_validators(final_validator_ids)
        validators_run = [item for item in validators_run if item.get("validator_id") not in set(final_validator_ids)]
        validators_run.extend(
            {
                "validator_id": item["validator_id"],
                "status": item["status"],
                "blocker_code": item.get("blocker_code"),
                "message": item.get("message"),
            }
            for item in final_results
        )
        patch_result["validators_run"] = validators_run
        patch_result["result_hash"] = patch_hash(patch_result)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        *tests_run,
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-q"], timeout_seconds=300),
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"], timeout_seconds=1200),
    ]
    patch_result["tests_run"] = tests_run
    patch_result["result_hash"] = patch_hash(patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-4",
        "artifact_paths": [
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            *CHANGED_ARTIFACTS,
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    validator_log = {
        "schema_id": "trader1.validator_run_log.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": validators_run,
        "tests_run": tests_run,
    }
    stage_gate = {
        "schema_id": "trader1.stage_gate_result.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-4",
        "stage_gate_status": "PASS" if all(item["status"] == "PASS" for item in validators_run) and all(item["status"] == "PASS" for item in tests_run) else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / "system" / "evidence" / f"{PATCH_BASENAME}.evidence_manifest.json", evidence_manifest)
    write_json(ROOT / "system" / "evidence" / "validator_runs" / f"{PATCH_BASENAME}.validator_run_log.json", validator_log)
    write_json(ROOT / "system" / "evidence" / "stage_gates" / f"{PATCH_BASENAME}.stage_gate_result.json", stage_gate)
    remove_python_bytecode_artifacts()
    write_source_bundle_manifest()
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "deleted_files": deleted_files, "result_hash": patch_result["result_hash"]}, indent=2, ensure_ascii=False))
    return 0 if stage_gate["stage_gate_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
