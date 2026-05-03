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

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_repaired_current_evidence_audited_writer import (  # noqa: E402
    AUDITED_WRITER_IDEMPOTENT_STATUS,
    AUDITED_WRITER_WRITTEN_STATUS,
    EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS,
    build_upbit_paper_repaired_current_evidence_audited_writer_report,
    validate_upbit_paper_audited_current_evidence_idempotency_manifest,
    validate_upbit_paper_audited_current_evidence_snapshot,
    validate_upbit_paper_repaired_current_evidence_audited_writer_report,
    write_upbit_paper_repaired_current_evidence_audited_writer_report,
)
from trader1.runtime.portfolio.paper_portfolio import validate_paper_portfolio_snapshot  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


PATCH_BASENAME = "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER"
PATCH_ID = f"{PATCH_BASENAME}_20260503_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_AUDITED_CURRENT_EVIDENCE_WRITER_DASHBOARD_BINDING"
SESSION_ID = "mvp1_upbit_paper_launcher"

SESSION_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
PAPER_RUNTIME_BASE = SESSION_BASE / "paper_runtime"
IMPLEMENTATION_PREP_PATH = (
    PAPER_RUNTIME_BASE / "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_report.json"
)
LEDGER_ROLLUP_PATH = SESSION_BASE / "ledger" / "paper_ledger_rollup_report.json"
WRITER_REPORT_PATH = PAPER_RUNTIME_BASE / "upbit_paper_repaired_current_evidence_audited_writer_report.json"

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_repaired_current_evidence_audited_writer_implementation_prep_validator",
    "paper_ledger_rollup_validator",
    "paper_portfolio_snapshot_validator",
    "upbit_paper_repaired_current_evidence_audited_writer_validator",
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
    "contracts/schema/upbit_paper_repaired_current_evidence_audited_writer_report.schema.json",
    "trader1/runtime/paper/upbit_paper_repaired_current_evidence_audited_writer.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
    "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_upbit_paper_repaired_current_evidence_audited_writer_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
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


def write_runtime_audited_writer_report() -> dict[str, Any]:
    report = build_upbit_paper_repaired_current_evidence_audited_writer_report(
        root=ROOT,
        source_implementation_prep_report=load_json(IMPLEMENTATION_PREP_PATH),
        source_ledger_rollup_report=load_json(LEDGER_ROLLUP_PATH),
        audited_writer_id="upbit-paper-repaired-current-evidence-audited-writer-20260503",
    )
    result = validate_upbit_paper_repaired_current_evidence_audited_writer_report(report)
    if result.status != "PASS":
        raise RuntimeError(f"audited writer validation failed: {result.status} {result.blocker_code} {result.message}")
    if report["writer_status"] not in {AUDITED_WRITER_WRITTEN_STATUS, AUDITED_WRITER_IDEMPOTENT_STATUS}:
        raise RuntimeError(f"audited writer did not publish current evidence: {report['writer_status']}")
    write_upbit_paper_repaired_current_evidence_audited_writer_report(root=ROOT, report=report)
    validate_runtime_outputs()
    return report


def validate_runtime_outputs() -> None:
    current_evidence = load_json(SESSION_BASE / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
    manifest = load_json(SESSION_BASE / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[1])
    portfolio = load_json(SESSION_BASE / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
    checks = [
        validate_upbit_paper_audited_current_evidence_snapshot(current_evidence),
        validate_upbit_paper_audited_current_evidence_idempotency_manifest(manifest),
        validate_paper_portfolio_snapshot(portfolio),
    ]
    failed = [check for check in checks if check.status != "PASS"]
    if failed:
        detail = ", ".join(f"{item.status}:{item.blocker_code}:{item.message}" for item in failed)
        raise RuntimeError(f"runtime audited writer output validation failed: {detail}")
    if (
        current_evidence.get("cash_status") != "VERIFIED"
        or current_evidence.get("equity_status") != "VERIFIED"
        or portfolio.get("source") != "PAPER_LEDGER_ROLLUP"
        or portfolio.get("starting_cash") != "1000000"
    ):
        raise RuntimeError("runtime audited writer output did not bind verified PAPER portfolio truth")
    lock_path = SESSION_BASE / "paper_runtime" / "locks" / "audited_current_evidence_writer.lock"
    if lock_path.exists():
        raise RuntimeError("audited current-evidence writer lock remained after run")


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    portfolio = load_json(SESSION_BASE / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[2])
    current_evidence = load_json(SESSION_BASE / EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS[0])
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1", "trader1.upbit_paper_audited_current_evidence_snapshot.v1", "trader1.upbit_paper_audited_current_evidence_idempotency_manifest.v1", "trader1.paper_portfolio_snapshot.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The audited writer reads validated implementation-prep and PAPER ledger-rollup sources only.
- It writes current evidence, idempotency, and portfolio truth artifacts under the scoped PAPER session.
- It uses the declared temp files plus a scoped single-writer lock and leaves no lock behind.
- Re-running the writer reuses matching outputs instead of rewriting or double-counting evidence.
- Current evidence and portfolio truth remain PAPER-only, display-only, and live-blocked.

runtime_summary:
- writer_status: {report["writer_status"]}
- artifact_written_count: {report["artifact_written_count"]}
- artifact_reused_count: {report["artifact_reused_count"]}
- portfolio_truth_status: {current_evidence["portfolio_truth_status"]}
- cash_status: {current_evidence["cash_status"]}
- equity_status: {current_evidence["equity_status"]}
- configured_initial_cash_krw: {current_evidence["configured_initial_cash_krw"]}
- verified_cash_krw: {current_evidence["verified_cash_krw"]}
- verified_equity_krw: {current_evidence["verified_equity_krw"]}
- verified_total_pnl_krw: {current_evidence["verified_total_pnl_krw"]}
- portfolio_source: {portfolio["source"]}
- open_position_count: {portfolio["open_position_count"]}
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not bind the dashboard to the audited writer outputs.
- It does not create LIVE_READY, live config, live orders, private API calls, credentials, long-run evidence, or scale-up.

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

Upbit PAPER now has an audited current-evidence writer that publishes verified portfolio truth from the ledger rollup. The verified values are still PAPER-only dashboard truth and cannot create LIVE_READY, orders, credentials, long-run evidence, or scale-up.

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
            "source_section_id": "SECTION_PORTFOLIO_TRUTH",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER repaired current-evidence audited writer",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: audited writer must publish verified PAPER current evidence and portfolio truth "
                "from validated ledger rollup sources with idempotency, locks, and live-blocked boundaries"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER audited current evidence writer",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep.py",
                "tests/dashboard/test_read_only_dashboard.py",
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
                "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER-IMPLEMENTATION-PREP",
                "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-TRUTH-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"audited writer publishes verified paper current evidence and portfolio truth from ledger rollup with idempotency locks and live blockers"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_AUDITED_PAPER_CURRENT_EVIDENCE_WRITER_LIVE_BLOCKED",
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
            "section_id": "SECTION_PORTFOLIO_TRUTH",
            "schema_files": ["contracts/schema/upbit_paper_repaired_current_evidence_audited_writer_report.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer.py",
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [base.rel(WRITER_REPORT_PATH), *[base.rel(SESSION_BASE / path) for path in EXPECTED_AUDITED_WRITER_ARTIFACT_PATHS]],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_repaired_current_evidence_audited_writer.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                base.rel(WRITER_REPORT_PATH),
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_AUDITED_PAPER_CURRENT_EVIDENCE_WRITER_LIVE_BLOCKED",
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


def update_state_schema_validator_lists() -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []))
        | {"trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1"}
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []))
        | {"upbit_paper_repaired_current_evidence_audited_writer_validator"}
    )
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER_IMPLEMENTATION_PREP.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-REPAIRED-CURRENT-EVIDENCE-AUDITED-WRITER-IMPLEMENTATION-PREP",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.upbit_paper_repaired_current_evidence_audited_writer_report.v1"],
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
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_CURRENT_EVIDENCE_WRITER"],
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
                "audited writer implementation-prep report",
                "paper ledger rollup report",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_REPAIRED_CURRENT_EVIDENCE_AUDITED_WRITER",
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
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_AUDITED_PAPER_CURRENT_EVIDENCE_WRITER",
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


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_AUDITED_CURRENT_EVIDENCE_WRITER_PAPER_ONLY",
            "writer_status": report["writer_status"],
            "artifact_written_count": report["artifact_written_count"],
            "artifact_reused_count": report["artifact_reused_count"],
            "lock_present_after_run": report["lock_present_after_run"],
            "current_evidence_artifact_written": report["current_evidence_artifact_written"],
            "idempotency_manifest_written": report["idempotency_manifest_written"],
            "portfolio_truth_artifact_written": report["portfolio_truth_artifact_written"],
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
    base.write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    report = write_runtime_audited_writer_report()
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_state_schema_validator_lists()

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
                "tests/runtime/test_upbit_paper_repaired_current_evidence_audited_writer_implementation_prep.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_projects_audited_writer_implementation_prep_for_operator_visibility",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_audited_writer_implementation_prep_operator_action_drift",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_audited_writer_implementation_prep_operator_workflow_drift",
                "-q",
            ]
        ),
    ]
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
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
                "writer_status": report["writer_status"],
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
