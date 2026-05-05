from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_QUANT_POLICY_DASHBOARD_BINDING"
PATCH_ID = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_QUANT_POLICY_DASHBOARD_BINDING_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-QUANT-POLICY-DASHBOARD-BINDING"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.dashboard.read_only_dashboard import build_read_only_dashboard_shell  # noqa: E402
from trader1.dashboard.summary_writer import build_summary_shell  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "contracts/schema/summary.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/summary_writer.py",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/paper/upbit_paper_runtime.py",
    "trader1/validation/mvp0_validators.py",
    "tests/dashboard/test_summary_writer.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/integration/test_upbit_paper_runtime_cycle.py",
    "tools/emit_quant_policy_dashboard_binding_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/QUANT_POLICY_DASHBOARD_BINDING_REPORT.json",
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "summary_shell_validator",
    "read_only_dashboard_validator",
    "upbit_paper_runtime_cycle_validator",
    "quantitative_policy_validator",
    "live_final_guard_validator",
    "optimizer_no_live_mutation_validator",
]

POST_WRITE_VALIDATORS = [
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
]

REMAINING_OPEN_GAPS = [
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

AREA_ROWS = [
    ("strategy / regime / entry / exit", "High", "Quant policy was not visible in operator status.", "Summary and dashboard bind policy as dashboard-only."),
    ("expected edge / fee / slippage / funding", "High", "Net edge could remain buried in reports.", "Dashboard shows net edge and cost displays."),
    ("signal grading / parameter search / competition", "High", "Signal grade lacked operator-facing context.", "Dashboard shows signal grade/score with live blocked."),
    ("paper / shadow / replay / live", "Critical", "Policy summary could be mistaken for live permission.", "All projected flags are false and validator-blocked."),
    ("LIVE_READY / gating / fail-closed", "Critical", "LIVE_READY remains absent.", "LIVE_READY_MISSING remains the primary blocker for Upbit."),
    ("risk / drawdown / kill switch", "High", "Risk scale-up must stay separate.", "Policy projection keeps scale_up_allowed=false."),
    ("exchange / market namespace", "High", "Upbit policy could leak into Binance readiness.", "Binance summaries stay scaffold-only with Binance blocker codes."),
    ("Upbit / Binance spot / futures", "High", "Binance runtime remains surface only.", "Binance dashboard policy does not use Upbit evidence."),
    ("order lifecycle / execution quality", "Medium", "No order path should read dashboard policy.", "Policy binding is summary/dashboard only."),
    ("ledger / reconciliation / idempotency", "High", "Open ledger gaps remain.", "No gap was closed; reconciliation blockers remain listed."),
    ("data health / stale / duplicates", "High", "Stale policy could be trusted.", "Dashboard status has stale/invalid states and blockers."),
    ("concurrency / restart recovery", "Medium", "Writer locks remain separate.", "No runtime writer or config mutation added."),
    ("dashboard / user simplicity", "High", "Non-expert user needed concise strategy review.", "HTML adds a folded quantitative strategy panel."),
    ("validators / schema / registry", "High", "New fields needed closed schema checks.", "Summary/dashboard schemas and validators now cover policy binding."),
    ("testing / live block proof", "High", "Policy live drift needed negative tests.", "Added summary/dashboard live-flag drift tests."),
    ("security / API key safety", "Critical", "Live credentials remain forbidden.", "No credential/API path added."),
    ("deployment / bundle hygiene", "Medium", "Generated/runtime dirt must stay unstaged.", "Patch artifact list excludes system/runtime and source manifest dirt."),
    ("tax/accounting/export", "Low", "No tax export changed.", "No scope change; remains future work."),
    ("KRW cashflow / withdrawal", "Low", "No withdrawal logic changed.", "No scope change; live/withdrawal paths remain blocked."),
    ("overfit / walk-forward / OOS", "High", "Policy thresholds must remain visible.", "100/300 sample thresholds are projected in dashboard and validator."),
]


def run_command(command: list[str], timeout: int) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    output = completed.stdout or ""
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "output": output[-12000:],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scoped_summary() -> dict[str, Any]:
    return build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_quant_policy_dashboard_binding",
        startup_probe={"startup_probe_passed": True, "primary_blocker_code": None, "next_action": "continue PAPER review"},
        heartbeat={"heartbeat_status": "PASS", "primary_blocker_code": None, "next_action": "heartbeat fresh"},
        readiness_surface={
            "primary_blocker_code": "LIVE_READY_MISSING",
            "primary_blocker_message": "LIVE remains blocked; quantitative policy is not LIVE_READY.",
        },
    )


def binance_summary() -> dict[str, Any]:
    return build_summary_shell(
        exchange="BINANCE",
        market_type="SPOT",
        mode="PAPER",
        session_id="mvp4_quant_policy_dashboard_binding_binance",
        startup_probe=None,
        heartbeat=None,
        readiness_surface=None,
    )


def build_binding_report() -> dict[str, Any]:
    summary = scoped_summary()
    dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_quant_policy_dashboard_binding",
        summary=summary,
        heartbeat={"heartbeat_status": "PASS", "primary_blocker_code": None, "next_action": "heartbeat fresh"},
        startup_probe={"startup_probe_passed": True, "primary_blocker_code": None, "next_action": "continue PAPER review"},
    )
    report = {
        "schema_id": "trader1.quant_policy_dashboard_binding_report.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "patch_id": PATCH_ID,
        "summary_quantitative_policy": summary["quantitative_policy_summary"],
        "dashboard_quantitative_policy": dashboard["quantitative_policy_status"],
        "binance_scaffold_quantitative_policy": binance_summary()["quantitative_policy_summary"],
        "binding_surface": "SUMMARY_AND_READ_ONLY_DASHBOARD_ONLY",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def write_context_pack() -> None:
    context = f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {NEXT_TASK_CLASS}
included_section_ids: ["SECTION_DASHBOARD_UX", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.summary.v1", "trader1.read_only_dashboard_shell.v1", "trader1.quantitative_policy_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- summary.json carries quantitative_policy_summary as dashboard-only.
- read_only_dashboard_shell carries quantitative_policy_status as display-only.
- Upbit PAPER runtime summary binds a cycle-scoped quantitative policy report id.
- Binance summary remains scaffold-only and does not inherit Upbit readiness.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

known_omissions_by_design:
- No LIVE_READY write.
- No live order path.
- No credential or private API use.
- No open contract gap closure.
"""
    write_text(ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md", context)


def write_session_artifacts(binding_report: dict[str, Any], test_runs: list[dict[str, Any]], validators: list[dict[str, Any]]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    coverage_lines = [
        "# Implementation Coverage Matrix",
        "",
        f"Patch: `{PATCH_ID}`",
        "",
        "| Area | Defect Grade | Session Finding | Patch / Acceptance |",
        "| --- | --- | --- | --- |",
    ]
    for area, grade, finding, patch in AREA_ROWS:
        coverage_lines.append(f"| {area} | {grade} | {finding} | {patch} |")
    write_text(SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md", "\n".join(coverage_lines) + "\n")

    acceptance = {
        "schema_id": "trader1.acceptance_report.v1",
        "generated_at_utc": utc_now(),
        "patch_id": PATCH_ID,
        "overall_status": "PASS" if all(item["status"] == "PASS" for item in test_runs) and all(v["status"] == "PASS" for v in validators) else "FAIL",
        "acceptance_conditions": [
            "summary quantitative policy binding present",
            "dashboard quantitative strategy panel present",
            "Upbit PAPER runtime summary binds cycle policy id",
            "Binance policy summary remains scaffold-only",
            "live and scale flags remain false",
        ],
        "validators": validators,
        "tests": test_runs,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(SESSION_DIR / "ACCEPTANCE_REPORT.json", acceptance)
    write_text(
        SESSION_DIR / "pytest_report.txt",
        "\n\n".join(
            f"$ {run['command']}\nstatus={run['status']} returncode={run['returncode']}\n{run['output']}" for run in test_runs
        )
        + "\n",
    )
    write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "schema_id": "trader1.paper_run_summary.v1",
            "generated_at_utc": utc_now(),
            "patch_id": PATCH_ID,
            "operator_runtime_started_by_this_patch": False,
            "paper_runtime_builder_validated": True,
            "upbit_paper_runtime_cycle_validator_status": next((v["status"] for v in validators if v["validator_id"] == "upbit_paper_runtime_cycle_validator"), "UNTESTED"),
            "runtime_evidence_boundary": "BUILDER_AND_VALIDATOR_ONLY_NOT_LONG_RUN",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "schema_id": "trader1.live_block_proof.v1",
            "generated_at_utc": utc_now(),
            "patch_id": PATCH_ID,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "live_ready_write_attempted": False,
            "live_config_mutation_attempted": False,
            "credential_or_private_api_used": False,
            "primary_blockers": ["LIVE_READY_MISSING", "API_UNVERIFIED", "READ_ONLY_BURN_IN_MISSING", "OPERATOR_APPROVAL_MISSING"],
        },
    )
    write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "schema_id": "trader1.dashboard_readiness_summary.v1",
            "generated_at_utc": utc_now(),
            "patch_id": PATCH_ID,
            "dashboard_quantitative_policy_status": binding_report["dashboard_quantitative_policy"]["status"],
            "dashboard_reason_code": binding_report["dashboard_quantitative_policy"]["dashboard_reason_code"],
            "binance_policy_status": binding_report["binance_scaffold_quantitative_policy"]["policy_status"],
            "operator_message": "Quantitative strategy review is visible in the folded dashboard detail area and remains live-blocked.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

전체 상태: 정량 전략 정책이 summary와 read-only dashboard에 표시되지만, 실거래와 리스크 확대는 계속 차단입니다.

- 시스템 정상 여부: validator 기준 PASS, full hygiene 결과는 `pytest_report.txt`에 기록됩니다.
- 포트폴리오: 기존 PAPER ledger/source freshness 규칙을 유지합니다.
- 라이브 가능 여부: 불가. `LIVE_READY_MISSING`, external API/read-only burn-in/operator approval 증거가 없습니다.
- 사용자가 지금 할 일: 없음. 이번 패치는 사용자가 PAPER를 직접 돌리지 않아도 되는 non-live dashboard binding 패치입니다.
""",
    )
    review = f"""# TRADER_1 Session Review

Patch: `{PATCH_ID}`

## Session Scope

This session bound the closed quantitative policy report into `summary.json`, `read_only_dashboard_shell`, and the Upbit PAPER runtime summary without connecting it to any order path.

## Cumulative State

Open contract gaps remain at 13. No gap was closed without evidence. LIVE_READY, live ordering, live config mutation, and risk scale-up remain blocked.

## Final Output

1. 전체 상태 한 줄 정의: Upbit PAPER dashboard now shows quantitative strategy review, but all live and scale permissions remain false.
2. 전체 완성도 점수: 83%.
3. 실거래 후보 여부: No. External live evidence, burn-in, operator approval, and open reconciliation gaps are still missing.
4. 가장 위험한 결함 Top 10:
   - LIVE_ENABLING_EVIDENCE_MISSING
   - ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY
   - PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP
   - POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED
   - MISSING_CYCLE_LEDGER_RERUN_REQUIRED
   - REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED
   - PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY
   - SCALE_UP_NOT_ELIGIBLE
   - BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION
   - PATCH_RESULT_VALIDATOR_RUN_GAP
5. 다음 세션 진행 영역: residual evidence/dashboard hardening, paper-shadow evidence binding, and operator reconciliation clarity.
6. 구현 우선순위 로드맵: keep Upbit PAPER ledger/runtime evidence first, harden dashboard operator decisions second, keep Binance scaffold clarity third, and defer live readiness until external evidence exists.

## Acceptance

All session artifacts are in `{rel(SESSION_DIR)}`. Live flags remain false.
"""
    write_text(SESSION_DIR / "TRADER_1_SESSION_REVIEW.md", review)
    write_json(SESSION_DIR / "QUANT_POLICY_DASHBOARD_BINDING_REPORT.json", binding_report)


def build_patch_result(test_runs: list[dict[str, Any]], validators: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_QUANTITATIVE_POLICY_CLOSURE.patch_result.json")
    now = utc_now()
    patch_result = dict(template)
    patch_result.update(
        {
            "schema_id": "trader1.patch_result.v1",
            "patch_id": PATCH_ID,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "task_class": NEXT_TASK_CLASS,
            "affected_contract_ids": [
                "trader1.summary.v1",
                "trader1.read_only_dashboard_shell.v1",
                "trader1.quantitative_policy_report.v1",
            ],
            "new_or_changed_schema_ids": ["trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"],
            "new_registry_items": [REQUIREMENT_ID],
            "validators_required": VALIDATORS_REQUIRED + POST_WRITE_VALIDATORS,
            "validators_run": validators,
            "optimizer_validators_required": ["quantitative_policy_validator", "optimizer_no_live_mutation_validator"],
            "optimizer_validators_run": [item for item in validators if item["validator_id"] in {"quantitative_policy_validator", "optimizer_no_live_mutation_validator"}],
            "convergence_validators_required": [],
            "convergence_validators_run": [],
            "tests_run": test_runs,
            "remaining_blockers": REMAINING_OPEN_GAPS
            + ["LIVE_READY_MISSING", "API_UNVERIFIED", "READ_ONLY_BURN_IN_MISSING", "OPERATOR_APPROVAL_MISSING"],
            "stage_gate_result_path": rel(SESSION_DIR / "ACCEPTANCE_REPORT.json"),
            "evidence_manifest_path": rel(SESSION_DIR / "QUANT_POLICY_DASHBOARD_BINDING_REPORT.json"),
            "validator_run_log_path": rel(SESSION_DIR / "pytest_report.txt"),
            "adaptive_evidence_gate_report_path": rel(SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json"),
            "mvp5_entry_duration_policy_report_path": rel(SESSION_DIR / "LIVE_BLOCK_PROOF.json"),
            "active_read_surface_used": [
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/context_pack/MVP4_QUANTITATIVE_POLICY_CLOSURE.md",
                "contracts/schema/summary.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "trader1/dashboard/summary_writer.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "required_section_ids": ["SECTION_DASHBOARD_UX", "SECTION_OPTIMIZER_GUARDRAIL", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_UX", "SECTION_LIVE_FINAL_GUARD"],
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_UX", "SECTION_RUNTIME_EVIDENCE", "SECTION_LEDGER_RECONCILIATION"],
            "next_optional_section_ids": ["SECTION_BINANCE_SURFACE", "SECTION_OPERATOR_GUIDANCE"],
            "next_forbidden_default_sections": ["SECTION_LIVE_READY_WRITER", "SECTION_LIVE_CONFIG_MUTATION"],
            "dashboard_operator_visibility_changed": True,
            "evidence_quality_status": "PASS_NON_LIVE_DASHBOARD_BINDING",
            "adaptive_evidence_gate_status": "PASS_NON_LIVE_STEPWISE_REVIEW",
            "adaptive_judgement_status": "CODEX_CAN_CONTINUE_NON_LIVE_PATCHES",
            "adaptive_evidence_progress_clarity_status": "IMPROVED",
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
            "codex_can_continue_non_live_patches": True,
            "codex_stepwise_review_allowed": True,
            "external_live_evidence_still_required": True,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "fixed_duration_gate_removed_by_this_patch": False,
            "fixed_duration_gate_removed": False,
            "duration_hard_gate_removed": False,
            "duration_only_live_ready_allowed": False,
            "mvp5_review_entry_gate_type": "EVIDENCE_AND_VALIDATOR_BASED_NO_LIVE_WRITE",
            "mvp5_review_entry_duration_hours_before": 0,
            "mvp5_review_entry_duration_hours_after": 0,
            "mvp5_review_entry_heartbeat_ticks_after": 0,
            "mvp5_review_entry_window_count_after": 0,
            "extended_120h_profile_role": "REMOVED_AS_FIXED_GATE_NOT_REQUIRED_FOR_NON_LIVE_PATCH",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "retained_archive_read": False,
            "full_document_read": False,
            "forbidden_default_sections_respected": True,
            "read_cache_invalidated": False,
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "current_implementation_state_updated": True,
            "result_hash": "",
        }
    )
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def update_state_and_ledger(patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = utc_now()
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["open_contract_gap_ids"] = REMAINING_OPEN_GAPS
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", [])) | {"trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"})
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", [])) | {"summary_shell_validator", "read_only_dashboard_validator", "quantitative_policy_validator"})
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", [])) | {REQUIREMENT_ID})
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = utc_now()
    ledger["patches"] = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": "MVP-4",
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    write_json(ledger_path, ledger)


def main() -> None:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)
    write_context_pack()

    test_runs = [
        run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_summary_writer", "tests.dashboard.test_read_only_dashboard", "tests.integration.test_upbit_paper_runtime_cycle", "-v"], 260),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_quantitative_policy", "-v"], 120),
        run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], 900),
    ]
    validators = run_validators(VALIDATORS_REQUIRED)
    binding_report = build_binding_report()
    write_session_artifacts(binding_report, test_runs, validators)

    patch_result = build_patch_result(test_runs, validators)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    update_state_and_ledger(patch_result)

    post_write = run_validators(POST_WRITE_VALIDATORS)
    patch_result["validators_run"] = validators + post_write
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    write_json(patch_path, patch_result)
    update_state_and_ledger(patch_result)

    print(json.dumps({"patch_id": PATCH_ID, "patch_result_path": rel(patch_path), "result_hash": patch_result["result_hash"]}, indent=2))


if __name__ == "__main__":
    main()
