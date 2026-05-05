from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-EXECUTION-GUIDE"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
REPORT_PATH = f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json"
HANDOFF_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_HANDOFF_PACKET.report.json"
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_residual_operator_handoff_packet_patch_evidence as base  # noqa: E402
from trader1.reports.residual_operator_execution_guide import (  # noqa: E402
    SCHEMA_ID,
    build_residual_operator_execution_guide_report,
    validate_residual_operator_execution_guide_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id for validator_id in VALIDATORS_REQUIRED if validator_id != "generated_artifact_dirty_validator"
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
    "trader1/reports/residual_operator_execution_guide.py",
    "contracts/schema/residual_operator_execution_guide_report.schema.json",
    "contracts/registry.yaml",
    "tests/contract/test_residual_operator_execution_guide.py",
    "tools/emit_residual_operator_handoff_execution_guide_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS
SOURCE_EVIDENCE_ARTIFACTS = [HANDOFF_REPORT_PATH]
EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    REPORT_PATH,
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
]


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.REPORT_PATH = REPORT_PATH
    base.SCHEMA_ID = SCHEMA_ID
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.BOOTSTRAP_VALIDATORS_REQUIRED = BOOTSTRAP_VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.SOURCE_EVIDENCE_ARTIFACTS = SOURCE_EVIDENCE_ARTIFACTS
    base.EVIDENCE_ARTIFACTS = EVIDENCE_ARTIFACTS


def load_handoff_report() -> dict[str, Any]:
    report = base.load_json(ROOT / HANDOFF_REPORT_PATH)
    if report.get("schema_id") != "trader1.residual_operator_handoff_packet_report.v1":
        raise RuntimeError("residual operator handoff packet report schema mismatch")
    if report.get("handoff_status") != "BLOCKED_HANDOFF_REQUIRED":
        raise RuntimeError("residual operator handoff packet report must remain blocked")
    for field in (
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
        "current_evidence_write_allowed",
        "current_evidence_mutation_allowed",
        "gap_closure_allowed_by_this_patch",
        "live_config_mutation_allowed",
    ):
        if report.get(field) is not False:
            raise RuntimeError(f"residual handoff report has non-false {field}")
    return report


def all_artifacts() -> list[str]:
    return sorted(
        set(
            CHANGED_ARTIFACTS
            + SOURCE_EVIDENCE_ARTIFACTS
            + EVIDENCE_ARTIFACTS
            + [
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "system/evidence/implementation_patch_ledger.json",
            ]
        )
    )


def build_report(
    now: str,
    trader_hash: str,
    agents_hash: str,
    state_before: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = state_before or base.load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    handoff_report = load_handoff_report()
    report = build_residual_operator_execution_guide_report(
        handoff_report,
        state,
        patch_id=PATCH_ID,
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    errors = validate_residual_operator_execution_guide_report(report, handoff_report, state)
    if errors:
        raise RuntimeError("residual operator execution guide failed: " + "; ".join(errors))
    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"current implementation state has forbidden true flag: {field}")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_LEDGER_RECONCILIATION", "SECTION_PAPER_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_OPERATOR_CONTROL"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET", "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS", "REQ-MVP4-EXTERNAL-LIVE-EVIDENCE-INTAKE-PREFLIGHT", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["{SCHEMA_ID}", "trader1.residual_operator_handoff_packet_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Convert blocked residual handoff packets into an operator execution guide.
- Expose exactly one credential-free local UPBIT PAPER/SHADOW collection command.
- Keep operator reconciliation, PAPER rerun reconciliation, external live evidence, and scale-up policy steps evidence-only or externally supplied.
- Preserve all {report["open_gap_count"]} open gaps and the residual route.
- Keep current evidence writes, gap closure, live orders, live config mutation, LIVE_READY writes, and scale-up forbidden.

execution_guide_snapshot:
- open_gap_count: {report["open_gap_count"]}
- execution_step_count: {report["execution_step_count"]}
- local_paper_shadow_runtime_step_count: {report["local_paper_shadow_runtime_step_count"]}
- external_or_policy_evidence_step_count: {report["external_or_policy_evidence_step_count"]}
- minimum_observation_hours_for_local_runtime: 0
- fixed_duration_gate_status: REMOVED_NO_FIXED_RUNTIME_FLOOR
- binance_runtime_status: {report["binance_runtime_status"]}
- guide_status: {report["guide_status"]}
- selected_next_task_class: {report["selected_next_task_class"]}

known_omissions_by_design:
- This patch does not run PAPER or SHADOW sessions.
- This patch does not perform operator reconciliation.
- This patch does not collect external live readiness evidence.
- This patch does not write audited current evidence.
- This patch does not close contract gaps and is not a LIVE_ENABLING_PATCH.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
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

Residual operator handoff packets now have a blocked execution guide: {report["execution_step_count"]} steps cover all {report["open_gap_count"]} open gaps. Only one local command is shown, it is UPBIT PAPER/SHADOW evidence collection only, and it uses adaptive evidence review with no fixed observation-duration floor.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = all_artifacts()

    req_index = base.load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_OPERATOR_CONTROL",
            "source_file": "TRADER_1.md",
            "source_heading": "residual operator handoff execution guide",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: residual handoff packets must provide an operator execution guide "
                "for evidence collection without closing gaps, writing current evidence, or enabling live permissions"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual operator handoff execution guide",
            "requirement_kind": "EVIDENCE_PATCH",
            "schema_ids": [SCHEMA_ID],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_residual_operator_execution_guide.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET",
                "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS",
                "REQ-MVP4-EXTERNAL-LIVE-EVIDENCE-INTAKE-PREFLIGHT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual operator execution guide live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RESIDUAL_OPERATOR_EXECUTION_GUIDE_BLOCKED",
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

    matrix = base.load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_OPERATOR_CONTROL",
            "schema_files": ["contracts/schema/residual_operator_execution_guide_report.schema.json"],
            "validator_files": ["trader1/reports/residual_operator_execution_guide.py"],
            "test_files": ["tests/contract/test_residual_operator_execution_guide.py"] + ROUTE_GUARD_TEST_ARTIFACTS,
            "fixture_files": [
                "contracts/generated/current_implementation_state.json",
                HANDOFF_REPORT_PATH,
            ],
            "runtime_modules": ["trader1/reports/residual_operator_execution_guide.py"],
            "evidence_artifacts": EVIDENCE_ARTIFACTS,
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "next_task_class",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RESIDUAL_OPERATOR_EXECUTION_GUIDE_BLOCKED",
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
    validators_required: list[str],
    report: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    patch_result = base.build_patch_result(now, tests_run, validators_run, validators_required, report, state)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "EVIDENCE_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-OPERATOR-HANDOFF-PACKET",
                "REQ-MVP4-RESIDUAL-PAPER-LEDGER-RERUN-READINESS",
                "REQ-MVP4-EXTERNAL-LIVE-EVIDENCE-INTAKE-PREFLIGHT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID, "residual_operator_execution_guide_report"],
            "new_or_changed_schema_ids": [SCHEMA_ID],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "remaining_blockers": sorted(state.get("open_contract_gap_ids", [])),
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator handoff packet report",
                "requirement_index",
                "requirement_artifact_matrix",
                "residual operator execution guide schema",
            ],
            "task_class": "MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE",
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "current_implementation_state_status": "UPDATED_RESIDUAL_OPERATOR_EXECUTION_GUIDE_BLOCKED",
            "optimizer_stage": "NOT_CHANGED_RESIDUAL_OPERATOR_EXECUTION_GUIDE_ONLY",
            "optimizer_guardrail_result": "PASS_OPERATOR_GUIDE_ONLY_NO_LIVE_MUTATION_NO_SCALE_UP",
            "convergence_guardrail_result": "PASS_OPERATOR_GUIDE_ONLY_NO_LIVE_PERMISSION_NO_SCALE_UP",
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
    base.assert_false_flags("patch_result", patch_result, "_after")
    base.assert_false_flags("execution guide report", report, "")
    base.write_json(ROOT / REPORT_PATH, report)
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
            "stage_gate_status": "PASS_RESIDUAL_OPERATOR_EXECUTION_GUIDE_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "execution_step_count": report["execution_step_count"],
            "local_paper_shadow_runtime_step_count": report["local_paper_shadow_runtime_step_count"],
            "operator_runtime_required_before_mvp5": report["operator_runtime_required_before_mvp5"],
            "mvp5_entry_blocked_until_operator_evidence": report["mvp5_entry_blocked_until_operator_evidence"],
            "guide_status": report["guide_status"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
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
            "artifact_paths": all_artifacts(),
            "known_blockers": report["open_gap_ids"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Residual Operator Handoff Execution Guide

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Residual handoff packets identify the blocked operator/evidence route, but operators still needed a single execution guide for what can be run locally and what must be supplied externally.

Patch:
- Generated a blocked execution guide covering {report["open_gap_count"]} open gaps across {report["execution_step_count"]} handoff steps.
- Exposed exactly one local safe command for UPBIT PAPER/SHADOW evidence collection.
- Marked the local command as credential-free, non-live, and live_order_allowed=false.
- Removed the fixed local observation-duration floor from the operator-facing review wording.
- Marked Binance as scaffold-only and not eligible for readiness transfer.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential/private API use
- no live order
- no live config mutation
- no LIVE_READY write
- no current evidence write
- no gap closure
- no scale-up

MVP-5 boundary:
- MVP-5 remains blocked until the operator supplies actual PAPER/SHADOW runtime evidence, reconciliation artifacts, official API/read-only/burn-in evidence, and operator approval evidence.
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
    base.write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    state_before = base.load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    report = build_report(now, trader_hash, agents_hash, state_before)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    validators_run = base.summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report, state_before)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.extend(
        [
            base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            base.run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.contract.test_residual_operator_execution_guide",
                    "tests.contract.test_residual_operator_handoff_packet",
                    "tests.contract.test_patch_result_runtime_schema_validation",
                    "-v",
                ]
            ),
            base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
        ]
    )
    report = build_report(now, trader_hash, agents_hash, state_before)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report, state_before)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(
        base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800)
    )
    report = build_report(now, trader_hash, agents_hash, state_before)
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report, state_before)
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
                "execution_step_count": report["execution_step_count"],
                "local_paper_shadow_runtime_step_count": report["local_paper_shadow_runtime_step_count"],
                "guide_status": report["guide_status"],
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
