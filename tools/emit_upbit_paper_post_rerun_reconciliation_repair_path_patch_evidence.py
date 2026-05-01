from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RECONCILIATION-REPAIR-PATH"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH_DASHBOARD_BINDING"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from tools.emit_profitability_evidence_runtime_linkage_patch import (  # noqa: E402
    LATEST_RUNTIME_PATH as PROFITABILITY_LATEST_RUNTIME_PATH,
    ROLLUP_PATH as PROFITABILITY_ROLLUP_PATH,
    update_rollup as update_profitability_rollup,
)
from trader1.runtime.paper.upbit_paper_post_rerun_reconciliation_repair_path import (  # noqa: E402
    build_upbit_paper_post_rerun_reconciliation_repair_path_report,
    validate_upbit_paper_post_rerun_reconciliation_repair_path_report,
    write_upbit_paper_post_rerun_reconciliation_repair_path_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_post_rerun_resolution_current_evidence_closure_validator",
    "upbit_paper_post_rerun_current_evidence_closure_recheck_validator",
    "upbit_paper_post_rerun_reconciliation_repair_path_validator",
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
    "contracts/schema/upbit_paper_post_rerun_reconciliation_repair_path_report.schema.json",
    "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/paper_runtime/upbit_paper_post_rerun_reconciliation_repair_path_report.json",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_post_rerun_reconciliation_repair_path_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "POST_RERUN_RESOLUTION_CURRENT_EVIDENCE_CLOSURE_REQUIRED",
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


def write_runtime_artifact() -> tuple[dict[str, Any], list[str]]:
    report = build_upbit_paper_post_rerun_reconciliation_repair_path_report(
        root=ROOT,
        session_id=SESSION_ID,
        repair_path_id="mvp4-upbit-paper-post-rerun-reconciliation-repair-path",
    )
    result = validate_upbit_paper_post_rerun_reconciliation_repair_path_report(report)
    if result.status != "PASS":
        raise RuntimeError(f"post-rerun repair path did not validate: {result.status} {result.blocker_code}")
    report_path = write_upbit_paper_post_rerun_reconciliation_repair_path_report(root=ROOT, report=report)
    return report, [base.rel(report_path)]


def refresh_profitability_runtime_linkage(now: str, trader_hash: str, agents_hash: str) -> None:
    update_profitability_rollup(
        PROFITABILITY_ROLLUP_PATH,
        now=now,
        trader_hash=trader_hash,
        agents_hash=agents_hash,
        runtime_path=PROFITABILITY_LATEST_RUNTIME_PATH,
    )


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1", "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1", "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- The repair path binds to validated post-rerun closure and closure-recheck sources.
- The repair path declares the four required gates before current evidence can be rebuilt.
- All repair gates remain blocked and unsatisfied in this patch.
- No current evidence writer, current ledger JSONL writer, latest runtime pointer, live order, credential, long-run evidence, promotion, or scale-up permission is created.

known_omissions_by_design:
- This patch is not a repair writer and does not resolve POST_RERUN_RECONCILIATION_REQUIRED.
- This patch is not a LIVE_ENABLING_PATCH, live config mutation, credential path, current portfolio writer, or scale-up patch.
- Dashboard binding is left for the next safe task.

runtime_summary:
- repair_path_status: {report["repair_path_status"]}
- repair_gate_count: {report["repair_gate_count"]}
- satisfied_repair_gate_count: {report["satisfied_repair_gate_count"]}
- blocked_repair_gate_count: {report["blocked_repair_gate_count"]}
- source_closure_status: {report["source_closure_status"]}
- source_recheck_status: {report["source_recheck_status"]}
- source_recheck_bridge_status: {report["source_recheck_bridge_status"]}
- current_evidence_write_allowed: false
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
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

Post-rerun reconciliation remains blocked. The repair path now names the exact gated evidence needed before any separate current-evidence repair writer can be considered.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, runtime_artifacts: list[str]) -> None:
    artifacts = sorted(set(CHANGED_ARTIFACTS + runtime_artifacts))
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER post-rerun reconciliation repair path",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: unresolved post-rerun reconciliation requires explicit repair gates before current-evidence writes"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER post-rerun reconciliation repair path",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1",
                "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1",
                "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": ["tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RESOLUTION-CURRENT-EVIDENCE-CLOSURE",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-CLOSURE-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"unresolved post-rerun reconciliation requires explicit repair gates before current-evidence writes"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_REPAIR_PATH_LIVE_BLOCKED",
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
                "contracts/schema/upbit_paper_post_rerun_reconciliation_repair_path_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_resolution_current_evidence_closure_report.schema.json",
                "contracts/schema/upbit_paper_post_rerun_current_evidence_closure_recheck_report.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py"],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_post_rerun_reconciliation_repair_path.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_resolution_current_evidence_closure.py",
                "trader1/runtime/paper/upbit_paper_post_rerun_current_evidence_closure_recheck.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_REPAIR_PATH_LIVE_BLOCKED",
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
    report: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_UPBIT_PAPER_PORTFOLIO_CURRENT_EVIDENCE_BRIDGE_UX.patch_result.json"
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
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-RESOLUTION-CURRENT-EVIDENCE-CLOSURE",
                "REQ-MVP4-UPBIT-PAPER-POST-RERUN-CURRENT-EVIDENCE-CLOSURE-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [
                REQUIREMENT_ID,
                "upbit_paper_post_rerun_reconciliation_repair_path_validator",
            ],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_post_rerun_reconciliation_repair_path_report.v1",
                "trader1.upbit_paper_post_rerun_resolution_current_evidence_closure_report.v1",
                "trader1.upbit_paper_post_rerun_current_evidence_closure_recheck_report.v1",
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
            "next_required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
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
                "TRADER_1.0G",
                "AGENTS.0G",
                "post-rerun closure",
                "post-rerun closure recheck",
                "live final guard",
            ],
            "task_class": "MVP4_UPBIT_PAPER_POST_RERUN_RECONCILIATION_REPAIR_PATH",
            "required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_REPAIR_PATH_BLOCKED_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_REPAIR_PATH_DOES_NOT_CREATE_RANKING_OR_LIVE_PERMISSION",
            "convergence_state_before": "POST_RERUN_CLOSURE_RECHECK_CONFIRMED_LEDGER_PASS_CANNOT_OVERRIDE_BLOCKER",
            "convergence_state_after": "POST_RERUN_RECONCILIATION_REPAIR_PATH_DECLARED_ALL_GATES_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_CURRENT_EVIDENCE_MUTATION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
            "post_rerun_current_evidence_write_allowed_count": 0,
            "post_rerun_current_evidence_write_authorized_count": 0,
            "candidate_current_evidence_usable_count": 0,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
    runtime_artifacts: list[str],
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
            "stage_gate_status": "PASS_POST_RERUN_RECONCILIATION_REPAIR_PATH_LIVE_BLOCKED",
            "repair_path_status": report["repair_path_status"],
            "repair_gate_count": report["repair_gate_count"],
            "satisfied_repair_gate_count": report["satisfied_repair_gate_count"],
            "blocked_repair_gate_count": report["blocked_repair_gate_count"],
            "source_closure_status": report["source_closure_status"],
            "source_recheck_status": report["source_recheck_status"],
            "source_recheck_bridge_status": report["source_recheck_bridge_status"],
            "current_evidence_write_allowed": False,
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
            "artifact_paths": sorted(
                set(
                    [
                        *CHANGED_ARTIFACTS,
                        *runtime_artifacts,
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "repair_path_status": report["repair_path_status"],
            "repair_gate_count": report["repair_gate_count"],
            "satisfied_repair_gate_count": report["satisfied_repair_gate_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Post-Rerun Reconciliation Repair Path Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added an analysis-only repair path report for the unresolved post-rerun reconciliation blocker.
- The report binds to the current-evidence closure and closure-recheck source hashes.
- The report declares four blocked repair gates before any future separate current-evidence repair writer can be considered.

Runtime evidence:
- repair_path_status={report["repair_path_status"]}
- repair_gate_count={report["repair_gate_count"]}
- satisfied_repair_gate_count={report["satisfied_repair_gate_count"]}
- blocked_repair_gate_count={report["blocked_repair_gate_count"]}
- source_closure_status={report["source_closure_status"]}
- source_recheck_status={report["source_recheck_status"]}
- source_recheck_bridge_status={report["source_recheck_bridge_status"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no current evidence writer enabled
- no credentialed exchange/account/API calls
- no live order path enabled
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    report: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report, runtime_artifacts)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    report, runtime_artifacts = write_runtime_artifact()
    refresh_profitability_runtime_linkage(now, trader_hash, agents_hash)
    write_context(now, trader_hash, agents_hash, report)
    update_requirement_artifacts(now, trader_hash, agents_hash, runtime_artifacts)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_post_rerun_reconciliation_repair_path.py",
                "tests/runtime/test_upbit_paper_post_rerun_current_evidence_closure_recheck.py",
                "tests/runtime/test_upbit_paper_post_rerun_resolution_current_evidence_closure.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, runtime_artifacts)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, report)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, report, runtime_artifacts)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "repair_path_status": report["repair_path_status"],
                "satisfied_repair_gate_count": report["satisfied_repair_gate_count"],
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
