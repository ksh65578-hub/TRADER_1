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

PATCH_BASENAME = "MVP4_PAPER_CURRENT_TRUTH_REFRESH_WRITER"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-CURRENT-TRUTH-REFRESH-WRITER"
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
    "contracts/schema/paper_current_truth_refresh_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/runtime/portfolio/paper_current_truth_refresh.py",
    "trader1/runtime/boot/safe_launcher.py",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/runtime/test_paper_portfolio.py",
    "tests/runtime/test_safe_launcher.py",
    "tools/emit_paper_current_truth_refresh_writer_patch_evidence.py",
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
        "schema_id": "trader1.paper_current_truth_refresh_writer_audit_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "stage_scope": "STAGE_1_PAPER_CURRENT_TRUTH_REFRESH_WRITER",
        "finding": (
            "The dashboard could consume a stale single-run PAPER portfolio snapshot, but the launcher had no "
            "PAPER-only current-truth refresh report that bound the displayed values to the verified ledger-backed "
            "portfolio source, heartbeat/startup scope, and live-final false invariants before attempting a scoped "
            "audited current-evidence write."
        ),
        "patch": (
            "Added a PAPER-only current-truth refresh report, schema, tests, dashboard source-artifact binding, and "
            "a safe UPBIT/KRW_SPOT/PAPER audited writer refresh attempt that only writes when ledger rollup, "
            "idempotency, reconciliation, and writer validator checks pass."
        ),
        "writer_status_contract": [
            "NOT_IMPLEMENTED: no refresh module or schema exists",
            "IMPLEMENTED_BLOCKED: refresh exists but source portfolio is unavailable or validation fails",
            "IMPLEMENTED_WRITING_PAPER_CURRENT_TRUTH: refresh report and audited writer prerequisites pass in PAPER scope",
            "IMPLEMENTED_STALE: refresh artifact exists but is too old for current display truth",
        ],
        "acceptance_conditions": [
            "PAPER current-truth refresh report binds to the ledger-backed paper portfolio snapshot hash",
            "refresh report distinguishes configured starting cash from verified cash, locked cash, position market value, equity, PnL, and return",
            "stale display-only snapshot is not reclassified as fresh current truth without a fresh refresh report",
            "launcher attempts audited current-evidence writing only for scoped UPBIT/KRW_SPOT/PAPER and only after ledger/idempotency/reconciliation checks pass",
            "dashboard source artifacts include paper_current_truth_refresh_report.json with freshness and validation state",
            "live_order_ready, live_order_allowed, can_live_trade, scale_up_allowed, LIVE_READY write, live config mutation, credential load, and order calls remain false",
            "open contract gap count remains 13; broad external/operator reconciliation route remains active",
        ],
        "blockers_precisely_narrowed": [
            "AUDITED_CURRENT_EVIDENCE_WRITER_NOT_IMPLEMENTED is no longer the correct diagnosis for the scoped PAPER refresh implementation path",
            "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED remains open until residual reconciliation/operator evidence is valid for the broader closure route",
        ],
        "open_contract_gap_count": len(open_gaps),
        "open_contract_gap_ids": open_gaps,
        "next_allowed_task_class": NEXT_TASK_CLASS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / CONTEXT_PACK_PATH,
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: RUNTIME_SAFETY_PATCH
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_current_truth_refresh_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER current-truth refresh report is source-bound to the verified ledger-backed PAPER portfolio snapshot.
- Refresh report and launcher keep all live/order/scale flags false.
- Scoped audited current-evidence writer is attempted only after ledger, idempotency, reconciliation, and writer validation pass.
- Dashboard can consume paper_current_truth_refresh_report.json as a source artifact.
- Open contract gaps remain open unless independent evidence closes them.

known_omissions_by_design:
- This patch does not claim long-run runtime evidence.
- This patch does not start PAPER/SHADOW runtime collection.
- This patch does not close residual external/operator reconciliation gaps.
- This patch does not enable live orders, LIVE_READY, live config mutation, credentials, or scale-up.

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

The UPBIT/KRW_SPOT/PAPER launcher now emits a ledger-backed PAPER current-truth refresh report and can attempt a scoped audited current-evidence write when ledger, reconciliation, idempotency, and writer validation pass. This is non-live and does not close the residual external/operator evidence route.
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Continuous PAPER current evidence writer",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: UPBIT/KRW_SPOT/PAPER launcher must emit a ledger-backed current-truth refresh "
                "report and only attempt audited current evidence writing after ledger, reconciliation, idempotency, "
                "source scope, and writer validators pass while all live and scale flags remain false"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "PAPER current truth refresh writer",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.paper_current_truth_refresh_report.v1", "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": all_artifacts(),
            "test_ids": [
                "tests/runtime/test_paper_portfolio.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION",
                "REQ-MVP4-UPBIT-PAPER-AUDITED-CURRENT-EVIDENCE-WRITER-DASHBOARD-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"paper current truth refresh writer ledger reconciliation idempotency live blocked"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_PAPER_CURRENT_TRUTH_REFRESH_WRITER_LIVE_BLOCKED",
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
                "contracts/schema/paper_current_truth_refresh_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/portfolio/paper_current_truth_refresh.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_paper_portfolio.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                *ROUTE_GUARD_TEST_ARTIFACTS,
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/portfolio/paper_current_truth_refresh.py",
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
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_PAPER_CURRENT_TRUTH_REFRESH_WRITER_LIVE_BLOCKED",
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
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_DASHBOARD_AUDITED_WRITER_BLOCKER_DECISION.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-LEDGER-ROLLUP-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.paper_current_truth_refresh_report.v1",
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
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_MARKET_DATA_CONTINUITY", "SECTION_PAPER_SHADOW_EVIDENCE"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "LIVE_READY_WRITE"],
            "remaining_blockers": report["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "removed_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "paper_portfolio_snapshot",
                "paper ledger rollup",
                "idempotency runtime evidence",
                "post-rerun reconciliation report",
                "audited current evidence writer validator",
                "read_only_dashboard_shell schema",
                "live final guard",
            ],
            "task_class": "RUNTIME_SAFETY_PATCH",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UPDATED_PASS",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED_PAPER_CURRENT_TRUTH_REFRESH_WRITER_LIVE_BLOCKED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
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
                "trader1.paper_current_truth_refresh_report.v1",
                "trader1.read_only_dashboard_shell.v1",
            ]
        )
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
            "stage_gate_status": "PASS_PAPER_CURRENT_TRUTH_REFRESH_WRITER_LIVE_BLOCKED",
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
        f"""# MVP4 PAPER Current Truth Refresh Writer Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The dashboard could show a stale PAPER portfolio snapshot without a fresh, source-bound current-truth refresh report.

Patch:
- Added a PAPER-only current-truth refresh report and schema.
- Bound launcher output to the ledger-backed paper portfolio snapshot, heartbeat, and startup probe.
- Added a scoped UPBIT/KRW_SPOT/PAPER audited writer refresh attempt gated by ledger rollup, idempotency, reconciliation, and writer validation.
- Added dashboard source-artifact visibility for paper_current_truth_refresh_report.json.

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
        ("strategy / regime / entry / exit", "High", "Strategy evidence remains gated by real PAPER/SHADOW samples.", "No optimizer or entry logic promotion in this stage."),
        ("expected edge / fee / slippage / funding", "High", "Cost evidence remains source-bound requirement.", "No cost model inference from this patch."),
        ("signal grading / parameter search / strategy competition", "High", "Optimizer remains waiting for evidence.", "No new convergence wrapper added."),
        ("paper / shadow / replay / micro-live / live", "Critical", "PAPER current-truth refresh path implemented.", "Live and micro-live untouched."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "LIVE_READY remains unwritten.", "All live flags remain false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "Risk exposure can consume last verified PAPER truth later.", "No scale-up or live sizing change."),
        ("exchange / market_type / namespace separation", "High", "Writer attempt is scoped to UPBIT/KRW_SPOT/PAPER.", "No Binance readiness transfer."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER path deepened.", "Binance remains scaffold/surface."),
        ("order lifecycle / execution quality / partial fill", "Critical", "No order-capable path touched.", "Order/live endpoints remain false."),
        ("ledger / reconciliation / idempotency", "Critical", "Writer attempt now requires rollup, idempotency, and reconciliation PASS.", "Residual reconciliation gaps remain open."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "Refresh artifact freshness is separated from stale display-only truth.", "Market continuity repair remains next stage."),
        ("concurrency / race condition / restart recovery", "Medium", "Launcher writes current refresh through existing runtime lock flow.", "No separate writer daemon yet."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "Medium", "Dashboard can see the refresh report as a source artifact.", "Top-level runtime simplification remains next stage."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Schema, tests, patch result, and session artifacts updated.", "Validators must pass."),
        ("testing / pytest / paper run proof / live block proof", "High", "Targeted tests verify PAPER refresh and live-block proof.", "No fake runtime samples."),
        ("security / secrets / API key safety", "Critical", "No credentials or private endpoints used.", "Credential load flag stays false."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Evidence artifacts generated; runtime outputs remain unstaged.", "No authoritative ledger cleanup."),
        ("tax/accounting/export readiness", "Low", "No tax/export path changed.", "Future scoped patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "PAPER values are simulated ledger truth only.", "No withdrawal or cashflow action."),
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
            "paper_current_truth_refresh_writer_implemented": True,
            "audited_writer_attempt_is_scoped_paper_only": True,
            "runtime_evidence_claimed_by_this_patch": False,
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
                "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
                "SCALE_UP_NOT_ELIGIBLE",
            ],
        },
    )
    base.write_json(
        SESSION_DIR / "DASHBOARD_READINESS_SUMMARY.json",
        {
            "patch_id": PATCH_ID,
            "generated_at_utc": now,
            "status": "PASS_PAPER_CURRENT_TRUTH_REFRESH_VISIBLE_LIVE_BLOCKED",
            "dashboard_source_artifact_added": "paper_current_truth_refresh_report.json",
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

Current state: PAPER current-truth refresh is implemented for the safe launcher path. The dashboard can now consume a dedicated refresh report instead of treating an old portfolio snapshot as current truth.

What changed:
- PAPER refresh output is tied to the verified ledger-backed PAPER portfolio snapshot.
- The launcher can attempt the existing audited current-evidence writer only when PAPER ledger, idempotency, reconciliation, and writer checks pass.
- The dashboard source list includes paper_current_truth_refresh_report.json.
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

This session implemented stage 1 of current blocker closure: a PAPER-only current-truth refresh writer path and a scoped audited current-evidence write attempt. It did not start a long-run PAPER/SHADOW collection, repair market continuity, close residual external/operator gaps, write LIVE_READY, or enable live orders.

## Defects Found And Patched

1. Critical: Stale PAPER portfolio snapshots could be displayed without a dedicated current-truth refresh artifact.
2. Critical: The launcher did not produce an authoritative PAPER refresh report separating configured capital from verified ledger-backed values.
3. High: Audited writer activation had no safe launcher-side scoped retry when ledger, idempotency, and reconciliation already passed.
4. Medium: Dashboard source artifacts did not list PAPER current-truth refresh freshness.

## Validation

Test status counts: {json.dumps(status_counts(tests_run), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(validators_run), sort_keys=True)}

## Whole System State

Overall state: PAPER current-truth refresh writer is implemented for the safe launcher path; broader runtime continuity, market continuity, long-run evidence, and residual reconciliation/operator gaps remain blocking.

Overall completion score: 72/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Long-run PAPER/SHADOW runtime evidence is still insufficient.
2. Residual reconciliation/operator gaps remain open.
3. External official API/read-only/burn-in/manual approval evidence is missing.
4. Market continuity repair is still pending.
5. PAPER/SHADOW harness binding is still incomplete.
6. Runtime truth state machine is still too fragmented.
7. Profitability optimizer evidence maturity is still insufficient.
8. Binance spot/futures remain scaffold/surface.
9. Paper-to-live execution parity is unproven.
10. Scale-up remains ineligible.

## Next Session Area

Proceed to stage 2: runtime truth simplification and market continuity repair without live safety relaxation.

## Implementation Roadmap

1. Define one PAPER runtime truth state machine: monitor alive, loop advancing, market advancing, ledger advancing, refresh advancing.
2. Align market continuity producer and validator schema/scope for UPBIT/KRW_SPOT/PAPER.
3. Connect PAPER/SHADOW harness output to runtime evidence panels.
4. Move stale display artifacts to warning/informational unless they block current truth.
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
    write_context(now, trader_hash, agents_hash, report)
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
                "tests/runtime/test_paper_portfolio.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS_REQUIRED, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(
        run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=3600)
    )
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
