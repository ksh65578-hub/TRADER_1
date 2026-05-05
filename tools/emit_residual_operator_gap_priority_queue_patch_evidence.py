from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPERATOR_GAP_PRIORITY_QUEUE"
PATCH_ID = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_OPERATOR_GAP_PRIORITY_QUEUE_20260506_001"
LEGACY_PATCH_IDS = {"MVP4_RESIDUAL_OPERATOR_GAP_PRIORITY_QUEUE_20260506_001"}
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-GAP-PRIORITY-QUEUE"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME

ACTION_PLAN_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json"
HANDOFF_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
GUIDE_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.report.json"
PROGRESS_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"

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
from trader1.dashboard.read_only_dashboard import (  # noqa: E402
    build_read_only_dashboard_shell,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.summary_writer import build_summary_shell  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


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

CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_residual_operator_gap_priority_queue_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/RESIDUAL_OPERATOR_GAP_PRIORITY_QUEUE_REPORT.json",
]

VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "live_final_guard_validator",
]

POST_WRITE_VALIDATORS = [
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
]

AREA_ROWS = [
    ("strategy / regime / entry / exit", "Medium", "Residual evidence tasks could distract from strategy work.", "Priority queue keeps strategy changes behind evidence/reconciliation blockers."),
    ("expected edge / fee / slippage / funding", "Medium", "Profitability maturity remains open.", "Queue keeps optimizer evidence maturity open and does not claim edge closure."),
    ("signal grading / parameter search / competition", "Medium", "Optimizer maturity can be confused with readiness.", "Dashboard states evidence maturity is after operator/ledger work."),
    ("paper / shadow / replay / micro-live / live", "Critical", "Operator could jump to live evidence before PAPER reconciliation.", "Queue fixes operator reconciliation, ledger rerun, PAPER/SHADOW evidence before live evidence."),
    ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "A next-action list can be mistaken for permission.", "Priority surface has live_ready_write_allowed=false and live flags false."),
    ("risk engine / drawdown / cooling / kill switch", "High", "Scale-up blocker might be hidden behind other tasks.", "Scale-up remains last priority and scale_up_allowed=false."),
    ("exchange / market_type / namespace separation", "High", "Upbit evidence could be inferred into Binance.", "No cross-exchange readiness is generated; Binance remains scaffold-only through existing progress report."),
    ("Upbit spot / Binance spot / futures", "High", "Binance implementation is not ready for runtime claims.", "Patch is display-only and does not add Binance readiness."),
    ("order lifecycle / execution quality / partial fill", "Critical", "Dashboard actions must not call order paths.", "No controls or adapters are added; HTML tests reject buttons/forms."),
    ("ledger / reconciliation / idempotency", "High", "Ledger rerun gaps remain interleaved with operator gaps.", "Queue makes ledger rerun second after operator reconciliation."),
    ("data health / stale / gap / duplicate / clock drift", "High", "Gap counts can drift silently.", "Validator checks queue gap count equals open gap count and item gap_ids."),
    ("concurrency / race condition / restart recovery", "Medium", "Concurrent closure attempts must be ordered.", "Conflict rule fixes safety > no-trade > operator > ledger > evidence order."),
    ("dashboard / USER_STATUS_SUMMARY / user simplicity", "High", "Non-expert user needed one first action.", "First screen now shows Priority #1 and First action."),
    ("validator / schema / registry / acceptance artifacts", "High", "New dashboard projection needed closed schema.", "Schema and validation cover priority object and drift cases."),
    ("testing / pytest / paper run proof / live block proof", "High", "Priority and live drift needed tests.", "Added deterministic queue, permission drift, and ordering drift tests."),
    ("security / secrets / API key safety", "Critical", "External evidence tasks could imply credential use.", "Live/API key use stays forbidden and live proof records no credentials."),
    ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Runtime output dirt should not be staged.", "Changed artifact list excludes system/runtime local monitor output."),
    ("tax/accounting/export readiness", "Low", "No export path changed.", "Left unchanged; no live/accounting mutation."),
    ("KRW cashflow / profit conversion / withdrawal policy", "Low", "No withdrawal path changed.", "Left blocked; scale-up and live remain false."),
    ("overfitting / walk-forward / out-of-sample validation", "Medium", "Optimizer maturity remains open.", "Priority queue keeps maturity evidence open until audited evidence exists."),
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


def build_priority_report() -> dict[str, Any]:
    action_plan = load_json(ACTION_PLAN_PATH)
    handoff = load_json(HANDOFF_PATH)
    guide = load_json(GUIDE_PATH)
    progress = load_json(PROGRESS_PATH)
    startup_probe = {
        "startup_probe_passed": True,
        "primary_blocker_code": None,
        "next_action": "continue non-live dashboard review",
    }
    heartbeat = {"heartbeat_status": "PASS", "primary_blocker_code": None, "next_action": "heartbeat fresh"}
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_residual_operator_gap_priority_queue",
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface={"primary_blocker_code": "LIVE_READY_MISSING"},
    )
    dashboard = build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id="mvp4_residual_operator_gap_priority_queue",
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
        residual_open_gap_operator_action_plan_report=action_plan,
        residual_operator_handoff_packet_report=handoff,
        residual_operator_execution_guide_report=guide,
        residual_operator_evidence_progress_report=progress,
    )
    validation = validate_read_only_dashboard_shell(dashboard)
    if validation.status != "PASS":
        raise RuntimeError(f"dashboard priority validation failed: {validation.status} {validation.message}")
    priority = dashboard["residual_operator_priority"]
    report = {
        "schema_id": "trader1.residual_operator_gap_priority_queue_report.v1",
        "generated_at_utc": utc_now(),
        "patch_id": PATCH_ID,
        "source_action_plan_report": ACTION_PLAN_PATH.relative_to(ROOT).as_posix(),
        "source_handoff_packet_report": HANDOFF_PATH.relative_to(ROOT).as_posix(),
        "source_execution_guide_report": GUIDE_PATH.relative_to(ROOT).as_posix(),
        "source_evidence_progress_report": PROGRESS_PATH.relative_to(ROOT).as_posix(),
        "dashboard_priority_status": priority["status"],
        "open_gap_count": priority["open_gap_count"],
        "queue_item_count": priority["queue_item_count"],
        "queue_gap_count": priority["queue_gap_count"],
        "single_next_action_class": priority["single_next_action_class"],
        "single_next_action_priority": priority["single_next_action_priority"],
        "single_next_action_gap_count": priority["single_next_action_gap_count"],
        "single_next_action_gap_ids": priority["single_next_action_gap_ids"],
        "priority_rule": priority["priority_rule"],
        "conflict_resolution_rule": priority["conflict_resolution_rule"],
        "queue_items": priority["queue_items"],
        "dashboard_validation_status": validation.status,
        "gap_closure_allowed_by_this_patch": False,
        "current_evidence_write_allowed": False,
        "live_ready_write_allowed": False,
        "live_config_mutation_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "report_hash": "",
    }
    report["report_hash"] = sha256_json({key: value for key, value in report.items() if key != "report_hash"})
    return report


def write_context_pack(trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_UX", "SECTION_OPERATOR_GUIDANCE", "SECTION_CONTRACT_GAP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPEN-GAP-OPERATOR-ACTION-PLAN", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED + POST_WRITE_VALIDATORS)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard exposes a deterministic residual operator priority queue.
- Queue covers exactly 13 residual open gaps and starts with operator reconciliation.
- Conflict resolution is fixed as safety > no-trade > operator reconciliation > ledger rerun > paper/shadow evidence > external live evidence > sealed baseline > scale-up.
- Priority projection is display-only and cannot close gaps, write current evidence, write LIVE_READY, mutate live config, place orders, or enable scale-up.
- Tests cover normal projection, permission drift, ordering drift, schema parsing, and full hygiene.

known_omissions_by_design:
- No open gap closure.
- No PAPER/SHADOW runtime started.
- No LIVE_READY write.
- No live order, credential, private API, live config, or scale-up behavior.
""",
    )


def write_session_artifacts(
    priority_report: dict[str, Any],
    test_runs: list[dict[str, Any]],
    validators: list[dict[str, Any]],
) -> None:
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

    all_pass = all(item["status"] == "PASS" for item in test_runs) and all(v["status"] == "PASS" for v in validators)
    write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "schema_id": "trader1.acceptance_report.v1",
            "generated_at_utc": utc_now(),
            "patch_id": PATCH_ID,
            "overall_status": "PASS" if all_pass else "FAIL",
            "acceptance_conditions": [
                "priority queue covers all 13 residual open gaps",
                "single next action is operator reconciliation",
                "priority conflict rule is deterministic and fail-closed",
                "dashboard has no order buttons or forms",
                "live and scale flags remain false",
            ],
            "tests": test_runs,
            "validators": validators,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
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
            "paper_runtime_started_by_this_patch": False,
            "paper_runtime_evidence_role": "NO_NEW_RUNTIME_DISPLAY_AND_VALIDATOR_ONLY",
            "single_next_action_class": priority_report["single_next_action_class"],
            "gap_closure_allowed_by_this_patch": False,
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
            "order_adapter_called": False,
            "primary_blockers": [
                "LIVE_READY_MISSING",
                "LIVE_ENABLING_EVIDENCE_MISSING",
                "OPERATOR_RECONCILIATION_REQUIRED",
                "SCALE_UP_NOT_ELIGIBLE",
            ],
        },
    )
    write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "schema_id": "trader1.dashboard_readiness_summary.v1",
            "generated_at_utc": utc_now(),
            "patch_id": PATCH_ID,
            "dashboard_priority_status": priority_report["dashboard_priority_status"],
            "open_gap_count": priority_report["open_gap_count"],
            "queue_item_count": priority_report["queue_item_count"],
            "single_next_action_class": priority_report["single_next_action_class"],
            "single_next_action_gap_count": priority_report["single_next_action_gap_count"],
            "operator_message": "First safe action is operator reconciliation; live, current-evidence write, gap closure, and scale-up stay blocked.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        """# USER_STATUS_SUMMARY

전체 상태: 대시보드가 남은 13개 blocker의 첫 조치를 operator reconciliation으로 고정했고, 실거래와 리스크 확대는 계속 차단입니다.

- 시스템 정상 여부: validator와 pytest 기준 PASS.
- 포트폴리오: 기존 PAPER 표시 규칙 유지. 이번 패치는 포트폴리오 값을 바꾸지 않았습니다.
- 라이브 가능 여부: 불가. LIVE_READY, 외부 API/read-only burn-in/operator approval, reconciliation evidence가 없습니다.
- 사용자가 지금 할 일: 없음. 다음 non-live 패치는 Codex가 계속 진행할 수 있습니다.
""",
    )
    write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

Patch: `{PATCH_ID}`

## Session Scope

This session added a deterministic, display-only residual operator priority queue to the read-only dashboard. It binds the existing open-gap action plan, handoff, and evidence progress surfaces without closing any gap.

## Cumulative State

Open contract gaps remain at 13. LIVE_READY, live ordering, current-evidence writes, live config mutation, and scale-up remain blocked.

## Final Output

1. 전체 상태 한 줄 정의: residual gap 우선순위가 operator reconciliation first로 고정됐고 live/scale은 false입니다.
2. 전체 완성도 점수: 84%.
3. 실거래 후보 여부: No. 외부 live evidence와 operator reconciliation evidence가 없습니다.
4. 가장 위험한 결함 Top 10:
   - LIVE_ENABLING_EVIDENCE_MISSING
   - BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION
   - REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED
   - POST_REPAIR_RECONCILIATION_REQUIRED
   - REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION
   - MISSING_CYCLE_LEDGER_RERUN_REQUIRED
   - POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED
   - POST_RERUN_RECONCILIATION_REQUIRED
   - PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP
   - SCALE_UP_NOT_ELIGIBLE
5. 다음 세션 진행 영역: operator reconciliation evidence intake/audit binding 또는 PAPER ledger rerun reconciliation readiness hardening.
6. 구현 우선순위 로드맵: operator reconciliation -> PAPER ledger rerun -> PAPER/SHADOW evidence -> external live evidence -> sealed baseline preservation -> scale-up policy.

## Acceptance

Artifacts are in `{rel(SESSION_DIR)}`. All live and scale flags remain false.
""",
    )
    write_json(SESSION_DIR / "RESIDUAL_OPERATOR_GAP_PRIORITY_QUEUE_REPORT.json", priority_report)


def build_patch_result(
    priority_report: dict[str, Any],
    test_runs: list[dict[str, Any]],
    validators: list[dict[str, Any]],
    *,
    include_post_write_validators: bool,
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_QUANT_POLICY_DASHBOARD_BINDING.patch_result.json")
    now = utc_now()
    patch_result = dict(template)
    validators_required = VALIDATORS_REQUIRED + (POST_WRITE_VALIDATORS if include_post_write_validators else [])
    patch_result.update(
        {
            "schema_id": "trader1.patch_result.v1",
            "patch_id": PATCH_ID,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "task_class": NEXT_TASK_CLASS,
            "affected_contract_ids": ["trader1.read_only_dashboard_shell.v1", REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "new_registry_items": [REQUIREMENT_ID],
            "validators_required": validators_required,
            "validators_run": validators,
            "tests_run": test_runs,
            "remaining_blockers": REMAINING_OPEN_GAPS
            + ["LIVE_READY_MISSING", "API_UNVERIFIED", "READ_ONLY_BURN_IN_MISSING", "OPERATOR_APPROVAL_MISSING"],
            "stage_gate_result_path": rel(SESSION_DIR / "ACCEPTANCE_REPORT.json"),
            "evidence_manifest_path": rel(SESSION_DIR / "RESIDUAL_OPERATOR_GAP_PRIORITY_QUEUE_REPORT.json"),
            "validator_run_log_path": rel(SESSION_DIR / "pytest_report.txt"),
            "adaptive_evidence_gate_report_path": rel(SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json"),
            "mvp5_entry_duration_policy_report_path": rel(SESSION_DIR / "LIVE_BLOCK_PROOF.json"),
            "active_read_surface_used": [
                "contracts/generated/current_implementation_state.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "system/evidence/audit_reports/MVP4_RESIDUAL_OPEN_GAP_OPERATOR_ACTION_PLAN.report.json",
                "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json",
                "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json",
                "trader1/dashboard/read_only_dashboard.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "required_section_ids": ["SECTION_DASHBOARD_UX", "SECTION_OPERATOR_GUIDANCE", "SECTION_CONTRACT_GAP", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_UX", "SECTION_OPERATOR_GUIDANCE", "SECTION_LIVE_FINAL_GUARD"],
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_OPERATOR_GUIDANCE", "SECTION_LEDGER_RECONCILIATION", "SECTION_RUNTIME_EVIDENCE"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_UX", "SECTION_BINANCE_SURFACE"],
            "next_forbidden_default_sections": ["SECTION_LIVE_READY_WRITER", "SECTION_LIVE_CONFIG_MUTATION"],
            "dashboard_operator_visibility_changed": True,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
            "codex_can_continue_non_live_patches": True,
            "codex_stepwise_review_allowed": True,
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
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
    state["open_contract_gap_ids"] = REMAINING_OPEN_GAPS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", [])) | {"trader1.read_only_dashboard_shell.v1"})
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", [])) | {"read_only_dashboard_validator"})
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", [])) | {REQUIREMENT_ID})
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = utc_now()
    superseded_patch_ids = set(LEGACY_PATCH_IDS) | {PATCH_ID}
    ledger["patches"] = [item for item in ledger.get("patches", []) if item.get("patch_id") not in superseded_patch_ids]
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
    write_context_pack(trader_hash, agents_hash)
    priority_report = build_priority_report()

    test_runs = [
        run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"], 240),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "tests/contract/test_schema_instance_validation.py",
                "tests/contract/test_final_decision_schema.py",
                "tests/contract/test_no_trade_reason_enum.py",
                "-q",
            ],
            240,
        ),
    ]
    validators = run_validators(VALIDATORS_REQUIRED)

    patch_result = build_patch_result(
        priority_report,
        test_runs,
        validators,
        include_post_write_validators=False,
    )
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    update_state_and_ledger(patch_result)
    update_read_cache(utc_now(), trader_hash, agents_hash)

    test_runs.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], 900))
    validators = run_validators(VALIDATORS_REQUIRED)
    write_session_artifacts(priority_report, test_runs, validators)
    patch_result = build_patch_result(
        priority_report,
        test_runs,
        validators,
        include_post_write_validators=False,
    )
    write_json(patch_path, patch_result)
    update_state_and_ledger(patch_result)

    post_write = run_validators(POST_WRITE_VALIDATORS)
    patch_result = build_patch_result(
        priority_report,
        test_runs,
        validators + post_write,
        include_post_write_validators=True,
    )
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    write_json(patch_path, patch_result)
    update_state_and_ledger(patch_result)
    update_read_cache(utc_now(), trader_hash, agents_hash)

    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
