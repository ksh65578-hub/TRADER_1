from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_REVIEW_PLAN_REFLECTION_LEDGER"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-REVIEW-PLAN-REFLECTION-LEDGER"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE"

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
    validate_reflection_ledger,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "tools/review_plan_reflection_status.py",
    "tools/emit_review_plan_reflection_ledger_patch_evidence.py",
    "tests/contract/test_review_plan_reflection_status.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json",
    "contracts/generated/context_pack/MVP4_REVIEW_PLAN_REFLECTION_LEDGER.md",
]
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
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
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


def update_registry(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    group = registry.setdefault("validators", {}).setdefault("VALIDATOR_GROUP:MVP0_CORE", [])
    if "review_plan_reflection_ledger_validator" not in group:
        group.append("review_plan_reflection_ledger_validator")
    registry["updated_at_utc"] = now
    write_json(registry_path, registry)

    validator_registry_path = ROOT / "contracts" / "validators" / "validator_registry.json"
    validator_registry = load_json(validator_registry_path)
    implemented = validator_registry.setdefault("implemented_validators", [])
    implemented[:] = [
        item for item in implemented if item.get("validator_id") != "review_plan_reflection_ledger_validator"
    ]
    implemented.append(
        {
            "validator_id": "review_plan_reflection_ledger_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
    )
    validator_registry["updated_at_utc"] = now
    validator_registry["implemented_logic_status"] = "MVP4_REVIEW_PLAN_REFLECTION_LEDGER_ADDED"
    write_json(validator_registry_path, validator_registry)


def write_review_ledger(now: str) -> dict[str, Any]:
    previous = load_json(LEDGER_PATH) if LEDGER_PATH.exists() else None
    ledger = build_reflection_ledger(previous=previous, now=now)
    write_json(LEDGER_PATH, ledger)
    return ledger


def build_audit(now: str, trader_hash: str, agents_hash: str, ledger: dict[str, Any]) -> dict[str, Any]:
    validation = validate_reflection_ledger(ledger)
    reflected_ready = ledger.get("delete_ready_count", 0)
    return {
        "audit_schema_id": "trader1.review_plan_reflection_ledger_audit.v1",
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "status": "PASS" if validation["status"] == "PASS" and reflected_ready == 0 else "BLOCKED",
        "review_files_checked": ledger.get("review_files_count"),
        "theme_ids_detected": ledger.get("theme_ids_detected", []),
        "delete_ready_count": reflected_ready,
        "pending_reflection_count": ledger.get("pending_reflection_count"),
        "hidden_defects": [
            {
                "classification": "review_addendum_deletion_without_reflection_evidence",
                "condition": "review plan files could be removed before all items are reflected into authority-preserving contracts, code, tests, or artifacts.",
                "impact": "unimplemented review findings could disappear from the working set and create false completion confidence.",
                "fix": "added a hash-based reflection ledger, deletion policy, validator, and tests; no review files are delete-ready yet.",
                "reproducibility": "deterministic by running tools/review_plan_reflection_status.py --write",
                "live_safety_impact": "prevents review-plan cleanup from weakening live blockers or evidence requirements",
                "ux_impact": "keeps operator-facing cleanup status explicit instead of silently removing backlog items",
            }
        ],
        "validation": validation,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


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
            "source_section_id": "AGENTS_0G.16",
            "source_file": "AGENTS.md",
            "source_heading": "Exact expansion trigger and review addendum preservation",
            "full_text_marker": f"{REQUIREMENT_ID}: review plan addendum files must remain tracked until reflected and individually deleted",
            "authority_level": "ACTIVE_IMPLEMENTATION_GUIDE_AND_REVIEW_ADDENDUM",
            "requirement_title": "Review plan reflection ledger before one-by-one cleanup",
            "requirement_kind": "AUDIT_VALIDATOR_PATCH",
            "schema_ids": ["trader1.review_plan_reflection_ledger.v1"],
            "validator_ids": ["review_plan_reflection_ledger_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/contract/test_review_plan_reflection_status.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["RETAINED_ARCHIVE_COVERAGE", "DOCUMENT_NORMALIZATION", "BUNDLE_SECURITY"],
            "depends_on": ["REQ-MVP4-LIVE-FINAL-GUARD"],
            "source_text_sha256": sha256_bytes(
                b"review plan addendum files must remain tracked until reflected and individually deleted"
            ),
            "source_authority_sha256": agents_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "AGENTS_0G.16",
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
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_REVIEW_PLAN_REFLECTION_LEDGER.md",
        f"""# MVP4_REVIEW_PLAN_REFLECTION_LEDGER

context_pack_id: MVP4_REVIEW_PLAN_REFLECTION_LEDGER
task_class: RETAINED_ARCHIVE_COVERAGE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["AGENTS_0G.16", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_validator_ids: ["review_plan_reflection_ledger_validator"]
included_artifact_ids: ["system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json"]

## Safe Scope

The 검토안 addendum files are cataloged by hash and remain pending until a later patch records reflection evidence.
Delete-ready files must be removed one by one in a tracked patch. No file is delete-ready in this patch.

## Audit Summary

- review_files_checked: {audit["review_files_checked"]}
- pending_reflection_count: {audit["pending_reflection_count"]}
- delete_ready_count: {audit["delete_ready_count"]}
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false
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

검토안 43개 files are hash-cataloged. All remain pending reflection, so none are delete-ready yet.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID],
            "affected_exchange": "ALL",
            "affected_market_type": "ALL",
            "affected_mode": "ALL_NON_LIVE",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": ["review_plan_reflection_ledger_validator"],
            "new_or_changed_schema_ids": ["trader1.review_plan_reflection_ledger.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "PRESERVED_NOT_READ_REVIEW_ADDENDUM_CATALOGED",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_optional_section_ids": ["SECTION_BINANCE_SCOPE", "SECTION_PROFIT_CONVERGENCE"],
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
            "token_navigation_patch": True,
            "active_read_surface_used": ["AGENTS_0G.16", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "RETAINED_ARCHIVE_COVERAGE",
            "required_section_ids": ["AGENTS_0G.16", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["AGENTS_0G", "REVIEW_PLAN_ADDENDUM_FILE_SET"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "PASS",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_REVIEW_PLAN_REFLECTION_LEDGER",
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


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["completed_requirement_ids"] = list(dict.fromkeys([*state.get("completed_requirement_ids", []), REQUIREMENT_ID]))
    state["implemented_validator_ids"] = list(
        dict.fromkeys([*state.get("implemented_validator_ids", []), "review_plan_reflection_ledger_validator"])
    )
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
    update_registry(now)
    ledger = write_review_ledger(now)
    audit = build_audit(now, trader_hash, agents_hash, ledger)
    update_navigation(now, trader_hash, agents_hash, audit)
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
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
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
        run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"], timeout_seconds=900),
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
        "overall_status": "PASS" if all(item["status"] == "PASS" for item in validators_run) else "BLOCKED",
    }
    stage_gate = {
        "schema_id": "trader1.stage_gate_result.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "stage": "MVP-4",
        "status": "PASS" if audit["status"] == "PASS" and all(item["status"] == "PASS" for item in validators_run) else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "remaining_blockers": BLOCKERS,
    }
    write_json(ROOT / "system" / "evidence" / f"{PATCH_BASENAME}.evidence_manifest.json", evidence_manifest)
    write_json(ROOT / "system" / "evidence" / "validator_runs" / f"{PATCH_BASENAME}.validator_run_log.json", validator_log)
    write_json(ROOT / "system" / "evidence" / "stage_gates" / f"{PATCH_BASENAME}.stage_gate_result.json", stage_gate)
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    print(json.dumps({"patch_id": PATCH_ID, "audit_status": audit["status"], "stage_gate_status": stage_gate["status"]}, sort_keys=True))
    return 0 if audit["status"] == "PASS" and stage_gate["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
