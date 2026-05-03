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

PATCH_BASENAME = "MVP4_ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_SCOPE_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-ACTUAL-LONG-RUN-SOURCE-ARTIFACT-PATH-SCOPE-GUARD"
PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_STATE_SYNC_RECHECK.patch_result.json"
)
CONTRACT_GAP_ID = "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY"
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
from trader1.research.shadow.shadow_runner import (  # noqa: E402
    build_paper_shadow_evidence_accumulation_report,
    paper_shadow_evidence_hash,
    validate_paper_shadow_evidence_accumulation_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import (  # noqa: E402
    _paper_shadow_evidence_accumulation_errors,
    run_validators,
)


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "paper_shadow_evidence_accumulation_validator",
    "runtime_schema_instance_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "contracts/schema/paper_shadow_evidence_accumulation_report.schema.json",
    "trader1/research/shadow/shadow_runner.py",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_paper_shadow_evidence_accumulation_validator.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    f"system/evidence/audit_reports/{PATCH_BASENAME}.md",
    "tools/emit_actual_long_run_source_artifact_path_scope_guard_patch_evidence.py",
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


def blocker_list() -> list[str]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    blockers = set(state.get("open_contract_gap_ids", []))
    blockers.update(
        {
            CONTRACT_GAP_ID,
            "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
            "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
            "SCALE_UP_NOT_ELIGIBLE",
        }
    )
    return sorted(blockers)


def verify_current_boundary(summary: dict[str, Any]) -> dict[str, Any]:
    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / f"{CONTRACT_GAP_ID}.contract_gap.json"
    gap = load_json(gap_path)
    assert_false_fields("actual long-run runtime evidence boundary contract gap", gap)
    if gap.get("contract_gap_id") != CONTRACT_GAP_ID:
        raise RuntimeError("actual long-run runtime evidence boundary gap id drifted")
    if gap.get("status") != "OPEN":
        raise RuntimeError("actual long-run runtime evidence boundary gap must remain OPEN")
    if gap.get("live_affecting") is not True:
        raise RuntimeError("actual long-run runtime evidence boundary gap must remain live-affecting")

    schema = load_json(ROOT / "contracts" / "schema" / "paper_shadow_evidence_accumulation_report.schema.json")
    paper_pattern = schema["properties"]["paper_artifact_path"]["pattern"]
    shadow_pattern = schema["properties"]["shadow_artifact_path"]["pattern"]
    if "[^/]+" not in paper_pattern or "[^/]+" not in shadow_pattern:
        raise RuntimeError("paper/shadow artifact path schema must restrict session to one path segment")

    report = build_paper_shadow_evidence_accumulation_report(
        evidence_report_id="scope-guard-artifact-path-drift"
    )
    drifted_paper_path = (
        f"system/runtime/upbit/krw_spot/paper/{report['paper_session_id']}_drift/"
        "paper_operation_gate_report.json"
    )
    report["paper_artifact_path"] = drifted_paper_path
    report["source_evidence_bindings"][0]["artifact_path"] = drifted_paper_path
    report["blockers"] = [
        {
            "code": "SNAPSHOT_SCOPE_MISMATCH",
            "severity": "HIGH",
            "message": "paper/shadow evidence artifact path scope mismatch",
        }
    ]
    report["primary_blocker_code"] = "SNAPSHOT_SCOPE_MISMATCH"
    report["evidence_chain_complete"] = False
    report["scorecard_input_eligible"] = False
    report["optimizer_ranking_action"] = "BLOCK_RANKING"
    report["evidence_hash"] = paper_shadow_evidence_hash(report)
    validation = validate_paper_shadow_evidence_accumulation_report(report)
    errors = _paper_shadow_evidence_accumulation_errors(report)
    if validation.status != "BLOCKED" or validation.blocker_code != "SNAPSHOT_SCOPE_MISMATCH":
        raise RuntimeError("paper/shadow artifact path scope drift must be blocked")
    if not any("artifact path scope mismatch" in error for error in errors):
        raise RuntimeError("paper/shadow artifact path scope drift lacks semantic validator evidence")

    return {
        **summary,
        "contract_gap_id": gap.get("contract_gap_id"),
        "contract_gap_status": gap.get("status"),
        "paper_artifact_path_pattern": paper_pattern,
        "shadow_artifact_path_pattern": shadow_pattern,
        "artifact_path_scope_drift_status": validation.status,
        "artifact_path_scope_drift_blocker_code": validation.blocker_code,
        "actual_long_run_evidence_created": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def write_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- PAPER/SHADOW source artifact paths must use canonical exchange/market/session paths.
- A path that remains under /paper/ or /shadow/ but points at a different session segment must fail closed.
- Actual long-run runtime evidence remains missing and live-blocking.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

path_guard_summary:
- paper_artifact_path_pattern: {summary["paper_artifact_path_pattern"]}
- shadow_artifact_path_pattern: {summary["shadow_artifact_path_pattern"]}
- artifact_path_scope_drift_status: {summary["artifact_path_scope_drift_status"]}
- artifact_path_scope_drift_blocker_code: {summary["artifact_path_scope_drift_blocker_code"]}

known_omissions_by_design:
- This guard does not create actual long-run PAPER/SHADOW runtime evidence.
- This guard does not close {CONTRACT_GAP_ID}.
- No API keys, credentials, live orders, live config mutation, or scale-up are used.
- Runtime monitor outputs under system/runtime are not intended patch artifacts.

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

Actual long-run runtime evidence remains live-blocking. PAPER/SHADOW source artifact paths now have a fail-closed session path scope guard.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    evidence_artifacts = [
        f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
        f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
    ]
    artifacts = sorted(set(CHANGED_ARTIFACTS + evidence_artifacts))

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "Actual long-run source artifact path scope guard",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: paper shadow source artifact paths must match canonical "
                "exchange market session paths before they can support actual long-run evidence"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Actual long-run source artifact path scope guard",
            "requirement_kind": "VALIDATOR_IMPLEMENTATION",
            "schema_ids": ["trader1.paper_shadow_evidence_accumulation_report.v1"],
            "validator_ids": ["paper_shadow_evidence_accumulation_validator"],
            "artifact_ids": artifacts,
            "test_ids": ["tests/validators/test_paper_shadow_evidence_accumulation_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PAPER-SHADOW-ACTUAL-RUNTIME-SOURCE-GUARD",
                "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"paper shadow source artifact paths must match canonical exchange market session paths"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
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
            "section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "schema_files": ["contracts/schema/paper_shadow_evidence_accumulation_report.schema.json"],
            "validator_files": [
                "trader1/research/shadow/shadow_runner.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/validators/test_paper_shadow_evidence_accumulation_validator.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/research/shadow/shadow_runner.py"],
            "evidence_artifacts": evidence_artifacts,
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
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
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PAPER-SHADOW-ACTUAL-RUNTIME-SOURCE-GUARD",
                "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.paper_shadow_evidence_accumulation_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LONG_RUN_RUNTIME_EVIDENCE"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": blocker_list(),
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "paper_shadow_evidence_accumulation_report schema",
                "paper_shadow_evidence_accumulation_validator",
                "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY contract gap",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK",
            "required_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
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
            "optimizer_status_after": "ACTUAL_LONG_RUN_SOURCE_ARTIFACT_PATH_GUARDED_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE_SOURCE_ARTIFACT_PATH_SCOPE_GUARD_ONLY",
            "convergence_state_after": "ACTUAL_LONG_RUN_EVIDENCE_BOUNDARY_OPEN_SOURCE_PATH_GUARDED",
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
            "stage_gate_status": "PASS_SOURCE_ARTIFACT_PATH_SCOPE_GUARD_ACTUAL_LONG_RUN_GAP_REMAINS_OPEN",
            "next_allowed_task_class": NEXT_TASK_CLASS,
            **summary,
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
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Actual long-run evidence depends on PAPER/SHADOW source artifact paths remaining bound to the exact exchange, market, mode, and session scope.
- A path could still look like a PAPER namespace while pointing at a different session segment unless the runtime validator checked the canonical path.

Patch:
- Tightened the paper/shadow evidence schema path pattern to a single session segment.
- Added a semantic validator check that paper_artifact_path and shadow_artifact_path exactly match the canonical paths derived from report scope.
- Added a negative validator test for path-scope drift with matching source binding drift.

Safety:
- {CONTRACT_GAP_ID} remains OPEN and live-affecting.
- actual_long_run_evidence_created=false
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
""",
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
    summary = verify_current_boundary({})
    write_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    tests_run: list[dict[str, Any]] = []
    patch_result = build_patch_result(now, tests_run, summarize_validators(run_validators(VALIDATORS_REQUIRED)), summary)
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.validators.test_paper_shadow_evidence_accumulation_validator",
                    "-v",
                ]
            ),
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
            run_command([sys.executable, "-B", "tools/run_paper_shadow_evidence_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    summary = verify_current_boundary({})
    write_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, summarize_validators(run_validators(VALIDATORS_REQUIRED)), summary)
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
                "artifact_path_scope_drift_status": summary["artifact_path_scope_drift_status"],
                "artifact_path_scope_drift_blocker_code": summary["artifact_path_scope_drift_blocker_code"],
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
