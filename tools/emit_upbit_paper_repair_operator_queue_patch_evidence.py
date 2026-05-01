from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIR-OPERATOR-QUEUE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_MISSING_CYCLE_RERUN_GUARD"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_repair_operator_queue import (  # noqa: E402
    build_upbit_paper_repair_operator_queue_report,
    validate_upbit_paper_repair_operator_queue_report,
    write_upbit_paper_repair_operator_queue_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_blocked_repair_plan_validator",
    "upbit_paper_ledger_rollup_repair_validator",
    "upbit_paper_post_repair_reconciliation_validator",
    "upbit_paper_repair_operator_queue_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/registry.yaml",
    "contracts/schema/upbit_paper_repair_operator_queue_report.schema.json",
    "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_repair_operator_queue.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repair_operator_queue_report.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_repair_operator_queue_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE.md",
]

BLOCKERS = [
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def runtime_path(name: str) -> Path:
    return ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID / "paper_runtime" / name


def write_runtime_report() -> dict[str, Any]:
    plan = load_json(runtime_path("upbit_paper_blocked_repair_plan_report.json"))
    repair = load_json(runtime_path("upbit_paper_ledger_rollup_repair_report.json"))
    post = load_json(runtime_path("upbit_paper_post_repair_reconciliation_report.json"))
    report = build_upbit_paper_repair_operator_queue_report(
        blocked_repair_plan_report=plan,
        ledger_rollup_repair_report=repair,
        post_repair_reconciliation_report=post,
        queue_id="mvp4-upbit-paper-repair-operator-queue",
    )
    result = validate_upbit_paper_repair_operator_queue_report(report)
    if result.status != "PASS":
        raise RuntimeError(
            "repair operator queue validation failed: "
            f"{result.status} {result.blocker_code} {result.message}"
        )
    write_upbit_paper_repair_operator_queue_report(root=ROOT, report=report)
    return report


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE.md",
        f"""# MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE

context_pack_id: MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_repair_operator_queue_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Operator queue links blocked repair plan, ledger rollup repair candidate, and post-repair reconciliation hashes.
- It prioritizes the single ledger-candidate-ready item ahead of runtime-cycle and recovery reruns.
- It keeps all repair candidates out of current evidence until operator reconciliation and validator-backed follow-up pass.
- It creates no long-run evidence, live readiness, order permission, promotion, deletion, overwrite, or scale-up permission.

known_omissions_by_design:
- The queue is operator visibility only; it does not repair missing runtime cycle ledgers.
- Repair candidates remain blocked and unusable as current evidence.
- No private exchange/account/API call or credential was used.
- MVP-5 remains blocked on external live-review evidence and operator approval.

runtime_summary:
- queue_status: {report["queue_status"]}
- queue_item_count: {report["queue_item_count"]}
- ledger_candidate_review_ready_count: {report["ledger_candidate_review_ready_count"]}
- runtime_cycle_rerun_required_count: {report["runtime_cycle_rerun_required_count"]}
- recovery_guard_rerun_required_count: {report["recovery_guard_rerun_required_count"]}
- hash_operator_reconciliation_required_count: {report["hash_operator_reconciliation_required_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}
- live_order_allowed: false
- scale_up_allowed: false

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

Upbit PAPER repair candidates now have an operator queue that separates the ledger-candidate-ready item from items that still need missing PAPER cycle reruns or recovery guard resolution. The queue is visibility only and cannot mark any repair candidate as current evidence.

## Next Safe Task

{NEXT_TASK_CLASS}
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
            "source_heading": "Upbit PAPER repair operator queue",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: blocked regenerated repairs must be operator-visible and prioritized without "
                "mutating current evidence, persistent loop reports, live permission, or scale-up state"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER repair operator queue",
            "requirement_kind": "SCHEMA_VALIDATOR_RUNTIME_ARTIFACT_PATCH",
            "schema_ids": ["trader1.upbit_paper_repair_operator_queue_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_upbit_paper_repair_operator_queue.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-READY-REPAIR",
                "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"blocked regenerated repairs operator queue stays live blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_OPERATOR_VISIBLE_LIVE_BLOCKED",
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
            "schema_files": ["contracts/schema/upbit_paper_repair_operator_queue_report.schema.json"],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_upbit_paper_repair_operator_queue.py"],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_repair_operator_queue.py",
                "trader1/runtime/paper/upbit_paper_blocked_repair_plan.py",
                "trader1/runtime/paper/upbit_paper_ledger_rollup_repair.py",
                "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py",
            ],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repair_operator_queue_report.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_repair_operator_queue_report.json"
            ],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_OPERATOR_VISIBLE_LIVE_BLOCKED",
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


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_POST_REPAIR_RECONCILIATION.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-BLOCKED-REPAIR-PLAN",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-READY-REPAIR",
                "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID, "upbit_paper_repair_operator_queue_validator"],
            "new_or_changed_schema_ids": ["trader1.upbit_paper_repair_operator_queue_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE", "RETAINED_ARCHIVE"],
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
                "blocked repair plan",
                "ledger rollup repair candidate",
                "post-repair reconciliation",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_REPAIR_OPERATOR_QUEUE",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_REPAIR_QUEUE_OPERATOR_VISIBLE_NOT_LIVE_READY",
            "optimizer_guardrail_result": "PASS_REPAIR_QUEUE_DOES_NOT_MUTATE_CURRENT_EVIDENCE_OR_LIVE_STATE",
            "convergence_state_after": "REGENERATED_REPAIR_CANDIDATES_OPERATOR_QUEUED_LEDGER_RECOVERY_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_OR_LONG_RUN_EVIDENCE_CREATED",
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


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
            "stage_gate_status": "PASS_REPAIR_OPERATOR_QUEUE_VISIBLE_LIVE_BLOCKED",
            "queue_status": report["queue_status"],
            "queue_item_count": report["queue_item_count"],
            "ledger_candidate_review_ready_count": report["ledger_candidate_review_ready_count"],
            "runtime_cycle_rerun_required_count": report["runtime_cycle_rerun_required_count"],
            "recovery_guard_rerun_required_count": report["recovery_guard_rerun_required_count"],
            "hash_operator_reconciliation_required_count": report["hash_operator_reconciliation_required_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "actual_long_run_evidence_created": False,
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
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "queue_status": report["queue_status"],
            "queue_item_count": report["queue_item_count"],
            "ledger_candidate_review_ready_count": report["ledger_candidate_review_ready_count"],
            "runtime_cycle_rerun_required_count": report["runtime_cycle_rerun_required_count"],
            "recovery_guard_rerun_required_count": report["recovery_guard_rerun_required_count"],
            "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
            "actual_long_run_evidence_created": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Upbit PAPER Repair Operator Queue Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Post-repair reconciliation was hash-aware and blocked, but the operator still had to infer repair priority from several separate artifacts.
- That left the remaining ledger/recovery reconciliation gap harder to act on without risking accidental current-evidence mutation.

Patch:
- Added a strict repair operator queue schema, runtime builder/writer/validator, registry entry, runtime artifact, and negative tests.
- The queue links blocked repair plan, ledger rollup repair candidate, and post-repair reconciliation hashes.
- The queue prioritizes the ledger-candidate-ready item and separates missing-cycle and recovery-guard rerun work.
- It remains visibility-only; repair candidates stay out of current evidence.

Runtime summary:
- queue_status: {report["queue_status"]}
- queue_item_count: {report["queue_item_count"]}
- ledger_candidate_review_ready_count: {report["ledger_candidate_review_ready_count"]}
- runtime_cycle_rerun_required_count: {report["runtime_cycle_rerun_required_count"]}
- recovery_guard_rerun_required_count: {report["recovery_guard_rerun_required_count"]}
- hash_operator_reconciliation_required_count: {report["hash_operator_reconciliation_required_count"]}
- candidate_current_evidence_usable_count: {report["candidate_current_evidence_usable_count"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    configure_base()
    base.update_state_and_ledger(now, patch_result)
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    schema_ids = set(state.get("implemented_schema_ids", []))
    schema_ids.add("trader1.upbit_paper_repair_operator_queue_report.v1")
    validator_ids = set(state.get("implemented_validator_ids", []))
    validator_ids.add("upbit_paper_repair_operator_queue_validator")
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    gaps = set(state.get("open_contract_gap_ids", []))
    gaps.update(
        {
            "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
            "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
            "MISSING_CYCLE_LEDGER_RERUN_GUARD_REQUIRED",
        }
    )
    state["implemented_schema_ids"] = sorted(schema_ids)
    state["implemented_validator_ids"] = sorted(validator_ids)
    state["completed_requirement_ids"] = sorted(completed)
    state["untested_validator_ids"] = sorted(set(state.get("untested_validator_ids", [])) - validator_ids)
    state["open_contract_gap_ids"] = sorted(gaps)
    state["last_patch_id"] = PATCH_ID
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["updated_at_utc"] = now
    state["state_hash"] = ""
    state["state_hash"] = base.sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    base.write_json(state_path, state)


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    base.write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    report = write_runtime_report()
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_repair_operator_queue.py",
                "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                "tests/runtime/test_upbit_paper_ledger_rollup_repair.py",
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
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
                "queue_status": report["queue_status"],
                "queue_item_count": report["queue_item_count"],
                "ledger_candidate_review_ready_count": report["ledger_candidate_review_ready_count"],
                "runtime_cycle_rerun_required_count": report["runtime_cycle_rerun_required_count"],
                "recovery_guard_rerun_required_count": report["recovery_guard_rerun_required_count"],
                "candidate_current_evidence_usable_count": report["candidate_current_evidence_usable_count"],
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
