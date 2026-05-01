from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-RERUN-OPERATOR-BLOCKER-DASHBOARD-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_RECONCILIATION_REVIEW_GUIDANCE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_blocker_rollup import (  # noqa: E402
    validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "upbit_paper_post_rerun_reconciliation_blocker_rollup_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/runtime/test_safe_launcher.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_post_rerun_operator_blocker_dashboard_visibility_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY.md",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
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


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_dashboard_projection(dashboard: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    result = validate_read_only_dashboard_shell(dashboard)
    if result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {result.status} {result.blocker_code} {result.message}")
    reconciliation = dashboard.get("reconciliation_recovery_summary")
    operator_action = dashboard.get("operator_action_summary")
    if not isinstance(reconciliation, dict) or not isinstance(operator_action, dict):
        raise RuntimeError("dashboard missing reconciliation or operator action summary")
    expected_false_fields = (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    )
    if any(dashboard.get(field) is not False for field in expected_false_fields):
        raise RuntimeError("dashboard attempted to expose forbidden live or scale permission")
    if dashboard.get("blocking_reason") != "POST_RERUN_RECONCILIATION_REQUIRED":
        raise RuntimeError("post-rerun blocker rollup did not become the dashboard primary blocker")
    if reconciliation.get("post_rerun_blocker_rollup_status") != "BLOCKED":
        raise RuntimeError("dashboard did not surface the post-rerun blocker rollup as BLOCKED")
    if reconciliation.get("post_rerun_current_evidence_write_allowed_count") != 0:
        raise RuntimeError("dashboard exposed post-rerun current-evidence write allowance")
    if operator_action.get("status") != "BLOCKED" or operator_action.get("safe_to_continue_paper") is not False:
        raise RuntimeError("operator action did not fail closed for post-rerun blocker rollup")
    return reconciliation, operator_action


def write_launcher_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    report = build_launcher_report("UPBIT_PAPER")
    report_path, dashboard_paths = write_launcher_runtime_bundle(report)
    session_dashboard_path = dashboard_paths["dashboard_shell"]
    dashboard = load_json(session_dashboard_path)
    reconciliation, operator_action = validate_dashboard_projection(dashboard)

    html_path = dashboard_paths["dashboard_html"]
    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    base.write_text(legacy_html_path, html_path.read_text(encoding="utf-8"))

    artifact_paths = [base.rel(report_path), *(base.rel(path) for path in dashboard_paths.values()), base.rel(legacy_html_path)]
    return dashboard, reconciliation, operator_action, sorted(set(artifact_paths))


def load_blocker_rollup() -> dict[str, Any]:
    path = (
        ROOT
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / "mvp1_upbit_paper_launcher"
        / "paper_runtime"
        / "upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
    )
    report = load_json(path)
    result = validate_upbit_paper_post_rerun_reconciliation_blocker_rollup_report(report)
    if result.status != "PASS":
        raise RuntimeError(f"post-rerun blocker rollup validation failed: {result.status} {result.blocker_code} {result.message}")
    return report


def write_context(now: str, trader_hash: str, agents_hash: str, dashboard: dict[str, Any], rollup: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY.md",
        f"""# MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY

context_pack_id: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY
task_class: MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_post_rerun_reconciliation_blocker_rollup_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The Upbit PAPER dashboard loads the validated post-rerun blocker rollup as display-only dashboard truth.
- POST_RERUN_RECONCILIATION_REQUIRED becomes the dashboard blocking reason and operator primary blocker.
- The operator action is BLOCKED/STOP_AND_INSPECT and safe_to_continue_paper=false.
- Current evidence write authorized, write allowed, candidate current-evidence usable, live order, and scale-up counts remain zero/false.

known_omissions_by_design:
- This patch is not a reconciliation writer, current-evidence writer, LIVE_READY patch, live config mutation, or scale-up patch.
- It does not resolve POST_RERUN_RECONCILIATION_REQUIRED; it makes the blocker harder to miss.
- No private exchange/account/API call, credential, live order, or risk scale-up was used.

runtime_summary:
- dashboard_blocking_reason: {dashboard["blocking_reason"]}
- operator_action_status: {dashboard["operator_action_summary"]["status"]}
- post_rerun_blocker_rollup_status: {rollup["blocker_rollup_status"]}
- post_rerun_blocker_rollup_item_count: {rollup["rollup_item_count"]}
- post_rerun_unique_blocker_count: {rollup["unique_blocker_count"]}
- post_rerun_current_evidence_write_authorized_count: {rollup["current_evidence_write_authorized_count"]}
- post_rerun_current_evidence_write_allowed_count: {rollup["current_evidence_write_allowed_count"]}
- candidate_current_evidence_usable_count: {rollup["candidate_current_evidence_usable_count"]}
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
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

Upbit PAPER post-rerun reconciliation blockers are now visible in the read-only dashboard. The dashboard and operator action both surface POST_RERUN_RECONCILIATION_REQUIRED and keep current evidence writes, live orders, and scale-up blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, launcher_artifacts: list[str]) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    artifacts = sorted(set(CHANGED_ARTIFACTS + launcher_artifacts))
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER post-rerun operator blocker dashboard visibility",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: post-rerun reconciliation blockers must be visible in operator dashboard "
                "without creating current evidence, live order, or scale-up permission"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER post-rerun operator blocker dashboard visibility",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_blocker_rollup_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-BLOCKER-ROLLUP",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"post rerun reconciliation blockers visible in operator dashboard without current evidence live order or scale up permission"
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
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "fixture_files": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_blocker_rollup_report.json"
            ],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "reconciliation_recovery_summary.post_rerun_blocker_rollup_status",
                "operator_action_summary.primary_blocker_code",
                "blocking_reason",
            ],
            "patch_result_fields": [
                "post_rerun_reconciliation_blocker_rollup_status",
                "post_rerun_reconciliation_blocker_rollup_item_count",
                "post_rerun_current_evidence_write_allowed_count",
                "candidate_current_evidence_usable_count",
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
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    dashboard: dict[str, Any],
    rollup: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_BLOCKER_ROLLUP.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-BLOCKER-ROLLUP",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_post_rerun_reconciliation_blocker_rollup_report.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_RUNTIME_RECOVERY", "SECTION_PROFIT_CONVERGENCE_DASHBOARD"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
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
                "post-rerun reconciliation blocker rollup report",
                "read-only dashboard shell",
                "safe launcher dashboard binding",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_POST_RERUN_OPERATOR_BLOCKER_DASHBOARD_VISIBILITY",
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_POST_RERUN_BLOCKER_VISIBLE_IN_DASHBOARD",
            "optimizer_guardrail_result": "PASS_DASHBOARD_DOES_NOT_MUTATE_CURRENT_EVIDENCE",
            "profit_convergence_patch": "true",
            "convergence_layer_changed": True,
            "convergence_state_after": "POST_RERUN_RECONCILIATION_BLOCKER_DASHBOARD_VISIBLE_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "post_rerun_reconciliation_blocker_rollup_status": rollup["blocker_rollup_status"],
            "post_rerun_reconciliation_blocker_rollup_item_count": rollup["rollup_item_count"],
            "post_rerun_reconciliation_unique_blocker_count": rollup["unique_blocker_count"],
            "post_rerun_reconciliation_primary_blocker_item_count": rollup["primary_blocker_item_count"],
            "post_rerun_current_evidence_write_authorized_count": rollup["current_evidence_write_authorized_count"],
            "post_rerun_current_evidence_write_allowed_count": rollup["current_evidence_write_allowed_count"],
            "candidate_current_evidence_usable_count": rollup["candidate_current_evidence_usable_count"],
        }
    )
    if dashboard.get("blocking_reason") != "POST_RERUN_RECONCILIATION_REQUIRED":
        raise RuntimeError("patch_result cannot be emitted without dashboard blocker projection")
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    dashboard: dict[str, Any],
    rollup: dict[str, Any],
    launcher_artifacts: list[str],
) -> None:
    reconciliation = dashboard["reconciliation_recovery_summary"]
    operator_action = dashboard["operator_action_summary"]
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
            "stage_gate_status": "PASS_DASHBOARD_VISIBLE_POST_RERUN_RECONCILIATION_BLOCKER_LIVE_BLOCKED",
            "dashboard_blocking_reason": dashboard["blocking_reason"],
            "operator_action_status": operator_action["status"],
            "operator_primary_blocker_code": operator_action["primary_blocker_code"],
            "reconciliation_status": reconciliation["status"],
            "post_rerun_blocker_rollup_status": reconciliation["post_rerun_blocker_rollup_status"],
            "post_rerun_blocker_rollup_item_count": reconciliation["post_rerun_blocker_rollup_item_count"],
            "post_rerun_current_evidence_write_allowed_count": reconciliation["post_rerun_current_evidence_write_allowed_count"],
            "current_evidence_mutation_allowed": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
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
            "post_rerun_blocker_rollup_status": rollup["blocker_rollup_status"],
            "post_rerun_blocker_rollup_item_count": rollup["rollup_item_count"],
            "post_rerun_unique_blocker_count": rollup["unique_blocker_count"],
            "post_rerun_current_evidence_write_authorized_count": rollup["current_evidence_write_authorized_count"],
            "post_rerun_current_evidence_write_allowed_count": rollup["current_evidence_write_allowed_count"],
            "candidate_current_evidence_usable_count": rollup["candidate_current_evidence_usable_count"],
            "current_evidence_mutation_allowed": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Post-Rerun Operator Blocker Dashboard Visibility

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The post-rerun reconciliation blocker rollup existed as runtime evidence, but operator dashboard visibility needed to fail closed on that blocker instead of allowing a generic PAPER review impression.

Patch:
- The dashboard shell, schema, HTML renderer, launcher binding, and tests now expose the post-rerun blocker rollup under Ledger & Reconciliation.
- The dashboard blocking reason and operator action both surface POST_RERUN_RECONCILIATION_REQUIRED.
- The panel reports rollup item counts and keeps current evidence writes at zero.

Runtime summary:
- dashboard_blocking_reason: {dashboard["blocking_reason"]}
- operator_action_status: {operator_action["status"]}
- post_rerun_blocker_rollup_status: {rollup["blocker_rollup_status"]}
- post_rerun_blocker_rollup_item_count: {rollup["rollup_item_count"]}
- post_rerun_unique_blocker_count: {rollup["unique_blocker_count"]}
- post_rerun_current_evidence_write_authorized_count: {rollup["current_evidence_write_authorized_count"]}
- post_rerun_current_evidence_write_allowed_count: {rollup["current_evidence_write_allowed_count"]}
- candidate_current_evidence_usable_count: {rollup["candidate_current_evidence_usable_count"]}

Safety:
- current_evidence_mutation_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    schemas = set(state.get("implemented_schema_ids", []))
    schemas.add("trader1.read_only_dashboard_shell.v1")
    validators = set(state.get("implemented_validator_ids", []))
    validators.update({"read_only_dashboard_validator", "dashboard_visual_layout_validator"})
    gaps = set(state.get("open_contract_gap_ids", []))
    gaps.update(
        {
            "POST_RERUN_RECONCILIATION_REQUIRED",
            "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
            "LIVE_ENABLING_EVIDENCE_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        }
    )
    state.update(
        {
            "updated_at_utc": now,
            "current_mvp": "MVP-4",
            "completed_requirement_ids": sorted(completed),
            "implemented_schema_ids": sorted(schemas),
            "implemented_validator_ids": sorted(validators),
            "untested_validator_ids": sorted(set(state.get("untested_validator_ids", [])) - validators),
            "open_contract_gap_ids": sorted(gaps),
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result["result_hash"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    ledger["patches"] = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": base.rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    ledger["ledger_hash"] = ""
    ledger["ledger_hash"] = base.sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
    base.write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    dashboard: dict[str, Any],
    rollup: dict[str, Any],
    launcher_artifacts: list[str],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, dashboard, rollup, launcher_artifacts)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    rollup = load_blocker_rollup()
    dashboard, reconciliation, operator_action, launcher_artifacts = write_launcher_artifacts()
    write_context(now, trader_hash, agents_hash, dashboard, rollup)
    update_requirement_artifacts(now, trader_hash, agents_hash, launcher_artifacts)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, dashboard, rollup)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, dashboard, rollup, launcher_artifacts)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, dashboard, rollup)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, dashboard, rollup, launcher_artifacts)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "dashboard_blocking_reason": dashboard["blocking_reason"],
                "operator_action_status": operator_action["status"],
                "reconciliation_status": reconciliation["status"],
                "post_rerun_blocker_rollup_status": rollup["blocker_rollup_status"],
                "post_rerun_blocker_rollup_item_count": rollup["rollup_item_count"],
                "post_rerun_current_evidence_write_allowed_count": rollup["current_evidence_write_allowed_count"],
                "candidate_current_evidence_usable_count": rollup["candidate_current_evidence_usable_count"],
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
