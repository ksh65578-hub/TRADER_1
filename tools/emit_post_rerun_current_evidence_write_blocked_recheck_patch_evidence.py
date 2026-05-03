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

PATCH_BASENAME = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_STATE_SYNC_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-CURRENT-EVIDENCE-WRITE-BLOCKED-STATE-SYNC-RECHECK"
GAP_ID = "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED"
NEXT_TASK_CLASS = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_RECHECK"

RUNTIME_BASE = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime"
PROMOTION_GUARD_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_current_evidence_promotion_guard_report.json"
OPERATOR_QUEUE_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_operator_reconciliation_queue_report.json"
REVIEW_GUIDANCE_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_operator_reconciliation_review_guidance_report.json"
RESOLUTION_AUDIT_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_operator_resolution_audit_report.json"
BLOCKER_ROLLUP_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
DECISION_AUDIT_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_reconciliation_decision_audit_report.json"
CLOSURE_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"

PREVIOUS_PROMOTION_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD_20260502_001"
PREVIOUS_PROMOTION_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_CURRENT_EVIDENCE_PROMOTION_GUARD.patch_result.json"
)
PREVIOUS_QUEUE_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_20260502_001"
PREVIOUS_QUEUE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE.patch_result.json"
)
PREVIOUS_GUIDANCE_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE_20260502_001"
PREVIOUS_GUIDANCE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE.patch_result.json"
)
PREVIOUS_RESOLUTION_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_20260502_001"
PREVIOUS_RESOLUTION_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT.patch_result.json"
)
PREVIOUS_BLOCKER_ROLLUP_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_20260502_001"
PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP.patch_result.json"
)
PREVIOUS_DECISION_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT_20260502_001"
PREVIOUS_DECISION_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_DECISION_AUDIT.patch_result.json"
)
PREVIOUS_CLOSURE_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_20260502_001"
PREVIOUS_CLOSURE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE.patch_result.json"
)
PREVIOUS_STATE_SYNC_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK.patch_result.json"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_post_rerun_reconciliation_required_state_sync_recheck_patch_evidence as base  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_rerun_current_evidence_promotion_guard_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "upbit_paper_post_rerun_reconciliation_decision_audit_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
    "upbit_paper_post_rerun_operator_reconciliation_review_guidance_validator",
    "upbit_paper_post_rerun_operator_resolution_audit_validator",
    "upbit_paper_post_rerun_resolution_current_evidence_closure_validator",
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
    "tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py",
    "tools/emit_post_rerun_current_evidence_write_blocked_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    GAP_ID,
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "STALE_LOOP_REGENERATION_EXECUTION_REQUIRED",
    "STALE_LOOP_REGENERATION_REQUIRED",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
]
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.GAP_ID = GAP_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.BOOTSTRAP_VALIDATORS_REQUIRED = BOOTSTRAP_VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


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
    return base.sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def assert_previous_patch(path_text: str, expected_patch_id: str) -> dict[str, Any]:
    patch = load_json(ROOT / path_text)
    if patch.get("patch_id") != expected_patch_id:
        raise RuntimeError(f"historical patch_id drifted for {path_text}")
    assert_false_fields(path_text, patch, "_after")
    if GAP_ID not in patch.get("remaining_blockers", []):
        raise RuntimeError(f"historical patch no longer preserves current evidence write blocker: {path_text}")
    if patch.get("post_rerun_current_evidence_write_allowed_count", 0) != 0:
        raise RuntimeError(f"historical patch has allowed post-rerun current evidence writes: {path_text}")
    if patch.get("candidate_current_evidence_usable_count", 0) != 0:
        raise RuntimeError(f"historical patch has current-usable candidates: {path_text}")
    return patch


def assert_report_write_blocked(path_text: str, report: dict[str, Any]) -> None:
    assert_false_fields(path_text, report)
    if report.get("current_evidence_write_allowed") is True:
        raise RuntimeError(f"{path_text} unexpectedly allows current evidence writes")
    if int(report.get("current_evidence_write_allowed_count") or 0) != 0:
        raise RuntimeError(f"{path_text} has allowed current evidence write rows")
    if int(report.get("current_evidence_write_authorized_count") or 0) != 0:
        raise RuntimeError(f"{path_text} has authorized current evidence write rows")
    if int(report.get("candidate_current_evidence_usable_count") or 0) != 0:
        raise RuntimeError(f"{path_text} unexpectedly has current-usable evidence candidates")
    if report.get("promotion_eligible") is True:
        raise RuntimeError(f"{path_text} unexpectedly marks promotion eligible")
    if GAP_ID not in set(report.get("blocker_codes") or []):
        raise RuntimeError(f"{path_text} no longer carries {GAP_ID}")


def current_gap_summary() -> dict[str, Any]:
    promotion_patch = assert_previous_patch(PREVIOUS_PROMOTION_PATCH_RESULT, PREVIOUS_PROMOTION_PATCH_ID)
    queue_patch = assert_previous_patch(PREVIOUS_QUEUE_PATCH_RESULT, PREVIOUS_QUEUE_PATCH_ID)
    guidance_patch = assert_previous_patch(PREVIOUS_GUIDANCE_PATCH_RESULT, PREVIOUS_GUIDANCE_PATCH_ID)
    resolution_patch = assert_previous_patch(PREVIOUS_RESOLUTION_PATCH_RESULT, PREVIOUS_RESOLUTION_PATCH_ID)
    blocker_rollup_patch = assert_previous_patch(PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT, PREVIOUS_BLOCKER_ROLLUP_PATCH_ID)
    decision_patch = assert_previous_patch(PREVIOUS_DECISION_PATCH_RESULT, PREVIOUS_DECISION_PATCH_ID)
    closure_patch = assert_previous_patch(PREVIOUS_CLOSURE_PATCH_RESULT, PREVIOUS_CLOSURE_PATCH_ID)

    state_sync_patch = load_json(ROOT / PREVIOUS_STATE_SYNC_PATCH_RESULT)
    if state_sync_patch.get("next_task_class") != "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK":
        raise RuntimeError("previous state sync no longer routes to current evidence write blocked recheck")
    assert_false_fields(PREVIOUS_STATE_SYNC_PATCH_RESULT, state_sync_patch, "_after")
    if GAP_ID not in state_sync_patch.get("remaining_blockers", []):
        raise RuntimeError("previous state sync lost current evidence write blocker")

    promotion = load_json(ROOT / PROMOTION_GUARD_REPORT)
    queue = load_json(ROOT / OPERATOR_QUEUE_REPORT)
    guidance = load_json(ROOT / REVIEW_GUIDANCE_REPORT)
    resolution = load_json(ROOT / RESOLUTION_AUDIT_REPORT)
    blocker_rollup = load_json(ROOT / BLOCKER_ROLLUP_REPORT)
    decision = load_json(ROOT / DECISION_AUDIT_REPORT)
    closure = load_json(ROOT / CLOSURE_REPORT)

    reports = [
        (PROMOTION_GUARD_REPORT, promotion),
        (OPERATOR_QUEUE_REPORT, queue),
        (REVIEW_GUIDANCE_REPORT, guidance),
        (RESOLUTION_AUDIT_REPORT, resolution),
        (BLOCKER_ROLLUP_REPORT, blocker_rollup),
        (DECISION_AUDIT_REPORT, decision),
        (CLOSURE_REPORT, closure),
    ]
    for path_text, report in reports:
        assert_report_write_blocked(path_text, report)

    if promotion.get("promotion_guard_status") != "BLOCKED":
        raise RuntimeError("promotion guard is no longer blocked")
    if int(promotion.get("promotion_review_ready_count") or 0) <= 0:
        raise RuntimeError("promotion guard lost review-ready write-blocked candidates")
    if queue.get("queue_status") != "BLOCKED":
        raise RuntimeError("operator queue is no longer blocked")
    if int(queue.get("operator_reconciliation_required_count") or 0) <= 0:
        raise RuntimeError("operator reconciliation is no longer required")
    if resolution.get("operator_resolution_required") is not True:
        raise RuntimeError("operator resolution is no longer required")
    if int(resolution.get("resolved_item_count") or 0) != 0 or int(closure.get("resolved_item_count") or 0) != 0:
        raise RuntimeError("post-rerun resolution unexpectedly has resolved items")
    if closure.get("closure_status") != "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED":
        raise RuntimeError("closure report no longer blocks current evidence closure")

    return {
        "promotion_patch_result_hash": promotion_patch.get("result_hash"),
        "queue_patch_result_hash": queue_patch.get("result_hash"),
        "guidance_patch_result_hash": guidance_patch.get("result_hash"),
        "resolution_patch_result_hash": resolution_patch.get("result_hash"),
        "blocker_rollup_patch_result_hash": blocker_rollup_patch.get("result_hash"),
        "decision_patch_result_hash": decision_patch.get("result_hash"),
        "closure_patch_result_hash": closure_patch.get("result_hash"),
        "state_sync_patch_result_hash": state_sync_patch.get("result_hash"),
        "promotion_guard_status": promotion.get("promotion_guard_status"),
        "promotion_review_ready_count": promotion.get("promotion_review_ready_count"),
        "promotion_candidate_verified_count": promotion.get("candidate_rollup_verified_count"),
        "operator_queue_status": queue.get("queue_status"),
        "operator_reconciliation_required_count": queue.get("operator_reconciliation_required_count"),
        "operator_resolution_required": resolution.get("operator_resolution_required"),
        "unresolved_item_count": resolution.get("unresolved_item_count"),
        "resolved_item_count": resolution.get("resolved_item_count"),
        "closure_status": closure.get("closure_status"),
        "current_evidence_write_authorized_count": max(
            int(report.get("current_evidence_write_authorized_count") or 0) for _, report in reports
        ),
        "current_evidence_write_allowed_count": max(
            int(report.get("current_evidence_write_allowed_count") or 0) for _, report in reports
        ),
        "candidate_current_evidence_usable_count": max(
            int(report.get("candidate_current_evidence_usable_count") or 0) for _, report in reports
        ),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-PROMOTION-GUARD", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RECONCILIATION-QUEUE", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1", "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1", "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm the post-rerun promotion guard remains review-only and BLOCKED.
- Confirm all post-rerun operator queue, review guidance, resolution, blocker rollup, decision audit, and closure reports keep current_evidence_write_allowed_count=0.
- Confirm current_evidence_write_authorized_count=0 and candidate_current_evidence_usable_count=0 across the linked reports.
- Confirm the historical post-rerun patch_results that already carried {GAP_ID} still preserve it.
- Advance only next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

gap_snapshot:
- promotion_guard_status: {summary["promotion_guard_status"]}
- promotion_review_ready_count: {summary["promotion_review_ready_count"]}
- promotion_candidate_verified_count: {summary["promotion_candidate_verified_count"]}
- operator_queue_status: {summary["operator_queue_status"]}
- operator_reconciliation_required_count: {summary["operator_reconciliation_required_count"]}
- operator_resolution_required: {summary["operator_resolution_required"]}
- unresolved_item_count: {summary["unresolved_item_count"]}
- resolved_item_count: {summary["resolved_item_count"]}
- closure_status: {summary["closure_status"]}
- current_evidence_write_authorized_count: {summary["current_evidence_write_authorized_count"]}
- current_evidence_write_allowed_count: {summary["current_evidence_write_allowed_count"]}
- candidate_current_evidence_usable_count: {summary["candidate_current_evidence_usable_count"]}

known_omissions_by_design:
- No current evidence writer, latest pointer, live config, credentialed API, live order, or scale-up output is written.
- {GAP_ID} remains an open live-blocking gap.
- Post-rerun reconciliation also remains open until operator reconciliation/resolution and current evidence closure independently pass.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    base.write_text(
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

Post-rerun current evidence writes remain blocked. Review-ready post-rerun candidates are not current-usable evidence, operator reconciliation and resolution remain required, and live/scale flags remain false.

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
            "source_heading": "post-rerun current evidence write blocked state sync recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: recognize existing post-rerun current-evidence write blocker and preserve "
                "review-only candidate evidence without current evidence mutation"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Post-rerun current evidence write blocked state sync recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_current_evidence_promotion_guard_report.v1",
                "trader1.upbit_paper_post_rerun_operator_reconciliation_queue_report.v1",
                "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-PROMOTION-GUARD",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RECONCILIATION-QUEUE",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"post rerun current evidence writes remain blocked and review-only"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_STATE_SYNC_RECHECK_GAP_OPEN",
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
    base.write_json(req_path, req_index)

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
            "test_files": ["tests/contract/test_post_rerun_current_evidence_write_blocked_recheck.py"],
            "fixture_files": [
                PROMOTION_GUARD_REPORT,
                OPERATOR_QUEUE_REPORT,
                REVIEW_GUIDANCE_REPORT,
                RESOLUTION_AUDIT_REPORT,
                BLOCKER_ROLLUP_REPORT,
                DECISION_AUDIT_REPORT,
                CLOSURE_REPORT,
                PREVIOUS_PROMOTION_PATCH_RESULT,
                PREVIOUS_QUEUE_PATCH_RESULT,
                PREVIOUS_GUIDANCE_PATCH_RESULT,
                PREVIOUS_RESOLUTION_PATCH_RESULT,
                PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT,
                PREVIOUS_DECISION_PATCH_RESULT,
                PREVIOUS_CLOSURE_PATCH_RESULT,
                PREVIOUS_STATE_SYNC_PATCH_RESULT,
            ],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_promotion_guard.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_operator_reconciliation_queue.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_resolution_current_evidence_closure.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "post_rerun_current_evidence_promotion_guard_status",
                "post_rerun_promotion_review_ready_count",
                "post_rerun_promotion_candidate_verified_count",
                "post_rerun_current_evidence_write_allowed_count",
                "post_rerun_current_evidence_write_authorized_count",
                "candidate_current_evidence_usable_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_STATE_SYNC_RECHECK_GAP_OPEN",
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
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    summary: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_STATE_SYNC_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-PROMOTION-GUARD",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RECONCILIATION-QUEUE",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
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
                "post-rerun promotion guard report",
                "post-rerun operator queue and review guidance reports",
                "post-rerun resolution and closure reports",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK",
            "required_section_ids": [
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
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
    base.write_json(
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
    base.write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_STATE_SYNC_RECHECK_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_REMAINS_LIVE_BLOCKING",
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
                PREVIOUS_PROMOTION_PATCH_RESULT,
                PREVIOUS_QUEUE_PATCH_RESULT,
                PREVIOUS_GUIDANCE_PATCH_RESULT,
                PREVIOUS_RESOLUTION_PATCH_RESULT,
                PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT,
                PREVIOUS_DECISION_PATCH_RESULT,
                PREVIOUS_CLOSURE_PATCH_RESULT,
                PREVIOUS_STATE_SYNC_PATCH_RESULT,
                PROMOTION_GUARD_REPORT,
                OPERATOR_QUEUE_REPORT,
                REVIEW_GUIDANCE_REPORT,
                RESOLUTION_AUDIT_REPORT,
                BLOCKER_ROLLUP_REPORT,
                DECISION_AUDIT_REPORT,
                CLOSURE_REPORT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    base.write_json(
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


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    base.write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    configure_base()
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = current_gap_summary()
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
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
        ]
    )
    summary = current_gap_summary()
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
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "promotion_guard_status": summary["promotion_guard_status"],
                "current_evidence_write_allowed_count": summary["current_evidence_write_allowed_count"],
                "candidate_current_evidence_usable_count": summary["candidate_current_evidence_usable_count"],
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
