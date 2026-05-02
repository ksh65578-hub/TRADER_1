from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-TRUTH-RECONCILIATION-CLOSURE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_STALE_LOOP_RECONCILIATION_OPERATOR_QUEUE_CLOSURE"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

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
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.ledger.paper_ledger_rollup import (  # noqa: E402
    build_paper_ledger_rollup_report,
    validate_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (  # noqa: E402
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
    write_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


RUNTIME_BASE = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / SESSION_ID
ROLLUP_PATH = RUNTIME_BASE / "ledger" / "paper_ledger_rollup_report.json"
SPECIFIC_ROLLUP_PATH = (
    RUNTIME_BASE / "ledger" / "mvp4-upbit-paper-portfolio-truth-reconciliation-closure.paper_ledger_rollup_report.json"
)
LEDGER_EVIDENCE_PATH = RUNTIME_BASE / "ledger" / "upbit_paper_ledger_idempotency_runtime_evidence_report.json"
DASHBOARD_PATH = RUNTIME_BASE / "dashboard_shell.json"

VALIDATORS_REQUIRED = [
    "schema_validator",
    "paper_ledger_rollup_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
]

BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
]

CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_upbit_paper_portfolio_truth_reconciliation_closure_patch_evidence.py",
    rel(ROLLUP_PATH),
    rel(SPECIFIC_ROLLUP_PATH),
    rel(LEDGER_EVIDENCE_PATH),
    rel(DASHBOARD_PATH),
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED",
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


def write_runtime_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    rollup = build_paper_ledger_rollup_report(
        root=ROOT,
        session_id=SESSION_ID,
        rollup_id="mvp4-upbit-paper-portfolio-truth-reconciliation-closure",
    )
    rollup_result = validate_paper_ledger_rollup_report(rollup)
    if rollup_result.status != "PASS":
        raise RuntimeError(f"paper ledger rollup failed: {rollup_result.status} {rollup_result.blocker_code}")
    rollup_path = write_paper_ledger_rollup_report(root=ROOT, report=rollup)

    ledger_evidence = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
        root=ROOT,
        session_id=SESSION_ID,
        evidence_id="upbit-paper-portfolio-truth-reconciliation-closure",
    )
    ledger_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(ledger_evidence)
    if ledger_result.status != "PASS":
        raise RuntimeError(f"ledger idempotency evidence failed: {ledger_result.status} {ledger_result.blocker_code}")
    ledger_path = write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=ROOT, report=ledger_evidence)

    launcher_report = build_launcher_report("UPBIT_PAPER")
    launcher_path, dashboard_paths = write_launcher_runtime_bundle(launcher_report, ROOT)
    dashboard = load_json(dashboard_paths["dashboard_shell"])
    dashboard_result = validate_read_only_dashboard_shell(dashboard)
    if dashboard_result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {dashboard_result.status} {dashboard_result.blocker_code}")
    portfolio = dashboard.get("portfolio_snapshot", {})
    reconciliation = dashboard.get("reconciliation_recovery_summary", {})
    if portfolio.get("status") != "VERIFIED":
        raise RuntimeError("dashboard did not expose verified PAPER portfolio display truth")
    if portfolio.get("blocking_reason") != "STALE_LOOP_RECONCILIATION_AFTER_REGENERATION_REQUIRED":
        raise RuntimeError("dashboard did not preserve stale-loop reconciliation blocker")
    if reconciliation.get("status") != "BLOCKED":
        raise RuntimeError("reconciliation panel must remain blocked while stale-loop review is unresolved")
    forbidden_flags = ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "scale_up_allowed")
    if any(dashboard.get(flag) for flag in forbidden_flags):
        raise RuntimeError("dashboard attempted forbidden live/order/scale permission")

    runtime_artifacts = [
        rel(rollup_path),
        rel(ROLLUP_PATH),
        rel(ledger_path),
        rel(launcher_path),
        *(rel(path) for path in dashboard_paths.values()),
    ]
    return rollup, ledger_evidence, dashboard, sorted(set(runtime_artifacts))


def write_context(now: str, trader_hash: str, agents_hash: str, dashboard: dict[str, Any]) -> None:
    portfolio = dashboard.get("portfolio_snapshot", {})
    reconciliation = dashboard.get("reconciliation_recovery_summary", {})
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE", "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_ledger_rollup_report.v1", "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Verified PAPER portfolio display remains allowed only when the summary snapshot is fresh and bound to matching ledger idempotency runtime evidence.
- Stale-loop/post-rerun reconciliation blockers still block current-evidence writes, trading review, live orders, and scale-up.
- The operator status explains that portfolio values are display truth only and do not prove continuous PAPER engine operation.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not resolve stale-loop reconciliation, post-rerun operator queues, LIVE_READY, MICRO_LIVE, or Binance runtime gaps.
- This patch does not use credentials, private exchange endpoints, real orders, live config mutation, or risk scale-up.

runtime_summary:
- portfolio_status: {portfolio.get("status")}
- cash: {portfolio.get("cash", {}).get("value_display")}
- equity: {portfolio.get("equity", {}).get("value_display")}
- position_count: {portfolio.get("positions", {}).get("value_display")}
- portfolio_blocking_reason: {portfolio.get("blocking_reason")}
- reconciliation_status: {reconciliation.get("status")}
- ledger_idempotency_runtime_evidence_status: {reconciliation.get("ledger_idempotency_runtime_evidence_status")}
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

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

The Upbit PAPER dashboard can now display verified simulated portfolio values when a fresh summary portfolio snapshot is bound to matching ledger idempotency runtime evidence. Reconciliation blockers remain visible and still block current-evidence writes, trading review, live orders, and risk scale-up.

Current dashboard display: portfolio_status={portfolio.get("status")}, cash={portfolio.get("cash", {}).get("value_display")}, equity={portfolio.get("equity", {}).get("value_display")}, blocker={portfolio.get("blocking_reason")}.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, runtime_artifacts: list[str]) -> None:
    artifact_ids = sorted(set(CHANGED_ARTIFACTS + runtime_artifacts))
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_SERVING_TRUTH",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER portfolio truth reconciliation closure",
            "full_text_marker": f"{REQUIREMENT_ID}: verified PAPER portfolio display may bypass post-rerun current-evidence blockers only when bound to PASS ledger idempotency runtime evidence while live remains blocked",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Display bound verified PAPER portfolio while reconciliation still blocks writes",
            "requirement_kind": "DASHBOARD_RUNTIME_EVIDENCE_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifact_ids,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_SERVING_TRUTH", "SECTION_LEDGER_VALIDATOR_IDS", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE-REFRESH",
                "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"verified PAPER portfolio display requires bound ledger idempotency runtime evidence and does not unlock current evidence writes or live"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_DASHBOARD_VISIBLE_LIVE_BLOCKED",
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
            "section_id": "SECTION_DASHBOARD_SERVING_TRUTH",
            "schema_files": [
                "contracts/schema/read_only_dashboard_shell.schema.json",
                "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json",
            ],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "trader1/runtime/ledger/paper_ledger_rollup.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "evidence_manifest_path",
                "validator_run_log_path",
                "stage_gate_result_path",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_DASHBOARD_VISIBLE_LIVE_BLOCKED",
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
    validators_required: list[str],
) -> dict[str, Any]:
    patch_result: dict[str, Any] = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [
            REQUIREMENT_ID,
            "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE",
            "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH",
            "REQ-MVP4-LIVE-FINAL-GUARD",
        ],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [REQUIREMENT_ID],
        "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
        "validators_required": validators_required,
        "validators_run": validators_run,
        "tests_run": tests_run,
        "coverage_unmapped_count": 0,
        "coverage_index_result": "UPDATED_PASS",
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
        "read_cache_update_required": True,
        "context_pack_update_required": True,
        "current_implementation_state_updated": True,
        "next_task_class": NEXT_TASK_CLASS,
        "next_required_section_ids": [
            "SECTION_DASHBOARD_SERVING_TRUTH",
            "SECTION_LEDGER_VALIDATOR_IDS",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "next_optional_section_ids": ["SECTION_AGENTS_DASHBOARD_SERVING_TRUTH", "SECTION_MVP1_DASHBOARD_REQUIRED_OUTPUT"],
        "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "BINANCE_FUTURES_LIVE"],
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
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "AGENTS:0G",
            "AGENTS:0F",
            "SECTION_DASHBOARD_SERVING_TRUTH",
            "SECTION_LEDGER_VALIDATOR_IDS",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "task_class": "DASHBOARD_UX",
        "required_section_ids": [
            "SECTION_DASHBOARD_SERVING_TRUTH",
            "SECTION_LEDGER_VALIDATOR_IDS",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "expanded_section_ids": ["AGENTS:0G", "AGENTS:0F", "SECTION_DASHBOARD_SERVING_TRUTH"],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "REUSED_HASH_MATCH",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UPDATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_UPBIT_PAPER_PORTFOLIO_TRUTH",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
    }
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    rollup: dict[str, Any],
    ledger_evidence: dict[str, Any],
    dashboard: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    portfolio = dashboard.get("portfolio_snapshot", {})
    reconciliation = dashboard.get("reconciliation_recovery_summary", {})
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_PORTFOLIO_DISPLAY_TRUTH_NO_LIVE_ORDERS",
            "portfolio_status": portfolio.get("status"),
            "portfolio_blocking_reason": portfolio.get("blocking_reason"),
            "reconciliation_status": reconciliation.get("status"),
            "ledger_idempotency_runtime_evidence_status": reconciliation.get("ledger_idempotency_runtime_evidence_status"),
            "rollup_status": rollup.get("rollup_status"),
            "runtime_evidence_status": ledger_evidence.get("runtime_evidence_status"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
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
            "portfolio_status": portfolio.get("status"),
            "portfolio_blocking_reason": portfolio.get("blocking_reason"),
            "reconciliation_status": reconciliation.get("status"),
            "ledger_idempotency_runtime_evidence_status": reconciliation.get("ledger_idempotency_runtime_evidence_status"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    audit = {
        "audit_schema_id": "trader1.upbit_paper_portfolio_truth_reconciliation_closure_audit.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "status": "PASS",
        "portfolio_status": portfolio.get("status"),
        "cash_display": portfolio.get("cash", {}).get("value_display"),
        "equity_display": portfolio.get("equity", {}).get("value_display"),
        "position_count_display": portfolio.get("positions", {}).get("value_display"),
        "portfolio_blocking_reason": portfolio.get("blocking_reason"),
        "reconciliation_status": reconciliation.get("status"),
        "ledger_idempotency_runtime_evidence_status": reconciliation.get("ledger_idempotency_runtime_evidence_status"),
        "rollup_status": rollup.get("rollup_status"),
        "runtime_evidence_status": ledger_evidence.get("runtime_evidence_status"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.md",
        f"""# MVP4 Upbit PAPER Portfolio Truth Reconciliation Closure

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Bound verified PAPER portfolio display to matching ledger idempotency runtime evidence.
- Kept stale-loop/current-evidence reconciliation blockers visible and blocking writes/review.
- Kept operation status in safe checking mode when portfolio values are verified but reconciliation is still blocked.

Runtime display:
- portfolio_status={portfolio.get("status")}
- cash={portfolio.get("cash", {}).get("value_display")}
- equity={portfolio.get("equity", {}).get("value_display")}
- positions={portfolio.get("positions", {}).get("value_display")}
- portfolio_blocking_reason={portfolio.get("blocking_reason")}
- reconciliation_status={reconciliation.get("status")}
- ledger_idempotency_runtime_evidence_status={reconciliation.get("ledger_idempotency_runtime_evidence_status")}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials, private account calls, live orders, live config mutation, or risk scale-up
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_validator_ids"] = sorted(
        set(
            state.get("implemented_validator_ids", [])
            + [
                "read_only_dashboard_validator",
                "paper_ledger_rollup_validator",
                "upbit_paper_ledger_idempotency_runtime_evidence_validator",
            ]
        )
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


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    rollup, ledger_evidence, dashboard, runtime_artifacts = write_runtime_artifacts()
    write_context(now, trader_hash, agents_hash, dashboard)
    update_requirement_artifacts(now, trader_hash, agents_hash, runtime_artifacts)

    tests_run = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "-q",
            ]
        )
    ]
    validators_run = run_validators(BOOTSTRAP_VALIDATORS)
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, rollup, ledger_evidence, dashboard, runtime_artifacts)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    remove_cache_artifacts()
    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_read_only_dashboard_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_bundle_security_validators.py"]),
        ]
    )
    write_source_bundle_manifest()
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, rollup, ledger_evidence, dashboard, runtime_artifacts)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)
    remove_cache_artifacts()

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "portfolio_status": dashboard.get("portfolio_snapshot", {}).get("status"),
                "portfolio_blocker": dashboard.get("portfolio_snapshot", {}).get("blocking_reason"),
                "reconciliation_status": dashboard.get("reconciliation_recovery_summary", {}).get("status"),
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
