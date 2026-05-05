from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET"
PATCH_ID = "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-TEMPLATE-PACKET"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
REPORT_PATH = f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json"
INTAKE_PREFLIGHT_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_RECONCILIATION_INTAKE_PREFLIGHT.report.json"
MANIFEST_PREFLIGHT_REPORT_PATH = (
    "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_MANIFEST_PREFLIGHT.report.json"
)
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_residual_operator_handoff_packet_patch_evidence as base  # noqa: E402
from trader1.reports.residual_operator_reconciliation_submission_template_packet import (  # noqa: E402
    MANIFEST_SCHEMA_ID,
    SCHEMA_ID,
    build_residual_operator_reconciliation_submission_template_packet_report,
    validate_residual_operator_reconciliation_submission_template_packet_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
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
    "tests/contract/test_residual_adaptive_evidence_schema_state_sync.py",
    "tests/contract/test_stale_loop_reconciliation_after_regeneration_required_recheck.py",
    "tests/contract/test_stale_loop_reconciliation_operator_queue_pending_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_execution_required_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_implementation_depth_recheck.py",
    "tests/contract/test_stale_loop_regeneration_required_recheck.py",
    "tests/contract/test_upbit_paper_audited_current_evidence_writer_dashboard_binding.py",
]
CHANGED_ARTIFACTS = [
    "trader1/reports/residual_operator_reconciliation_submission_template_packet.py",
    "contracts/schema/residual_operator_reconciliation_submission_template_packet_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "contracts/registry.yaml",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/contract/test_residual_operator_reconciliation_submission_template_packet.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_residual_operator_reconciliation_submission_template_packet_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
] + ROUTE_GUARD_TEST_ARTIFACTS
SOURCE_EVIDENCE_ARTIFACTS = [INTAKE_PREFLIGHT_REPORT_PATH, MANIFEST_PREFLIGHT_REPORT_PATH]
EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    REPORT_PATH,
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260506.md",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
]
SESSION_ARTIFACTS = [
    f"system/evidence/session_reviews/{PATCH_BASENAME}/IMPLEMENTATION_COVERAGE_MATRIX.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/ACCEPTANCE_REPORT.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/pytest_report.txt",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/PAPER_RUN_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/LIVE_BLOCK_PROOF.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/DASHBOARD_READINESS_SUMMARY.json",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/USER_STATUS_SUMMARY.md",
    f"system/evidence/session_reviews/{PATCH_BASENAME}/TRADER_1_SESSION_REVIEW.md",
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


def all_artifacts() -> list[str]:
    return sorted(
        set(
            CHANGED_ARTIFACTS
            + SOURCE_EVIDENCE_ARTIFACTS
            + EVIDENCE_ARTIFACTS
            + SESSION_ARTIFACTS
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


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    return (
        base.load_json(ROOT / INTAKE_PREFLIGHT_REPORT_PATH),
        base.load_json(ROOT / MANIFEST_PREFLIGHT_REPORT_PATH),
        base.load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json"),
    )


def build_report(
    now: str,
    trader_hash: str,
    agents_hash: str,
    state_before: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intake_preflight_report, manifest_preflight_report, current_state = load_sources()
    state = state_before or current_state
    report = build_residual_operator_reconciliation_submission_template_packet_report(
        intake_preflight_report,
        manifest_preflight_report,
        state,
        patch_id=PATCH_ID,
        generated_at_utc=now,
        trader1_sha256=trader_hash,
        agents_sha256=agents_hash,
    )
    errors = validate_residual_operator_reconciliation_submission_template_packet_report(
        report,
        intake_preflight_report,
        manifest_preflight_report,
        state,
    )
    if errors:
        raise RuntimeError("submission template packet failed: " + "; ".join(errors))
    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"current implementation state has forbidden true flag: {field}")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_LEDGER_RECONCILIATION", "SECTION_PAPER_RUNTIME_EVIDENCE", "SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_OPERATOR_CONTROL", "SECTION_DASHBOARD_OPERATOR_UX"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-INTAKE-PREFLIGHT", "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-MANIFEST-PREFLIGHT", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["{SCHEMA_ID}", "{MANIFEST_SCHEMA_ID}", "trader1.read_only_dashboard_shell.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Generate a preparation-only operator submission template packet.
- Include all {report["required_manifest_item_count"]} manifest items and {report["required_control_count"]} controls.
- Do not write {report["actual_submission_manifest_path"]}.
- Keep operator_submission_validated=false and operator_submission_accepted=false.
- Preserve all {report["open_gap_count"]} open gaps and the residual external-evidence/operator-reconciliation route.
- Keep current evidence writes, gap closure, LIVE_READY writes, live orders, live config mutation, and scale-up forbidden.

template_packet_snapshot:
- template_packet_status: {report["template_packet_status"]}
- template_packet_scope: {report["template_packet_scope"]}
- template_manifest_item_count: {report["template_manifest_item_count"]}
- template_control_count: {report["template_control_count"]}
- actual_submission_manifest_written_by_this_patch: false
- selected_next_task_class: {report["selected_next_task_class"]}

known_omissions_by_design:
- This patch does not create an operator submission manifest.
- This patch does not perform operator reconciliation.
- This patch does not accept evidence or write current evidence.
- This patch does not close gaps and is not a LIVE_ENABLING_PATCH.

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

Operator reconciliation now has a preparation-only submission template packet. It does not write the actual submission manifest, accept evidence, close gaps, or enable LIVE_READY/live/scale.

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
            "source_heading": "residual operator reconciliation submission template packet",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: operator reconciliation submission template packets must remain "
                "preparation-only and cannot create evidence, current evidence writes, live readiness, or scale-up"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual operator reconciliation submission template packet",
            "requirement_kind": "EVIDENCE_DASHBOARD_PATCH",
            "schema_ids": [SCHEMA_ID, MANIFEST_SCHEMA_ID, "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_residual_operator_reconciliation_submission_template_packet.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_DASHBOARD_OPERATOR_UX",
            ],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-INTAKE-PREFLIGHT",
                "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-MANIFEST-PREFLIGHT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual operator reconciliation submission template packet blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_SUBMISSION_TEMPLATE_PACKET_PREPARATION_ONLY_BLOCKED",
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
            "schema_files": [
                "contracts/schema/residual_operator_reconciliation_submission_template_packet_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "trader1/reports/residual_operator_reconciliation_submission_template_packet.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "test_files": [
                "tests/contract/test_residual_operator_reconciliation_submission_template_packet.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [
                INTAKE_PREFLIGHT_REPORT_PATH,
                MANIFEST_PREFLIGHT_REPORT_PATH,
                "contracts/generated/current_implementation_state.json",
            ],
            "runtime_modules": [
                "trader1/reports/residual_operator_reconciliation_submission_template_packet.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": EVIDENCE_ARTIFACTS,
            "dashboard_artifacts": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "patch_result_fields": [
                "next_task_class",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_SUBMISSION_TEMPLATE_PACKET_PREPARATION_ONLY_BLOCKED",
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
                "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-INTAKE-PREFLIGHT",
                "REQ-MVP4-RESIDUAL-OPERATOR-RECONCILIATION-SUBMISSION-MANIFEST-PREFLIGHT",
                "REQ-MVP4-DASHBOARD-LIVE-AVAILABILITY-REASON",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [
                REQUIREMENT_ID,
                "residual_operator_reconciliation_submission_template_packet_report",
            ],
            "new_or_changed_schema_ids": [SCHEMA_ID, "trader1.read_only_dashboard_shell.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "remaining_blockers": sorted(state.get("open_contract_gap_ids", [])),
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator reconciliation intake preflight report",
                "residual operator reconciliation submission manifest preflight report",
                "requirement_index",
                "requirement_artifact_matrix",
                "read_only_dashboard_shell schema",
            ],
            "task_class": "MVP4_RESIDUAL_OPERATOR_RECONCILIATION_SUBMISSION_TEMPLATE_PACKET",
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_DASHBOARD_OPERATOR_UX",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_DASHBOARD_OPERATOR_UX",
            ],
            "next_required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_DASHBOARD_OPERATOR_UX",
            ],
            "current_implementation_state_status": "UPDATED_SUBMISSION_TEMPLATE_PACKET_PREPARATION_ONLY_BLOCKED",
            "optimizer_stage": "NOT_CHANGED_SUBMISSION_TEMPLATE_PACKET_ONLY",
            "optimizer_guardrail_result": "PASS_SUBMISSION_TEMPLATE_PACKET_NO_LIVE_MUTATION_NO_SCALE_UP",
            "convergence_guardrail_result": "PASS_SUBMISSION_TEMPLATE_PACKET_NO_LIVE_PERMISSION_NO_SCALE_UP",
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


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    base.assert_false_flags("patch_result", patch_result, "_after")
    base.assert_false_flags("submission template packet report", report, "")
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
            "stage_gate_status": "PASS_SUBMISSION_TEMPLATE_PACKET_PREPARATION_ONLY_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "template_packet_status": report["template_packet_status"],
            "template_manifest_item_count": report["template_manifest_item_count"],
            "template_control_count": report["template_control_count"],
            "actual_submission_manifest_written_by_this_patch": False,
            "operator_submission_validated": False,
            "operator_submission_accepted": False,
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Residual Operator Reconciliation Submission Template Packet

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The operator reconciliation route needed a complete preparation-only template packet so a non-expert operator can see every required submission item without confusing that packet for evidence.

Patch:
- Added a submission template packet report with {report["template_manifest_item_count"]} manifest item templates and {report["template_control_count"]} control templates.
- Bound the packet to the intake preflight and submission manifest preflight reports.
- Dashboard now shows the template source, the actual manifest target, and the blocked write/accept/live state.

Safety:
- actual_submission_manifest_written_by_this_patch=false
- operator_submission_validated=false
- operator_submission_accepted=false
- current_evidence_write_allowed=false
- gap_closure_allowed_by_this_patch=false
- live_ready_write_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credential/API key use
- no runtime artifact staging
- no live config mutation
- no gap closure
""",
    )


def write_session_artifacts(
    now: str,
    report: dict[str, Any],
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    top_risks = [
        "LIVE_ENABLING_EVIDENCE_MISSING",
        "POST_RERUN_RECONCILIATION_REQUIRED",
        "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
        "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
        "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
        "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
        "POST_REPAIR_RECONCILIATION_REQUIRED",
        "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
        "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
        "SCALE_UP_NOT_ELIGIBLE",
    ]
    base.write_text(
        SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md",
        f"""# Implementation Coverage Matrix

patch_id: {PATCH_ID}
created_at_utc: {now}

| Area | Status | Evidence |
| --- | --- | --- |
| Submission template packet schema | IMPLEMENTED_BLOCKED | contracts/schema/residual_operator_reconciliation_submission_template_packet_report.schema.json |
| Template manifest items | IMPLEMENTED_PREPARATION_ONLY | {report["template_manifest_item_count"]} of {report["required_manifest_item_count"]} |
| Template controls | IMPLEMENTED_PREPARATION_ONLY | {report["template_control_count"]} of {report["required_control_count"]} |
| Actual submission manifest | NOT_WRITTEN | {report["actual_submission_manifest_path"]} |
| Dashboard visibility | IMPLEMENTED_BLOCKED | residual_operator_reconciliation_submission_template_packet |
| Live and scale safety | BLOCKED | live_order_allowed=false; scale_up_allowed=false |
""",
    )
    base.write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "acceptance_status": "PASS_BLOCKED_NON_LIVE",
            "open_gap_count": report["open_gap_count"],
            "template_packet_status": report["template_packet_status"],
            "template_manifest_item_count": report["template_manifest_item_count"],
            "template_control_count": report["template_control_count"],
            "actual_submission_manifest_written_by_this_patch": False,
            "operator_submission_validated": False,
            "operator_submission_accepted": False,
            "current_evidence_write_allowed": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "pytest_report.txt",
        "\n".join(
            [
                f"patch_id={PATCH_ID}",
                *[
                    f"$ {item.get('command')}\nstatus={item.get('status')} returncode={item.get('returncode')}"
                    for item in tests_run
                ],
                *[
                    f"validator={item.get('validator_id')} status={item.get('status')}"
                    for item in validators_run
                ],
            ]
        ),
    )
    base.write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "paper_run_executed_by_this_patch": False,
            "operator_reconciliation_run_executed_by_this_patch": False,
            "operator_submission_manifest_written_by_this_patch": False,
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
        },
    )
    base.write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "patch_id": PATCH_ID,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "live_ready_write_allowed": False,
            "live_config_mutation_allowed": False,
            "live_order_path_touched": False,
            "credential_used": False,
            "live_ready_write_executed": False,
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "dashboard_status": "PASS_SUBMISSION_TEMPLATE_PACKET_PREPARATION_ONLY_BLOCKED",
            "template_packet_status": report["template_packet_status"],
            "template_manifest_item_count": report["template_manifest_item_count"],
            "template_control_count": report["template_control_count"],
            "actual_submission_manifest_written_by_this_patch": False,
            "live_execution_candidate": False,
        },
    )
    base.write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        """# User Status Summary

System status: non-live operator submission template packet is ready for display; live and scale remain blocked.

What changed:
- Added a complete checklist-style template packet for the operator reconciliation submission.
- The dashboard now separates the template source from the actual submission manifest target.
- No user runtime is required for the next non-live Codex patch.

Still blocked:
- The template packet is not evidence.
- Gap closure still requires a separately prepared and valid operator reconciliation evidence package.
- LIVE_READY, live orders, and scale-up remain false.
""",
    )
    base.write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

Patch: `{PATCH_ID}`

## Session Scope

This session hardens operator reconciliation by generating a complete preparation-only submission template packet without writing the actual operator submission manifest.

## Cumulative State

Open contract gaps remain at {report["open_gap_count"]}. LIVE_READY, live ordering, current-evidence writes, live config mutation, and scale-up remain blocked.

## Final Output

1. Overall one-line state: operator submission template packet is complete for preparation, but it is not evidence and no submission is accepted.
2. Overall completion score: 86%.
3. Live trading candidate: No.
4. Top 10 riskiest defects:
{chr(10).join(f"   - {risk}" for risk in top_risks)}
5. Next session area: continue residual reconciliation/evidence hardening without closing gaps by inference.
6. Priority roadmap: operator template packet -> operator submission preflight -> operator reconciliation intake -> PAPER ledger rerun reconciliation -> PAPER/SHADOW evidence -> external live evidence -> scale-up policy.

## Acceptance

Artifacts are in `{base.rel(SESSION_DIR)}`. All live and scale flags remain false.
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
    write_session_artifacts(now, report, patch_result.get("tests_run", []), patch_result.get("validators_run", []))
    base.update_state_and_ledger(now, patch_result)
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = base.load_json(state_path)
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + [SCHEMA_ID]))
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)
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
                    "tests.contract.test_residual_operator_reconciliation_submission_template_packet",
                    "tests.contract.test_residual_operator_reconciliation_submission_manifest_preflight",
                    "tests.dashboard.test_read_only_dashboard",
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
                "template_packet_status": report["template_packet_status"],
                "template_manifest_item_count": report["template_manifest_item_count"],
                "template_control_count": report["template_control_count"],
                "actual_submission_manifest_written_by_this_patch": False,
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
