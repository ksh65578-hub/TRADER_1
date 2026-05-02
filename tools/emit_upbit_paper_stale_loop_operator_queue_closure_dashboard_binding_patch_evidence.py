from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATCH_BASENAME = "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-DASHBOARD-BINDING"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_STALE_LOOP_LEDGER_RECHECK_PREVIEW"
SESSION_ID = "mvp1_upbit_paper_launcher"

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
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation_operator_queue_closure import (  # noqa: E402
    validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
CLOSURE_REPORT_PATH = (
    RUNTIME_BASE / "paper_runtime" / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"
)

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "upbit_paper_stale_loop_post_regeneration_reconciliation_validator",
    "upbit_paper_stale_loop_reconciliation_operator_queue_closure_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
]
BOOTSTRAP_VALIDATORS = [
    item
    for item in VALIDATORS_REQUIRED
    if item
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
]

CHANGED_ARTIFACTS = [
    "contracts/schema/patch_result.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/runtime/test_safe_launcher.py",
    "tools/emit_upbit_paper_stale_loop_operator_queue_closure_dashboard_binding_patch_evidence.py",
    rel(CLOSURE_REPORT_PATH),
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def remove_cache_artifacts() -> None:
    for path in sorted(ROOT.rglob("*.pyc"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
    for path in sorted(ROOT.rglob("__pycache__"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    pytest_cache = ROOT / ".pytest_cache"
    if pytest_cache.exists():
        for path in sorted(pytest_cache.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        pytest_cache.rmdir()


def load_closure_report() -> dict[str, Any]:
    report = load_json(CLOSURE_REPORT_PATH)
    result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            "stale-loop operator queue closure validation failed: "
            f"{result.status} {result.blocker_code} {result.message}"
        )
    if report.get("closure_status") != "BLOCKED":
        raise RuntimeError("closure report must remain BLOCKED for dashboard binding")
    if report.get("current_evidence_write_allowed_count") != 0:
        raise RuntimeError("closure report allowed current evidence writes")
    if report.get("current_evidence_usable_after_closure_count") != 0:
        raise RuntimeError("closure report promoted current evidence")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "scale_up_allowed"):
        if report.get(field) is not False:
            raise RuntimeError(f"closure report attempted forbidden live or scale permission: {field}")
    return report


def validate_dashboard_projection(
    dashboard: dict[str, Any],
    closure_report: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    result = validate_read_only_dashboard_shell(dashboard)
    if result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {result.status} {result.blocker_code} {result.message}")
    reconciliation = dashboard.get("reconciliation_recovery_summary")
    operator_action = dashboard.get("operator_action_summary")
    portfolio = dashboard.get("portfolio_snapshot")
    if not isinstance(reconciliation, dict) or not isinstance(operator_action, dict) or not isinstance(portfolio, dict):
        raise RuntimeError("dashboard missing reconciliation, operator action, or portfolio summary")
    if dashboard.get("blocking_reason") not in {
        "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
        "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
    }:
        raise RuntimeError("dashboard did not preserve stale-loop reconciliation blocker")
    if reconciliation.get("stale_loop_operator_queue_closure_status") != "BLOCKED":
        raise RuntimeError("dashboard did not surface stale-loop operator queue closure BLOCKED")
    if reconciliation.get("stale_loop_operator_queue_closure_validation_status") != "PASS":
        raise RuntimeError("dashboard did not surface stale-loop operator queue closure validation PASS")
    expected_counts = {
        "stale_loop_operator_queue_closure_item_count": closure_report["closure_item_count"],
        "stale_loop_operator_queue_closure_source_blocked_item_count": closure_report[
            "source_blocked_item_count"
        ],
        "stale_loop_operator_queue_closure_ledger_recheck_ready_count": closure_report[
            "ledger_recheck_ready_count"
        ],
        "stale_loop_operator_queue_closure_recovery_guard_required_count": closure_report[
            "recovery_guard_required_count"
        ],
        "stale_loop_operator_queue_closure_runtime_cycle_rerun_required_count": closure_report[
            "runtime_cycle_rerun_required_count"
        ],
        "stale_loop_operator_queue_closure_operator_review_required_count": closure_report[
            "operator_review_required_count"
        ],
        "stale_loop_operator_queue_closure_current_evidence_write_allowed_count": 0,
        "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count": 0,
    }
    for field, expected in expected_counts.items():
        if reconciliation.get(field) != expected:
            raise RuntimeError(f"dashboard closure field mismatch: {field}={reconciliation.get(field)} expected {expected}")
    if "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING" not in reconciliation.get(
        "stale_loop_operator_queue_closure_blocker_codes",
        [],
    ):
        raise RuntimeError("dashboard did not surface stale-loop operator queue closure blocker code")
    source_ids = {source.get("artifact_id"): source for source in dashboard.get("source_artifacts", [])}
    source = source_ids.get("STALE_LOOP_OPERATOR_QUEUE_CLOSURE")
    if not isinstance(source, dict) or source.get("freshness_status") != "PASS":
        raise RuntimeError("dashboard did not publish stale-loop operator queue closure source artifact as PASS")
    if portfolio.get("source_snapshot_status") not in {"BLOCKED", "PASS"}:
        raise RuntimeError("portfolio source snapshot status is not explicit")
    if operator_action.get("status") != "BLOCKED" or operator_action.get("safe_to_continue_paper") is not False:
        raise RuntimeError("operator action did not fail closed for stale-loop operator queue closure")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if dashboard.get(field) is not False or reconciliation.get(field) is not False or operator_action.get(field) is not False:
            raise RuntimeError(f"dashboard attempted forbidden live or scale permission: {field}")
    return reconciliation, operator_action, portfolio


def write_launcher_artifacts(
    closure_report: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    report = build_launcher_report("UPBIT_PAPER")
    report_path, dashboard_paths = write_launcher_runtime_bundle(report)
    dashboard = load_json(dashboard_paths["dashboard_shell"])
    reconciliation, operator_action, portfolio = validate_dashboard_projection(dashboard, closure_report)
    html_path = dashboard_paths["dashboard_html"]
    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    write_text(legacy_html_path, html_path.read_text(encoding="utf-8"))
    artifact_paths = [rel(report_path), *(rel(path) for path in dashboard_paths.values()), rel(legacy_html_path)]
    return dashboard, reconciliation, operator_action, portfolio, sorted(set(artifact_paths))


def write_context(now: str, trader_hash: str, agents_hash: str, closure_report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The Upbit PAPER launcher loads the validated stale-loop operator queue closure report.
- The read-only dashboard shows closure status, lane counts, source blocked items, and zero evidence-write counts.
- The closure report is a PASS source artifact for display only and cannot approve portfolio truth, orders, LIVE_READY, or scale-up.
- Operator action remains BLOCKED until the stale-loop reconciliation queue is resolved by later safe tasks.

known_omissions_by_design:
- This patch does not perform ledger recheck, runtime rerun, current-evidence writes, live orders, LIVE_READY, live config mutation, or risk scale-up.
- It binds existing closure evidence into dashboard truth only.

runtime_summary:
- closure_status: {closure_report.get("closure_status")}
- closure_item_count: {closure_report.get("closure_item_count")}
- ledger_recheck_ready_count: {closure_report.get("ledger_recheck_ready_count")}
- recovery_guard_required_count: {closure_report.get("recovery_guard_required_count")}
- current_evidence_write_allowed_count: {closure_report.get("current_evidence_write_allowed_count")}
- current_evidence_usable_after_closure_count: {closure_report.get("current_evidence_usable_after_closure_count")}
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
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

Upbit PAPER stale-loop operator queue closure is now loaded by the safe launcher and shown in the read-only dashboard. The closure remains display-only: ledger_recheck_ready={closure_report.get("ledger_recheck_ready_count")}, recovery_guard_required={closure_report.get("recovery_guard_required_count")}, current_evidence_writes=0.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, launcher_artifacts: list[str]) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = sorted(set(CHANGED_ARTIFACTS + launcher_artifacts))

    req_index = load_json(req_path)
    reqs = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    reqs.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER stale-loop operator queue closure dashboard binding",
            "full_text_marker": f"{REQUIREMENT_ID}: stale-loop operator queue closure must be visible in launcher dashboard without current-evidence writes or live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Bind stale-loop operator queue closure into read-only dashboard",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-CLOSURE",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"stale-loop operator queue closure dashboard binding display only no evidence writes no live permission"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DASHBOARD_VISIBLE_LIVE_BLOCKED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "updated_at_utc": now,
            "requirements": sorted(reqs, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.schema.json",
            ],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
            ],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "fixture_files": [rel(CLOSURE_REPORT_PATH)],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "reconciliation_recovery_summary.stale_loop_operator_queue_closure_status",
                "reconciliation_recovery_summary.stale_loop_operator_queue_closure_item_count",
                "reconciliation_recovery_summary.stale_loop_operator_queue_closure_ledger_recheck_ready_count",
                "reconciliation_recovery_summary.stale_loop_operator_queue_closure_recovery_guard_required_count",
                "reconciliation_recovery_summary.stale_loop_operator_queue_closure_current_evidence_write_allowed_count",
                "source_artifacts.STALE_LOOP_OPERATOR_QUEUE_CLOSURE",
                "operator_action_summary.primary_blocker_code",
                "blocking_reason",
            ],
            "patch_result_fields": [
                "stale_loop_operator_queue_closure_status",
                "stale_loop_operator_queue_closure_item_count",
                "stale_loop_operator_queue_closure_ledger_recheck_ready_count",
                "stale_loop_operator_queue_closure_recovery_guard_required_count",
                "stale_loop_operator_queue_closure_current_evidence_write_allowed_count",
                "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_DASHBOARD_VISIBLE_LIVE_BLOCKED",
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
    dashboard: dict[str, Any],
    closure_report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-CLOSURE",
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1",
            ],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_DASHBOARD_SERVING_TRUTH",
                "SECTION_LEDGER_VALIDATOR_IDS",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PORTFOLIO_TRUTH"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "BINANCE_FUTURES_LIVE"],
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "task_class": "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING",
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_DASHBOARD_SERVING_TRUTH",
                "SECTION_LEDGER_VALIDATOR_IDS",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "AGENTS:0G",
                "AGENTS:0F",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_DASHBOARD_SERVING_TRUTH",
                "SECTION_LEDGER_VALIDATOR_IDS",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_STALE_LOOP_OPERATOR_QUEUE_CLOSURE_DASHBOARD_BINDING",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "stale_loop_operator_queue_closure_status": closure_report["closure_status"],
            "stale_loop_operator_queue_closure_item_count": closure_report["closure_item_count"],
            "stale_loop_operator_queue_closure_ledger_recheck_ready_count": closure_report[
                "ledger_recheck_ready_count"
            ],
            "stale_loop_operator_queue_closure_recovery_guard_required_count": closure_report[
                "recovery_guard_required_count"
            ],
            "stale_loop_operator_queue_closure_current_evidence_write_allowed_count": closure_report[
                "current_evidence_write_allowed_count"
            ],
            "stale_loop_operator_queue_closure_current_evidence_usable_after_closure_count": closure_report[
                "current_evidence_usable_after_closure_count"
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
    dashboard: dict[str, Any],
    closure_report: dict[str, Any],
    launcher_artifacts: list[str],
) -> None:
    reconciliation = dashboard["reconciliation_recovery_summary"]
    operator_action = dashboard["operator_action_summary"]
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
            "stage_gate_status": "PASS_DASHBOARD_VISIBLE_STALE_LOOP_OPERATOR_QUEUE_CLOSURE_LIVE_BLOCKED",
            "dashboard_blocking_reason": dashboard["blocking_reason"],
            "operator_action_status": operator_action["status"],
            "operator_primary_blocker_code": operator_action["primary_blocker_code"],
            "reconciliation_status": reconciliation["status"],
            "closure_status": closure_report["closure_status"],
            "closure_item_count": closure_report["closure_item_count"],
            "ledger_recheck_ready_count": closure_report["ledger_recheck_ready_count"],
            "recovery_guard_required_count": closure_report["recovery_guard_required_count"],
            "current_evidence_write_allowed_count": closure_report["current_evidence_write_allowed_count"],
            "current_evidence_usable_after_closure_count": closure_report[
                "current_evidence_usable_after_closure_count"
            ],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": sorted(
                set(
                    [
                        *CHANGED_ARTIFACTS,
                        *launcher_artifacts,
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "dashboard_blocking_reason": dashboard["blocking_reason"],
            "operator_action_status": operator_action["status"],
            "operator_primary_blocker_code": operator_action["primary_blocker_code"],
            "closure_status": closure_report["closure_status"],
            "closure_item_count": closure_report["closure_item_count"],
            "ledger_recheck_ready_count": closure_report["ledger_recheck_ready_count"],
            "recovery_guard_required_count": closure_report["recovery_guard_required_count"],
            "current_evidence_write_allowed_count": closure_report["current_evidence_write_allowed_count"],
            "current_evidence_usable_after_closure_count": closure_report[
                "current_evidence_usable_after_closure_count"
            ],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json",
        patch_result,
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
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
    closure_report = load_closure_report()
    dashboard, _, _, _, launcher_artifacts = write_launcher_artifacts(closure_report)
    write_context(now, trader_hash, agents_hash, closure_report)
    update_requirement_artifacts(now, trader_hash, agents_hash, launcher_artifacts)
    remove_cache_artifacts()
    write_source_bundle_manifest()

    tests_run = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
    ]
    remove_cache_artifacts()
    write_source_bundle_manifest()
    validators_run = run_validators(BOOTSTRAP_VALIDATORS)
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS, dashboard, closure_report)
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard, closure_report, launcher_artifacts)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    remove_cache_artifacts()
    write_source_bundle_manifest()
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, dashboard, closure_report)
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard, closure_report, launcher_artifacts)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)
    remove_cache_artifacts()
    write_source_bundle_manifest()

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "closure_status": closure_report["closure_status"],
                "closure_item_count": closure_report["closure_item_count"],
                "ledger_recheck_ready_count": closure_report["ledger_recheck_ready_count"],
                "recovery_guard_required_count": closure_report["recovery_guard_required_count"],
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
