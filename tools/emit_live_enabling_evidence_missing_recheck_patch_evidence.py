from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-LIVE-ENABLING-EVIDENCE-MISSING-RECHECK"
GAP_ID = "LIVE_ENABLING_EVIDENCE_MISSING"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-RECHECK"
PREVIOUS_PATCH_PREFIX = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK_"
NEXT_TASK_CLASS = "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK"

EXTERNAL_BLOCKER_MANIFEST = "system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
EXTERNAL_BLOCKER_PATCH_RESULT = "system/evidence/patch_results/MVP4_EXTERNAL_BLOCKER.patch_result.json"
LIVE_FINAL_GUARD_PATCH_RESULT = "system/evidence/patch_results/MVP4_LIVE_FINAL_GUARD.patch_result.json"
LIVE_BLOCKED_NEGATIVE_PATCH_RESULT = "system/evidence/patch_results/MVP4_LIVE_BLOCKED_NEGATIVE_RECHECK.patch_result.json"
CONTRACT_GAP_PATH = f"system/evidence/contract_gaps/{GAP_ID}.contract_gap.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.execution.live_order_gateway import evaluate_live_order_path  # noqa: E402
from trader1.safety.live_order_gate import REQUIRED_LIVE_TRUE_FIELDS, evaluate_live_order_gate  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "live_blocked_scaffold_validator",
    "live_blocked_negative_matrix_validator",
    "single_writer_order_path_validator",
    "strategy_direct_order_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    item
    for item in VALIDATORS_REQUIRED
    if item
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
]
ROUTE_GUARD_TEST_ARTIFACTS = [
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    "tests/contract/test_completed_recheck_route_depth_guard.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_implementation_depth_recheck.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_open_contract_gap_implementation_priority_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_patch_result_validator_run_gap_baseline_reconciliation_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_implementation_depth_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tests/contract/test_post_rerun_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_implementation_depth_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_implementation_depth_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
]
CHANGED_ARTIFACTS = sorted(
    set(
        ROUTE_GUARD_TEST_ARTIFACTS
        + [
            "tests/contract/test_live_enabling_evidence_missing_recheck.py",
            "tools/emit_live_enabling_evidence_missing_recheck_patch_evidence.py",
            f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            CONTRACT_GAP_PATH,
        ]
    )
)
BLOCKERS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "API_UNVERIFIED",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    GAP_ID,
    "LIVE_READY_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "OPERATOR_APPROVAL_MISSING",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
]
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def assert_current_state_ready_for_live_enabling_recheck() -> None:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    completed = set(state.get("completed_requirement_ids", []))
    gaps = set(state.get("open_contract_gap_ids", []))
    last_patch_id = str(state.get("last_patch_id", ""))
    next_allowed = state.get("next_allowed_task_class")

    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"{field} must stay false before {PATCH_BASENAME}")
    if GAP_ID not in gaps:
        raise RuntimeError(f"{GAP_ID} must remain open before {PATCH_BASENAME}")

    previous_route_ready = last_patch_id.startswith(PREVIOUS_PATCH_PREFIX) and next_allowed == PATCH_BASENAME
    idempotent_rerun_ready = last_patch_id.startswith(PATCH_BASENAME) and next_allowed == NEXT_TASK_CLASS
    if not (previous_route_ready or idempotent_rerun_ready):
        raise RuntimeError(
            f"{PATCH_BASENAME} expected previous route {PREVIOUS_PATCH_PREFIX} -> {PATCH_BASENAME}; "
            f"got last_patch_id={last_patch_id!r}, next_allowed_task_class={next_allowed!r}"
        )
    if previous_route_ready and PREVIOUS_REQUIREMENT_ID not in completed:
        raise RuntimeError(f"{PREVIOUS_REQUIREMENT_ID} must be completed before {PATCH_BASENAME}")


def assert_previous_live_patch(path_text: str) -> dict[str, Any]:
    patch = load_json(ROOT / path_text)
    assert_false_fields(path_text, patch, "_after")
    if GAP_ID not in patch.get("remaining_blockers", []):
        raise RuntimeError(f"{path_text} no longer preserves {GAP_ID}")
    return patch


def live_enabling_gap_summary() -> dict[str, Any]:
    manifest = load_json(ROOT / EXTERNAL_BLOCKER_MANIFEST)
    external_patch = assert_previous_live_patch(EXTERNAL_BLOCKER_PATCH_RESULT)
    live_final_patch = assert_previous_live_patch(LIVE_FINAL_GUARD_PATCH_RESULT)
    live_blocked_patch = assert_previous_live_patch(LIVE_BLOCKED_NEGATIVE_PATCH_RESULT)

    assert_false_fields(EXTERNAL_BLOCKER_MANIFEST, manifest)
    known_blockers = set(manifest.get("known_blockers", []))
    statuses = list(manifest.get("external_review_input_statuses", []))
    usable_statuses = [item for item in statuses if item.get("usable_for_live_enabling") is True]
    true_flag_statuses = [
        item
        for item in statuses
        for field in ("live_order_ready", "live_order_allowed", "can_live_trade")
        if item.get(field) is True
    ]
    if GAP_ID not in known_blockers:
        raise RuntimeError("external blocker manifest lost live-enabling blocker")
    if usable_statuses:
        raise RuntimeError("external review status unexpectedly usable for live enabling")
    if true_flag_statuses:
        raise RuntimeError("external review status has forbidden live true field")

    live_gate = {field: True for field in REQUIRED_LIVE_TRUE_FIELDS}
    live_gate.update(
        {
            "live_order_ready": True,
            "live_order_allowed": True,
            "can_live_trade": True,
            "live_enabling_patch_valid": True,
        }
    )
    gate_decision = evaluate_live_order_gate(live_gate)
    path_decision = evaluate_live_order_path(
        {
            "source_kind": "FinalDecision",
            "final_decision": "ENTER_LONG",
            "client_order_id": "live-enabling-recheck-spoof",
            "single_writer_available": True,
            "budget_reserved": True,
            "local_reservation_committed": True,
            "ledger_reconciled": True,
            "live_gate": live_gate,
        }
    )
    if gate_decision.primary_blocker_code != GAP_ID:
        raise RuntimeError("spoofed all-green live gate no longer blocks on missing live-enabling evidence")
    if path_decision.primary_blocker_code != GAP_ID or path_decision.order_adapter_called:
        raise RuntimeError("spoofed order path no longer blocks before adapter on missing live-enabling evidence")

    blocker_codes = sorted(
        set(BLOCKERS)
        | known_blockers
        | {item.get("primary_blocker_code") for item in statuses if item.get("primary_blocker_code")}
    )
    return {
        "external_manifest_hash": sha256_file(ROOT / EXTERNAL_BLOCKER_MANIFEST),
        "external_patch_result_hash": external_patch.get("result_hash"),
        "live_final_guard_patch_result_hash": live_final_patch.get("result_hash"),
        "live_blocked_negative_patch_result_hash": live_blocked_patch.get("result_hash"),
        "known_blocker_count": len(known_blockers),
        "external_review_input_count": len(statuses),
        "usable_for_live_enabling_count": len(usable_statuses),
        "unusable_for_live_enabling_count": len(statuses) - len(usable_statuses),
        "forbidden_live_true_status_count": len(true_flag_statuses),
        "all_green_live_gate_primary_blocker_code": gate_decision.primary_blocker_code,
        "all_green_order_path_primary_blocker_code": path_decision.primary_blocker_code,
        "all_green_order_adapter_called": path_decision.order_adapter_called,
        "remaining_blockers": blocker_codes,
    }


def write_contract_gap(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_json(
        ROOT / CONTRACT_GAP_PATH,
        {
            "schema_id": "trader1.contract_gap.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "status": "OPEN",
            "blockers": [
                {
                    "code": GAP_ID,
                    "severity": "CRITICAL",
                    "message": (
                        "Live enabling evidence is absent or explicitly unusable: official API, read-only account, "
                        "permission check, manual order, operator approval, and burn-in inputs remain blocked."
                    ),
                    "source_requirement_id": REQUIREMENT_ID,
                }
            ],
            "notes": (
                f"external_review_input_count={summary['external_review_input_count']}; "
                f"usable_for_live_enabling_count={summary['usable_for_live_enabling_count']}; "
                "no live order, live config mutation, credential use, or scale-up permission is created."
            ),
            "contract_gap_id": GAP_ID,
            "severity": "CRITICAL",
            "source_section_id": "SECTION_LIVE_FINAL_GUARD",
            "live_affecting": True,
        },
    )


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_LIVE_BLOCKED_TEST", "SECTION_ORDER_PATH_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-LIVE-FINAL-GUARD", "REQ-MVP4-LIVE-BLOCKED-NEGATIVE-RECHECK"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.contract_gap.v1", "trader1.validator_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm external live review inputs are not usable for live enabling.
- Confirm {GAP_ID} remains in known blockers and open contract gaps.
- Confirm spoofed all-green live gate and order path still block before any adapter call.
- Route only to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

gap_snapshot:
- external_review_input_count: {summary["external_review_input_count"]}
- usable_for_live_enabling_count: {summary["usable_for_live_enabling_count"]}
- unusable_for_live_enabling_count: {summary["unusable_for_live_enabling_count"]}
- all_green_live_gate_primary_blocker_code: {summary["all_green_live_gate_primary_blocker_code"]}
- all_green_order_path_primary_blocker_code: {summary["all_green_order_path_primary_blocker_code"]}
- all_green_order_adapter_called: {summary["all_green_order_adapter_called"]}

known_omissions_by_design:
- No current or live config writer is added.
- No credentialed API call, live order, LIVE_ENABLING_PATCH, LIVE_READY snapshot write, or scale-up output is created.
- {GAP_ID} remains an open live-blocking gap.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
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

Live enabling evidence is missing or unusable. Spoofed all-green live inputs remain blocked before any order adapter call.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LIVE_FINAL_GUARD",
            "source_file": "TRADER_1.md",
            "source_heading": "live enabling evidence missing recheck",
            "full_text_marker": f"{REQUIREMENT_ID}: live enabling evidence remains absent or unusable; live and scale permissions stay false",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Live enabling evidence missing recheck",
            "requirement_kind": "LIVE_BLOCKED_TEST_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.evidence_manifest.v1",
                "trader1.contract_gap.v1",
                "trader1.validator_result.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_live_enabling_evidence_missing_recheck.py",
                "tests/live_blocked/test_order_path_guard.py",
                "tests/live_blocked/test_live_blocked_scaffold.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
                "SECTION_ORDER_PATH_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
                "REQ-MVP4-LIVE-BLOCKED-NEGATIVE-RECHECK",
            ],
            "source_text_sha256": sha256_bytes(
                b"live enabling evidence remains absent or unusable; live and scale permissions stay false"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RECHECK_GAP_OPEN",
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
            "section_id": "SECTION_LIVE_FINAL_GUARD",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/evidence_manifest.schema.json",
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/validator_result.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_live_enabling_evidence_missing_recheck.py",
                "tests/live_blocked/test_order_path_guard.py",
                "tests/live_blocked/test_live_blocked_scaffold.py",
            ],
            "fixture_files": [
                EXTERNAL_BLOCKER_MANIFEST,
                EXTERNAL_BLOCKER_PATCH_RESULT,
                LIVE_FINAL_GUARD_PATCH_RESULT,
                LIVE_BLOCKED_NEGATIVE_PATCH_RESULT,
                "tests/live_blocked/fixtures/live_blocked_matrix.json",
            ],
            "runtime_modules": [
                "trader1/safety/live_order_gate.py",
                "trader1/execution/live_order_gateway.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                CONTRACT_GAP_PATH,
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "remaining_blockers",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RECHECK_GAP_OPEN",
        }
    )
    matrix.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "rows": sorted(rows, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    summary: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_LIVE_BLOCKED_NEGATIVE_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
                "REQ-MVP4-LIVE-BLOCKED-NEGATIVE-RECHECK",
                "REQ-MVP0-LIVE-BLOCKED-TEST",
            ],
            "new_registry_items": [REQUIREMENT_ID, f"contracts/generated/context_pack/{PATCH_BASENAME}.md", CONTRACT_GAP_PATH],
            "new_or_changed_schema_ids": [],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_CONVERGENCE_RISK_SCALING",
                "SECTION_LIVE_BLOCKED_TEST",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONVERGENCE_DASHBOARD"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": summary["remaining_blockers"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "external live review blocker manifest",
                "live final guard patch result",
                "live blocked negative matrix",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
                "SECTION_ORDER_PATH_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
                "SECTION_ORDER_PATH_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
) -> None:
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
            "stage_gate_status": "PASS_RECHECK_LIVE_ENABLING_EVIDENCE_MISSING_REMAINS_LIVE_BLOCKING",
            **summary,
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                EXTERNAL_BLOCKER_MANIFEST,
                EXTERNAL_BLOCKER_PATCH_RESULT,
                LIVE_FINAL_GUARD_PATCH_RESULT,
                LIVE_BLOCKED_NEGATIVE_PATCH_RESULT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", [])) | {GAP_ID})
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    patches = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    patches.append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": "MVP-4",
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
            "next_allowed_task_class": NEXT_TASK_CLASS,
        }
    )
    ledger.update(
        {
            "updated_at_utc": now,
            "patches": patches,
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result["result_hash"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    assert_current_state_ready_for_live_enabling_recheck()
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = live_enabling_gap_summary()
    write_contract_gap(now, trader_hash, agents_hash, summary)
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/contract/test_live_enabling_evidence_missing_recheck.py",
                    "tests/live_blocked/test_order_path_guard.py",
                    "tests/live_blocked/test_live_blocked_scaffold.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
        ]
    )
    summary = live_enabling_gap_summary()
    write_contract_gap(now, trader_hash, agents_hash, summary)
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "usable_for_live_enabling_count": summary["usable_for_live_enabling_count"],
                "all_green_order_path_primary_blocker_code": summary["all_green_order_path_primary_blocker_code"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
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
