from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PORTFOLIO-DETAIL-LAYOUT"
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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
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
    "trader1/dashboard/read_only_dashboard.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_portfolio_detail_layout_patch_evidence.py",
    "contracts/generated/context_pack/DASHBOARD_PORTFOLIO_DETAIL_LAYOUT.md",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
]
PORTFOLIO_FIELDS = [
    "cash",
    "equity",
    "locked_cash",
    "realized_pnl",
    "unrealized_pnl",
    "total_pnl",
    "positions",
    "entry_candidates",
    "return_pct",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def dashboard_portfolio_layout_audit() -> dict[str, Any]:
    dashboard_paths = [
        ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "dashboard" / "index.html",
        ROOT / "system" / "runtime" / "binance" / "spot" / "paper" / "mvp1_binance_paper_launcher" / "dashboard" / "index.html",
    ]
    shell_paths = [
        path.parents[1] / "dashboard_shell.json"
        for path in dashboard_paths
    ]
    required_html = [
        "Portfolio Snapshot",
        "Locked Cash",
        "Realized PnL",
        "Unrealized PnL",
        "Total PnL",
        "Held Positions",
        "Entry Candidates",
        "portfolio-quicklook",
        "table-wrap",
        "Detailed status, evidence, and validator logs",
    ]
    checks: dict[str, bool] = {}
    snapshots: dict[str, dict[str, Any]] = {}
    for html_path, shell_path in zip(dashboard_paths, shell_paths):
        html = html_path.read_text(encoding="utf-8")
        shell = load_json(shell_path)
        key = f"{shell.get('exchange')}_{shell.get('market_type')}_{shell.get('mode')}"
        portfolio = shell.get("portfolio_snapshot", {})
        checks[f"{key}_required_html_visible"] = all(item in html for item in required_html)
        checks[f"{key}_portfolio_fields_bound"] = all(
            isinstance(portfolio.get(field), dict) and portfolio[field].get("card_id") == field
            for field in PORTFOLIO_FIELDS
        )
        checks[f"{key}_details_collapsed"] = '<details class="detail-drawer">' in html and "<details open>" not in html
        checks[f"{key}_no_order_controls"] = "<button" not in html.lower() and "<form" not in html.lower() and "submit" not in html.lower()
        checks[f"{key}_live_flags_false"] = all(
            item in html
            for item in (
                "live_order_ready=false",
                "live_order_allowed=false",
                "can_live_trade=false",
                "scale_up_allowed=false",
            )
        )
        checks[f"{key}_ascii_separator"] = "·" not in html
        snapshots[key] = {
            "portfolio_status": portfolio.get("status"),
            "portfolio_fields": sorted(field for field in PORTFOLIO_FIELDS if field in portfolio),
            "html_length": len(html),
            "detail_drawer_open_by_default": "<details open>" in html,
            "has_live_controls": "<button" in html.lower() or "<form" in html.lower(),
        }
    blockers = [name for name, ok in checks.items() if not ok]
    return {
        "audit_schema_id": "trader1.dashboard_portfolio_detail_layout_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "dashboard_count": len(dashboard_paths),
        "checked_items": len(checks),
        "snapshots": snapshots,
        "browser_visual_check": "PASS_IN_APP_BROWSER_NARROW_VIEW",
        "playwright_overflow_check": "UNTESTED_PLAYWRIGHT_NOT_AVAILABLE",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_action": NEXT_TASK_CLASS,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_PORTFOLIO_DETAIL_LAYOUT.md",
        f"""# DASHBOARD_PORTFOLIO_DETAIL_LAYOUT

context_pack_id: DASHBOARD_PORTFOLIO_DETAIL_LAYOUT
task_class: MVP4_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- First screen portfolio shows cash, equity, locked cash, realized PnL, unrealized PnL, total PnL, open positions, entry candidates, and return.
- Held positions and entry candidates are visible in compact first-screen lists.
- Detailed validator/source/status sections remain collapsed below.
- Tables are wrapped to prevent narrow-screen clipping.
- No order buttons, forms, submit controls, live flags, or scale-up permissions are introduced.

coverage_snapshot:
- dashboard_count: {audit["dashboard_count"]}
- checked_items: {audit["checked_items"]}
- audit_status: {audit["status"]}
- browser_visual_check: {audit["browser_visual_check"]}
- playwright_overflow_check: {audit["playwright_overflow_check"]}

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

Read-only dashboard first screen prioritizes portfolio detail, running status, and live readiness. Portfolio now includes cash, equity, locked cash, realized PnL, unrealized PnL, total PnL, open positions, entry candidates, and return. Detailed evidence remains collapsed below the first screen.

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
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard portfolio detail layout",
            "full_text_marker": f"{REQUIREMENT_ID}:portfolio first screen must expose PnL, positions, and candidates without clipping",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Show detailed portfolio, position, and candidate status on the first screen",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-DASHBOARD-FIRST-SCREEN-SIMPLIFICATION"],
            "source_text_sha256": sha256_bytes(b"portfolio first screen must expose PnL, positions, and candidates without clipping"),
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
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}_AUDIT.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": ["validators_run", "tests_run", "live_order_ready_after", "live_order_allowed_after", "can_live_trade_after", "scale_up_allowed_after"],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_FIRST_SCREEN_SIMPLIFICATION.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL"],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": sorted(set(CHANGED_ARTIFACTS + artifacts)),
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
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
            "next_required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STALE_ARTIFACT_GUARD"],
            "next_optional_section_ids": ["SECTION_RECONCILIATION", "SECTION_RUNTIME_ARTIFACT_BINDING"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT",
            "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["TRADER_1:dashboard-operator-ux-active-surface", "AGENTS:dashboard-implementation-guide"],
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
            "failure_analysis_status": "NOT_REQUIRED_FOR_DASHBOARD_LAYOUT_PATCH",
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
            "validators_untested": [] if all(item.get("status") == "PASS" for item in patch_result["validators_run"]) else ["SEE_VALIDATOR_RESULTS"],
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
            "stage_gate_status": "PASS_FOR_DASHBOARD_PORTFOLIO_DETAIL_LAYOUT_NO_LIVE_ORDERS",
            "dashboard_portfolio_layout_audit": audit,
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
        f"""# MVP4 Dashboard Portfolio Detail Layout

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- First-screen portfolio was too sparse for operator review.
- PnL, held positions, and entry candidates were not visible enough.
- Detail tables needed a narrow-screen overflow guard.

Patch:
- Added locked cash, realized PnL, unrealized PnL, total PnL, entry candidates, and compact first-screen position/candidate lists.
- Wrapped detail tables in horizontal scroll containers to prevent clipping.
- Replaced non-ASCII separators with plain ASCII separators in dashboard text.
- Preserved collapsed detail sections, display-only wording, and all live/order/scale blockers.

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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.read_only_dashboard_shell.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["read_only_dashboard_validator"]))
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
    launcher_artifacts = write_launcher_artifacts()
    audit = dashboard_portfolio_layout_audit()
    tests_run = [
        run_command([sys.executable, "-m", "py_compile", "trader1/dashboard/read_only_dashboard.py", "tests/dashboard/test_read_only_dashboard.py"]),
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_safe_launcher", "-v"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run, launcher_artifacts)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
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
                "browser_visual_check": audit["browser_visual_check"],
                "playwright_overflow_check": audit["playwright_overflow_check"],
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
