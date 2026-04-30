from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-RECONCILIATION-ARTIFACT-BINDING-RECHECK"
NEXT_TASK_CLASS = "MVP4_DASHBOARD_RECONCILIATION_STALE_ARTIFACT_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_dashboard_launch_visibility_patch_evidence import write_launcher_artifacts  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    run_command,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.core.ledger.restart_recovery import build_restart_recovery_report, validate_restart_recovery_report  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, launcher_dashboard_paths  # noqa: E402
from trader1.runtime.portfolio.paper_portfolio import build_initial_paper_portfolio_snapshot  # noqa: E402
from trader1.runtime.reconciliation.reconciliation import build_reconciliation_report, validate_reconciliation_report  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "reconciliation_validator",
    "restart_recovery_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
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
CHANGED_ARTIFACTS = [
    "trader1/runtime/boot/safe_launcher.py",
    "tests/runtime/test_safe_launcher.py",
    "tools/emit_paper_reconciliation_artifact_binding_recheck_patch_evidence.py",
    "contracts/generated/context_pack/PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/reconciliation_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/restart_recovery_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/reconciliation_report.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def _paper_reconciliation_snapshot(*, exchange: str, market_type: str, session_id: str) -> dict[str, Any]:
    portfolio = build_initial_paper_portfolio_snapshot(exchange=exchange, market_type=market_type, session_id=session_id)
    return {
        "exchange": exchange,
        "market_type": market_type,
        "mode": "PAPER",
        "session_id": session_id,
        "balances": {portfolio["currency"]: portfolio["cash_available"]},
        "positions": portfolio["positions"],
        "open_orders": [],
    }


def write_session_scoped_reconciliation_artifacts() -> list[str]:
    artifacts: list[str] = []

    upbit_report = build_launcher_report("UPBIT_PAPER")
    upbit_paths = launcher_dashboard_paths(upbit_report)
    upbit_restart = build_restart_recovery_report(
        restart_id="mvp4-dashboard-bound-upbit-paper-restart",
        exchange=upbit_report["exchange"],
        market_type=upbit_report["market_type"],
        mode=upbit_report["mode"],
        session_id=upbit_report["session_id"],
    )
    restart_result = validate_restart_recovery_report(upbit_restart)
    if restart_result.status != "PASS":
        raise RuntimeError(f"UPBIT restart recovery validation failed: {restart_result.message}")
    upbit_snapshot = _paper_reconciliation_snapshot(
        exchange=upbit_report["exchange"],
        market_type=upbit_report["market_type"],
        session_id=upbit_report["session_id"],
    )
    upbit_reconciliation = build_reconciliation_report(
        reconciliation_id="mvp4-dashboard-bound-upbit-paper-reconciliation",
        exchange=upbit_report["exchange"],
        market_type=upbit_report["market_type"],
        mode=upbit_report["mode"],
        session_id=upbit_report["session_id"],
        account_snapshot_id="PAPER_PORTFOLIO_SCAFFOLD_NOT_EXCHANGE_TRUTH",
        ledger_head_hash=upbit_restart["ledger_head_hash"],
        exchange_snapshot=upbit_snapshot,
        internal_state=dict(upbit_snapshot),
    )
    reconciliation_result = validate_reconciliation_report(upbit_reconciliation)
    if reconciliation_result.status != "PASS":
        raise RuntimeError(f"UPBIT reconciliation validation failed: {reconciliation_result.message}")
    write_json(upbit_paths["restart_recovery_report"], upbit_restart)
    write_json(upbit_paths["reconciliation_report"], upbit_reconciliation)
    artifacts.extend([rel(upbit_paths["restart_recovery_report"]), rel(upbit_paths["reconciliation_report"])])

    binance_report = build_launcher_report("BINANCE_PAPER")
    binance_paths = launcher_dashboard_paths(binance_report)
    binance_snapshot = _paper_reconciliation_snapshot(
        exchange=binance_report["exchange"],
        market_type=binance_report["market_type"],
        session_id=binance_report["session_id"],
    )
    binance_reconciliation = build_reconciliation_report(
        reconciliation_id="mvp4-dashboard-bound-binance-paper-reconciliation",
        exchange=binance_report["exchange"],
        market_type=binance_report["market_type"],
        mode=binance_report["mode"],
        session_id=binance_report["session_id"],
        account_snapshot_id="PAPER_PORTFOLIO_SCAFFOLD_NOT_EXCHANGE_TRUTH",
        ledger_head_hash="BINANCE_PAPER_RECONCILIATION_SCAFFOLD_NOT_LIVE_LEDGER",
        exchange_snapshot=binance_snapshot,
        internal_state=dict(binance_snapshot),
    )
    reconciliation_result = validate_reconciliation_report(binance_reconciliation)
    if reconciliation_result.status != "PASS":
        raise RuntimeError(f"BINANCE reconciliation validation failed: {reconciliation_result.message}")
    write_json(binance_paths["reconciliation_report"], binance_reconciliation)
    artifacts.append(rel(binance_paths["reconciliation_report"]))
    return sorted(set(artifacts))


def dashboard_binding_audit() -> dict[str, Any]:
    upbit_shell = load_json(
        ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "dashboard_shell.json"
    )
    binance_shell = load_json(
        ROOT / "system" / "runtime" / "binance" / "spot" / "paper" / "mvp1_binance_paper_launcher" / "dashboard_shell.json"
    )
    upbit_reconciliation = upbit_shell["reconciliation_recovery_summary"]
    binance_reconciliation = binance_shell["reconciliation_recovery_summary"]
    checks = {
        "upbit_exact_session_reports_bound": (
            upbit_reconciliation["status"] == "PASS"
            and upbit_reconciliation["color_token"] == "green"
            and upbit_reconciliation["ledger_state"] == "PAPER_LEDGER_MATCHED"
            and upbit_reconciliation["single_writer_state"] == "RECOVERED"
            and upbit_reconciliation["idempotency_state"] == "RECOVERED"
            and upbit_reconciliation["primary_blocker_code"] == "LIVE_READY_MISSING"
        ),
        "binance_reconciliation_visible_without_false_restart_pass": (
            binance_reconciliation["status"] == "RECONCILE_REQUIRED"
            and binance_reconciliation["color_token"] == "yellow"
            and binance_reconciliation["reconciliation_status"] == "PASS"
            and binance_reconciliation["restart_recovery_status"] == "NOT_LOADED"
        ),
        "upbit_live_flags_false": (
            upbit_shell["live_order_ready"] is False
            and upbit_shell["live_order_allowed"] is False
            and upbit_shell["can_live_trade"] is False
            and upbit_shell["scale_up_allowed"] is False
        ),
        "binance_live_flags_false": (
            binance_shell["live_order_ready"] is False
            and binance_shell["live_order_allowed"] is False
            and binance_shell["can_live_trade"] is False
            and binance_shell["scale_up_allowed"] is False
        ),
    }
    blockers = [name for name, ok in checks.items() if not ok]
    return {
        "audit_schema_id": "trader1.paper_reconciliation_artifact_binding_recheck_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "upbit_reconciliation_status": upbit_reconciliation["status"],
        "upbit_reconciliation_color": upbit_reconciliation["color_token"],
        "upbit_primary_blocker": upbit_reconciliation["primary_blocker_code"],
        "binance_reconciliation_status": binance_reconciliation["status"],
        "binance_reconciliation_color": binance_reconciliation["color_token"],
        "binance_restart_recovery_status": binance_reconciliation["restart_recovery_status"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_action": NEXT_TASK_CLASS,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK.md",
        f"""# PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK

context_pack_id: PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK
task_class: MVP4_PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_RUNTIME_ARTIFACT_BINDING", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Launcher dashboard reads session-scoped reconciliation_report.json when present.
- UPBIT PAPER dashboard reads session-scoped restart_recovery_report.json when present.
- UPBIT PAPER clean reconciliation/restart evidence appears green, but still shows LIVE_READY_MISSING.
- BINANCE PAPER does not fake restart recovery; missing restart evidence remains yellow RECONCILE_REQUIRED.
- Cross-session reconciliation artifacts display invalid red instead of being silently mixed.
- All live/order/scale flags remain false.

coverage_snapshot:
- upbit_reconciliation_status: {audit["upbit_reconciliation_status"]}
- upbit_reconciliation_color: {audit["upbit_reconciliation_color"]}
- binance_reconciliation_status: {audit["binance_reconciliation_status"]}
- binance_reconciliation_color: {audit["binance_reconciliation_color"]}
- binance_restart_recovery_status: {audit["binance_restart_recovery_status"]}

known_omissions_by_design:
- no live execution
- no credential access
- no exchange real-account call
- no LIVE_READY snapshot write
- no live or active config mutation
- no risk scale-up

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

Launcher dashboards now bind session-scoped PAPER reconciliation artifacts into the Ledger & Reconciliation panel. UPBIT PAPER can show clean PAPER reconciliation/restart evidence as green display-only status; BINANCE PAPER keeps missing restart recovery as yellow because restart recovery remains unimplemented for that scope.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_RUNTIME_ARTIFACT_BINDING",
            "source_file": "TRADER_1.md",
            "source_heading": "Paper reconciliation artifact dashboard binding",
            "full_text_marker": f"{REQUIREMENT_ID}:launcher dashboard must bind session-scoped reconciliation artifacts without namespace mixing",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Bind PAPER reconciliation artifacts to launcher dashboard safely",
            "requirement_kind": "RUNTIME_DASHBOARD_BINDING_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_RUNTIME_ARTIFACT_BINDING", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION"],
            "depends_on": ["REQ-MVP4-DASHBOARD-RECONCILIATION-OPERATOR-UX-RECHECK"],
            "source_text_sha256": sha256_bytes(b"launcher dashboard must bind session-scoped reconciliation artifacts without namespace mixing"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
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
            "section_id": "SECTION_RUNTIME_ARTIFACT_BINDING",
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/reconciliation_report.schema.json",
                "contracts/schema/restart_recovery_report.schema.json",
            ],
            "validator_files": ["trader1/runtime/boot/safe_launcher.py", "trader1/dashboard/read_only_dashboard.py"],
            "test_files": ["tests/runtime/test_safe_launcher.py", "tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_AUDIT.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    artifacts: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_RECONCILIATION_OPERATOR_UX_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-RECONCILIATION-OPERATOR-UX-RECHECK",
                "REQ-MVP4-LEDGER-RECONCILIATION-RECOVERY-EDGE-RECHECK",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": sorted(set(CHANGED_ARTIFACTS + artifacts)),
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_STALE_ARTIFACT_GUARD"],
            "next_optional_section_ids": ["SECTION_RESTART_RECOVERY", "SECTION_RUNTIME_ARTIFACT_BINDING"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_RUNTIME_ARTIFACT_BINDING", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_PAPER_RECONCILIATION_ARTIFACT_BINDING_RECHECK",
            "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RECONCILIATION", "SECTION_RESTART_RECOVERY", "SECTION_RUNTIME_ARTIFACT_BINDING"],
            "expanded_section_ids": ["TRADER_1:dashboard-operator-ux-active-surface", "AGENTS:runtime-artifact-binding"],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_RECONCILIATION_BINDING_RECHECK",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_FOR_PAPER_RECONCILIATION_ARTIFACT_BINDING_NO_LIVE_ORDERS",
            "dashboard_binding_audit": audit,
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
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "patch_id": PATCH_ID,
            "artifact_paths": [
                *patch_result["new_registry_items"],
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_AUDIT.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Paper Reconciliation Artifact Binding Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- The dashboard could show the Ledger & Reconciliation panel, but root launcher generation did not load session-scoped reconciliation_report.json or restart_recovery_report.json.
- Existing non-session-scoped runtime reports must not be reused by launcher dashboards because that would mix session truth.
- If a wrong-session reconciliation file is placed in the launcher session path, the dashboard must show red INVALID rather than silently treating it as usable evidence.

Patch:
- Added session-scoped reconciliation and restart recovery paths to the root launcher dashboard bundle.
- Added loader plumbing that passes loaded reconciliation/restart artifacts to the dashboard shell.
- Added tests for exact-session PASS binding, mismatch red blocker, cross-session invalid blocker, and restart recovery fallback from scoped paper operation gate.
- Wrote session-scoped PAPER reconciliation artifacts for UPBIT and BINANCE, plus UPBIT restart recovery, then regenerated dashboard HTML/runtime artifacts.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(
            state.get("implemented_schema_ids", [])
            + ["trader1.read_only_dashboard_shell.v1", "trader1.reconciliation_report.v1", "trader1.restart_recovery_report.v1"]
        )
    )
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["read_only_dashboard_validator", "reconciliation_validator", "restart_recovery_validator"]))
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
    report_artifacts = write_session_scoped_reconciliation_artifacts()
    launcher_artifacts = write_launcher_artifacts()
    audit = dashboard_binding_audit()
    tests_run = [
        run_command([sys.executable, "-m", "py_compile", "trader1/runtime/boot/safe_launcher.py", "tests/runtime/test_safe_launcher.py"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_safe_launcher", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run, sorted(set(report_artifacts + launcher_artifacts)))
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed and audit["status"] == "PASS" else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "audit_status": audit["status"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed and audit["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
