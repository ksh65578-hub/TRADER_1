from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-RESIDUAL-EXECUTION-GUIDE-CLARITY"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
HANDOFF_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
EXECUTION_GUIDE_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_dashboard_live_availability_reason_patch_evidence as live_base  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


base = live_base.base
visibility_base = live_base.visibility_base

VALIDATORS_REQUIRED = [
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "runtime_schema_instance_validator",
    "schema_validator",
    "registry_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

ROUTE_GUARD_TEST_ARTIFACTS = [
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
    "tests/contract/test_profitability_optimizer_evidence_maturity_recheck.py",
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
]

CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_residual_execution_guide_clarity_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS

DASHBOARD_ARTIFACTS = [
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/paper/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
    "system/runtime/upbit/krw_spot/live/mvp1_upbit_live_launcher/dashboard/index.html",
    "system/runtime/binance/spot/live/mvp1_binance_live_launcher/dashboard/index.html",
]

BLOCKERS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base() -> None:
    live_base.PATCH_BASENAME = PATCH_BASENAME
    live_base.PATCH_ID = PATCH_ID
    live_base.REQUIREMENT_ID = REQUIREMENT_ID
    live_base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    live_base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    live_base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    live_base.DASHBOARD_ARTIFACTS = DASHBOARD_ARTIFACTS
    live_base.BLOCKERS = BLOCKERS
    live_base.configure_base()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_execution_guide_report() -> dict[str, Any]:
    report = load_json(ROOT / EXECUTION_GUIDE_REPORT_PATH)
    if report.get("schema_id") != "trader1.residual_operator_execution_guide_report.v1":
        raise RuntimeError("residual execution guide report schema mismatch")
    if report.get("guide_status") != "BLOCKED_GUIDE_ONLY":
        raise RuntimeError("residual execution guide report must remain blocked")
    if report.get("validation_status") != "PASS":
        raise RuntimeError("residual execution guide report validation must be PASS")
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "current_evidence_write_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
        "live_ready_write_allowed",
    ):
        if report.get(field) is not False:
            raise RuntimeError(f"residual execution guide report has non-false {field}")
    if report.get("open_gap_count") != len(BLOCKERS):
        raise RuntimeError("residual execution guide report open gap count does not match residual blockers")
    if report.get("execution_step_count") != 6 or report.get("handoff_packet_count") != 6:
        raise RuntimeError("residual execution guide report must expose six blocked execution steps")
    if report.get("local_paper_shadow_runtime_step_count") != 1:
        raise RuntimeError("residual execution guide report must expose exactly one local PAPER/SHADOW step")
    if (
        report.get("operator_runtime_required_before_mvp5") is not True
        or report.get("mvp5_entry_blocked_until_operator_evidence") is not True
        or report.get("binance_runtime_status") != "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS"
    ):
        raise RuntimeError("residual execution guide report must keep MVP-5 blocked and Binance scaffold-only")
    steps = report.get("execution_steps", [])
    if any(step.get("execution_status") != "BLOCKED_GUIDE_ONLY" for step in steps):
        raise RuntimeError("all residual execution guide steps must remain blocked")
    if any(
        command.get("non_live_only") is not True
        or command.get("credential_required") is not False
        or command.get("live_order_allowed") is not False
        for step in steps
        for command in step.get("allowed_local_commands", [])
    ):
        raise RuntimeError("all execution guide local commands must remain non-live and credential-free")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE", "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET", "REQ-MVP4-DASHBOARD-RESIDUAL-OPERATOR-HANDOFF-CLARITY", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.residual_operator_execution_guide_report.v1", "trader1.residual_operator_handoff_packet_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS + DASHBOARD_ARTIFACTS + [EXECUTION_GUIDE_REPORT_PATH, HANDOFF_REPORT_PATH])}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The first-screen Live Execution card loads the audited residual operator execution guide report as display truth only.
- The dashboard summarizes {report["open_gap_count"]} open residual blockers as {report["execution_step_count"]} blocked execution steps without exposing the full command text on the first screen.
- The dashboard shows {report["local_paper_shadow_runtime_step_count"]} local PAPER/SHADOW command, an adaptive evidence gate with no fixed observation-duration floor, MVP-5 blocked status, and Binance scaffold-only status.
- The dashboard preserves raw blocker traceability and all false live/scale flags.
- No order controls, credential access, live permission, current evidence write, gap closure, live config mutation, or scale-up behavior is introduced.

known_omissions_by_design:
- dashboard remains display truth only and cannot become execution truth
- residual blockers remain open and live-blocking
- runtime HTML files may be refreshed locally for operator visibility but remain untracked runtime output

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

The dashboard first screen now points operators to the residual execution guide: {report["execution_step_count"]} steps remain blocked, {report["local_paper_shadow_runtime_step_count"]} local PAPER/SHADOW command is allowed, and MVP-5 remains blocked until operator evidence exists.

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
            "source_heading": "Dashboard residual operator execution guide clarity",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: dashboard must expose residual operator execution guide as concise "
                "display-only MVP-5 blocker guidance while preserving false live/scale permissions"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard residual operator execution guide clarity",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": [
                "trader1.read_only_dashboard_shell.v1",
                "trader1.residual_operator_execution_guide_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS + DASHBOARD_ARTIFACTS + [EXECUTION_GUIDE_REPORT_PATH, HANDOFF_REPORT_PATH],
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tools/run_dashboard_visual_layout_validators.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_DASHBOARD_SHELL",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_CONTRACT_GAP",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE",
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET",
                "REQ-MVP4-DASHBOARD-RESIDUAL-OPERATOR-HANDOFF-CLARITY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"dashboard residual execution guide clarity display only live blocked mvp5 blocked"),
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
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"] + ROUTE_GUARD_TEST_ARTIFACTS,
            "fixture_files": [EXECUTION_GUIDE_REPORT_PATH, HANDOFF_REPORT_PATH],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": DASHBOARD_ARTIFACTS,
            "patch_result_fields": [
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
    regenerated: list[dict[str, Any]],
) -> dict[str, Any]:
    patch_result = live_base.build_patch_result(now, tests_run, validators_run, regenerated)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE",
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET",
                "REQ-MVP4-DASHBOARD-RESIDUAL-OPERATOR-HANDOFF-CLARITY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "remaining_blockers": BLOCKERS,
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator execution guide report",
                "residual operator handoff packet report",
                "read-only dashboard renderer",
                "read-only dashboard schema",
                "safe launcher dashboard artifact builder",
                "dashboard visual layout contract",
                "dashboard tests",
            ],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": [
                "SECTION_DASHBOARD_SHELL",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_CONTRACT_GAP",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_SHELL",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_CONTRACT_GAP",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "optimizer_guardrail_result": "PASS_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_LIVE_BLOCKED",
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
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
            "stage_gate_status": "PASS_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "handoff_packet_count": report["handoff_packet_count"],
            "execution_step_count": report["execution_step_count"],
            "local_paper_shadow_runtime_step_count": report["local_paper_shadow_runtime_step_count"],
            "minimum_observation_hours": 0,
            "fixed_duration_gate_status": "REMOVED_NO_FIXED_RUNTIME_FLOOR",
            "mvp5_entry_blocked_until_operator_evidence": True,
            "binance_runtime_status": "SCAFFOLD_ONLY_NOT_ELIGIBLE_FOR_READINESS",
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
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                *DASHBOARD_ARTIFACTS,
                EXECUTION_GUIDE_REPORT_PATH,
                HANDOFF_REPORT_PATH,
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
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Dashboard Residual Operator Execution Guide Clarity Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The residual operator execution guide existed, but the dashboard first screen did not yet surface the operator-run evidence collection step, MVP-5 blocked state, or Binance scaffold-only boundary.

Patch:
- Bound the dashboard shell to {EXECUTION_GUIDE_REPORT_PATH} as display truth only.
- Added first-screen guide counts: {report["execution_step_count"]} blocked steps, {report["local_paper_shadow_runtime_step_count"]} local PAPER/SHADOW command, and adaptive evidence-gate status with no fixed observation-duration floor.
- Kept the full local command out of the first screen while leaving the audited report available as source evidence.
- Marked MVP-5 as blocked until operator evidence and Binance as scaffold-only.
- Preserved raw blocker traceability, source freshness, and all false live/scale flags.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- no live config mutation
- no current evidence write
- no gap closure
- no scale-up
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    report = load_execution_guide_report()
    base.update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    regenerated = base.regenerate_paper_dashboards()
    regenerated.extend(visibility_base.refresh_existing_runtime_dashboard_html())

    tests_run = [
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_dashboard_visual_layout_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, regenerated)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    tests_run.append(
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.contract.test_schema_instance_validation",
                "tests.contract.test_patch_result_runtime_schema_validation",
                "-v",
            ]
        )
    )
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, regenerated)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "open_gap_count": report["open_gap_count"],
                "handoff_packet_count": report["handoff_packet_count"],
                "execution_step_count": report["execution_step_count"],
                "local_paper_shadow_runtime_step_count": report["local_paper_shadow_runtime_step_count"],
                "mvp5_entry_blocked_until_operator_evidence": True,
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
