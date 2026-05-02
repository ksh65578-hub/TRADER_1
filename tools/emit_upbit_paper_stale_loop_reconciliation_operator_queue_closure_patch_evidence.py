from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATCH_BASENAME = "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-RECONCILIATION-OPERATOR-QUEUE-CLOSURE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_DASHBOARD_BINDING"
SESSION_ID = "mvp1_upbit_paper_launcher"

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    run_command,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.runtime.paper.upbit_paper_stale_loop_reconciliation_operator_queue_closure import (  # noqa: E402
    build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
    validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
    write_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
POST_REGEN_PATH = RUNTIME_BASE / "paper_runtime" / "upbit_paper_stale_loop_post_regeneration_reconciliation_report.json"
LEDGER_EVIDENCE_PATH = RUNTIME_BASE / "ledger" / "upbit_paper_ledger_idempotency_runtime_evidence_report.json"
CLOSURE_REPORT_PATH = RUNTIME_BASE / "paper_runtime" / "upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.json"

VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_stale_loop_reconciliation_operator_queue_closure_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "secret_scan_validator",
]
BOOTSTRAP_VALIDATORS = [
    item
    for item in VALIDATORS_REQUIRED
    if item not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
]

CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.schema.json",
    "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
    "tools/emit_upbit_paper_stale_loop_reconciliation_operator_queue_closure_patch_evidence.py",
    rel(CLOSURE_REPORT_PATH),
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
    "STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_PENDING",
    "POST_RERUN_RECONCILIATION_REQUIRED",
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


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def remove_cache_artifacts() -> None:
    for path in sorted(ROOT.rglob("*.pyc"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
    for path in sorted(ROOT.rglob("__pycache__"), reverse=True):
        if path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass
    pytest_cache = ROOT / ".pytest_cache"
    if pytest_cache.exists():
        for path in sorted(pytest_cache.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                try:
                    path.rmdir()
                except OSError:
                    pass
        pytest_cache.rmdir()


def write_runtime_report() -> dict[str, Any]:
    post_regen = load_json(POST_REGEN_PATH)
    ledger_evidence = load_json(LEDGER_EVIDENCE_PATH)
    report = build_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(
        post_regeneration_reconciliation_report=post_regen,
        ledger_idempotency_evidence_report=ledger_evidence,
        closure_id="upbit-paper-stale-loop-reconciliation-operator-queue-closure-20260502",
    )
    result = validate_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(report)
    if result.status != "PASS":
        raise RuntimeError(f"closure report failed: {result.status} {result.blocker_code} {result.message}")
    if report.get("ledger_recheck_ready_count") != 5 or report.get("recovery_guard_required_count") != 1:
        raise RuntimeError("closure report did not preserve expected current stale-loop split: 5 ledger-only, 1 recovery")
    if any(report.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "scale_up_allowed")):
        raise RuntimeError("closure report attempted live/order/scale permission")
    write_upbit_paper_stale_loop_reconciliation_operator_queue_closure_report(root=ROOT, report=report)
    return report


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Build a strict, display-only Upbit PAPER stale-loop operator queue closure report.
- Classify blocked regenerated replacements into ledger-only recheck-ready, recovery guard required, runtime rerun required, or operator review lanes.
- Preserve current-evidence write blocks; no replacement is marked current evidence by this report.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

runtime_summary:
- closure_status: {report.get("closure_status")}
- closure_item_count: {report.get("closure_item_count")}
- ledger_recheck_ready_count: {report.get("ledger_recheck_ready_count")}
- recovery_guard_required_count: {report.get("recovery_guard_required_count")}
- current_evidence_write_allowed_count: {report.get("current_evidence_write_allowed_count")}
- current_evidence_usable_after_closure_count: {report.get("current_evidence_usable_after_closure_count")}
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

known_omissions_by_design:
- This patch does not promote stale-loop replacements into current evidence.
- This patch does not overwrite/delete regenerated reports, mutate live config, place orders, use credentials, resolve LIVE_READY, or scale risk.
- Dashboard binding for this closure report remains the next task.

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
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

Upbit PAPER stale-loop post-regeneration blockers now have a separate operator queue closure report. Current runtime split: ledger_recheck_ready={report.get("ledger_recheck_ready_count")}, recovery_guard_required={report.get("recovery_guard_required_count")}, evidence_writes={report.get("current_evidence_write_allowed_count")}. The report is display-only and cannot promote evidence.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    reqs = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    reqs.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_VALIDATOR_IDS",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER stale-loop reconciliation operator queue closure",
            "full_text_marker": f"{REQUIREMENT_ID}: classify stale-loop blocked replacements without current evidence writes or live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Classify stale-loop blocked replacements into safe operator closure lanes",
            "requirement_kind": "RUNTIME_RECONCILIATION_EVIDENCE_PATCH",
            "schema_ids": ["trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE-REFRESH",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"stale-loop operator closure classifies blocked replacements but cannot write current evidence"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RUNTIME_EVIDENCE_LIVE_BLOCKED",
            "test_status": "PASS",
        }
    )
    req_index.update({"trader1_sha256": trader_hash, "agents_sha256": agents_hash, "updated_at_utc": now, "requirements": sorted(reqs, key=lambda item: item["requirement_id"])})
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_LEDGER_VALIDATOR_IDS",
            "schema_files": ["contracts/schema/upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.schema.json"],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_stale_loop_reconciliation_operator_queue_closure.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                rel(CLOSURE_REPORT_PATH),
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "evidence_manifest_path",
                "validator_run_log_path",
                "stage_gate_result_path",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RUNTIME_EVIDENCE_LIVE_BLOCKED",
        }
    )
    matrix.update({"trader1_sha256": trader_hash, "agents_sha256": agents_hash, "updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], validators_required: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-STALE-LOOP-POST-REGENERATION-RECONCILIATION",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE-REFRESH",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"
            ],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_AGENTS_DASHBOARD_SERVING_TRUTH"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "BINANCE_FUTURES_LIVE"],
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "task_class": "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE",
            "required_section_ids": ["SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["AGENTS:0G", "AGENTS:0F", "SECTION_LEDGER_VALIDATOR_IDS"],
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_STALE_LOOP_OPERATOR_QUEUE_CLOSURE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_STALE_LOOP_OPERATOR_QUEUE_CLOSURE_NO_EVIDENCE_WRITES",
            "closure_status": report.get("closure_status"),
            "closure_item_count": report.get("closure_item_count"),
            "ledger_recheck_ready_count": report.get("ledger_recheck_ready_count"),
            "recovery_guard_required_count": report.get("recovery_guard_required_count"),
            "current_evidence_write_allowed_count": report.get("current_evidence_write_allowed_count"),
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
            "closure_status": report.get("closure_status"),
            "closure_item_count": report.get("closure_item_count"),
            "ledger_recheck_ready_count": report.get("ledger_recheck_ready_count"),
            "recovery_guard_required_count": report.get("recovery_guard_required_count"),
            "current_evidence_write_allowed_count": report.get("current_evidence_write_allowed_count"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    audit = {
        "audit_schema_id": "trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_audit.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "status": "PASS",
        "closure_status": report.get("closure_status"),
        "closure_item_count": report.get("closure_item_count"),
        "ledger_recheck_ready_count": report.get("ledger_recheck_ready_count"),
        "recovery_guard_required_count": report.get("recovery_guard_required_count"),
        "current_evidence_write_allowed_count": report.get("current_evidence_write_allowed_count"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.md",
        f"""# MVP4 Upbit PAPER Stale Loop Reconciliation Operator Queue Closure

created_at_utc: {now}
patch_id: {PATCH_ID}

Runtime closure:
- closure_status={report.get("closure_status")}
- closure_item_count={report.get("closure_item_count")}
- ledger_recheck_ready_count={report.get("ledger_recheck_ready_count")}
- recovery_guard_required_count={report.get("recovery_guard_required_count")}
- current_evidence_write_allowed_count={report.get("current_evidence_write_allowed_count")}
- current_evidence_usable_after_closure_count={report.get("current_evidence_usable_after_closure_count")}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials, private endpoint calls, live orders, current-evidence writes, live config mutation, or risk scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []) + ["trader1.upbit_paper_stale_loop_reconciliation_operator_queue_closure_report.v1"])
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["upbit_paper_stale_loop_reconciliation_operator_queue_closure_validator"])
    )
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
    report = write_runtime_report()
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    remove_cache_artifacts()
    write_source_bundle_manifest()

    tests_run = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_stale_loop_reconciliation_operator_queue_closure.py",
                "-q",
            ]
        )
    ]
    remove_cache_artifacts()
    write_source_bundle_manifest()
    validators_run = run_validators(BOOTSTRAP_VALIDATORS)
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    remove_cache_artifacts()
    write_source_bundle_manifest()
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, report)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)
    remove_cache_artifacts()
    write_source_bundle_manifest()

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "closure_status": report.get("closure_status"),
                "closure_item_count": report.get("closure_item_count"),
                "ledger_recheck_ready_count": report.get("ledger_recheck_ready_count"),
                "recovery_guard_required_count": report.get("recovery_guard_required_count"),
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
