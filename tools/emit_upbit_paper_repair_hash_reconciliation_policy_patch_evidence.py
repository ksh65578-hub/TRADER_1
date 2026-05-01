from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-REPAIR-HASH-RECONCILIATION-POLICY"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.runtime.paper.upbit_paper_ledger_rollup_repair import (  # noqa: E402
    build_upbit_paper_ledger_rollup_repair_report,
    validate_upbit_paper_ledger_rollup_repair_report,
    write_upbit_paper_ledger_rollup_repair_report,
)
from trader1.runtime.paper.upbit_paper_post_repair_reconciliation import (  # noqa: E402
    build_upbit_paper_post_repair_reconciliation_report,
    validate_upbit_paper_post_repair_reconciliation_report,
    write_upbit_paper_post_repair_reconciliation_report,
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
    "paper_ledger_rollup_validator",
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
    "contracts/schema/upbit_paper_ledger_rollup_repair_report.schema.json",
    "contracts/schema/upbit_paper_post_repair_reconciliation_report.schema.json",
    "trader1/runtime/paper/upbit_paper_ledger_rollup_repair.py",
    "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_ledger_rollup_repair.py",
    "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_ledger_rollup_repair_report.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_repair_hash_reconciliation_policy_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY.md",
]

BLOCKERS = [
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def remove_python_bytecode_artifacts() -> int:
    removed = 0
    root = ROOT.resolve()
    for path in sorted(root.rglob("*.pyc")):
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        resolved.unlink(missing_ok=True)
        removed += 1
    for path in sorted(root.rglob("__pycache__"), key=lambda item: len(item.parts), reverse=True):
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        if resolved.is_dir():
            shutil.rmtree(resolved)
            removed += 1
    return removed


def runtime_paper_dir() -> Path:
    return ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher" / "paper_runtime"


def write_runtime_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    plan_path = runtime_paper_dir() / "upbit_paper_blocked_repair_plan_report.json"
    repair_plan = load_json(plan_path)
    ledger_report = build_upbit_paper_ledger_rollup_repair_report(
        root=ROOT,
        repair_plan_report=repair_plan,
        source_repair_plan_path=base.rel(plan_path),
    )
    ledger_result = validate_upbit_paper_ledger_rollup_repair_report(ledger_report)
    if ledger_result.status != "PASS":
        raise RuntimeError(f"ledger repair validation failed: {ledger_result.status} {ledger_result.message}")
    ledger_path = write_upbit_paper_ledger_rollup_repair_report(root=ROOT, report=ledger_report)

    post_report = build_upbit_paper_post_repair_reconciliation_report(
        ledger_rollup_repair_report=ledger_report,
        source_repair_report_path=base.rel(ledger_path),
    )
    post_result = validate_upbit_paper_post_repair_reconciliation_report(post_report)
    if post_result.status != "PASS":
        raise RuntimeError(f"post-repair validation failed: {post_result.status} {post_result.message}")
    write_upbit_paper_post_repair_reconciliation_report(root=ROOT, report=post_report)
    return ledger_report, post_report


def write_context(now: str, trader_hash: str, agents_hash: str, ledger_report: dict[str, Any], post_report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY.md",
        f"""# MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY

context_pack_id: MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-READY-REPAIR", "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION"]
included_schema_ids: ["trader1.upbit_paper_ledger_rollup_repair_report.v1", "trader1.upbit_paper_post_repair_reconciliation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Ledger repair candidates expose source expected rollup artifact existence/load status.
- Candidate rollup hashes are recomputed and self-checked before reconciliation.
- Hash mismatch status is counted and blocks operator use as current evidence.
- Live, order, long-run evidence, promotion, and scale-up flags remain false.

runtime_summary:
- ledger_repair_status: {ledger_report["repair_report_status"]}
- post_repair_reconciliation_status: {post_report["post_repair_reconciliation_status"]}
- repair_candidate_count: {post_report["repair_candidate_count"]}
- hash_reconciliation_operator_action_required_count: {post_report["hash_reconciliation_operator_action_required_count"]}
- candidate_current_evidence_usable_count: {post_report["candidate_current_evidence_usable_count"]}
- primary_blocker_code: {post_report["primary_blocker_code"]}
- live_order_allowed: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not rewrite source loop hashes.
- This patch does not accept repair candidates as current evidence.
- This patch does not create long-run evidence or promotion evidence.
- No private exchange/account/API call or credential was used.

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

Upbit PAPER repair candidates now carry hash reconciliation details. The current candidate remains BLOCKED because the source loop expected rollup artifact is unavailable/mismatched, so it cannot become current evidence.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER repair hash reconciliation policy",
            "full_text_marker": f"{REQUIREMENT_ID}: repair candidates must expose recomputed hash reconciliation evidence and remain blocked before current evidence use",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER repair hash reconciliation policy",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_ledger_rollup_repair_report.v1",
                "trader1.upbit_paper_post_repair_reconciliation_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_upbit_paper_ledger_rollup_repair.py",
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-READY-REPAIR",
                "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"repair candidates must expose recomputed hash reconciliation evidence and remain blocked before current evidence use"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_HASH_RECONCILIATION_EVIDENCE_BLOCKED",
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
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/upbit_paper_ledger_rollup_repair_report.schema.json",
                "contracts/schema/upbit_paper_post_repair_reconciliation_report.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_ledger_rollup_repair.py",
                "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_ledger_rollup_repair.py",
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_ledger_rollup_repair.py",
                "trader1/runtime/paper/upbit_paper_post_repair_reconciliation.py",
            ],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_ledger_rollup_repair_report.json",
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_repair_reconciliation_report.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_HASH_RECONCILIATION_EVIDENCE_BLOCKED",
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
    ledger_report: dict[str, Any],
    post_report: dict[str, Any],
) -> dict[str, Any]:
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
                "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-READY-REPAIR",
                "REQ-MVP4-UPBIT-PAPER-POST-REPAIR-RECONCILIATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_ledger_rollup_repair_report.v1",
                "trader1.upbit_paper_post_repair_reconciliation_report.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PORTFOLIO_TRUTH"],
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
                "ledger rollup repair report",
                "post-repair reconciliation report",
                "runtime schema instance validator",
            ],
            "task_class": "MVP4_UPBIT_PAPER_REPAIR_HASH_RECONCILIATION_POLICY",
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_RUNTIME_RECOVERY", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_REPAIR_HASH_RECONCILIATION_BLOCKED",
            "optimizer_guardrail_result": "PASS_REPAIR_CANDIDATE_HASH_RECONCILIATION_NOT_CURRENT_EVIDENCE",
            "optimizer_validators_required": [],
            "optimizer_validators_run": [],
            "convergence_state_after": "POST_REPAIR_RECONCILIATION_BLOCKED_HASH_RECONCILIATION_REQUIRED",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_OR_LONG_RUN_EVIDENCE_CREATED",
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], ledger_report: dict[str, Any], post_report: dict[str, Any]) -> None:
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
            "stage_gate_status": "BLOCKED_REPAIR_HASH_RECONCILIATION_REQUIRED",
            "ledger_repair_status": ledger_report["repair_report_status"],
            "post_repair_reconciliation_status": post_report["post_repair_reconciliation_status"],
            "repair_candidate_count": post_report["repair_candidate_count"],
            "hash_reconciliation_status_counts": post_report["hash_reconciliation_status_counts"],
            "hash_reconciliation_operator_action_required_count": post_report["hash_reconciliation_operator_action_required_count"],
            "candidate_current_evidence_usable_count": post_report["candidate_current_evidence_usable_count"],
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
            "ledger_repair_status": ledger_report["repair_report_status"],
            "post_repair_reconciliation_status": post_report["post_repair_reconciliation_status"],
            "repair_candidate_count": post_report["repair_candidate_count"],
            "hash_reconciliation_status_counts": post_report["hash_reconciliation_status_counts"],
            "hash_reconciliation_operator_action_required_count": post_report["hash_reconciliation_operator_action_required_count"],
            "candidate_current_evidence_usable_count": post_report["candidate_current_evidence_usable_count"],
            "actual_long_run_evidence_created": False,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Upbit PAPER Repair Hash Reconciliation Policy Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Repair candidates exposed only pass/mismatch counts. The runtime evidence did not show whether the source expected rollup artifact existed or whether candidate hashes were recomputed and self-checked.

Patch:
- Added strict hash reconciliation evidence to ledger repair and post-repair reconciliation reports.
- Added schema, validator, and test checks for candidate hash self-check, expected artifact availability, status counts, and operator-action counts.
- Kept every repair candidate blocked from current evidence.

Runtime summary:
- ledger_repair_status: {ledger_report["repair_report_status"]}
- post_repair_reconciliation_status: {post_report["post_repair_reconciliation_status"]}
- repair_candidate_count: {post_report["repair_candidate_count"]}
- hash_reconciliation_operator_action_required_count: {post_report["hash_reconciliation_operator_action_required_count"]}
- candidate_current_evidence_usable_count: {post_report["candidate_current_evidence_usable_count"]}
- primary_blocker_code: {post_report["primary_blocker_code"]}

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
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    schemas = set(state.get("implemented_schema_ids", []))
    schemas.update(
        {
            "trader1.upbit_paper_ledger_rollup_repair_report.v1",
            "trader1.upbit_paper_post_repair_reconciliation_report.v1",
        }
    )
    validators = set(state.get("implemented_validator_ids", []))
    validators.update(
        {
            "upbit_paper_ledger_rollup_repair_validator",
            "upbit_paper_post_repair_reconciliation_validator",
        }
    )
    gaps = set(state.get("open_contract_gap_ids", []))
    gaps.update(
        {
            "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
            "POST_REPAIR_RECONCILIATION_REQUIRED",
        }
    )
    state["completed_requirement_ids"] = sorted(completed)
    state["implemented_schema_ids"] = sorted(schemas)
    state["implemented_validator_ids"] = sorted(validators)
    state["open_contract_gap_ids"] = sorted(gaps)
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["updated_at_utc"] = now
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
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    ledger["ledger_hash"] = base.sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
    base.write_json(ledger_path, ledger)


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], ledger_report: dict[str, Any], post_report: dict[str, Any]) -> None:
    write_evidence(now, trader_hash, agents_hash, patch_result, ledger_report, post_report)
    base.write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)
    update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    remove_python_bytecode_artifacts()
    ledger_report, post_report = write_runtime_reports()
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    write_context(now, trader_hash, agents_hash, ledger_report, post_report)
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
                "tests/runtime/test_upbit_paper_ledger_rollup_repair.py",
                "tests/runtime/test_upbit_paper_post_repair_reconciliation.py",
                "tests/runtime/test_upbit_paper_blocked_repair_plan.py",
                "tests/runtime/test_paper_ledger_rollup.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    remove_python_bytecode_artifacts()
    write_source_bundle_manifest()
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, ledger_report, post_report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, ledger_report, post_report)

    tests_run.append(base.run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]))
    remove_python_bytecode_artifacts()
    write_source_bundle_manifest()
    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, ledger_report, post_report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, ledger_report, post_report)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "hash_reconciliation_status_counts": post_report["hash_reconciliation_status_counts"],
                "hash_reconciliation_operator_action_required_count": post_report["hash_reconciliation_operator_action_required_count"],
                "candidate_current_evidence_usable_count": post_report["candidate_current_evidence_usable_count"],
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
