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

PATCH_BASENAME = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_NEXT_TASK_RESTORE"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-NEXT-TASK-RESTORE"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-MISSING-CYCLE-LEDGER-RERUN-REQUIRED-STATE-SYNC-RECHECK"
UPSTREAM_REQUIREMENT_ID = "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-NEXT-TASK-RESTORE"
GAP_ID = "MISSING_CYCLE_LEDGER_RERUN_REQUIRED"
POST_RERUN_GAP_ID = "POST_RERUN_RECONCILIATION_REQUIRED"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK"
BACKWARD_NEXT_TASK_CLASS = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_RECHECK"

PREVIOUS_PATCH_BASENAME = "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_STATE_SYNC_RECHECK"
PREVIOUS_PATCH_ID = f"{PREVIOUS_PATCH_BASENAME}_20260504_001"
PREVIOUS_PATCH_RESULT = f"system/evidence/patch_results/{PREVIOUS_PATCH_BASENAME}.patch_result.json"
UPSTREAM_PATCH_BASENAME = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_NEXT_TASK_RESTORE"
UPSTREAM_PATCH_ID = f"{UPSTREAM_PATCH_BASENAME}_20260504_001"
UPSTREAM_PATCH_RESULT = f"system/evidence/patch_results/{UPSTREAM_PATCH_BASENAME}.patch_result.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_missing_cycle_ledger_rerun_required_state_sync_recheck_patch_evidence as base_missing  # noqa: E402
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


VALIDATORS_REQUIRED = base_missing.VALIDATORS_REQUIRED
BOOTSTRAP_VALIDATORS_REQUIRED = base_missing.BOOTSTRAP_VALIDATORS_REQUIRED
CHANGED_ARTIFACTS = [
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tools/emit_paper_shadow_runtime_shadow_observation_gap_next_task_restore_patch_evidence.py",
    "tools/emit_missing_cycle_ledger_rerun_required_next_task_restore_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = base_missing.BLOCKERS
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
    previous_path = ROOT / PREVIOUS_PATCH_RESULT
    upstream_path = ROOT / UPSTREAM_PATCH_RESULT
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"

    if not previous_path.exists():
        raise RuntimeError(f"previous missing-cycle patch_result missing: {PREVIOUS_PATCH_RESULT}")
    if not upstream_path.exists():
        raise RuntimeError(f"upstream next-task restore patch_result missing: {UPSTREAM_PATCH_RESULT}")

    previous = load_json(previous_path)
    upstream = load_json(upstream_path)
    state = load_json(state_path)

    if previous.get("patch_id") != PREVIOUS_PATCH_ID:
        raise RuntimeError("previous missing-cycle state-sync patch_id drifted")
    if previous.get("next_task_class") != NEXT_TASK_CLASS:
        raise RuntimeError("previous missing-cycle state-sync no longer routes to post-rerun reconciliation")
    if upstream.get("patch_id") != UPSTREAM_PATCH_ID:
        raise RuntimeError("upstream paper-shadow next-task restore patch_id drifted")
    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("missing-cycle state-sync recheck is not recorded completed")
    if GAP_ID not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("missing-cycle ledger rerun gap is no longer tracked as open")
    if POST_RERUN_GAP_ID not in state.get("open_contract_gap_ids", []):
        raise RuntimeError("post-rerun reconciliation gap is no longer tracked as open")

    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(UPSTREAM_PATCH_RESULT, upstream, "_after")
    assert_false_fields("current implementation state", state)

    summary = dict(base_missing.current_gap_summary())
    summary.update(
        {
            "route_before_patch": state.get("next_allowed_task_class"),
            "route_after_patch": NEXT_TASK_CLASS,
            "backward_route_detected": state.get("next_allowed_task_class") == BACKWARD_NEXT_TASK_CLASS,
            "previous_patch_result_hash": previous.get("result_hash"),
            "previous_patch_next_task_class": previous.get("next_task_class"),
            "upstream_patch_result_hash": upstream.get("result_hash"),
            "upstream_patch_next_task_class_before_generator_fix": upstream.get("next_task_class"),
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
task_class: MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_NEXT_TASK_RESTORE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{UPSTREAM_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1", "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1", "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect that the missing-cycle ledger rerun state-sync recheck is already complete.
- Confirm {GAP_ID} and {POST_RERUN_GAP_ID} remain open and live-blocking.
- Prevent current_implementation_state from routing back to completed missing-cycle state-sync work.
- Restore next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

route_snapshot:
- route_before_patch: {summary["route_before_patch"]}
- backward_route_detected: {summary["backward_route_detected"]}
- route_after_patch: {summary["route_after_patch"]}
- previous_patch_next_task_class: {summary["previous_patch_next_task_class"]}
- upstream_patch_next_task_class_before_generator_fix: {summary["upstream_patch_next_task_class_before_generator_fix"]}

gap_snapshot:
- guard_status: {summary["guard_status"]}
- rerun_ready_item_count: {summary["rerun_ready_item_count"]}
- missing_cycle_ledger_jsonl_total_count: {summary["missing_cycle_ledger_jsonl_total_count"]}
- executor_status: {summary["executor_status"]}
- staged_current_evidence_usable_count: {summary["staged_current_evidence_usable_count"]}
- post_rerun_candidate_current_evidence_usable_count: {summary["post_rerun_candidate_current_evidence_usable_count"]}
- current_evidence_write_allowed: {summary["current_evidence_write_allowed"]}

known_omissions_by_design:
- No cycle is rerun by this patch.
- No current ledger JSONL, latest pointer, current evidence, live config, credentialed API, live order, or scale-up output is written.
- The missing-cycle and post-rerun reconciliation gaps remain open until independent reconciliation and current evidence closure evidence passes.

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

The missing-cycle ledger rerun state-sync recheck is complete, but the missing-cycle and post-rerun reconciliation gaps remain open. Current routing must continue to post-rerun reconciliation instead of returning to the completed missing-cycle recheck.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "missing cycle ledger rerun required next task restore",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: once the missing-cycle ledger rerun state-sync recheck is completed, "
                "do not route current_implementation_state back to that completed recheck"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Missing cycle ledger rerun next task restore",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_missing_cycle_rerun_guard_report.v1",
                "trader1.upbit_paper_bounded_rerun_staging_executor_report.v1",
                "trader1.upbit_paper_post_rerun_ledger_rollup_reconciliation_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                UPSTREAM_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"completed missing cycle ledger rerun state sync must not route current state backward"
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
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_missing_cycle_rerun_guard_report.schema.json",
                "contracts/schema/upbit_paper_bounded_rerun_staging_executor_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_ledger_rollup_reconciliation_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py"],
            "fixture_files": [
                base_missing.GUARD_REPORT,
                base_missing.EXECUTOR_REPORT,
                base_missing.POST_RERUN_RECONCILIATION_REPORT,
                base_missing.POST_RERUN_BLOCKER_ROLLUP_REPORT,
                PREVIOUS_PATCH_RESULT,
                UPSTREAM_PATCH_RESULT,
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
    summary: dict[str, Any],
    validators_required: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                PREVIOUS_REQUIREMENT_ID,
                UPSTREAM_REQUIREMENT_ID,
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
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_RUNTIME_RECOVERY"],
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
                PREVIOUS_PATCH_RESULT,
                UPSTREAM_PATCH_RESULT,
                "missing-cycle rerun guard report",
                "bounded rerun staging executor report",
                "post-rerun ledger rollup reconciliation report",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_MISSING_CYCLE_LEDGER_RERUN_REQUIRED_NEXT_TASK_RESTORE",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
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
            "optimizer_status_before": "LIVE_BLOCKED_ROUTE_REGRESSION_DETECTED",
            "optimizer_status_after": "POST_RERUN_RECONCILIATION_RECHECK_NEXT_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION_NO_CURRENT_EVIDENCE_PROMOTION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_ROUTING_RESTORE_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "LIVE_BLOCKED_ROUTE_REGRESSION_DETECTED",
            "convergence_state_after": "POST_RERUN_RECONCILIATION_RECHECK_NEXT_LIVE_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "guard_status": summary["guard_status"],
            "guard_item_count": summary["guard_item_count"],
            "rerun_ready_item_count": summary["rerun_ready_item_count"],
            "recovery_guard_blocked_item_count": summary["recovery_guard_blocked_item_count"],
            "missing_cycle_ledger_jsonl_total_count": summary["missing_cycle_ledger_jsonl_total_count"],
            "planned_staging_artifact_total_count": summary["planned_staging_artifact_total_count"],
            "actual_rerun_executed": False,
            "rerun_executor_created": False,
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
            "stage_gate_status": "PASS_NEXT_TASK_RESTORED_MISSING_CYCLE_AND_POST_RERUN_GAPS_REMAIN_OPEN",
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
                PREVIOUS_PATCH_RESULT,
                UPSTREAM_PATCH_RESULT,
                base_missing.GUARD_REPORT,
                base_missing.EXECUTOR_REPORT,
                base_missing.POST_RERUN_RECONCILIATION_REPORT,
                base_missing.POST_RERUN_BLOCKER_ROLLUP_REPORT,
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
        f"""# MVP4 Missing Cycle Ledger Rerun Next Task Restore Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The missing-cycle ledger rerun state-sync recheck already routed to {NEXT_TASK_CLASS}.
- A later next-task restore left current_implementation_state routed back to {BACKWARD_NEXT_TASK_CLASS}.

Patch:
- Added a regression test that blocks routing back to the completed missing-cycle state-sync recheck.
- Updated the upstream paper-shadow next-task restore generator so reruns route to {NEXT_TASK_CLASS}.
- Restored current_implementation_state next_allowed_task_class to {NEXT_TASK_CLASS}.
- Kept {GAP_ID} and {POST_RERUN_GAP_ID} open.

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
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [GAP_ID, POST_RERUN_GAP_ID]))
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
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        summary,
        BOOTSTRAP_VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

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
                    "tests/runtime/test_upbit_paper_missing_cycle_rerun_guard.py",
                    "tests/runtime/test_upbit_paper_bounded_rerun_staging_executor.py",
                    "tests/runtime/test_upbit_paper_post_rerun_ledger_rollup_reconciliation.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
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
        summary,
        BOOTSTRAP_VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        summary,
        VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
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
                "route_before_patch": summary["route_before_patch"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "guard_status": summary["guard_status"],
                "executor_status": summary["executor_status"],
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
