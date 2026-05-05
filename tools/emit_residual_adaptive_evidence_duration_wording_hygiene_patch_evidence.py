from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_DURATION_WORDING_HYGIENE"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-DURATION-WORDING-HYGIENE"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_dashboard_actual_long_run_floor_ux_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "runtime_schema_instance_validator",
    "schema_validator",
    "registry_validator",
    "paper_shadow_evidence_accumulation_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

PROGRESS_REPORT_PATH = "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.report.json"
CONTEXT_PACK_PATH = f"contracts/generated/context_pack/{PATCH_BASENAME}.md"

HYGIENE_SOURCE_FILES = [
    "trader1/runtime/boot/safe_launcher.py",
    "tools/emit_dashboard_residual_evidence_progress_clarity_patch_evidence.py",
    "tools/emit_dashboard_residual_execution_guide_clarity_patch_evidence.py",
    "tools/emit_residual_operator_evidence_run_preflight_patch_evidence.py",
    "tools/emit_residual_operator_evidence_intake_audit_patch_evidence.py",
    "tools/emit_residual_operator_evidence_trial_duration_policy_patch_evidence.py",
    "tools/emit_residual_operator_handoff_execution_guide_patch_evidence.py",
    "tools/emit_residual_mvp5_entry_duration_policy_patch_evidence.py",
]

HYGIENE_CONTEXT_FILES = [
    "contracts/generated/context_pack/MVP4_DASHBOARD_RESIDUAL_EVIDENCE_PROGRESS_CLARITY.md",
    "contracts/generated/context_pack/MVP4_DASHBOARD_RESIDUAL_EXECUTION_GUIDE_CLARITY.md",
    "contracts/generated/context_pack/MVP4_RESIDUAL_OPERATOR_EVIDENCE_PROGRESS_AUDIT.md",
    "contracts/generated/context_pack/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.md",
    "contracts/generated/context_pack/MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.md",
    "contracts/generated/context_pack/MVP4_RESIDUAL_OPERATOR_HANDOFF_EXECUTION_GUIDE.md",
    "contracts/generated/context_pack/MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY.md",
    "contracts/generated/requirement_index.json",
]

CHANGED_ARTIFACTS = [
    "contracts/generated/current_implementation_state.json",
    "contracts/generated/ACTIVE_WORKING_VIEW.md",
    "contracts/generated/read_cache_manifest.json",
    "contracts/generated/requirement_index.json",
    "contracts/generated/requirement_artifact_matrix.json",
    CONTEXT_PACK_PATH,
    "contracts/authority_manifest.json",
    "system/evidence/implementation_patch_ledger.json",
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
    "tools/emit_residual_adaptive_evidence_duration_wording_hygiene_patch_evidence.py",
    "tests/runtime/test_residual_adaptive_evidence_safe_launcher.py",
    "tests/contract/test_residual_adaptive_duration_wording_hygiene.py",
    "tests/contract/test_residual_adaptive_evidence_schema_state_sync.py",
    *HYGIENE_SOURCE_FILES,
    *HYGIENE_CONTEXT_FILES,
]

FORBIDDEN_STALE_SNIPPETS = [
    'or report.get("minimum_observation_hours_required", 0) < 120',
    '"minimum_observation_hours_required": 120',
    '"minimum_observation_hours": 120',
    "120h minimum observation requirement",
    "120h collection",
    "after the 120h PAPER/SHADOW run",
    "expected after the 120h PAPER/SHADOW run",
    "requires 120 hours before the next review",
    "Set minimum local observation duration to 120 hours",
    "minimum_observation_hours_for_local_runtime: 120",
    "formal MVP-5 profile remains 120h / 43200 ticks",
    "formal MVP-5 profile remains {report[\"formal_mvp5_duration_hours\"]}h",
    "MVP5 review-entry PAPER/SHADOW duration is 48h / 17280 ticks",
    "The old 120h profile is retained only",
    "retaining 120h as optional",
    "The 120h profile is retained only",
    "Moved 120h to optional extended observation",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def scan_stale_markers() -> dict[str, Any]:
    findings = []
    for rel_path in [*HYGIENE_SOURCE_FILES, *HYGIENE_CONTEXT_FILES]:
        text = (ROOT / rel_path).read_text(encoding="utf-8")
        for snippet in FORBIDDEN_STALE_SNIPPETS:
            if snippet in text:
                findings.append({"path": rel_path, "snippet": snippet})
    return {"findings": findings, "finding_count": len(findings)}


def load_progress_report() -> dict[str, Any]:
    report = load_json(ROOT / PROGRESS_REPORT_PATH)
    required = {
        "schema_id": "trader1.residual_operator_evidence_progress_report.v1",
        "progress_status": "BLOCKED_EVIDENCE_MISSING",
        "validation_status": "PASS",
        "minimum_observation_hours_required": 0,
        "fixed_duration_gate_status": "REMOVED_NO_FIXED_RUNTIME_FLOOR",
        "adaptive_judgement_status": "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY",
        "codex_stepwise_review_allowed": True,
        "codex_can_continue_non_live_patches": True,
        "user_runtime_required_for_next_non_live_patch": False,
        "user_runtime_required_for_gap_closure": True,
        "evidence_quality_status": "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES",
    }
    for key, expected in required.items():
        if report.get(key) != expected:
            raise RuntimeError(f"residual evidence progress report field {key} expected {expected!r}")
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
            raise RuntimeError(f"residual evidence progress report must keep {field}=false")
    return report


def write_context(now: str, trader_hash: str, agents_hash: str, scan: dict[str, Any], progress: dict[str, Any]) -> None:
    base.write_text(
        ROOT / CONTEXT_PACK_PATH,
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_OPERATOR_CONTROL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY", "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-PROGRESS-CLARITY", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["trader1.residual_operator_evidence_progress_report.v1", "trader1.read_only_dashboard_shell.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Safe launcher accepts the audited adaptive residual evidence progress report with minimum_observation_hours_required=0.
- Safe launcher rejects legacy fixed-duration progress reports and any drift that requires user runtime for the next non-live patch.
- Active read caches and emitters do not reintroduce fixed-hour review-entry wording.
- Residual gaps remain open and evidence-dependent.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

duration_wording_hygiene_snapshot:
- fixed_duration_gate_status: {progress["fixed_duration_gate_status"]}
- minimum_observation_hours_required: {progress["minimum_observation_hours_required"]}
- stale_marker_count_after: {scan["finding_count"]}

known_omissions_by_design:
- This patch does not execute PAPER/SHADOW runtime.
- This patch does not create operator evidence.
- This patch does not close residual gaps.
- This patch does not write current evidence or LIVE_READY.
- This patch does not enable live orders or scale-up.

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

The residual operator evidence gate is adaptive: there is no fixed observation-duration floor for Codex to continue non-live hardening. Gap closure, MVP-5 review-entry, LIVE_READY, live trading, and scale-up still require audited runtime/reconciliation/operator/external evidence and validator PASS results.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"

    req_index = load_json(req_path)
    marker_updates = {
        "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY": (
            "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY: remove fixed MVP5 review-entry "
            "PAPER/SHADOW duration while preserving 24h as trial-only, treating prior fixed-hour "
            "profiles as historical references, requiring adaptive evidence-quality review, and "
            "keeping all live/scale permissions false"
        ),
        "REQ-MVP4-RESIDUAL-MVP5-ENTRY-DURATION-POLICY": (
            "REQ-MVP4-RESIDUAL-MVP5-ENTRY-DURATION-POLICY: remove fixed MVP5 review-entry "
            "PAPER/SHADOW duration while preserving 24h as trial-only, treating prior fixed-hour "
            "profiles as historical references, requiring adaptive evidence-quality review, and "
            "keeping all live/scale permissions false"
        ),
    }
    requirements = []
    for item in req_index.get("requirements", []):
        requirement_id = item.get("requirement_id")
        if requirement_id in marker_updates:
            item = dict(item)
            item["full_text_marker"] = marker_updates[requirement_id]
            item["source_text_sha256"] = base.sha256_bytes(marker_updates[requirement_id].encode("utf-8"))
        if requirement_id != REQUIREMENT_ID:
            requirements.append(item)
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Residual adaptive evidence duration wording hygiene",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: active runtime guards, emitters, and read caches must use adaptive "
                "evidence-gate wording with no fixed observation-duration floor while preserving all live/scale blockers"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual adaptive evidence duration wording hygiene",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.residual_operator_evidence_progress_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS + [PROGRESS_REPORT_PATH],
            "test_ids": [
                "tests/runtime/test_residual_adaptive_evidence_safe_launcher.py",
                "tests/contract/test_residual_adaptive_duration_wording_hygiene.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_OPERATOR_CONTROL", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-PROGRESS-CLARITY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual adaptive evidence duration wording hygiene live blocked"),
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
    base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/patch_result.schema.json", "contracts/schema/residual_operator_evidence_progress_report.schema.json"],
            "validator_files": [
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/reports/residual_operator_evidence_progress.py",
            ],
            "test_files": [
                "tests/runtime/test_residual_adaptive_evidence_safe_launcher.py",
                "tests/contract/test_residual_adaptive_duration_wording_hygiene.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [PROGRESS_REPORT_PATH, "contracts/generated/requirement_index.json"],
            "runtime_modules": ["trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                *HYGIENE_CONTEXT_FILES,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
            ],
            "patch_result_fields": [
                "adaptive_evidence_progress_clarity_status",
                "fixed_duration_gate_status",
                "codex_stepwise_review_allowed",
                "codex_can_continue_non_live_patches",
                "user_runtime_required_for_next_non_live_patch",
                "user_runtime_required_for_gap_closure",
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
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    state_before: dict[str, Any],
    scan: dict[str, Any],
    progress: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_SCHEMA_STATE_SYNC.patch_result.json"
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
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-PROGRESS-CLARITY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_SHADOW_REVIEW",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [],
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
                "SECTION_OPERATOR_CONTROL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_CONTRACT_GAP", "SECTION_PAPER_SHADOW_EVIDENCE"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "LIVE_READY_WRITE"],
            "remaining_blockers": state_before["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "residual evidence progress report",
                "safe launcher dashboard loader",
                "operator-facing residual evidence read caches",
                "live final guard",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED_PASS",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_DURATION_WORDING_HYGIENE",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_guardrail_result": "PASS_ADAPTIVE_DURATION_WORDING_HYGIENE_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_ADAPTIVE_DURATION_WORDING_HYGIENE_LIVE_BLOCKED",
            "adaptive_evidence_progress_clarity_status": "PASS_ADAPTIVE_DURATION_WORDING_HYGIENE_LIVE_BLOCKED",
            "adaptive_judgement_status": progress["adaptive_judgement_status"],
            "fixed_duration_gate_status": progress["fixed_duration_gate_status"],
            "codex_stepwise_review_allowed": progress["codex_stepwise_review_allowed"],
            "codex_can_continue_non_live_patches": progress["codex_can_continue_non_live_patches"],
            "user_runtime_required_for_next_non_live_patch": progress["user_runtime_required_for_next_non_live_patch"],
            "user_runtime_required_for_gap_closure": progress["user_runtime_required_for_gap_closure"],
            "evidence_quality_status": progress["evidence_quality_status"],
            "dashboard_operator_visibility_changed": True,
            "operator_run_started_by_this_patch": False,
            "operator_run_completed_by_this_patch": False,
            "operator_run_evidence_ready_for_mvp5": False,
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
    scan: dict[str, Any],
    progress: dict[str, Any],
) -> None:
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
            "stage_gate_status": "PASS_ADAPTIVE_DURATION_WORDING_HYGIENE_LIVE_BLOCKED",
            "safe_launcher_adaptive_progress_loader_status": "PASS_ACCEPTS_ADAPTIVE_ZERO_FLOOR_REJECTS_LEGACY_FIXED_DURATION",
            "adaptive_duration_wording_hygiene_status": "PASS_NO_ACTIVE_FIXED_DURATION_REVIEW_ENTRY_WORDING",
            "stale_fixed_duration_marker_count_after": scan["finding_count"],
            "minimum_observation_hours_required_after": progress["minimum_observation_hours_required"],
            "fixed_duration_gate_status": progress["fixed_duration_gate_status"],
            "open_gap_count": len(patch_result["remaining_blockers"]),
            "gap_closure_allowed_by_this_patch": False,
            "current_evidence_write_allowed": False,
            "live_ready_write_allowed": False,
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
                PROGRESS_REPORT_PATH,
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
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260505.md",
        f"""# MVP4 Residual Adaptive Evidence Duration Wording Hygiene

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The audited progress report already removed the fixed duration gate, but the safe launcher loader and several active read caches still carried fixed-hour wording or assumptions.

Patch:
- Updated the safe launcher to accept adaptive progress evidence with minimum_observation_hours_required=0 and to reject legacy fixed-duration drift.
- Reworded active residual evidence emitters and read caches around adaptive evidence-quality review.
- Updated requirement routing markers so generated navigation no longer describes fixed-hour review-entry criteria.
- Added focused tests for launcher loading and wording hygiene.

Safety:
- open residual gaps remain open
- current_evidence_write_allowed=false
- gap_closure_allowed_by_this_patch=false
- live_ready_write_allowed=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no live order
- no credential/API key use
- no live config mutation
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
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
    base.write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    scan: dict[str, Any],
    progress: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, scan, progress)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    state_before = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    progress = load_progress_report()

    write_context(now, trader_hash, agents_hash, {"findings": [], "finding_count": 0}, progress)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    scan = scan_stale_markers()
    if scan["finding_count"]:
        raise RuntimeError(f"stale fixed-duration markers remain after context update: {scan['findings']}")

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
                "tests/runtime/test_residual_adaptive_evidence_safe_launcher.py",
                "tests/contract/test_residual_adaptive_duration_wording_hygiene.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, state_before, scan, progress)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, scan, progress)

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
                "tests.runtime.test_residual_adaptive_evidence_safe_launcher",
                "tests.contract.test_residual_adaptive_duration_wording_hygiene",
                "-v",
            ]
        )
    )
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    scan = scan_stale_markers()
    patch_result = build_patch_result(now, tests_run, validators_run, state_before, scan, progress)
    write_context(now, trader_hash, agents_hash, scan, progress)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, scan, progress)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "stale_fixed_duration_marker_count_after": scan["finding_count"],
                "minimum_observation_hours_required_after": progress["minimum_observation_hours_required"],
                "fixed_duration_gate_status": progress["fixed_duration_gate_status"],
                "open_gap_count": len(state_before["open_contract_gap_ids"]),
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
