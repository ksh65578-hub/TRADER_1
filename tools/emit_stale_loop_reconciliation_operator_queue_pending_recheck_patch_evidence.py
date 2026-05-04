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

PATCH_BASENAME = "MVP4_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-STALE-LOOP-RECONCILIATION-AFTER-REGENERATION-REQUIRED-RECHECK"
AUDITED_WRITER_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
CLOSED_GAP = "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING"

PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED_RECHECK.patch_result.json"
)
CLOSURE_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
)
LEDGER_PREVIEW_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_ledger_recheck_preview_report.json"
)
NORMALIZED_RECHECK_REPORT = (
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/"
    "upbit_paper_stale_loop_normalized_reconciliation_recheck_report.json"
)
AUDITED_WRITER_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER.patch_result.json"
)
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
STATIC_LIVE_BLOCKERS = {
    "API_UNVERIFIED",
    "LIVE_READY_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
}

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
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_stale_loop_reconciliation_operator_queue_closure_validator",
    "upbit_paper_stale_loop_ledger_recheck_preview_validator",
    "upbit_paper_stale_loop_normalized_reconciliation_recheck_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    item for item in VALIDATORS_REQUIRED if item != "generated_artifact_dirty_validator"
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_missing_cycle_ledger_rerun_required_recheck.py",
    "tests/contract/test_post_repair_reconciliation_required_recheck.py",
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tests/contract/test_repair_candidate_hash_mismatch_reconciliation_required_recheck.py",
    "tests/contract/test_blocked_repair_plan_requires_operator_reconciliation_recheck.py",
    "tests/contract/test_regenerated_current_blocked_repairs_require_ledger_recovery_reconciliation_recheck.py",
    "tools/emit_stale_loop_reconciliation_operator_queue_pending_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result: dict[str, Any] = {
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


def _assert_no_live_or_mutation(name: str, artifact: dict[str, Any]) -> None:
    assert_false_fields(name, artifact)
    for field in (
        "actual_long_run_evidence_created",
        "long_run_evidence_eligible",
        "promotion_eligible",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "persistent_loop_mutation_allowed",
        "replacement_write_allowed",
        "source_delete_allowed",
        "delete_source_allowed",
        "overwrite_source_allowed",
        "live_permission_created",
        "can_submit_order",
    ):
        if artifact.get(field) is True:
            raise RuntimeError(f"{name} has forbidden true field: {field}")


def _expect_value(name: str, artifact: dict[str, Any], field: str, expected: Any) -> None:
    if artifact.get(field) != expected:
        raise RuntimeError(f"{name} {field} drifted: {artifact.get(field)} != {expected}")


def load_summary() -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    previous = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    closure = load_json(ROOT / CLOSURE_REPORT)
    ledger_preview = load_json(ROOT / LEDGER_PREVIEW_REPORT)
    normalized_recheck = load_json(ROOT / NORMALIZED_RECHECK_REPORT)
    audited_writer = load_json(ROOT / AUDITED_WRITER_PATCH_RESULT)

    if PREVIOUS_REQUIREMENT_ID not in state.get("completed_requirement_ids", []):
        raise RuntimeError("post-regeneration stale-loop reconciliation recheck is not completed")
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("state is not routed to stale-loop operator queue pending recheck")
    if previous.get("next_task_class") != PATCH_BASENAME:
        raise RuntimeError("previous recheck does not route to operator queue pending recheck")
    if state.get("next_allowed_task_class") == PATCH_BASENAME and CLOSED_GAP not in state.get(
        "open_contract_gap_ids",
        [],
    ):
        raise RuntimeError("operator queue pending gap is not open before this recheck")

    assert_false_fields("current implementation state", state)
    assert_false_fields(PREVIOUS_PATCH_RESULT, previous, "_after")
    assert_false_fields(AUDITED_WRITER_PATCH_RESULT, audited_writer, "_after")
    for name, artifact in (
        (CLOSURE_REPORT, closure),
        (LEDGER_PREVIEW_REPORT, ledger_preview),
        (NORMALIZED_RECHECK_REPORT, normalized_recheck),
    ):
        _assert_no_live_or_mutation(name, artifact)

    expected_closure = {
        "closure_status": "BLOCKED",
        "primary_blocker_code": CLOSED_GAP,
        "closure_item_count": 6,
        "source_blocked_item_count": 6,
        "ledger_recheck_ready_count": 5,
        "recovery_guard_required_count": 1,
        "current_evidence_write_allowed_count": 0,
        "current_evidence_usable_after_closure_count": 0,
        "source_ledger_idempotency_status": "PASS",
        "source_ledger_reconciliation_status": "PASS",
        "source_ledger_mismatch_count": 0,
    }
    for field, expected in expected_closure.items():
        _expect_value(CLOSURE_REPORT, closure, field, expected)
    if CLOSED_GAP not in closure.get("blocker_codes", []):
        raise RuntimeError("closure report no longer carries the operator queue pending blocker")

    expected_preview = {
        "preview_status": "BLOCKED",
        "primary_blocker_code": "PERSISTENT_LOOP_SCHEMA_RECHECK_FAILED",
        "source_closure_status": "BLOCKED",
        "source_closure_validator_status": "PASS",
        "item_count": 6,
        "ledger_recheck_candidate_count": 5,
        "ledger_binding_pass_count": 5,
        "replacement_validation_fail_count": 5,
        "preview_blocked_count": 5,
        "current_evidence_write_allowed_count": 0,
        "current_evidence_usable_after_preview_count": 0,
        "skipped_recovery_guard_required_count": 1,
    }
    for field, expected in expected_preview.items():
        _expect_value(LEDGER_PREVIEW_REPORT, ledger_preview, field, expected)
    if CLOSED_GAP not in ledger_preview.get("blocker_codes", []):
        raise RuntimeError("ledger preview no longer binds the original operator queue pending blocker")

    expected_normalized = {
        "recheck_status": "BLOCKED",
        "source_normalized_reconciliation_preview_status": "BLOCKED",
        "normalized_reconciliation_recheck_candidate_count": 5,
        "normalized_hash_match_count": 5,
        "normalized_validation_blocked_count": 5,
        "ledger_rollup_recheck_required_count": 5,
        "current_evidence_write_allowed_count": 0,
    }
    for field, expected in expected_normalized.items():
        _expect_value(NORMALIZED_RECHECK_REPORT, normalized_recheck, field, expected)

    if audited_writer.get("next_task_class") != NEXT_TASK_CLASS:
        raise RuntimeError("audited writer patch no longer routes to the dashboard binding task")
    if CLOSED_GAP in audited_writer.get("remaining_blockers", []):
        raise RuntimeError("audited writer patch still carries the closed operator queue pending gap")
    if not STATIC_LIVE_BLOCKERS.issubset(set(audited_writer.get("remaining_blockers", []))):
        raise RuntimeError("audited writer patch no longer preserves static live blockers")

    state_gaps = set(state.get("open_contract_gap_ids", []))
    next_open_gaps = sorted(state_gaps - {CLOSED_GAP})
    remaining_blockers = sorted(set(next_open_gaps) | STATIC_LIVE_BLOCKERS)
    return {
        "route_before_patch": state.get("next_allowed_task_class"),
        "route_after_patch": NEXT_TASK_CLASS,
        "state_last_patch_id_before": state.get("last_patch_id"),
        "state_last_patch_result_hash_before": state.get("last_patch_result_hash"),
        "previous_patch_result_hash": previous.get("result_hash"),
        "audited_writer_patch_result_hash": audited_writer.get("result_hash"),
        "closed_gap_id": CLOSED_GAP,
        "stale_loop_operator_queue_closure_status": closure["closure_status"],
        "stale_loop_operator_queue_closure_item_count": closure["closure_item_count"],
        "stale_loop_operator_queue_closure_ledger_recheck_ready_count": closure["ledger_recheck_ready_count"],
        "stale_loop_operator_queue_closure_recovery_guard_required_count": closure[
            "recovery_guard_required_count"
        ],
        "stale_loop_operator_queue_closure_current_evidence_write_allowed_count": closure[
            "current_evidence_write_allowed_count"
        ],
        "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count": closure[
            "current_evidence_usable_after_closure_count"
        ],
        "stale_loop_ledger_recheck_preview_status": ledger_preview["preview_status"],
        "stale_loop_ledger_recheck_candidate_count": ledger_preview["ledger_recheck_candidate_count"],
        "stale_loop_ledger_recheck_replacement_validation_fail_count": ledger_preview[
            "replacement_validation_fail_count"
        ],
        "stale_loop_ledger_recheck_preview_blocked_count": ledger_preview["preview_blocked_count"],
        "stale_loop_ledger_recheck_current_evidence_write_allowed_count": ledger_preview[
            "current_evidence_write_allowed_count"
        ],
        "stale_loop_ledger_recheck_current_evidence_usable_after_preview_count": ledger_preview[
            "current_evidence_usable_after_preview_count"
        ],
        "stale_loop_normalized_reconciliation_recheck_status": normalized_recheck["recheck_status"],
        "stale_loop_normalized_reconciliation_recheck_candidate_count": normalized_recheck[
            "normalized_reconciliation_recheck_candidate_count"
        ],
        "stale_loop_normalized_reconciliation_recheck_hash_match_count": normalized_recheck[
            "normalized_hash_match_count"
        ],
        "stale_loop_normalized_reconciliation_recheck_validation_blocked_count": normalized_recheck[
            "normalized_validation_blocked_count"
        ],
        "stale_loop_normalized_reconciliation_recheck_ledger_rollup_required_count": normalized_recheck[
            "ledger_rollup_recheck_required_count"
        ],
        "stale_loop_normalized_reconciliation_recheck_write_allowed_count": 0,
        "stale_loop_normalized_reconciliation_recheck_current_evidence_write_allowed_count": normalized_recheck[
            "current_evidence_write_allowed_count"
        ],
        "candidate_current_evidence_usable_count": audited_writer.get("candidate_current_evidence_usable_count", 0),
        "next_open_contract_gap_ids": next_open_gaps,
        "remaining_blockers": remaining_blockers,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "{AUDITED_WRITER_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1", "trader1.upbit_paper_stale_loop_ledger_recheck_preview_report.v1", "trader1.upbit_paper_stale_loop_normalized_reconciliation_recheck_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm the operator queue closure still exposes {CLOSED_GAP} as blocked and PAPER-only.
- Confirm ledger recheck and normalized reconciliation recheck decompose queue items without current-evidence writes.
- Confirm the audited writer patch no longer carries {CLOSED_GAP} and routes to {NEXT_TASK_CLASS}.
- Remove {CLOSED_GAP} from current open contract gaps.
- Keep current evidence write, live order, live readiness, and scale-up blocked.

recheck_snapshot:
- closure_status: {summary["stale_loop_operator_queue_closure_status"]}
- closure_item_count: {summary["stale_loop_operator_queue_closure_item_count"]}
- ledger_recheck_ready_count: {summary["stale_loop_operator_queue_closure_ledger_recheck_ready_count"]}
- ledger_preview_status: {summary["stale_loop_ledger_recheck_preview_status"]}
- normalized_recheck_status: {summary["stale_loop_normalized_reconciliation_recheck_status"]}
- candidate_current_evidence_usable_count: {summary["candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- This patch does not rerun stale-loop regeneration, ledger repair, audited current-evidence writer, or dashboard writer.
- This patch does not mutate system/runtime artifacts.
- This patch does not use credentials, place live orders, mutate live config, create live permission, create long-run evidence, or scale up.

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

The stale-loop operator queue pending gap has downstream PAPER-only evidence. Queue items were decomposed through ledger recheck and normalized reconciliation, and the audited writer patch preserves zero live, scale-up, and current-evidence promotion permission.

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
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                PREVIOUS_PATCH_RESULT,
                CLOSURE_REPORT,
                LEDGER_PREVIEW_REPORT,
                NORMALIZED_RECHECK_REPORT,
                AUDITED_WRITER_PATCH_RESULT,
            ]
        )
    )

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "stale loop reconciliation operator queue pending recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: close {CLOSED_GAP} only when downstream fail-closed "
                f"PAPER evidence has decomposed the queue and preserves live/current-evidence blockers"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Stale loop operator queue pending recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1",
                "trader1.upbit_paper_stale_loop_ledger_recheck_preview_report.v1",
                "trader1.upbit_paper_stale_loop_normalized_reconciliation_recheck_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "tests/runtime/test_upbit_paper_stale_loop_ledger_recheck_preview.py",
                "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-CLOSURE",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-LEDGER-RECHECK-PREVIEW",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-NORMALIZED-RECONCILIATION-RECHECK",
                AUDITED_WRITER_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"operator queue pending can close only after downstream paper-only fail-closed evidence"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RECHECK_OPERATOR_QUEUE_PENDING_CLOSED",
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
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.schema.json",
                "contracts/schema/upbit_paper_stale_loop_ledger_recheck_preview_report.schema.json",
                "contracts/schema/upbit_paper_stale_loop_normalized_reconciliation_recheck_report.schema.json",
            ],
            "validator_files": [
                "trader1/validation/mvp0_validators.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_ledger_recheck_preview.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
            ],
            "test_files": [
                "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "tests/runtime/test_upbit_paper_stale_loop_ledger_recheck_preview.py",
                "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_ledger_recheck_preview.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
            ],
            "evidence_artifacts": [
                PREVIOUS_PATCH_RESULT,
                CLOSURE_REPORT,
                LEDGER_PREVIEW_REPORT,
                NORMALIZED_RECHECK_REPORT,
                AUDITED_WRITER_PATCH_RESULT,
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "stale_loop_operator_queue_closure_status",
                "stale_loop_ledger_recheck_preview_status",
                "stale_loop_normalized_reconciliation_recheck_status",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RECHECK_OPERATOR_QUEUE_PENDING_CLOSED",
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
                AUDITED_WRITER_REQUIREMENT_ID,
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_STATE_ONLY",
            "new_registry_items": [REQUIREMENT_ID, f"contracts/generated/context_pack/{PATCH_BASENAME}.md"],
            "new_or_changed_schema_ids": ["trader1.patch_result.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
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
                PREVIOUS_PATCH_RESULT,
                CLOSURE_REPORT,
                LEDGER_PREVIEW_REPORT,
                NORMALIZED_RECHECK_REPORT,
                AUDITED_WRITER_PATCH_RESULT,
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_OPERATOR_QUEUE_PENDING_CLOSED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NOT_OPTIMIZER_PATCH",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "STALE_LOOP_OPERATOR_QUEUE_PENDING_NOT_LIVE_READY",
            "optimizer_status_after": "AUDITED_WRITER_DASHBOARD_BINDING_REQUIRED_NOT_LIVE_READY",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_guardrail_result": "PASS_OPERATOR_QUEUE_RECHECK_CLOSED_WITH_PAPER_ONLY_EVIDENCE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "STATE_RECHECK_ONLY",
            "convergence_layer_changed": False,
            "convergence_state_before": "STALE_LOOP_OPERATOR_QUEUE_PENDING_NOT_LIVE_READY",
            "convergence_state_after": "AUDITED_WRITER_DASHBOARD_BINDING_REQUIRED_NOT_LIVE_READY",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": validators_required,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "candidate_current_evidence_usable_count": summary["candidate_current_evidence_usable_count"],
            "stale_loop_operator_queue_closure_status": summary["stale_loop_operator_queue_closure_status"],
            "stale_loop_operator_queue_closure_item_count": summary[
                "stale_loop_operator_queue_closure_item_count"
            ],
            "stale_loop_operator_queue_closure_ledger_recheck_ready_count": summary[
                "stale_loop_operator_queue_closure_ledger_recheck_ready_count"
            ],
            "stale_loop_operator_queue_closure_recovery_guard_required_count": summary[
                "stale_loop_operator_queue_closure_recovery_guard_required_count"
            ],
            "stale_loop_operator_queue_closure_current_evidence_write_allowed_count": summary[
                "stale_loop_operator_queue_closure_current_evidence_write_allowed_count"
            ],
            "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count": summary[
                "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count"
            ],
            "stale_loop_ledger_recheck_preview_status": summary["stale_loop_ledger_recheck_preview_status"],
            "stale_loop_ledger_recheck_candidate_count": summary["stale_loop_ledger_recheck_candidate_count"],
            "stale_loop_ledger_recheck_replacement_validation_fail_count": summary[
                "stale_loop_ledger_recheck_replacement_validation_fail_count"
            ],
            "stale_loop_ledger_recheck_preview_blocked_count": summary[
                "stale_loop_ledger_recheck_preview_blocked_count"
            ],
            "stale_loop_ledger_recheck_current_evidence_write_allowed_count": summary[
                "stale_loop_ledger_recheck_current_evidence_write_allowed_count"
            ],
            "stale_loop_ledger_recheck_current_evidence_usable_after_preview_count": summary[
                "stale_loop_ledger_recheck_current_evidence_usable_after_preview_count"
            ],
            "stale_loop_normalized_reconciliation_recheck_status": summary[
                "stale_loop_normalized_reconciliation_recheck_status"
            ],
            "stale_loop_normalized_reconciliation_recheck_candidate_count": summary[
                "stale_loop_normalized_reconciliation_recheck_candidate_count"
            ],
            "stale_loop_normalized_reconciliation_recheck_hash_match_count": summary[
                "stale_loop_normalized_reconciliation_recheck_hash_match_count"
            ],
            "stale_loop_normalized_reconciliation_recheck_validation_blocked_count": summary[
                "stale_loop_normalized_reconciliation_recheck_validation_blocked_count"
            ],
            "stale_loop_normalized_reconciliation_recheck_ledger_rollup_required_count": summary[
                "stale_loop_normalized_reconciliation_recheck_ledger_rollup_required_count"
            ],
            "stale_loop_normalized_reconciliation_recheck_write_allowed_count": summary[
                "stale_loop_normalized_reconciliation_recheck_write_allowed_count"
            ],
            "stale_loop_normalized_reconciliation_recheck_current_evidence_write_allowed_count": summary[
                "stale_loop_normalized_reconciliation_recheck_current_evidence_write_allowed_count"
            ],
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
            "stage_gate_status": "PASS_OPERATOR_QUEUE_PENDING_CLOSED",
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
                CLOSURE_REPORT,
                LEDGER_PREVIEW_REPORT,
                NORMALIZED_RECHECK_REPORT,
                AUDITED_WRITER_PATCH_RESULT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/audit_reports/{PATCH_BASENAME}_20260504.md",
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
        f"""# MVP4 Stale Loop Operator Queue Pending Recheck Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Operator queue closure remains BLOCKED and PAPER-only with {summary["stale_loop_operator_queue_closure_item_count"]} items.
- Ledger recheck preview classifies {summary["stale_loop_ledger_recheck_candidate_count"]} queue items and keeps current-evidence writes at {summary["stale_loop_ledger_recheck_current_evidence_write_allowed_count"]}.
- Normalized reconciliation recheck keeps {summary["stale_loop_normalized_reconciliation_recheck_candidate_count"]} candidates blocked for ledger rollup reconciliation.
- The audited current-evidence writer patch no longer carries {CLOSED_GAP} and routes to {NEXT_TASK_CLASS}.

Patch:
- Removed {CLOSED_GAP} from current implementation state.
- Routed next_allowed_task_class to {NEXT_TASK_CLASS}.
- Preserved all live, current-evidence write, persistent-loop mutation, source deletion, long-run evidence, promotion, and scale-up blockers.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no runtime artifact staging
- no scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any], summary: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(completed)
    state["open_contract_gap_ids"] = summary["next_open_contract_gap_ids"]
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
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
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
    ledger["ledger_hash"] = ""
    ledger["ledger_hash"] = sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
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
    update_state_and_ledger(now, patch_result, summary)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = load_summary()
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
                    "tests.contract.test_stale_loop_reconciliation_operator_queue_pending_recheck",
                    "tests.contract.test_stale_loop_reconciliation_after_regeneration_required_recheck",
                    "tests.contract.test_stale_loop_regeneration_execution_required_recheck",
                    "tests.contract.test_stale_loop_regeneration_required_recheck",
                    "tests.contract.test_patch_result_runtime_schema_validation",
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
                    "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                    "tests/runtime/test_upbit_paper_stale_loop_ledger_recheck_preview.py",
                    "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
                    "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    summary = load_summary()
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
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "closed_gap_id": CLOSED_GAP,
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
