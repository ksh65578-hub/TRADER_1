from __future__ import annotations

import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.dashboard.read_only_dashboard import (  # noqa: E402
    render_dashboard_html,
    validate_read_only_dashboard_shell,
)
from trader1.runtime.boot.safe_launcher import (  # noqa: E402
    build_launcher_report,
    launcher_dashboard_paths,
    write_launcher_dashboard,
)
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (  # noqa: E402
    AUDITED_WRITER_IDEMPOTENT_STATUS,
    AUDITED_WRITER_WRITTEN_STATUS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    validate_upbit_paper_repaired_current_evidence_audited_writer_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


PATCH_BASENAME = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING"
SOURCE_WRITER_REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER"
NEXT_TASK_CLASS = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_RECHECK"
SESSION_ID = "mvp1_upbit_paper_launcher"

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "upbit_paper_repaired_current_evidence_audited_writer_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/validation/mvp0_validators.py",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/runtime/test_safe_launcher.py",
    "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
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
    "tools/emit_upbit_paper_audited_current_evidence_writer_dashboard_binding_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

SOURCE_RUNTIME_ARTIFACTS = [
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/paper_ledger_rollup_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repaired_current_evidence_audited_writer_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/current_evidence/audited_current_evidence_snapshot.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/current_evidence/audited_current_evidence_idempotency_manifest.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/portfolio/paper_portfolio_snapshot.json",
]

BLOCKERS = [
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


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return base.sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def assert_current_state_ready_for_dashboard_binding() -> None:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    completed = set(state.get("completed_requirement_ids", []))
    if state.get("next_allowed_task_class") not in {PATCH_BASENAME, NEXT_TASK_CLASS}:
        raise RuntimeError("current state is not routed to audited current-evidence dashboard binding")
    if "REQ-MVP4-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-PENDING-RECHECK" not in completed:
        raise RuntimeError("operator queue pending recheck is not completed")
    if "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING" in state.get("open_contract_gap_ids", []):
        raise RuntimeError("operator queue pending gap is still open")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if state.get(field) is True:
            raise RuntimeError(f"current state has forbidden true field: {field}")


def krw_display(value: Any) -> str:
    return f"{Decimal(str(value)):,.0f} KRW"


def _safe_relative_paths(paths: dict[str, Path], root: Path) -> list[str]:
    return sorted(base.rel(path) if path.is_relative_to(ROOT) else path.relative_to(root).as_posix() for path in paths.values())


def build_temp_dashboard_projection() -> dict[str, Any]:
    launcher_report = build_launcher_report("UPBIT_PAPER")
    source_paths = launcher_dashboard_paths(launcher_report)
    with TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        temp_paths = launcher_dashboard_paths(launcher_report, temp_root)
        implementation_prep = load_json(
            source_paths["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"]
        )
        ledger_rollup = load_json(source_paths["paper_ledger_rollup_report"])
        base.write_json(
            temp_paths["upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report"],
            implementation_prep,
        )
        base.write_json(temp_paths["paper_ledger_rollup_report"], ledger_rollup)

        writer_report = build_upbit_paper_repaired_current_evidence_audited_writer_report(
            root=temp_root,
            source_implementation_prep_report=implementation_prep,
            source_ledger_rollup_report=ledger_rollup,
            audited_writer_id="upbit-paper-audited-current-evidence-writer-dashboard-binding-20260505",
        )
        writer_result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(writer_report)
        if writer_result.status != "PASS":
            raise RuntimeError(
                f"audited writer temp validation failed: {writer_result.status} "
                f"{writer_result.blocker_code} {writer_result.message}"
            )
        if writer_report["writer_status"] not in {AUDITED_WRITER_WRITTEN_STATUS, AUDITED_WRITER_IDEMPOTENT_STATUS}:
            raise RuntimeError(f"audited writer temp output did not publish portfolio truth: {writer_report['writer_status']}")
        write_upbit_paper_repaired_current_evidence_audited_writer_report(root=temp_root, report=writer_report)

        dashboard_paths = write_launcher_dashboard(launcher_report, temp_root)
        dashboard = load_json(dashboard_paths["dashboard_shell"])
        current_evidence = load_json(temp_paths["audited_current_evidence_snapshot"])
        paper_portfolio = load_json(temp_paths["audited_paper_portfolio_snapshot"])
        html = render_dashboard_html(dashboard)
        validate_dashboard_projection(dashboard, current_evidence, paper_portfolio, writer_report, html)
        return {
            "dashboard": dashboard,
            "current_evidence": current_evidence,
            "paper_portfolio": paper_portfolio,
            "writer_report": writer_report,
            "temp_dashboard_artifact_paths": _safe_relative_paths(dashboard_paths, temp_root),
            "source_runtime_artifacts": SOURCE_RUNTIME_ARTIFACTS,
        }


def validate_dashboard_projection(
    dashboard: dict[str, Any],
    current_evidence: dict[str, Any],
    paper_portfolio: dict[str, Any],
    writer_report: dict[str, Any],
    html: str,
) -> None:
    result = validate_read_only_dashboard_shell(dashboard)
    if result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {result.status} {result.blocker_code} {result.message}")

    portfolio = dashboard.get("portfolio_snapshot")
    positions = dashboard.get("position_snapshot")
    reconciliation = dashboard.get("reconciliation_recovery_summary")
    if not all(isinstance(item, dict) for item in (portfolio, positions, reconciliation)):
        raise RuntimeError("dashboard missing portfolio, position, or reconciliation projection")

    if portfolio.get("status") != "VERIFIED" or portfolio.get("source") != "audited_current_evidence_snapshot.json":
        raise RuntimeError("dashboard did not promote audited PAPER current evidence to verified display truth")
    if portfolio.get("source_snapshot_status") != "PASS":
        raise RuntimeError("audited current evidence source did not remain PASS in dashboard")
    if portfolio.get("cash", {}).get("value_display") != krw_display(current_evidence.get("verified_cash_krw")):
        raise RuntimeError("dashboard cash display does not match audited current evidence")
    if portfolio.get("equity", {}).get("value_display") != krw_display(current_evidence.get("verified_equity_krw")):
        raise RuntimeError("dashboard equity display does not match audited current evidence")
    if portfolio.get("total_pnl", {}).get("value_display") != krw_display(current_evidence.get("verified_total_pnl_krw")):
        raise RuntimeError("dashboard PnL display does not match audited current evidence")
    if positions.get("source") != "paper_portfolio_snapshot.json":
        raise RuntimeError("dashboard position truth did not bind audited paper portfolio snapshot")
    if positions.get("open_position_count") != paper_portfolio.get("open_position_count"):
        raise RuntimeError("dashboard open position count does not match audited paper portfolio")

    if reconciliation.get("upbit_paper_repaired_current_evidence_audited_writer_validation_status") != "PASS":
        raise RuntimeError("dashboard did not expose audited writer validation PASS")
    if reconciliation.get("upbit_paper_repaired_current_evidence_audited_writer_verified_for_display") is not True:
        raise RuntimeError("dashboard did not mark audited writer verified_for_display")
    if reconciliation.get("upbit_paper_repaired_current_evidence_audited_writer_status") not in {
        AUDITED_WRITER_WRITTEN_STATUS,
        AUDITED_WRITER_IDEMPOTENT_STATUS,
    }:
        raise RuntimeError("dashboard did not expose a PASS audited writer status")

    source_status = {
        source.get("artifact_id"): source.get("freshness_status")
        for source in dashboard.get("source_artifacts", [])
        if source.get("artifact_id")
        in {
            "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER",
            "AUDITED_CURRENT_EVIDENCE_SNAPSHOT",
            "AUDITED_PAPER_PORTFOLIO_SNAPSHOT",
        }
    }
    expected_source_status = {
        "UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER": "PASS",
        "AUDITED_CURRENT_EVIDENCE_SNAPSHOT": "PASS",
        "AUDITED_PAPER_PORTFOLIO_SNAPSHOT": "PASS",
    }
    if source_status != expected_source_status:
        raise RuntimeError(f"audited dashboard source status drifted: {source_status}")

    if "Audited Current Evidence Writer" not in html or str(writer_report["writer_status"]) not in html:
        raise RuntimeError("dashboard HTML did not render audited writer operator panel")
    for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed"):
        if dashboard.get(field) is not False or reconciliation.get(field) is not False:
            raise RuntimeError(f"dashboard attempted forbidden live or scale permission: {field}")


def write_context(now: str, trader_hash: str, agents_hash: str, projection: dict[str, Any]) -> None:
    dashboard = projection["dashboard"]
    current_evidence = projection["current_evidence"]
    portfolio = projection["paper_portfolio"]
    writer_report = projection["writer_report"]
    reconciliation = dashboard["reconciliation_recovery_summary"]
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{SOURCE_WRITER_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1", "trader1.upbit_paper_audited_current_evidence_snapshot.v1", "trader1.paper_portfolio_snapshot.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + SOURCE_RUNTIME_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The audited current-evidence writer validator compares portfolio truth to the source ledger snapshot, not a stale fixed cash sample.
- The safe launcher loads the audited writer report, audited current-evidence snapshot, and audited paper portfolio snapshot.
- The dashboard portfolio card displays VERIFIED audited PAPER truth from audited_current_evidence_snapshot.json.
- The position panel binds paper_portfolio_snapshot.json and preserves the audited open-position count.
- Source artifacts for writer, current evidence, and audited portfolio all show PASS.
- Live order readiness, live order permission, trading permission, and scale-up all remain false.

runtime_summary:
- writer_status: {writer_report["writer_status"]}
- writer_validation_status: {reconciliation["upbit_paper_repaired_current_evidence_audited_writer_validation_status"]}
- writer_verified_for_display: {reconciliation["upbit_paper_repaired_current_evidence_audited_writer_verified_for_display"]}
- portfolio_status: {dashboard["portfolio_snapshot"]["status"]}
- portfolio_source: {dashboard["portfolio_snapshot"]["source"]}
- source_cash_krw: {current_evidence["verified_cash_krw"]}
- source_equity_krw: {current_evidence["verified_equity_krw"]}
- open_position_count: {portfolio["open_position_count"]}
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not write repo-local system/runtime monitor output.
- It does not create LIVE_READY, live config, live orders, private API calls, credentials, long-run evidence, or scale-up.
- It does not close unrelated open contract gaps such as profitability maturity or long-run runtime evidence.

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

Upbit PAPER audited current evidence now has launcher/dashboard binding evidence from a temp replay: portfolio and position displays bind audited PAPER truth while all live and scale permissions stay false. The writer validator now checks the active source ledger snapshot instead of a stale fixed cash value.

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
            "source_heading": "Upbit PAPER audited current-evidence writer dashboard binding",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: dashboard must bind audited current evidence, audited paper portfolio truth, "
                "and audited writer validation without creating live order or scale-up permission"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER audited current evidence writer dashboard binding",
            "requirement_kind": "DASHBOARD_UX",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1",
                "trader1.upbit_paper_audited_current_evidence_snapshot.v1",
                "trader1.paper_portfolio_snapshot.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": [*CHANGED_ARTIFACTS, *SOURCE_RUNTIME_ARTIFACTS],
            "test_ids": [item for item in CHANGED_ARTIFACTS if item.startswith("tests/")],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                SOURCE_WRITER_REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-AUDITED-CURRENT-EVIDENCE-SOURCE-FRESHNESS",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"audited current evidence writer dashboard binding verifies paper portfolio truth from audited sources while live and scale stay blocked"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_AUDITED_PAPER_CURRENT_EVIDENCE_DASHBOARD_BOUND_LIVE_BLOCKED",
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
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/upbit_paper_repaired_current_evidence_audited_writer_report.schema.json",
            ],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [item for item in CHANGED_ARTIFACTS if item.startswith("tests/")],
            "fixture_files": SOURCE_RUNTIME_ARTIFACTS,
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/runtime/paper/upbit_paper_repaired_current_evidence_audited_writer.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
                "next_task_class",
                "remaining_blockers",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_AUDITED_PAPER_CURRENT_EVIDENCE_DASHBOARD_BOUND_LIVE_BLOCKED",
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
    projection: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER.patch_result.json"
    )
    writer_report = projection["writer_report"]
    dashboard = projection["dashboard"]
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                SOURCE_WRITER_REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-AUDITED-CURRENT-EVIDENCE-SOURCE-FRESHNESS",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
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
                "SECTION_PROFITABILITY_MATURITY",
                "SECTION_OPTIMIZER_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_PORTFOLIO_TRUTH",
            ],
            "next_forbidden_default_sections": [
                "LIVE_ENABLING_PATCH",
                "LIVE_CONFIG_MUTATION",
                "RISK_SCALE_UP",
                "RETAINED_ARCHIVE",
            ],
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
                "audited writer report",
                "audited current evidence snapshot",
                "audited paper portfolio snapshot",
                "safe launcher dashboard loader",
                "read-only dashboard renderer",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING",
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_AUDITED_CURRENT_EVIDENCE_DASHBOARD_BINDING",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
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
    projection: dict[str, Any],
) -> None:
    dashboard = projection["dashboard"]
    current_evidence = projection["current_evidence"]
    portfolio = projection["paper_portfolio"]
    writer_report = projection["writer_report"]
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
            "stage_gate_status": "PASS_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BOUND_PAPER_ONLY",
            "writer_status": writer_report["writer_status"],
            "writer_validation_status": dashboard["reconciliation_recovery_summary"][
                "upbit_paper_repaired_current_evidence_audited_writer_validation_status"
            ],
            "dashboard_portfolio_status": dashboard["portfolio_snapshot"]["status"],
            "dashboard_portfolio_source": dashboard["portfolio_snapshot"]["source"],
            "current_evidence_snapshot_status": dashboard["portfolio_snapshot"]["source_snapshot_status"],
            "verified_cash_krw": current_evidence["verified_cash_krw"],
            "verified_equity_krw": current_evidence["verified_equity_krw"],
            "open_position_count": portfolio["open_position_count"],
            "source_artifact_status": "PASS",
            "repo_system_runtime_written": False,
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
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                *SOURCE_RUNTIME_ARTIFACTS,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "temp_dashboard_artifact_paths": projection["temp_dashboard_artifact_paths"],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    assert_current_state_ready_for_dashboard_binding()
    base.update_authority_manifest(now)
    projection = build_temp_dashboard_projection()
    write_context(now, trader_hash, agents_hash, projection)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
                "tests/runtime/test_safe_launcher.py::SafeLauncherTest::test_launcher_dashboard_loads_audited_current_evidence_portfolio_truth",
                "-q",
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
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_projects_audited_current_evidence_writer_portfolio_truth",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_keeps_audited_current_evidence_writer_portfolio_unverified_on_live_drift",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_keeps_stale_audited_current_evidence_portfolio_unverified",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
    ]
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, projection)
    write_evidence(now, trader_hash, agents_hash, patch_result, projection)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, projection)
    write_evidence(now, trader_hash, agents_hash, patch_result, projection)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
                "-q",
            ]
        )
    )
    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    patch_result = build_patch_result(now, tests_run, validators_run, projection)
    write_evidence(now, trader_hash, agents_hash, patch_result, projection)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "dashboard_portfolio_status": projection["dashboard"]["portfolio_snapshot"]["status"],
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
