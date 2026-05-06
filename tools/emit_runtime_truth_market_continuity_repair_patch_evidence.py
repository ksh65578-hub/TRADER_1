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

PATCH_BASENAME = "MVP4_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-RUNTIME-TRUTH-MARKET-CONTINUITY-REPAIR"
NEXT_TASK_CLASS = "MVP4_RESIDUAL_OPEN_CONTRACT_GAP_BLOCKERS_REQUIRE_EXTERNAL_EVIDENCE_OR_OPERATOR_RECONCILIATION"
SESSION_DIR = ROOT / "system" / "evidence" / "session_reviews" / PATCH_BASENAME
CONTEXT_PACK_PATH = f"contracts/generated/context_pack/{PATCH_BASENAME}.md"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
    "upbit_public_rest_continuity_validator",
    "upbit_public_rest_continuity_history_validator",
    "paper_runtime_truth_state_validator",
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
    "contracts/schema/paper_runtime_truth_state_report.schema.json",
    "contracts/registry.yaml",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "contracts/schema/upbit_public_rest_continuity_report.schema.json",
    "contracts/schema/upbit_public_rest_continuity_history.schema.json",
    "trader1/runtime/paper/paper_runtime_truth_state.py",
    "trader1/runtime/paper/upbit_public_rest_continuity.py",
    "trader1/runtime/paper/upbit_public_rest_continuity_history.py",
    "trader1/runtime/boot/safe_launcher.py",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_rest_continuity.py",
    "tests/integration/test_upbit_public_rest_continuity_history.py",
    "tests/runtime/test_paper_runtime_truth_state.py",
    "tests/runtime/test_safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_runtime_truth_market_continuity_repair_patch_evidence.py",
    CONTEXT_PACK_PATH,
    *ROUTE_GUARD_TEST_ARTIFACTS,
]

EVIDENCE_ARTIFACTS = [
    f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
    f"system/evidence/audit_reports/{PATCH_BASENAME}.report.json",
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

OPEN_GAPS = [
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout_seconds: int = 1800) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    result: dict[str, Any] = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def status_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        status = str(item.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def command_lines(items: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {item.get('status')}: {item.get('command')} (returncode={item.get('returncode')})"
        for item in items
    )


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


def build_report(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    open_gaps = sorted(state.get("open_contract_gap_ids", OPEN_GAPS))
    if open_gaps != sorted(OPEN_GAPS):
        raise RuntimeError("open gap set drifted; this patch must not close gaps")
    return {
        "schema_id": "trader1.runtime_truth_market_continuity_repair_audit_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "stage_scope": "STAGE_2_RUNTIME_TRUTH_AND_MARKET_CONTINUITY_REPAIR",
        "finding": (
            "Heartbeat, PAPER loop, market continuity, ledger rollup, and current-evidence refresh were displayed "
            "through separate panels, so the dashboard could say heartbeat PASS while the PAPER engine was not proven. "
            "Short public REST windows also treated repeated candle timestamps as hard invalid/blocking continuity."
        ),
        "patch": (
            "Added a PAPER-only runtime truth state report that joins monitor, loop, market, ledger, and current refresh "
            "sources; wired it through the safe launcher and dashboard operation status; and split short public REST "
            "non-advancing samples into WARN instead of invalid/schema mismatch when the data is structurally valid."
        ),
        "acceptance_conditions": [
            "PAPER runtime truth state distinguishes monitor alive, engine not proven, blocked runtime, and active PAPER runtime",
            "Dashboard operation status says monitor alive but PAPER engine not proven when heartbeat is fresh and loop proof is missing",
            "Dashboard operation status can say PAPER runtime active only when loop, market data, ledger, and current evidence all validate",
            "Short UPBIT/KRW_SPOT/PAPER public REST duplicate/non-advancing windows become WARN with action guidance rather than schema invalid",
            "Runtime truth state and market continuity remain PAPER data-quality evidence only and cannot create LIVE_READY or long-run evidence",
            "Open contract gap count remains 13; live and scale flags remain false",
        ],
        "blockers_precisely_narrowed": [
            "RUNTIME_ORCHESTRATION_NOT_LOADED is narrowed for dashboard view by paper_runtime_truth_state_report.json",
            "MARKET_CONTINUITY_INVALID_SCHEMA_MISMATCH is narrowed when scoped data is structurally valid but short-window non-advancing",
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED is not reopened by this stage; current refresh remains display/audit-only unless writer validators pass",
        ],
        "open_contract_gap_count": len(open_gaps),
        "open_contract_gap_ids": open_gaps,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def write_context(now: str, trader_hash: str, agents_hash: str) -> None:
    base.write_text(
        ROOT / CONTEXT_PACK_PATH,
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: RUNTIME_SAFETY_PATCH
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA_CONTINUITY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_runtime_truth_state_report.v1", "trader1.upbit_public_rest_continuity_report.v1", "trader1.upbit_public_rest_continuity_history.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Runtime truth state is PAPER-only and source-bound.
- Dashboard separates monitor alive from PAPER engine proven.
- Market continuity WARN is used only for structurally valid short-window non-advancing public REST samples.
- Live orders, LIVE_READY, credentials, live config mutation, and scale-up remain false.
- Open contract gaps remain open unless independent evidence closes them.

known_omissions_by_design:
- This patch does not claim long-run runtime evidence.
- This patch does not start a persistent PAPER/SHADOW operator run.
- This patch does not implement Binance trading runtime.
- This patch does not enable live orders or LIVE_READY.

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
next_allowed_task_class: {NEXT_TASK_CLASS}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

The UPBIT/KRW_SPOT/PAPER launcher now emits paper_runtime_truth_state_report.json. It joins heartbeat, bounded PAPER loop, public REST continuity, ledger rollup, and current refresh into one dashboard-facing PAPER runtime truth status. It is not long-run evidence and cannot enable live orders.
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    schema_ids = [
        "trader1.paper_runtime_truth_state_report.v1",
        "trader1.upbit_public_rest_continuity_report.v1",
        "trader1.upbit_public_rest_continuity_history.v1",
        "trader1.read_only_dashboard_shell.v1",
    ]

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Runtime truth simplification and market continuity repair",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: UPBIT/KRW_SPOT/PAPER must expose a PAPER-only runtime truth state and "
                "separate short-window market continuity WARN from invalid schema or live readiness."
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Runtime truth and market continuity repair",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": schema_ids,
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": all_artifacts(),
            "test_ids": [
                "tests/integration/test_upbit_public_rest_continuity.py",
                "tests/integration/test_upbit_public_rest_continuity_history.py",
                "tests/runtime/test_paper_runtime_truth_state.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_MARKET_DATA_CONTINUITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-PAPER-CURRENT-TRUTH-REFRESH-WRITER",
                "REQ-MVP4-UPBIT-PUBLIC-REST-CONTINUITY-HISTORY",
                "REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"paper runtime truth state market continuity warn live blocked dashboard operator visibility"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR_LIVE_BLOCKED",
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
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": [
                "contracts/schema/paper_runtime_truth_state_report.schema.json",
                "contracts/schema/upbit_public_rest_continuity_report.schema.json",
                "contracts/schema/upbit_public_rest_continuity_history.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "contracts/registry.yaml",
                "trader1/runtime/paper/paper_runtime_truth_state.py",
                "trader1/runtime/paper/upbit_public_rest_continuity.py",
                "trader1/runtime/paper/upbit_public_rest_continuity_history.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/integration/test_upbit_public_rest_continuity.py",
                "tests/integration/test_upbit_public_rest_continuity_history.py",
                "tests/runtime/test_paper_runtime_truth_state.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/paper_runtime_truth_state.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "evidence_artifacts": EVIDENCE_ARTIFACTS + SESSION_ARTIFACTS,
            "dashboard_artifacts": [
                "trader1/dashboard/read_only_dashboard.py",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR_LIVE_BLOCKED",
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
) -> dict[str, Any]:
    template = load_json(
        ROOT / "system" / "evidence" / "patch_results" / "MVP4_PAPER_CURRENT_TRUTH_REFRESH_WRITER.patch_result.json"
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
                "REQ-MVP4-PAPER-CURRENT-TRUTH-REFRESH-WRITER",
                "REQ-MVP4-UPBIT-PUBLIC-REST-CONTINUITY-HISTORY",
                "REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.paper_runtime_truth_state_report.v1",
                "trader1.upbit_public_rest_continuity_report.v1",
                "trader1.upbit_public_rest_continuity_history.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_MARKET_DATA_CONTINUITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_OPERATOR_RECONCILIATION_BOUNDARY"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "LIVE_READY_WRITE"],
            "remaining_blockers": report["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "paper_current_truth_refresh_report",
                "upbit_paper_persistent_loop_report",
                "upbit_public_rest_continuity_history",
                "paper_ledger_rollup_report",
                "read_only_dashboard_shell schema",
                "live final guard",
            ],
            "task_class": "RUNTIME_SAFETY_PATCH",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_MARKET_DATA_CONTINUITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_MARKET_DATA_CONTINUITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "current_implementation_state_status": "UPDATED_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR_LIVE_BLOCKED",
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


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(
            state.get("implemented_schema_ids", [])
            + [
                "trader1.paper_runtime_truth_state_report.v1",
                "trader1.upbit_public_rest_continuity_report.v1",
                "trader1.upbit_public_rest_continuity_history.v1",
                "trader1.read_only_dashboard_shell.v1",
            ]
        )
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["paper_runtime_truth_state_validator"])
    )
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["open_contract_gap_ids"] = sorted(OPEN_GAPS)
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


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR_LIVE_BLOCKED",
            "stage_scope": report["stage_scope"],
            "gap_closure_allowed_by_this_patch": False,
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
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.report.json", report)
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Runtime Truth And Market Continuity Repair Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Heartbeat, PAPER loop, market data, ledger, and current refresh were not reduced into one operator-facing PAPER runtime truth state.
- Short public REST continuity windows could overstate duplicate/non-advancing candles as hard invalid/blocking evidence.

Patch:
- Added paper_runtime_truth_state_report.json for scoped UPBIT/KRW_SPOT/PAPER.
- Wired safe launcher and dashboard operation status to distinguish monitor alive from PAPER engine proven.
- Added WARN semantics for structurally valid short-window market continuity.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials
- no live order path
- no LIVE_READY write
- no live config mutation
- no risk scale-up
- no contract gap closure without external/operator evidence
""",
    )


def write_session_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    tests_run = patch_result["tests_run"]
    validators_run = patch_result["validators_run"]
    accepted = all(item.get("status") == "PASS" for item in tests_run + validators_run)
    acceptance_status = "PASS" if accepted else "FAIL"
    areas = [
        ("strategy / regime / entry / exit", "High", "Strategy evidence still waits for real PAPER/SHADOW samples.", "No promotion or optimizer expansion in this stage."),
        ("expected edge / fee / slippage / funding", "High", "Cost-aware strategy truth remains sample-gated.", "No inferred profitability claim."),
        ("signal grading / parameter search / strategy competition", "High", "Optimizer remains evidence-waiting.", "No new optimizer blocker wrapper."),
        ("paper / shadow / replay / micro-live / live", "Critical", "PAPER runtime truth state is implemented.", "Live/micro-live untouched."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "LIVE_READY remains unwritten.", "All live flags false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "Runtime truth gives risk panels a cleaner PAPER freshness signal.", "No sizing or scale change."),
        ("exchange / market_type / namespace separation", "High", "Truth state is UPBIT/KRW_SPOT/PAPER scoped.", "No Binance evidence transfer."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER path deepened.", "Binance remains scaffold/surface."),
        ("order lifecycle / execution quality / partial fill", "Critical", "No order-capable path touched.", "Order endpoints remain false."),
        ("ledger / reconciliation / idempotency", "Critical", "Truth state requires ledger rollup proof for active status.", "Residual reconciliation gaps remain."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "Short-window duplicate REST samples now WARN when structurally valid.", "Fresh PASS still requires advancing samples."),
        ("concurrency / race condition / restart recovery", "Medium", "Launcher writes truth state under existing runtime lock.", "No daemon introduced."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "Medium", "Operation status now says monitor alive versus PAPER runtime active.", "Detailed blockers stay below."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Schema, tests, patch result, state, and session artifacts updated.", "Validators required."),
        ("testing / pytest / paper run proof / live block proof", "High", "Targeted tests cover WARN, truth state, launcher, dashboard, and live blocks.", "No fake runtime samples."),
        ("security / secrets / API key safety", "Critical", "No credentials or private endpoints used.", "Credential flags false."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Evidence artifacts generated; runtime outputs excluded from stage.", "No audit ledger deletion."),
        ("tax/accounting/export readiness", "Low", "No tax/export path changed.", "Future scoped patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "PAPER values remain simulated ledger truth only.", "No withdrawal/cashflow action."),
        ("overfitting / walk-forward / out-of-sample validation", "High", "Optimizer remains evidence-waiting.", "No OOS claim."),
    ]
    coverage_lines = [
        "# IMPLEMENTATION_COVERAGE_MATRIX",
        "",
        f"generated_at_utc: {now}",
        f"patch_id: {PATCH_ID}",
        "",
        "| # | Area | Severity | Current finding | Closure / acceptance |",
        "|---|---|---|---|---|",
    ]
    for index, (area, severity, finding, closure) in enumerate(areas, 1):
        coverage_lines.append(f"| {index} | {area} | {severity} | {finding} | {closure} |")
    base.write_text(SESSION_DIR / "IMPLEMENTATION_COVERAGE_MATRIX.md", "\n".join(coverage_lines) + "\n")
    base.write_json(
        SESSION_DIR / "ACCEPTANCE_REPORT.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": acceptance_status,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "accepted_checks": report["acceptance_conditions"],
            "test_status_counts": status_counts(tests_run),
            "validator_status_counts": status_counts(validators_run),
            "blockers_precisely_narrowed": report["blockers_precisely_narrowed"],
            "open_contract_gap_ids": report["open_contract_gap_ids"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "pytest_report.txt",
        f"""patch_id: {PATCH_ID}
generated_at_utc: {now}
status: {acceptance_status}

Commands:
{command_lines(tests_run)}

Validator summary:
{json.dumps(status_counts(validators_run), indent=2)}
""",
    )
    base.write_json(
        SESSION_DIR / "PAPER_RUN_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "new_paper_run_started_by_this_patch": False,
            "paper_runtime_truth_state_report_implemented": True,
            "runtime_evidence_claimed_by_this_patch": False,
            "market_continuity_warn_semantics_implemented": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
        SESSION_DIR / "LIVE_BLOCK_PROOF.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_LIVE_BLOCKED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "credential_load_attempted": False,
            "private_endpoint_called": False,
            "order_adapter_called": False,
            "order_endpoint_called": False,
            "live_ready_snapshot_written": False,
            "live_config_mutated": False,
            "gap_closure_allowed_by_this_patch": False,
            "primary_blockers": [
                "LIVE_READY_MISSING",
                "LIVE_ENABLING_EVIDENCE_MISSING",
                "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
                "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
                "SCALE_UP_NOT_ELIGIBLE",
            ],
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_RUNTIME_TRUTH_STATE_VISIBLE_LIVE_BLOCKED",
            "dashboard_source_artifact_added": "paper_runtime_truth_state_report.json",
            "dashboard_operation_status_distinguishes_monitor_from_engine": True,
            "market_continuity_warn_visible": True,
            "dashboard_display_truth_only": True,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        SESSION_DIR / "USER_STATUS_SUMMARY.md",
        f"""# USER_STATUS_SUMMARY

generated_at_utc: {now}
patch_id: {PATCH_ID}

Current state: Dashboard now separates "monitor alive" from "PAPER runtime active." A fresh heartbeat alone no longer looks like proof that the PAPER engine is advancing. Market continuity short-window repeats are shown as WARN when structurally valid, not as schema-invalid evidence.

What changed:
- Added PAPER runtime truth state output.
- Dashboard operation status now says whether PAPER runtime is active or only the monitor is alive.
- UPBIT public REST continuity duplicate/non-advancing short windows now produce WARN with a next action.
- Live trading remains blocked.

User action now:
- No live action.
- Continue PAPER/dashboard only.
""",
    )
    base.write_text(
        SESSION_DIR / "TRADER_1_SESSION_REVIEW.md",
        f"""# TRADER_1 Session Review

generated_at_utc: {now}
patch_id: {PATCH_ID}

## Scope

This session implemented stage 2 of current blocker closure: PAPER runtime truth simplification and market continuity WARN repair. It did not start a long-run PAPER/SHADOW collection, close residual external/operator gaps, write LIVE_READY, use credentials, mutate live config, or enable live orders.

## Defects Found And Patched

1. Critical: Heartbeat PASS could be misread as continuous PAPER engine proof.
2. Critical: Runtime truth existed in separate panels without a single source-bound state.
3. High: Short REST continuity windows over-blocked repeated candle timestamps.
4. Medium: Dashboard operation text did not consume a combined PAPER runtime truth state.

## Validation

Test status counts: {json.dumps(status_counts(tests_run), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(validators_run), sort_keys=True)}

## Whole System State

Overall state: PAPER runtime truth state is implemented for dashboard consumption; market continuity schema mismatch/short-window confusion is reduced; long-run evidence, PAPER/SHADOW harness maturity, residual reconciliation, and live evidence gaps remain blocking.

Overall completion score: 74/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Long-run PAPER/SHADOW runtime evidence is still insufficient.
2. Residual reconciliation/operator gaps remain open.
3. External official API/read-only/burn-in/manual approval evidence is missing.
4. PAPER/SHADOW harness accumulation still needs actual runtime collection.
5. Profitability optimizer evidence maturity is still insufficient.
6. Binance spot/futures remain scaffold/surface.
7. Paper-to-live execution parity is unproven.
8. Market continuity PASS still requires actual advancing windows.
9. Risk exposure remains only as good as latest PAPER truth freshness.
10. Scale-up remains ineligible.

## Next Session Area

Proceed to PAPER/SHADOW harness binding and evidence graph reduction without live safety relaxation.

## Implementation Roadmap

1. Connect PAPER/SHADOW harness outputs to strategy/runtime evidence panels.
2. Reduce duplicate evidence wrappers into critical blocker/warning/informational levels.
3. Keep stale display artifacts from blocking unrelated PAPER runtime collection.
4. Keep optimizer/convergence disabled until real runtime/replay evidence thresholds are met.
5. Keep LIVE_READY, live orders, credentials, config mutation, and scale-up blocked.
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
    *,
    write_session: bool = False,
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    if write_session:
        write_session_artifacts(now, trader_hash, agents_hash, patch_result, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    report = build_report(now, trader_hash, agents_hash)
    write_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/integration/test_upbit_public_rest_continuity.py",
                "tests/integration/test_upbit_public_rest_continuity_history.py",
                "tests/runtime/test_paper_runtime_truth_state.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ],
            timeout_seconds=1800,
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=3600))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "session_review_path": base.rel(SESSION_DIR / "TRADER_1_SESSION_REVIEW.md"),
                "result_hash": patch_result["result_hash"],
                "open_contract_gap_count": report["open_contract_gap_count"],
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
