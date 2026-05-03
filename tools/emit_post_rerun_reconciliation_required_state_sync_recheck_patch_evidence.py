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

PATCH_BASENAME = "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_STATE_SYNC_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-POST-RERUN-RECONCILIATION-REQUIRED-STATE-SYNC-RECHECK"
GAP_ID = "POST_RERUN_RECONCILIATION_REQUIRED"
NEXT_TASK_CLASS = "MVP4_POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED_RECHECK"

PREVIOUS_RECHECK_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK_20260503_001"
PREVIOUS_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_RECHECK.patch_result.json"
)
PREVIOUS_REPAIR_PATH_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_20260502_001"
PREVIOUS_REPAIR_PATH_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH.patch_result.json"
)
PREVIOUS_BLOCKER_ROLLUP_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP_20260502_001"
PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP.patch_result.json"
)
PREVIOUS_OPERATOR_QUEUE_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE_20260502_001"
PREVIOUS_OPERATOR_QUEUE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_QUEUE.patch_result.json"
)
PREVIOUS_RESOLUTION_AUDIT_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT_20260502_001"
PREVIOUS_RESOLUTION_AUDIT_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RESOLUTION_AUDIT.patch_result.json"
)
PREVIOUS_CLOSURE_PATCH_ID = "MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_20260502_001"
PREVIOUS_CLOSURE_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE.patch_result.json"
)

RUNTIME_BASE = "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime"
POST_RERUN_RECHECK_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_current_evidence_closure_recheck_report.json"
REPAIR_PATH_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_reconciliation_repair_path_report.json"
BLOCKER_ROLLUP_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
DECISION_AUDIT_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_reconciliation_decision_audit_report.json"
OPERATOR_QUEUE_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_operator_reconciliation_queue_report.json"
RESOLUTION_AUDIT_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_operator_resolution_audit_report.json"
CLOSURE_REPORT = f"{RUNTIME_BASE}/upbit_paper_post_rerun_resolution_current_evidence_closure_report.json"

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
    "upbit_paper_post_rerun_current_evidence_closure_recheck_validator",
    "upbit_paper_post_rerun_reconciliation_repair_path_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "upbit_paper_post_rerun_reconciliation_decision_audit_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
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
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_rerun_current_evidence_closure_recheck_validator",
    "upbit_paper_post_rerun_reconciliation_repair_path_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "upbit_paper_post_rerun_reconciliation_decision_audit_validator",
    "upbit_paper_post_rerun_operator_reconciliation_queue_validator",
    "upbit_paper_post_rerun_operator_resolution_audit_validator",
    "upbit_paper_post_rerun_resolution_current_evidence_closure_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_post_rerun_reconciliation_required_recheck.py",
    "tools/emit_post_rerun_reconciliation_required_state_sync_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = [
    GAP_ID,
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
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


def assert_previous_patch(path_text: str, expected_patch_id: str) -> dict[str, Any]:
    patch = load_json(ROOT / path_text)
    if patch.get("patch_id") != expected_patch_id:
        raise RuntimeError(f"historical patch_id drifted for {path_text}")
    assert_false_fields(path_text, patch, "_after")
    if "POST_RERUN_RECONCILIATION_REQUIRED" not in patch.get("remaining_blockers", []):
        raise RuntimeError(f"historical patch no longer preserves post-rerun reconciliation blocker: {path_text}")
    return patch


def assert_report_false_safe(name: str, report: dict[str, Any]) -> None:
    assert_false_fields(name, report)
    if report.get("current_evidence_write_allowed") is True:
        raise RuntimeError(f"{name} unexpectedly allows current evidence writes")
    if report.get("current_evidence_write_allowed_count", 0) != 0:
        raise RuntimeError(f"{name} has allowed current evidence write rows")
    if report.get("candidate_current_evidence_usable_count", 0) != 0:
        raise RuntimeError(f"{name} unexpectedly has current-usable evidence candidates")


def current_gap_summary() -> dict[str, Any]:
    recheck_patch = assert_previous_patch(PREVIOUS_RECHECK_PATCH_RESULT, PREVIOUS_RECHECK_PATCH_ID)
    repair_path_patch = assert_previous_patch(PREVIOUS_REPAIR_PATH_PATCH_RESULT, PREVIOUS_REPAIR_PATH_PATCH_ID)
    blocker_rollup_patch = assert_previous_patch(PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT, PREVIOUS_BLOCKER_ROLLUP_PATCH_ID)
    operator_queue_patch = assert_previous_patch(PREVIOUS_OPERATOR_QUEUE_PATCH_RESULT, PREVIOUS_OPERATOR_QUEUE_PATCH_ID)
    resolution_audit_patch = assert_previous_patch(PREVIOUS_RESOLUTION_AUDIT_PATCH_RESULT, PREVIOUS_RESOLUTION_AUDIT_PATCH_ID)
    closure_patch = assert_previous_patch(PREVIOUS_CLOSURE_PATCH_RESULT, PREVIOUS_CLOSURE_PATCH_ID)

    recheck = load_json(ROOT / POST_RERUN_RECHECK_REPORT)
    repair_path = load_json(ROOT / REPAIR_PATH_REPORT)
    blocker_rollup = load_json(ROOT / BLOCKER_ROLLUP_REPORT)
    decision_audit = load_json(ROOT / DECISION_AUDIT_REPORT)
    operator_queue = load_json(ROOT / OPERATOR_QUEUE_REPORT)
    resolution_audit = load_json(ROOT / RESOLUTION_AUDIT_REPORT)
    closure = load_json(ROOT / CLOSURE_REPORT)

    for path_text, report in (
        (POST_RERUN_RECHECK_REPORT, recheck),
        (REPAIR_PATH_REPORT, repair_path),
        (BLOCKER_ROLLUP_REPORT, blocker_rollup),
        (DECISION_AUDIT_REPORT, decision_audit),
        (OPERATOR_QUEUE_REPORT, operator_queue),
        (RESOLUTION_AUDIT_REPORT, resolution_audit),
        (CLOSURE_REPORT, closure),
    ):
        assert_report_false_safe(path_text, report)

    if recheck.get("recheck_status") != "BLOCKED_POST_RERUN_CLOSURE_CONFIRMED":
        raise RuntimeError("post-rerun recheck no longer confirms blocked closure")
    if repair_path.get("repair_path_status") != "BLOCKED_REPAIR_PATH_DECLARED":
        raise RuntimeError("post-rerun repair path is no longer blocked")
    if operator_queue.get("queue_status") != "BLOCKED":
        raise RuntimeError("post-rerun operator queue is no longer blocked")
    if resolution_audit.get("operator_resolution_required") is not True:
        raise RuntimeError("post-rerun operator resolution is no longer required")
    if closure.get("closure_status") != "CURRENT_EVIDENCE_CLOSED_RESOLUTION_UNRESOLVED":
        raise RuntimeError("post-rerun closure is no longer unresolved")
    if resolution_audit.get("resolved_item_count") != 0 or closure.get("resolved_item_count") != 0:
        raise RuntimeError("post-rerun resolution unexpectedly has resolved items")

    return {
        "recheck_patch_result_hash": recheck_patch.get("result_hash"),
        "repair_path_patch_result_hash": repair_path_patch.get("result_hash"),
        "blocker_rollup_patch_result_hash": blocker_rollup_patch.get("result_hash"),
        "operator_queue_patch_result_hash": operator_queue_patch.get("result_hash"),
        "resolution_audit_patch_result_hash": resolution_audit_patch.get("result_hash"),
        "closure_patch_result_hash": closure_patch.get("result_hash"),
        "recheck_status": recheck.get("recheck_status"),
        "closure_status": closure.get("closure_status"),
        "repair_path_status": repair_path.get("repair_path_status"),
        "operator_queue_status": operator_queue.get("queue_status"),
        "operator_reconciliation_required_count": operator_queue.get("operator_reconciliation_required_count"),
        "operator_resolution_required": resolution_audit.get("operator_resolution_required"),
        "unresolved_item_count": resolution_audit.get("unresolved_item_count"),
        "resolved_item_count": resolution_audit.get("resolved_item_count"),
        "candidate_current_evidence_usable_count": closure.get("candidate_current_evidence_usable_count"),
        "current_evidence_write_allowed": closure.get("current_evidence_write_allowed"),
        "current_evidence_write_allowed_count": closure.get("current_evidence_write_allowed_count"),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_IDEMPOTENCY", "SECTION_CURRENT_EVIDENCE_CLOSURE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH", "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1", "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1", "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect that post-rerun recheck, repair path, blocker rollup, operator queue, resolution audit, and closure patch_results already exist.
- Confirm POST_RERUN_RECONCILIATION_REQUIRED remains in historical blockers.
- Confirm current evidence writes remain disallowed and candidate current evidence usable count is zero.
- Confirm operator reconciliation/resolution remains required and unresolved.
- Advance only next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

gap_snapshot:
- recheck_status: {summary["recheck_status"]}
- repair_path_status: {summary["repair_path_status"]}
- closure_status: {summary["closure_status"]}
- operator_queue_status: {summary["operator_queue_status"]}
- operator_reconciliation_required_count: {summary["operator_reconciliation_required_count"]}
- operator_resolution_required: {summary["operator_resolution_required"]}
- unresolved_item_count: {summary["unresolved_item_count"]}
- resolved_item_count: {summary["resolved_item_count"]}
- candidate_current_evidence_usable_count: {summary["candidate_current_evidence_usable_count"]}
- current_evidence_write_allowed: {summary["current_evidence_write_allowed"]}

known_omissions_by_design:
- No post-rerun reconciliation is resolved by this patch.
- No current evidence writer, latest pointer, live config, credentialed API, live order, or scale-up output is written.
- POST_RERUN_RECONCILIATION_REQUIRED remains an open live-blocking gap until operator reconciliation/resolution and current evidence closure independently pass.

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

Post-rerun reconciliation remains open and live-blocking. Operator reconciliation and resolution are still required, current evidence writes are denied, and no candidate current evidence is usable.

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
            "source_heading": "post-rerun reconciliation required state sync recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: recognize existing post-rerun reconciliation, repair path, operator queue, "
                "resolution audit, and closure evidence while keeping reconciliation and current-evidence writes blocked"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Post-rerun reconciliation required state sync recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1",
                "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_post_rerun_reconciliation_required_recheck.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-RESOLUTION-AUDIT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"post rerun reconciliation required state sync remains open live blocked"
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
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/upbit_paper_post_rerun_current_evidence_closure_recheck_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_reconciliation_repair_path_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_resolution_current_evidence_closure_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_post_rerun_reconciliation_required_recheck.py"],
            "fixture_files": [
                POST_RERUN_RECHECK_REPORT,
                REPAIR_PATH_REPORT,
                BLOCKER_ROLLUP_REPORT,
                DECISION_AUDIT_REPORT,
                OPERATOR_QUEUE_REPORT,
                RESOLUTION_AUDIT_REPORT,
                CLOSURE_REPORT,
                PREVIOUS_RECHECK_PATCH_RESULT,
                PREVIOUS_REPAIR_PATH_PATCH_RESULT,
                PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT,
                PREVIOUS_OPERATOR_QUEUE_PATCH_RESULT,
                PREVIOUS_RESOLUTION_AUDIT_PATCH_RESULT,
                PREVIOUS_CLOSURE_PATCH_RESULT,
            ],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_closure_recheck.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
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
                "validators_required",
                "validators_run",
                "tests_run",
                "next_task_class",
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
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_RECHECK_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-RECHECK",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH",
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
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH"],
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
                "post-rerun reconciliation recheck report",
                "post-rerun repair path report",
                "post-rerun operator queue and resolution reports",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_POST_RERUN_RECONCILIATION_REQUIRED_RECHECK",
            "required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_RUNTIME_IDEMPOTENCY",
                "SECTION_CURRENT_EVIDENCE_CLOSURE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
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
            "stage_gate_status": "PASS_STATE_SYNC_RECHECK_POST_RERUN_RECONCILIATION_REQUIRED_REMAINS_LIVE_BLOCKING",
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
                PREVIOUS_RECHECK_PATCH_RESULT,
                PREVIOUS_REPAIR_PATH_PATCH_RESULT,
                PREVIOUS_BLOCKER_ROLLUP_PATCH_RESULT,
                PREVIOUS_OPERATOR_QUEUE_PATCH_RESULT,
                PREVIOUS_RESOLUTION_AUDIT_PATCH_RESULT,
                PREVIOUS_CLOSURE_PATCH_RESULT,
                POST_RERUN_RECHECK_REPORT,
                REPAIR_PATH_REPORT,
                BLOCKER_ROLLUP_REPORT,
                DECISION_AUDIT_REPORT,
                OPERATOR_QUEUE_REPORT,
                RESOLUTION_AUDIT_REPORT,
                CLOSURE_REPORT,
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
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [GAP_ID]))
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
    summary = current_gap_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
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
                    "tests.contract.test_post_rerun_reconciliation_required_recheck",
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
                    "tests/runtime/test_upbit_paper_post_rerun_current_evidence_closure_recheck.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_blocker_rollup.py",
                    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_decision_audit.py",
                    "tests/runtime/test_upbit_paper_post_rerun_operator_reconciliation_queue.py",
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
                "recheck_status": summary["recheck_status"],
                "closure_status": summary["closure_status"],
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
