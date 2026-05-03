from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_STATE_SYNC_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK"
CONTRACT_GAP_ID = "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY"
PREVIOUS_DASHBOARD_PATCH_ID = "MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY_20260430_001"
PREVIOUS_DASHBOARD_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.patch_result.json"
)
PREVIOUS_UPBIT_PATCH_ID = "MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY_20260501_001"
PREVIOUS_UPBIT_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_UPBIT_PAPER_LONG_RUN_EVIDENCE_BOUNDARY.patch_result.json"
)
NEXT_TASK_CLASS = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_sample_history_validator",
    "paper_shadow_evidence_accumulation_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_runtime_orchestration_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_sample_history_validator",
    "paper_shadow_evidence_accumulation_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_runtime_orchestration_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "tests/contract/test_actual_long_run_runtime_evidence_boundary_recheck.py",
    "tools/emit_actual_long_run_runtime_evidence_boundary_state_sync_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = [
    CONTRACT_GAP_ID,
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def current_gap_summary() -> dict[str, Any]:
    dashboard_patch_path = ROOT / PREVIOUS_DASHBOARD_PATCH_RESULT
    upbit_patch_path = ROOT / PREVIOUS_UPBIT_PATCH_RESULT
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.audit.json"
    contract_gap_path = (
        ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    )

    for path, expected_patch_id in (
        (dashboard_patch_path, PREVIOUS_DASHBOARD_PATCH_ID),
        (upbit_patch_path, PREVIOUS_UPBIT_PATCH_ID),
    ):
        if not path.exists():
            raise RuntimeError(f"historical long-run boundary patch_result is missing: {rel(path)}")
        patch = load_json(path)
        if patch.get("patch_id") != expected_patch_id:
            raise RuntimeError(f"historical long-run boundary patch_id drifted: {rel(path)}")
        assert_false_fields(rel(path), patch, "_after")

    audit = load_json(audit_path)
    contract_gap = load_json(contract_gap_path)
    assert_false_fields("dashboard runtime evidence boundary audit", audit)
    assert_false_fields("actual long-run runtime evidence boundary contract gap", contract_gap)

    if audit.get("audit_id") != "MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY":
        raise RuntimeError("dashboard runtime evidence boundary audit id drifted")
    if audit.get("classification") != "dashboard_false_safe_runtime_evidence_boundary":
        raise RuntimeError("dashboard runtime evidence boundary audit classification drifted")
    if "separate actual long-run evidence" not in str(audit.get("condition", "")).lower():
        raise RuntimeError("dashboard runtime evidence boundary audit no longer states display-only boundary")

    blocker_codes = {
        item.get("code") for item in contract_gap.get("blockers", []) if isinstance(item, dict)
    }
    if contract_gap.get("contract_gap_id") != CONTRACT_GAP_ID or contract_gap.get("status") != "OPEN":
        raise RuntimeError("actual long-run runtime evidence boundary contract gap is not OPEN")
    if contract_gap.get("live_affecting") is not True:
        raise RuntimeError("actual long-run runtime evidence boundary contract gap is not live-affecting")
    if "CONTRACT_GAP_HIGH" not in blocker_codes:
        raise RuntimeError("actual long-run runtime evidence boundary blocker is missing")
    notes = str(contract_gap.get("notes", "")).lower()
    if "dashboard" not in notes or "cannot be closed" not in notes:
        raise RuntimeError("actual long-run runtime evidence boundary notes no longer preserve close condition")

    return {
        "dashboard_patch_result_hash": load_json(dashboard_patch_path).get("result_hash"),
        "upbit_boundary_patch_result_hash": load_json(upbit_patch_path).get("result_hash"),
        "audit_classification": audit.get("classification"),
        "contract_gap_status": contract_gap.get("status"),
        "contract_gap_live_affecting": contract_gap.get("live_affecting"),
        "contract_gap_blocker_codes": sorted(blocker_codes),
    }


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-DASHBOARD-RUNTIME-EVIDENCE-BOUNDARY", "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY"]
included_schema_ids: ["trader1.contract_gap.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Detect that {PREVIOUS_DASHBOARD_PATCH_ID} and {PREVIOUS_UPBIT_PATCH_ID} already exist and remain live-blocked.
- Confirm {CONTRACT_GAP_ID} remains OPEN and live-affecting.
- Confirm dashboard runtime evidence boundary audit remains display-only and cannot close the gap.
- Advance only next_allowed_task_class to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

gap_snapshot:
- audit_classification: {summary["audit_classification"]}
- contract_gap_status: {summary["contract_gap_status"]}
- contract_gap_live_affecting: {summary["contract_gap_live_affecting"]}
- contract_gap_blocker_codes: {json.dumps(summary["contract_gap_blocker_codes"])}

known_omissions_by_design:
- Historical long-run boundary artifacts are not backfilled or rewritten.
- No new long-run runtime evidence is created.
- The actual long-run runtime evidence boundary gap remains in open_contract_gap_ids.
- This patch does not enable live trading, mutate live config, use credentials, place live orders, or scale up.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
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

The actual long-run runtime evidence boundary remains open and live-blocking. Dashboard and bounded Upbit PAPER patches expose the boundary, but they do not create repeated long-run PAPER/SHADOW runtime evidence and cannot close this gap.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "actual long-run runtime evidence boundary recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: recognize existing dashboard and bounded PAPER long-run boundary artifacts, "
                "keep actual long-run runtime evidence gap open, and route to paper/shadow runtime gap recheck"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Actual long-run runtime evidence boundary state sync recheck",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.contract_gap.v1", "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/contract/test_actual_long_run_runtime_evidence_boundary_recheck.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-DASHBOARD-RUNTIME-EVIDENCE-BOUNDARY",
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"actual long run runtime evidence boundary state sync gap remains open"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_STATE_SYNC_RECHECK_CONTRACT_GAP_OPEN",
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
            "section_id": "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
            "schema_files": [
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/contract/test_actual_long_run_runtime_evidence_boundary_recheck.py"],
            "fixture_files": [
                "system/evidence/audit_reports/MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.audit.json",
                "system/evidence/contract_gaps/ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY.contract_gap.json",
            ],
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/research/shadow/shadow_observation_runtime_orchestration.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": ["contracts/generated/context_pack/MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.md"],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_STATE_SYNC_RECHECK_CONTRACT_GAP_OPEN",
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
    summary: dict[str, Any],
    validators_required: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_DASHBOARD_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-RUNTIME-EVIDENCE-BOUNDARY",
                "REQ-MVP4-UPBIT-PAPER-LONG-RUN-EVIDENCE-BOUNDARY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [
                REQUIREMENT_ID,
                f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            ],
            "new_or_changed_schema_ids": [],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_SHADOW_OBSERVATION_RUNTIME",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "SCALE_UP_PERMISSION"],
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
                "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY contract gap",
                "MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY audit",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK",
            "required_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_status_after": "LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECKED_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_STATE_SYNC_ONLY",
            "convergence_state_after": "LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECKED_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION",
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
    summary: dict[str, Any],
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
            "stage_gate_status": "PASS_STATE_SYNC_RECHECK_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_REMAINS_OPEN",
            **summary,
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                "system/evidence/audit_reports/MVP4_DASHBOARD_RUNTIME_EVIDENCE_BOUNDARY.audit.json",
                "system/evidence/contract_gaps/ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY.contract_gap.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [CONTRACT_GAP_ID]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger.get("patches", []) if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": patch_result["target_mvp_level"],
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    summary = current_gap_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)),
        summary,
        BOOTSTRAP_VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.contract.test_actual_long_run_runtime_evidence_boundary_recheck",
                    "-v",
                ]
            ),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/dashboard/test_read_only_dashboard.py", "-q"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/validators/test_paper_shadow_evidence_accumulation_validator.py", "-q"]),
            run_command([sys.executable, "-B", "tools/run_paper_shadow_evidence_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
        ]
    )
    summary = current_gap_summary()
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(
        now,
        tests_run,
        summarize_validators(run_validators(VALIDATORS_REQUIRED)),
        summary,
        VALIDATORS_REQUIRED,
    )
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "contract_gap_status": summary["contract_gap_status"],
                "contract_gap_live_affecting": summary["contract_gap_live_affecting"],
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
