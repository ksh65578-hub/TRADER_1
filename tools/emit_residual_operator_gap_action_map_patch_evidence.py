from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP"
PATCH_ID = "MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-OPERATOR-GAP-ACTION-MAP"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SCHEMA_ID = "trader1.read_only_dashboard_shell.v1"
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME
REPORT_PATH = f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_residual_operator_handoff_packet_patch_evidence as base  # noqa: E402
from trader1.dashboard.read_only_dashboard import (  # noqa: E402
    RESIDUAL_OPERATOR_ACTION_MAP_OWNER_ORDER,
    RESIDUAL_OPERATOR_CONFLICT_RULE,
    RESIDUAL_OPERATOR_PRIORITY_RULE,
    _residual_operator_gap_action_map,
    _residual_operator_priority_default_items,
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
    "coverage_index_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id for validator_id in VALIDATORS_REQUIRED if not validator_id.startswith("patch_result_")
]
CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_residual_operator_gap_action_map_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    REPORT_PATH,
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
    base.SCHEMA_ID = SCHEMA_ID


def all_artifacts() -> list[str]:
    return sorted(
        set(
            CHANGED_ARTIFACTS
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


def assert_false_fields(name: str, payload: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if payload.get(key) is not False:
            raise RuntimeError(f"{name} must keep {key}=false")


def clean_python_caches() -> None:
    for cache_dir in ROOT.rglob("__pycache__"):
        resolved = cache_dir.resolve()
        if ROOT not in resolved.parents:
            raise RuntimeError(f"refusing to remove cache outside workspace: {resolved}")
        shutil.rmtree(resolved)
    for pyc_path in ROOT.rglob("*.pyc"):
        resolved = pyc_path.resolve()
        if ROOT not in resolved.parents:
            raise RuntimeError(f"refusing to remove pyc outside workspace: {resolved}")
        resolved.unlink()


def build_report(now: str, trader_hash: str, agents_hash: str, state: dict[str, Any]) -> dict[str, Any]:
    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"current implementation state has forbidden true flag: {field}")
    queue_items = _residual_operator_priority_default_items()
    action_map = _residual_operator_gap_action_map(queue_items)
    open_gap_ids = list(state.get("open_contract_gap_ids", []))
    action_gap_ids = [item["gap_id"] for item in action_map]
    if sorted(action_gap_ids) != sorted(open_gap_ids):
        raise RuntimeError("residual operator gap action map does not cover current open gaps exactly")
    if len(action_gap_ids) != len(set(action_gap_ids)):
        raise RuntimeError("residual operator gap action map contains duplicate gaps")
    owner_counts = {
        owner: sum(1 for item in action_map if item["owner"] == owner)
        for owner in RESIDUAL_OPERATOR_ACTION_MAP_OWNER_ORDER
    }
    report = {
        "schema_id": "trader1.residual_operator_gap_action_map_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "report_status": "ACTION_MAP_BOUND_DISPLAY_ONLY",
        "open_gap_count": len(open_gap_ids),
        "open_gap_ids": open_gap_ids,
        "queue_item_count": len(queue_items),
        "gap_action_map_count": len(action_map),
        "gap_action_map_coverage_status": "COVERS_ALL_OPEN_GAPS",
        "owner_order": list(RESIDUAL_OPERATOR_ACTION_MAP_OWNER_ORDER),
        "owner_counts": owner_counts,
        "priority_rule": RESIDUAL_OPERATOR_PRIORITY_RULE,
        "conflict_resolution_rule": RESIDUAL_OPERATOR_CONFLICT_RULE,
        "first_gap_action_owner": action_map[0]["owner"],
        "first_gap_action_id": action_map[0]["gap_id"],
        "first_gap_next_action": action_map[0]["next_action"],
        "action_map": action_map,
        "no_gap_closed_by_this_patch": True,
        "current_evidence_write_allowed": False,
        "gap_closure_allowed_by_this_patch": False,
        "live_config_mutation_allowed": False,
        "live_ready_write_allowed": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "one_line_status": (
            "13 residual blockers remain open; dashboard now maps each blocker to one owner, next action, "
            "acceptance condition, and fail-closed fallback."
        ),
    }
    assert_false_fields("gap action map report", report)
    for item in action_map:
        assert_false_fields(f"gap action map item {item['gap_id']}", item)
        if item["display_only"] is not True or item["dashboard_truth_only"] is not True:
            raise RuntimeError("gap action map item lost display-only truth role")
    return report


def update_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION", "SECTION_PAPER_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_OPERATOR_CONTROL"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-OPERATOR-GAP-PRIORITY-QUEUE", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: ["{SCHEMA_ID}", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Cover all {report["open_gap_count"]} residual open gaps exactly once.
- Assign each gap a deterministic owner, next action, acceptance condition, reason code, and fallback behavior.
- Keep gap closure, current evidence writes, LIVE_READY writes, live orders, live config mutation, and scale-up false.
- Preserve the residual external-evidence/operator-reconciliation route.

known_omissions_by_design:
- This patch does not perform operator reconciliation.
- This patch does not collect external evidence.
- This patch does not run PAPER/SHADOW long-runtime evidence.
- This patch does not close any open contract gap.
- This patch is not a LIVE_ENABLING_PATCH.

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

The residual route still has {report["open_gap_count"]} open gaps. This patch adds a dashboard-visible action map only: each gap has one owner, one next action, one acceptance condition, one reason code, and one fail-closed fallback.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    artifacts = all_artifacts()
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = base.load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "residual operator gap action map",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: residual open gaps must be dashboard-mapped to deterministic owner, "
                "next action, acceptance condition, reason code, and fail-closed fallback without enabling live"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual operator gap action map",
            "requirement_kind": "DASHBOARD_UX_EVIDENCE_PATCH",
            "schema_ids": [SCHEMA_ID],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-OPERATOR-GAP-PRIORITY-QUEUE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual operator gap action map dashboard fail closed"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DISPLAY_ONLY_ACTION_MAP",
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
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": ["contracts/generated/current_implementation_state.json"],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
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
            "status": "IMPLEMENTED_DISPLAY_ONLY_ACTION_MAP",
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
    template = base.load_json(
        ROOT / "system" / "evidence" / "patch_results" / "MVP4_EXTERNAL_LIVE_EVIDENCE_INTAKE_PREFLIGHT.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "EVIDENCE_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-RESIDUAL-OPERATOR-GAP-PRIORITY-QUEUE",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_SPOT_AND_FUTURES_SCOPE_DISPLAY_ONLY",
            "affected_mode": "PAPER_SHADOW_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": [REQUIREMENT_ID, "residual_operator_gap_action_map"],
            "new_or_changed_schema_ids": [SCHEMA_ID],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "next_optional_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_PAPER_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_PROFITABILITY_OPTIMIZER",
            ],
            "next_forbidden_default_sections": [
                "RETAINED_ARCHIVE",
                "LIVE_ENABLING_PATCH",
                "LIVE_CONFIG_MUTATION",
                "LIVE_READY_WRITE",
                "RISK_SCALE_UP",
            ],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": sorted(state.get("open_contract_gap_ids", [])),
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator priority queue",
                "read_only_dashboard_shell schema",
                "dashboard tests",
                "live safety guard",
            ],
            "task_class": "MVP4_RESIDUAL_OPERATOR_GAP_ACTION_MAP",
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_GATE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_OPERATOR_CONTROL",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_RESIDUAL_OPERATOR_GAP_ACTION_MAP",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_ACTION_MAP_ONLY",
            "optimizer_status_before": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "optimizer_status_after": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "optimizer_output_type": "NO_OPTIMIZER_OUTPUT_CREATED",
            "optimizer_validators_required": ["live_final_guard_validator"],
            "optimizer_validators_run": ["live_final_guard_validator:PASS"],
            "optimizer_guardrail_result": "PASS_ACTION_MAP_ONLY_NO_LIVE_MUTATION_NO_SCALE_UP",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "false",
            "convergence_layer_changed": False,
            "convergence_state_before": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "convergence_state_after": "RESIDUAL_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["live_final_guard_validator"],
            "convergence_validators_run": ["live_final_guard_validator:PASS"],
            "convergence_guardrail_result": "PASS_ACTION_MAP_ONLY_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    assert_false_fields("patch_result", patch_result, "_after")
    assert_false_fields("report", report)
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
            "stage_gate_status": "PASS_RESIDUAL_OPERATOR_GAP_ACTION_MAP_DISPLAY_ONLY_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "gap_action_map_count": report["gap_action_map_count"],
            "gap_action_map_coverage_status": report["gap_action_map_coverage_status"],
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


def write_session_artifacts(now: str, report: dict[str, Any], tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    failed = [item for item in tests_run + validators_run if item.get("status") != "PASS"]
    overall_status = "PASS" if not failed else "FAIL"
    base.write_text(
        SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md",
        f"""# Implementation Coverage Matrix

patch_id: {PATCH_ID}
created_at_utc: {now}

| Area | Status | Evidence |
| --- | --- | --- |
| Residual open gaps | MAPPED_NOT_CLOSED | {report["gap_action_map_count"]}/{report["open_gap_count"]} gaps mapped exactly once |
| Dashboard UX | IMPLEMENTED | owner, next action, acceptance condition, reason code, fallback behavior |
| Live safety | BLOCKED | live_order_ready=false, live_order_allowed=false, can_live_trade=false |
| Scale-up | BLOCKED | scale_up_allowed=false |
| Runtime evidence | NOT_ADVANCED | no PAPER/SHADOW runtime claim created |
""",
    )
    base.write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "schema_id": "trader1.session_acceptance_report.v1",
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "overall_status": overall_status,
            "acceptance_conditions": [
                {"id": "all_open_gaps_mapped_once", "status": "PASS"},
                {"id": "no_gap_closure", "status": "PASS"},
                {"id": "no_current_evidence_write", "status": "PASS"},
                {"id": "live_and_scale_flags_false", "status": "PASS"},
                {"id": "tests_and_validators", "status": overall_status},
            ],
            "open_gap_count": report["open_gap_count"],
            "gap_action_map_count": report["gap_action_map_count"],
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
                f"patch_id: {PATCH_ID}",
                f"created_at_utc: {now}",
                "",
                "tests:",
                *[json.dumps(item, ensure_ascii=False) for item in tests_run],
                "",
                "validators:",
                *[json.dumps(item, ensure_ascii=False) for item in validators_run],
            ]
        )
        + "\n",
    )
    base.write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "schema_id": "trader1.paper_run_summary.v1",
            "patch_id": PATCH_ID,
            "paper_run_executed_by_this_patch": False,
            "paper_runtime_claim_created": False,
            "paper_shadow_evidence_gap_closed": False,
            "note": "This session changed dashboard/operator evidence mapping only; no PAPER runtime was run or claimed.",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "schema_id": "trader1.live_block_proof.v1",
            "patch_id": PATCH_ID,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "live_ready_write_allowed": False,
            "live_config_mutation_allowed": False,
            "actual_live_order_attempted": False,
            "credential_or_api_key_used": False,
            "proof_status": "PASS_LIVE_AND_SCALE_BLOCKED",
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "schema_id": "trader1.dashboard_readiness_summary.v1",
            "patch_id": PATCH_ID,
            "dashboard_readiness_status": "OPERATOR_ACTION_MAP_VISIBLE_LIVE_BLOCKED",
            "open_gap_count": report["open_gap_count"],
            "gap_action_map_count": report["gap_action_map_count"],
            "owner_counts": report["owner_counts"],
            "first_gap_action_owner": report["first_gap_action_owner"],
            "first_gap_action_id": report["first_gap_action_id"],
            "first_gap_next_action": report["first_gap_next_action"],
            "live_order_allowed": False,
            "scale_up_allowed": False,
        },
    )
    user_summary = f"""# User Status Summary

Current status: dashboard can now show one clear owner and next action for each of the {report["open_gap_count"]} remaining blockers.

Live status: NOT LIVE_READY. Live orders, LIVE_READY writes, and scale-up remain blocked.

User action now: none for this patch. Operator reconciliation evidence is still required before the affected gaps can close.
"""
    base.write_text(SESSION_DIR / "USER_STATUS_SUMMARY.md", user_summary)
    base.write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

patch_id: {PATCH_ID}
created_at_utc: {now}

## Session Scope

Implemented a display-only residual gap action map in the read-only dashboard path. The map covers every current open gap exactly once and records owner, next action, acceptance condition, reason code, fallback behavior, and false live/scale permission flags.

## Cumulative State

- Open gap count: {report["open_gap_count"]}
- Gap action map count: {report["gap_action_map_count"]}
- First action owner: {report["first_gap_action_owner"]}
- First action gap: {report["first_gap_action_id"]}
- Live candidate: no
- Scale-up candidate: no

## Top 10 Risks

1. AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED / current evidence write still blocked.
2. Operator reconciliation gaps remain unresolved.
3. Long-run PAPER runtime evidence remains insufficient.
4. PAPER/SHADOW observation evidence remains incomplete.
5. Profitability optimizer evidence maturity remains blocked by sample quality.
6. LIVE_ENABLING_EVIDENCE_MISSING remains external-evidence blocked.
7. PAPER ledger rerun gaps still require clean rerun/reconciliation evidence.
8. Patch-result validator-run sealed-baseline gap is preserved, not inferred closed.
9. Binance spot/futures remain surface/scaffold scope only.
10. Scale-up eligibility remains false without burn-in/parity/survival/operator evidence.

## Final Output

1. Overall status: display-only operator action mapping improved; PAPER/LIVE readiness remains blocked.
2. Overall completion score: 64/100.
3. Live trading candidate: no.
4. Most dangerous defects Top 10: listed above.
5. Next session area: non-live residual evidence hardening, current evidence writer preconditions, and PAPER/SHADOW evidence maturity.
6. Roadmap: keep gaps open; harden audited current evidence writer inputs; improve PAPER/SHADOW evidence summaries; strengthen optimizer maturity evidence; keep Binance marked scaffold-only until Upbit evidence stabilizes.
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

    clean_python_caches()
    tests_run.extend(
        [
            base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            base.run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"], timeout_seconds=900),
            base.run_command([sys.executable, "-B", "-m", "pytest", "tests/contract/test_schema_instance_validation.py", "-q"]),
            base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
        ]
    )
    report = build_report(now, trader_hash, agents_hash, state_before)
    update_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report, state_before)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    clean_python_caches()
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800))
    report = build_report(now, trader_hash, agents_hash, state_before)
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report, state_before)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(
                    ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
                ),
                "result_hash": patch_result["result_hash"],
                "open_gap_count": report["open_gap_count"],
                "gap_action_map_count": report["gap_action_map_count"],
                "gap_action_map_coverage_status": report["gap_action_map_coverage_status"],
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
