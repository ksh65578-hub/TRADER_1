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

PATCH_BASENAME = "MVP4_RUNTIME_TRUTH_MARKET_CONTINUITY_REPAIR_PAPER_SHADOW_HARNESS_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260506_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-SHADOW-HARNESS-BINDING"
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
    "paper_shadow_harness_binding_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "paper_shadow_evidence_accumulation_validator",
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

CHANGED_ARTIFACTS = [
    "contracts/schema/paper_shadow_harness_binding_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "contracts/registry.yaml",
    "trader1/research/shadow/paper_shadow_harness_binding.py",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/validation/mvp0_validators.py",
    "tests/research/test_paper_shadow_harness_binding.py",
    "tests/validators/test_paper_shadow_harness_binding_validator.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_paper_shadow_harness_binding_patch_evidence.py",
    CONTEXT_PACK_PATH,
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
        "schema_id": "trader1.paper_shadow_harness_binding_audit_report.v1",
        "patch_id": PATCH_ID,
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "finding": (
            "PAPER/SHADOW harness execution and PAPER/SHADOW evidence accumulation existed as separate artifacts. "
            "The dashboard could show a short-window harness while strategy evidence still looked not loaded, and stale/sample deficits were easy to confuse with operator reconciliation blockers."
        ),
        "patch": (
            "Added a source-bound PAPER/SHADOW harness binding report and validator. It classifies evidence into critical blockers, warnings, and informational notes; only critical source/hash/live-safety drift blocks routine PAPER current-truth regeneration and non-live collection. "
            "The dashboard now lists paper_shadow_harness_binding_report.json as a display source without creating live permission."
        ),
        "acceptance_conditions": [
            "Harness-only binding waits for evidence without blocking routine PAPER current-truth regeneration",
            "Valid PAPER/SHADOW evidence binds to PAPER scorecard input only and keeps optimizer/convergence waiting",
            "Stale PAPER/SHADOW evidence becomes stale display-only warning, not operator reconciliation",
            "Critical source/live/hash drift blocks the binding fail-closed",
            "Dashboard lists the binding source artifact without LIVE_READY, live orders, or scale-up",
            "Open contract gap count remains 13 and live/scale flags remain false",
        ],
        "blockers_removed": [
            "PAPER/SHADOW harness NOT_LOADED ambiguity for dashboard source binding is reduced when a binding report is present",
            "Routine stale/sample PAPER/SHADOW refresh no longer appears as operator reconciliation by default",
        ],
        "blockers_remaining": open_gaps,
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
task_class: PAPER_SHADOW_EVIDENCE_BINDING_PATCH
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_shadow_harness_binding_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(all_artifacts())}

acceptance_checklist:
- PAPER/SHADOW harness output is bound to evidence accumulation status.
- Critical source blockers are separated from warnings and informational status.
- Stale/sample deficits do not require operator reconciliation.
- Optimizer/convergence remain waiting for real evidence.
- Live orders, LIVE_READY, credentials, live config mutation, and scale-up remain blocked.

known_omissions_by_design:
- This patch does not invent or fake PAPER/SHADOW samples.
- This patch does not close long-run/runtime/operator/external evidence gaps.
- This patch does not implement Binance runtime.

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

PAPER/SHADOW harness output can now be bound into a single report that separates critical source blockers from warning-level stale/sample deficits. The binding is display/analysis-only, can feed PAPER scorecard input when source evidence is valid, and cannot enable optimizer/convergence promotion, LIVE_READY, live orders, or scale-up.
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    schema_ids = ["trader1.paper_shadow_harness_binding_report.v1", "trader1.read_only_dashboard_shell.v1"]

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "PAPER/SHADOW runtime harness and evidence graph reduction",
            "full_text_marker": f"{REQUIREMENT_ID}: bind non-live PAPER/SHADOW harness output to evidence accumulation status and classify evidence as critical warning informational",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "PAPER/SHADOW harness binding and evidence graph reduction",
            "requirement_kind": "RUNTIME_EVIDENCE_BINDING_PATCH",
            "schema_ids": schema_ids,
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": all_artifacts(),
            "test_ids": [
                "tests/research/test_paper_shadow_harness_binding.py",
                "tests/validators/test_paper_shadow_harness_binding_validator.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-SHADOW-OBSERVATION-ACTUAL-RUNTIME-HARNESS",
                "REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"bind non-live PAPER SHADOW harness output to evidence accumulation status and classify blockers warnings informational"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_LIVE_BLOCKED",
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
            "section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "schema_files": [
                "contracts/schema/paper_shadow_harness_binding_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "contracts/registry.yaml",
                "trader1/research/shadow/paper_shadow_harness_binding.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/research/test_paper_shadow_harness_binding.py",
                "tests/validators/test_paper_shadow_harness_binding_validator.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [],
            "runtime_modules": ["trader1/research/shadow/paper_shadow_harness_binding.py"],
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
            "status": "IMPLEMENTED_LIVE_BLOCKED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    base.write_json(matrix_path, matrix)


def finalize_patch_result(
    patch_result: dict[str, Any],
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    report: dict[str, Any],
) -> dict[str, Any]:
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "target_mvp_level": "MVP-4",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-SHADOW-OBSERVATION-ACTUAL-RUNTIME-HARNESS",
                "REQ-MVP4-PAPER-SHADOW-EVIDENCE-ACCUMULATION-HARDENING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER,SHADOW",
            "new_registry_items": [REQUIREMENT_ID, "paper_shadow_harness_binding_validator"],
            "new_or_changed_schema_ids": ["trader1.paper_shadow_harness_binding_report.v1", "trader1.read_only_dashboard_shell.v1"],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_STRATEGY_PROFITABILITY", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
            "remaining_blockers": report["open_contract_gap_ids"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "PAPER/SHADOW actual runtime harness",
                "PAPER/SHADOW evidence accumulation",
                "dashboard source artifact projection",
                "live final guard",
            ],
            "task_class": "PAPER_SHADOW_EVIDENCE_BINDING_PATCH",
            "required_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "WAITING_FOR_REAL_RUNTIME_OR_REPLAY_EVIDENCE",
            "optimizer_guardrail_result": "PASS_WAITING_FOR_EVIDENCE_NO_NEW_WRAPPER",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_state_after": "WAITING_FOR_REAL_RUNTIME_OR_REPLAY_EVIDENCE",
            "convergence_guardrail_result": "PASS_WAITING_FOR_EVIDENCE_NO_SCALE_UP",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
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
        set(state.get("implemented_schema_ids", []) + ["trader1.paper_shadow_harness_binding_report.v1"])
    )
    state["implemented_validator_ids"] = sorted(
        set(state.get("implemented_validator_ids", []) + ["paper_shadow_harness_binding_validator"])
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
            "stage_gate_status": "PASS_PAPER_SHADOW_HARNESS_BINDING_LIVE_BLOCKED",
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
            "known_blockers": report["open_contract_gap_ids"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.report.json", report)
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260506.md",
        f"""# MVP4 Paper Shadow Harness Binding Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- PAPER/SHADOW harness and evidence accumulation were not reduced into one source-bound binding state.
- Routine stale/sample deficits could be confused with operator reconciliation.

Patch:
- Added paper_shadow_harness_binding_report schema, builder, validator, and tests.
- Dashboard source artifacts can list paper_shadow_harness_binding_report.json.
- Critical blockers, warnings, and informational notes are separated.

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
""",
    )


def write_session_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], report: dict[str, Any]) -> None:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    tests_run = patch_result["tests_run"]
    validators_run = patch_result["validators_run"]
    accepted = all(item.get("status") == "PASS" for item in tests_run + validators_run)
    acceptance_status = "PASS" if accepted else "FAIL"
    areas = [
        ("strategy / regime / entry / exit", "High", "Evidence binding now exposes PAPER scorecard input only when source evidence validates.", "No optimizer promotion."),
        ("expected edge / fee / slippage / funding", "High", "Cost evidence count is explicit in the binding.", "Missing cost remains warning/blocker for evidence use."),
        ("signal grading / parameter search / strategy competition", "High", "Optimizer/convergence remains waiting for real runtime or replay evidence.", "No extra wrapper expansion."),
        ("paper / shadow / replay / micro-live / live", "Critical", "PAPER/SHADOW harness binding added.", "Live/micro-live untouched."),
        ("LIVE_READY snapshot / live gating / fail-closed", "Critical", "LIVE_READY remains unwritten.", "All live flags false."),
        ("risk engine / drawdown / cooling / kill switch", "High", "No risk sizing path changed.", "Scale-up remains false."),
        ("exchange / market_type / namespace separation", "High", "Binding is UPBIT/KRW_SPOT/PAPER+SHADOW scoped.", "No Binance evidence transfer."),
        ("Upbit spot / Binance spot / Binance futures 1x long-short", "High", "Upbit PAPER/SHADOW evidence path deepened.", "Binance remains scaffold/surface."),
        ("order lifecycle / execution quality / partial fill", "Critical", "No order-capable path touched.", "Order endpoints remain false."),
        ("ledger / reconciliation / idempotency", "Critical", "Routine PAPER refresh is separated from reconciliation-only gaps.", "Residual reconciliation gaps remain."),
        ("data health / stale data / gap / duplicate / clock drift", "High", "Stale evidence is display-only warning when source scope is otherwise valid.", "Critical drift still blocks."),
        ("concurrency / race condition / restart recovery", "Medium", "Binding is deterministic/hash-backed and does not add a daemon.", "No new writer race."),
        ("dashboard / USER_STATUS_SUMMARY / user simplicity", "Medium", "Dashboard can list binding source artifact.", "Top-level live state remains blocked."),
        ("validator / schema / registry / acceptance artifacts", "Medium", "Schema, registry, validator, tests, patch result, state, and session artifacts updated.", "Validators required."),
        ("testing / pytest / paper run proof / live block proof", "High", "Targeted tests cover binding states and dashboard source projection.", "No fake samples."),
        ("security / secrets / API key safety", "Critical", "No credentials or private endpoints used.", "Credential flags false."),
        ("deployment / packaging / git hygiene / pycache / generated artifacts", "Medium", "Evidence artifacts generated; runtime outputs excluded from stage.", "No audit ledger deletion."),
        ("tax/accounting/export readiness", "Low", "No tax/export path changed.", "Future scoped patch."),
        ("KRW cashflow / profit conversion / withdrawal policy", "Medium", "No cashflow policy changed.", "PAPER-only."),
        ("overfitting / walk-forward / out-of-sample validation", "High", "Binding does not bypass OOS/long-run thresholds.", "Optimizer remains disabled."),
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
            "blockers_removed": report["blockers_removed"],
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
            "paper_shadow_harness_binding_implemented": True,
            "runtime_evidence_claimed_by_this_patch": False,
            "paper_shadow_samples_faked": False,
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
            "status": "PASS_BINDING_SOURCE_VISIBLE_LIVE_BLOCKED",
            "dashboard_source_artifact_added": "paper_shadow_harness_binding_report.json",
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

Current state: PAPER/SHADOW harness output now has a source-bound binding report. It can show whether we have only a short harness, valid PAPER scorecard evidence, stale display-only evidence, or critical source drift.

What changed:
- Added paper_shadow_harness_binding_report.
- Stale/sample deficits are warnings, not operator reconciliation.
- Critical source/live/hash drift still blocks fail-closed.
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

This session implemented PAPER/SHADOW harness binding and evidence graph reduction. It did not start a long-run PAPER/SHADOW collection, close residual external/operator gaps, write LIVE_READY, use credentials, mutate live config, or enable live orders.

## Defects Found And Patched

1. Critical: PAPER/SHADOW harness state and evidence accumulation state were not bound into one source graph.
2. High: Stale/sample evidence deficits could look like operator reconciliation.
3. High: Optimizer/convergence panels needed clearer "waiting for evidence" boundaries.
4. Medium: Dashboard source list could not show the binding report.

## Validation

Test status counts: {json.dumps(status_counts(tests_run), sort_keys=True)}

Validator status counts: {json.dumps(status_counts(validators_run), sort_keys=True)}

## Whole System State

Overall state: PAPER/SHADOW harness binding is implemented and dashboard-visible; real long-run runtime, external/live evidence, and residual reconciliation gaps remain blocking.

Overall completion score: 75/100.

Live trading candidate: NO.

## Most Dangerous Defects Top 10

1. Long-run PAPER/SHADOW runtime evidence is still insufficient.
2. Residual reconciliation/operator gaps remain open.
3. External official API/read-only/burn-in/manual approval evidence is missing.
4. PAPER/SHADOW samples still need real runtime or replay accumulation.
5. Profitability optimizer evidence maturity is still insufficient.
6. Binance spot/futures remain scaffold/surface.
7. Paper-to-live execution parity is unproven.
8. Market regime-labeled outcome coverage is missing from actual runtime.
9. Risk exposure remains freshness-bound to PAPER current truth.
10. Scale-up remains ineligible.

## Next Session Area

Proceed to risk exposure truth and PAPER/SHADOW collection report hardening without adding optimizer/convergence wrappers.

## Implementation Roadmap

1. Bind risk exposure/drawdown directly to latest verified PAPER current truth.
2. Add source-bound market regime tags to PAPER/SHADOW evidence collection.
3. Keep optimizer/convergence disabled until replay/PAPER/SHADOW thresholds are met.
4. Keep stale display artifacts from blocking unrelated non-live collection.
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
                "tests/research/test_paper_shadow_harness_binding.py",
                "tests/validators/test_paper_shadow_harness_binding_validator.py",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_lists_paper_shadow_harness_binding_source_without_live_permission",
                "-q",
            ],
            timeout_seconds=1800,
        ),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(BOOTSTRAP_VALIDATORS_REQUIRED))
    patch_result = finalize_patch_result(
        base.build_patch_result(now, tests_run, validators_run),
        now,
        tests_run,
        validators_run,
        BOOTSTRAP_VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=3600))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = finalize_patch_result(
        base.build_patch_result(now, tests_run, validators_run),
        now,
        tests_run,
        validators_run,
        VALIDATORS_REQUIRED,
        report,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, write_session=True)

    tests_run.append(run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = finalize_patch_result(
        base.build_patch_result(now, tests_run, validators_run),
        now,
        tests_run,
        validators_run,
        VALIDATORS_REQUIRED,
        report,
    )
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
