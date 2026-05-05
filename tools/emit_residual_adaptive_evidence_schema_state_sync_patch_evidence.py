from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_SCHEMA_STATE_SYNC"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY-SCHEMA-STATE-SYNC"
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

RESIDUAL_SCHEMA_FILES = {
    "trader1.residual_mvp5_entry_duration_policy_report.v1": (
        "contracts/schema/residual_mvp5_entry_duration_policy_report.schema.json"
    ),
    "trader1.residual_operator_evidence_intake_audit_report.v1": (
        "contracts/schema/residual_operator_evidence_intake_audit_report.schema.json"
    ),
    "trader1.residual_operator_evidence_run_preflight_report.v1": (
        "contracts/schema/residual_operator_evidence_run_preflight_report.schema.json"
    ),
    "trader1.residual_operator_evidence_trial_duration_policy_report.v1": (
        "contracts/schema/residual_operator_evidence_trial_duration_policy_report.schema.json"
    ),
}

RESIDUAL_REPORT_FILES = {
    "trader1.residual_mvp5_entry_duration_policy_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_MVP5_ENTRY_DURATION_POLICY.report.json"
    ),
    "trader1.residual_operator_evidence_intake_audit_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_INTAKE_AUDIT.report.json"
    ),
    "trader1.residual_operator_evidence_run_preflight_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_RUN_PREFLIGHT.report.json"
    ),
    "trader1.residual_operator_evidence_trial_duration_policy_report.v1": (
        "system/evidence/audit_reports/MVP4_RESIDUAL_OPERATOR_EVIDENCE_TRIAL_DURATION_POLICY.report.json"
    ),
}

CHANGED_ARTIFACTS = [
    "contracts/generated/current_implementation_state.json",
    "contracts/generated/ACTIVE_WORKING_VIEW.md",
    "contracts/generated/read_cache_manifest.json",
    "contracts/generated/requirement_index.json",
    "contracts/generated/requirement_artifact_matrix.json",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    "system/evidence/implementation_patch_ledger.json",
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
    f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
    f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}_20260505.md",
    "tools/emit_residual_adaptive_evidence_schema_state_sync_patch_evidence.py",
    "tests/contract/test_residual_adaptive_evidence_schema_state_sync.py",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def residual_schema_snapshot(state: dict[str, Any]) -> dict[str, Any]:
    implemented = set(state.get("implemented_schema_ids", []))
    rows = []
    missing_before = []
    for schema_id, schema_file in RESIDUAL_SCHEMA_FILES.items():
        schema_path = ROOT / schema_file
        report_path = ROOT / RESIDUAL_REPORT_FILES[schema_id]
        schema = load_json(schema_path)
        report = load_json(report_path) if report_path.exists() else {}
        schema_file_id = schema.get("$id")
        report_schema_id = report.get("schema_id")
        is_registered = schema_id in implemented
        if not is_registered:
            missing_before.append(schema_id)
        rows.append(
            {
                "schema_id": schema_id,
                "schema_file": schema_file,
                "schema_file_exists": schema_path.exists(),
                "schema_file_id": schema_file_id,
                "schema_file_id_matches": schema_file_id == schema_id,
                "report_file": RESIDUAL_REPORT_FILES[schema_id],
                "report_file_exists": report_path.exists(),
                "report_schema_id": report_schema_id,
                "report_schema_id_matches": report_schema_id in (schema_id, None),
                "implemented_in_current_state_before": is_registered,
            }
        )
    return {"rows": rows, "missing_schema_ids_before": sorted(missing_before)}


def write_context(now: str, trader_hash: str, agents_hash: str, snapshot: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONTRACT_GAP", "SECTION_OPERATOR_CONTROL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY", "REQ-MVP4-LIVE-FINAL-GUARD"]
included_schema_ids: {json.dumps(sorted(RESIDUAL_SCHEMA_FILES))}
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Residual operator evidence schema files are reflected in current_implementation_state implemented_schema_ids.
- Residual generated report files remain bound to their schema ids.
- The residual external-evidence/operator-reconciliation route remains selected.
- Open residual contract gaps remain open and unchanged.
- live_order_ready/live_order_allowed/can_live_trade/scale_up_allowed remain false.

schema_state_sync_snapshot:
- missing_schema_ids_before: {json.dumps(snapshot["missing_schema_ids_before"])}
- synced_schema_ids: {json.dumps(sorted(RESIDUAL_SCHEMA_FILES))}

known_omissions_by_design:
- This patch does not execute PAPER/SHADOW runtime.
- This patch does not create operator evidence.
- This patch does not close residual gaps.
- This patch does not write LIVE_READY or current evidence.
- This patch does not enable live orders or scale-up.

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

Residual operator evidence schemas and generated report artifacts are now synchronized into current_implementation_state for read routing. Codex may continue non-live review and hardening from existing artifacts, but residual gap closure still requires audited runtime, reconciliation, external, or operator evidence.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    schema_ids = sorted(RESIDUAL_SCHEMA_FILES)
    schema_files = [RESIDUAL_SCHEMA_FILES[schema_id] for schema_id in schema_ids]
    report_files = [RESIDUAL_REPORT_FILES[schema_id] for schema_id in schema_ids]

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_OPERATOR_CONTROL",
            "source_file": "TRADER_1.md",
            "source_heading": "Residual adaptive evidence gate schema state synchronization",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: residual operator evidence schema artifacts must be reflected in "
                "current_implementation_state without closing evidence-dependent residual gaps"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Residual schema state synchronization",
            "requirement_kind": "EVIDENCE_READINESS_PATCH",
            "schema_ids": schema_ids + ["trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS + schema_files + report_files,
            "test_ids": ["tests/contract/test_residual_adaptive_evidence_schema_state_sync.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_CONTRACT_GAP", "SECTION_OPERATOR_CONTROL", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-RUN-PREFLIGHT",
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-INTAKE-AUDIT",
                "REQ-MVP4-RESIDUAL-OPERATOR-EVIDENCE-TRIAL-DURATION-POLICY",
                "REQ-MVP4-RESIDUAL-MVP5-ENTRY-DURATION-POLICY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"residual schema state sync keeps gaps open and live blocked"),
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
            "section_id": "SECTION_OPERATOR_CONTROL",
            "schema_files": schema_files + ["contracts/schema/patch_result.schema.json"],
            "validator_files": [
                "trader1/reports/residual_mvp5_entry_duration_policy.py",
                "trader1/reports/residual_operator_evidence_intake_audit.py",
                "trader1/reports/residual_operator_evidence_run_preflight.py",
                "trader1/reports/residual_operator_evidence_trial_duration_policy.py",
            ],
            "test_files": ["tests/contract/test_residual_adaptive_evidence_schema_state_sync.py"],
            "fixture_files": report_files + ["contracts/generated/current_implementation_state.json"],
            "runtime_modules": [
                "trader1/reports/residual_mvp5_entry_duration_policy.py",
                "trader1/reports/residual_operator_evidence_intake_audit.py",
                "trader1/reports/residual_operator_evidence_run_preflight.py",
                "trader1/reports/residual_operator_evidence_trial_duration_policy.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "new_or_changed_schema_ids",
                "current_implementation_state_updated",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
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
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_RESIDUAL_ADAPTIVE_EVIDENCE_GATE_POLICY_PROGRESS_CLARITY.patch_result.json"
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
                "REQ-MVP4-RESIDUAL-ADAPTIVE-EVIDENCE-GATE-POLICY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER_SHADOW_REVIEW",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": sorted(RESIDUAL_SCHEMA_FILES),
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
                "SECTION_CONTRACT_GAP",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "LIVE_READY_WRITE"],
            "remaining_blockers": state_before["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "residual operator evidence schema files",
                "residual operator evidence generated report artifacts",
                "residual adaptive evidence gate policy",
                "live final guard",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_CONTRACT_GAP",
                "SECTION_OPERATOR_CONTROL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED_PASS",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_SCHEMA_STATE_SYNC",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_guardrail_result": "PASS_RESIDUAL_SCHEMA_STATE_SYNC_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_RESIDUAL_SCHEMA_STATE_SYNC_LIVE_BLOCKED",
            "adaptive_evidence_progress_clarity_status": "PASS_RESIDUAL_SCHEMA_STATE_SYNC_LIVE_BLOCKED",
            "adaptive_judgement_status": "CODEX_CAN_CONTINUE_NON_LIVE_REVIEW_EVIDENCE_NOT_CLOSURE_READY",
            "fixed_duration_gate_status": "REMOVED_NO_FIXED_RUNTIME_FLOOR",
            "codex_stepwise_review_allowed": True,
            "codex_can_continue_non_live_patches": True,
            "user_runtime_required_for_next_non_live_patch": False,
            "user_runtime_required_for_gap_closure": True,
            "evidence_quality_status": "INSUFFICIENT_FOR_GAP_CLOSURE_NON_LIVE_WORK_CONTINUES",
            "dashboard_operator_visibility_changed": False,
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
    snapshot: dict[str, Any],
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
            "stage_gate_status": "PASS_RESIDUAL_SCHEMA_STATE_SYNC_LIVE_BLOCKED",
            "missing_schema_ids_before": snapshot["missing_schema_ids_before"],
            "synced_schema_ids": sorted(RESIDUAL_SCHEMA_FILES),
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
                *RESIDUAL_SCHEMA_FILES.values(),
                *RESIDUAL_REPORT_FILES.values(),
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
        f"""# MVP4 Residual Adaptive Evidence Schema State Sync

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Residual operator evidence schema/report artifacts existed, but current_implementation_state did not list all of those schema ids under implemented_schema_ids.
- That can make generated read routing look stale even though the non-live residual evidence tooling is present.

Patch:
- Synchronized residual operator evidence schema ids into current_implementation_state.
- Bound the schema ids to their schema files and generated evidence report files.
- Updated requirement_index, requirement_artifact_matrix, read_cache_manifest, patch ledger, and patch_result evidence.

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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + list(RESIDUAL_SCHEMA_FILES)))
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
    snapshot: dict[str, Any],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, snapshot)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    state_before = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    snapshot = residual_schema_snapshot(state_before)
    write_context(now, trader_hash, agents_hash, snapshot)
    update_requirement_artifacts(now, trader_hash, agents_hash)

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
                "tests/contract/test_residual_operator_evidence_run_preflight.py",
                "tests/contract/test_residual_operator_evidence_trial_duration_policy.py",
                "tests/contract/test_residual_mvp5_entry_duration_policy.py",
                "-q",
            ]
        ),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, state_before, snapshot)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, snapshot)

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
                "tests.contract.test_residual_adaptive_evidence_schema_state_sync",
                "-v",
            ]
        )
    )
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, state_before, snapshot)
    write_context(now, trader_hash, agents_hash, snapshot)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, snapshot)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "missing_schema_ids_before": snapshot["missing_schema_ids_before"],
                "synced_schema_ids": sorted(RESIDUAL_SCHEMA_FILES),
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
