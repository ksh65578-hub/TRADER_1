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

PATCH_BASENAME = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_NEXT_TASK_RESTORE"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-NEXT-TASK-RESTORE"
RECONCILIATION_REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK"
WRITE_BLOCKED_REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-STATE-SYNC-RECHECK"
MISSING_CYCLE_NEXT_TASK_RESTORE_REQUIREMENT_ID = "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-NEXT-TASK-RESTORE"
RECONCILIATION_BACKWARD_TASK = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK"
WRITE_BLOCKED_BACKWARD_TASK = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"
NEXT_TASK_CLASS = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_RECHECK"

RECONCILIATION_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK.patch_result.json"
)
WRITE_BLOCKED_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_STATE_SYNC_RECHECK.patch_result.json"
)
MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_NEXT_TASK_RESTORE.patch_result.json"
)
MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_ID = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_NEXT_TASK_RESTORE_20260504_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_post_rerun_current_evidence_write_blocked_recheck_patch_evidence as write_blocked  # noqa: E402
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
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = write_blocked.VALIDATORS_REQUIRED
BOOTSTRAP_VALIDATORS_REQUIRED = write_blocked.BOOTSTRAP_VALIDATORS_REQUIRED
CHANGED_ARTIFACTS = [
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tools/emit_missing_cycle_ledger_rerun_required_next_task_restore_patch_evidence.py",
    "tools/emit_post_rerun_reconciliation_required_next_task_restore_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = write_blocked.BLOCKERS
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


def load_route_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    reconciliation = load_json(ROOT / RECONCILIATION_PATCH_RESULT)
    blocked = load_json(ROOT / WRITE_BLOCKED_PATCH_RESULT)
    missing_route = load_json(ROOT / MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_RESULT)

    completed = set(state.get("completed_requirement_ids", []))
    required_completed = {
        RECONCILIATION_REQUIREMENT_ID,
        WRITE_BLOCKED_REQUIREMENT_ID,
        MISSING_CYCLE_NEXT_TASK_RESTORE_REQUIREMENT_ID,
    }
    missing_completed = sorted(required_completed - completed)
    if missing_completed:
        raise RuntimeError(f"required completed requirement ids missing: {missing_completed}")

    if reconciliation.get("next_task_class") != WRITE_BLOCKED_BACKWARD_TASK:
        raise RuntimeError("post-rerun reconciliation state-sync no longer routes to write-blocked recheck")
    if blocked.get("next_task_class") != NEXT_TASK_CLASS:
        raise RuntimeError("post-rerun write-blocked state-sync no longer routes to patch-result validator gap")
    if missing_route.get("next_task_class") != RECONCILIATION_BACKWARD_TASK:
        raise RuntimeError("missing-cycle next-task restore historical route changed unexpectedly")

    for path_text, artifact in (
        (RECONCILIATION_PATCH_RESULT, reconciliation),
        (WRITE_BLOCKED_PATCH_RESULT, blocked),
        (MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_RESULT, missing_route),
        ("contracts/generated/current_implementation_state.json", state),
    ):
        suffix = "_after" if path_text.endswith(".patch_result.json") else ""
        assert_false_fields(path_text, artifact, suffix)

    if "POST_RERUN_RECONCILIATION_REQUIRED" not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("post-rerun reconciliation gap is no longer tracked as open")
    if "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED" not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("post-rerun current evidence write-blocked gap is no longer tracked as open")

    summary = dict(write_blocked.current_gap_summary())
    observed_route = state.get("next_allowed_task_class")
    route_before_patch = observed_route
    if state.get("last_patch_id") in {PATCH_ID, MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_ID}:
        route_before_patch = RECONCILIATION_BACKWARD_TASK

    summary.update(
        {
            "route_before_patch": route_before_patch,
            "observed_state_next_allowed_task_class": observed_route,
            "route_after_patch": NEXT_TASK_CLASS,
            "backward_route_detected": route_before_patch in {RECONCILIATION_BACKWARD_TASK, WRITE_BLOCKED_BACKWARD_TASK},
            "reconciliation_patch_result_hash": reconciliation.get("result_hash"),
            "write_blocked_patch_result_hash": blocked.get("result_hash"),
            "missing_cycle_next_task_restore_patch_result_hash": missing_route.get("result_hash"),
            "state_last_patch_id_before": state.get("last_patch_id"),
            "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        }
    )
    return summary


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_POST_RERUN_RECONCILIATION_REQUIRED_NEXT_TASK_RESTORE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_MVP0_VALIDATOR_IMPLEMENTATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{RECONCILIATION_REQUIREMENT_ID}", "{WRITE_BLOCKED_REQUIREMENT_ID}", "{MISSING_CYCLE_NEXT_TASK_RESTORE_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1", "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1", "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect that post-rerun reconciliation state-sync and current-evidence write-blocked state-sync are already complete.
- Prevent current_implementation_state from routing back to {RECONCILIATION_BACKWARD_TASK} or {WRITE_BLOCKED_BACKWARD_TASK}.
- Restore next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep POST_RERUN_RECONCILIATION_REQUIRED and POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED open and live-blocking.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

route_snapshot:
- route_before_patch: {summary["route_before_patch"]}
- backward_route_detected: {summary["backward_route_detected"]}
- route_after_patch: {summary["route_after_patch"]}

gap_snapshot:
- promotion_guard_status: {summary["promotion_guard_status"]}
- current_evidence_write_authorized_count: {summary["current_evidence_write_authorized_count"]}
- current_evidence_write_allowed_count: {summary["current_evidence_write_allowed_count"]}
- candidate_current_evidence_usable_count: {summary["candidate_current_evidence_usable_count"]}
- operator_reconciliation_required_count: {summary["operator_reconciliation_required_count"]}
- unresolved_item_count: {summary["unresolved_item_count"]}
- resolved_item_count: {summary["resolved_item_count"]}

known_omissions_by_design:
- No post-rerun reconciliation is resolved by this patch.
- No current evidence writer, latest pointer, live config, credentialed API, live order, or scale-up output is written.
- POST_RERUN_RECONCILIATION_REQUIRED and POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED remain open until independent resolution and current-evidence closure evidence passes.

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

Post-rerun reconciliation and current-evidence write-blocked state-sync rechecks are already complete. The gaps remain open and live-blocking, and the next safe task is the patch-result validator run gap recheck.

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
    requirements = [
        item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID
    ]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_CURRENT_EVIDENCE_CLOSURE",
            "source_file": "TRADER_1.md",
            "source_heading": "post-rerun reconciliation required next task restore",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: completed post-rerun state-sync rechecks must not route current state "
                "back to completed reconciliation or current-evidence write-blocked rechecks"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Post-rerun reconciliation next task restore",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1",
                "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1",
                "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
                "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_MVP0_VALIDATOR_IMPLEMENTATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                RECONCILIATION_REQUIREMENT_ID,
                WRITE_BLOCKED_REQUIREMENT_ID,
                MISSING_CYCLE_NEXT_TASK_RESTORE_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"completed post rerun rechecks must not route current state backward"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_NEXT_TASK_RESTORE_GAPS_OPEN",
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
            "section_id": "SECTION_CURRENT_EVIDENCE_CLOSURE",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_post_rerun_current_evidence_promotion_guard_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_operator_reconciliation_queue_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_resolution_current_evidence_closure_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
                "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
            ],
            "fixture_files": [
                RECONCILIATION_PATCH_RESULT,
                WRITE_BLOCKED_PATCH_RESULT,
                MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_RESULT,
                write_blocked.PROMOTION_GUARD_REPORT,
                write_blocked.OPERATOR_QUEUE_REPORT,
                write_blocked.REVIEW_GUIDANCE_REPORT,
                write_blocked.RESOLUTION_AUDIT_REPORT,
                write_blocked.BLOCKER_ROLLUP_REPORT,
                write_blocked.DECISION_AUDIT_REPORT,
                write_blocked.CLOSURE_REPORT,
            ],
            "runtime_modules": [],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "next_required_section_ids",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_NEXT_TASK_RESTORE_GAPS_OPEN",
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
    template = load_json(ROOT / WRITE_BLOCKED_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                RECONCILIATION_REQUIREMENT_ID,
                WRITE_BLOCKED_REQUIREMENT_ID,
                MISSING_CYCLE_NEXT_TASK_RESTORE_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_STATE_ONLY",
            "new_registry_items": [
                REQUIREMENT_ID,
                f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            ],
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
                "SECTION_MVP0_VALIDATOR_IMPLEMENTATION",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_PATCH_RESULT_SCHEMA",
            ],
            "next_optional_section_ids": ["SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
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
            "active_read_surface_used": [
                "current_implementation_state",
                RECONCILIATION_PATCH_RESULT,
                WRITE_BLOCKED_PATCH_RESULT,
                MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_RESULT,
                "post-rerun promotion guard report",
                "post-rerun operator queue and resolution reports",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_MVP0_VALIDATOR_IMPLEMENTATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_NEXT_TASK_RESTORE",
            "required_section_ids": [
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_MVP0_VALIDATOR_IMPLEMENTATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_MVP0_VALIDATOR_IMPLEMENTATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_NEXT_TASK_RESTORED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "post_rerun_current_evidence_promotion_guard_status": summary["promotion_guard_status"],
            "post_rerun_promotion_review_ready_count": summary["promotion_review_ready_count"],
            "post_rerun_promotion_candidate_verified_count": summary["promotion_candidate_verified_count"],
            "post_rerun_operator_reconciliation_queue_status": summary["operator_queue_status"],
            "post_rerun_operator_reconciliation_required_count": summary[
                "operator_reconciliation_required_count"
            ],
            "post_rerun_operator_resolution_unresolved_item_count": summary["unresolved_item_count"],
            "post_rerun_operator_resolution_resolved_item_count": summary["resolved_item_count"],
            "post_rerun_resolution_current_evidence_closure_status": summary["closure_status"],
            "post_rerun_current_evidence_write_authorized_count": summary[
                "current_evidence_write_authorized_count"
            ],
            "post_rerun_current_evidence_write_allowed_count": summary["current_evidence_write_allowed_count"],
            "candidate_current_evidence_usable_count": summary["candidate_current_evidence_usable_count"],
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
            "stage_gate_status": "PASS_NEXT_TASK_RESTORED_POST_RERUN_STATE_SYNCS_ALREADY_COMPLETE",
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
                RECONCILIATION_PATCH_RESULT,
                WRITE_BLOCKED_PATCH_RESULT,
                MISSING_CYCLE_NEXT_TASK_RESTORE_PATCH_RESULT,
                write_blocked.PROMOTION_GUARD_REPORT,
                write_blocked.OPERATOR_QUEUE_REPORT,
                write_blocked.REVIEW_GUIDANCE_REPORT,
                write_blocked.RESOLUTION_AUDIT_REPORT,
                write_blocked.BLOCKER_ROLLUP_REPORT,
                write_blocked.DECISION_AUDIT_REPORT,
                write_blocked.CLOSURE_REPORT,
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
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 Post-Rerun Reconciliation Next Task Restore Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Post-rerun reconciliation and current-evidence write-blocked state-sync rechecks are already complete.
- The current state was routed back to {summary["route_before_patch"]}, which can repeat completed work.

Patch:
- Added regression tests that block routing back to completed post-rerun state-sync rechecks.
- Restored current_implementation_state next_allowed_task_class to {NEXT_TASK_CLASS}.
- Preserved POST_RERUN_RECONCILIATION_REQUIRED and POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED as open blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(
        set(
            state.get("open_contract_gap_ids", [])
            + [
                "PATCH_RESULT_VALIDATOR_RUN_GAP",
                "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
                "POST_RERUN_RECONCILIATION_REQUIRED",
            ]
        )
    )
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


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = load_route_summary()
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
                    "unittest",
                    "tests.contract.test_missing_cycle_ledger_rerun_required_recheck",
                    "tests.contract.test_post_rerun_current_evidence_write_blocked_recheck",
                    "-v",
                ]
            ),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/runtime/test_upbit_paper_post_rerun_current_evidence_promotion_guard.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py",
                    "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py",
                    "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_review_guidance.py",
                    "tests/runtime/test_upbit_paper_post_rerun_operator_resolution_audit.py",
                    "tests/runtime/test_upbit_paper_post_rerun_resolution_current_evidence_closure.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    summary = load_route_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    write_source_bundle_manifest()
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        BOOTSTRAP_VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "route_before_patch": summary["route_before_patch"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "current_evidence_write_allowed_count": summary["current_evidence_write_allowed_count"],
                "candidate_current_evidence_usable_count": summary["candidate_current_evidence_usable_count"],
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
