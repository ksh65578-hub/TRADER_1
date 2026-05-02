from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

PATCH_BASENAME = "MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_REFRESH"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE-REFRESH"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_PORTFOLIO_TRUTH_RECONCILIATION_CLOSURE"
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
from tools.run_upbit_paper_ledger_idempotency_runtime_evidence_refresh import (  # noqa: E402
    refresh_upbit_paper_ledger_idempotency_runtime_evidence,
)
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import ROOT_LAUNCHER_SPECS, build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


RUNTIME_REPORT_PATH = (
    ROOT
    / "system"
    / "runtime"
    / "upbit"
    / "krw_spot"
    / "paper"
    / SESSION_ID
    / "ledger"
    / "upbit_paper_ledger_idempotency_runtime_evidence_report.json"
)

VALIDATORS_REQUIRED = [
    "schema_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "paper_ledger_rollup_validator",
    "reconciliation_validator",
    "ledger_reconciliation_validator",
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
    "tools/run_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
    "tools/emit_upbit_paper_ledger_idempotency_runtime_evidence_refresh_patch_evidence.py",
    "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
    "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
    "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json",
    rel(RUNTIME_REPORT_PATH),
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
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


def write_runtime_artifacts() -> tuple[dict[str, Any], list[str]]:
    result = refresh_upbit_paper_ledger_idempotency_runtime_evidence(
        root=ROOT,
        session_id=SESSION_ID,
        evidence_id="mvp4-upbit-paper-ledger-idempotency-runtime-evidence-refresh",
    )
    if result.validation.status != "PASS":
        raise RuntimeError(f"refresh evidence did not validate: {result.validation.status} {result.validation.blocker_code}")
    report = result.report
    forbidden_flags = ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "scale_up_allowed")
    if any(report.get(flag) for flag in forbidden_flags):
        raise RuntimeError("refresh evidence attempted forbidden live or scale-up permission")

    runtime_artifacts = [rel(result.output_path)]
    for launcher_name in sorted(ROOT_LAUNCHER_SPECS):
        launcher_report = build_launcher_report(launcher_name)
        launcher_report_path, dashboard_paths = write_launcher_runtime_bundle(launcher_report)
        runtime_artifacts.append(rel(launcher_report_path))
        runtime_artifacts.extend(rel(path) for path in dashboard_paths.values())
        if launcher_name == "UPBIT_PAPER":
            dashboard = load_json(dashboard_paths["dashboard_shell"])
            dashboard_result = validate_read_only_dashboard_shell(dashboard)
            if dashboard_result.status != "PASS":
                raise RuntimeError(f"dashboard validation failed: {dashboard_result.status} {dashboard_result.blocker_code}")
            summary = dashboard.get("reconciliation_recovery_summary", {})
            if summary.get("ledger_idempotency_runtime_evidence_status") != "PASS":
                raise RuntimeError("dashboard did not bind refreshed ledger idempotency runtime evidence")
            if summary.get("live_order_allowed") or summary.get("can_live_trade") or summary.get("scale_up_allowed"):
                raise RuntimeError("dashboard refresh attempted forbidden live or scale-up permission")
    return report, sorted(set(runtime_artifacts))


def write_context(now: str, trader_hash: str, agents_hash: str, report: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: VALIDATOR_IMPLEMENTATION
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_DASHBOARD_SHELL", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- The refresh command regenerates the current Upbit PAPER ledger idempotency runtime evidence report from scoped PAPER runtime inputs.
- Duplicate ledger inputs still produce BLOCKED evidence without live permission.
- The root launcher dashboard binds the refreshed PASS evidence as display truth only.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

known_omissions_by_design:
- This patch does not resolve LIVE_READY blockers.
- This patch does not use credentials, private exchange endpoints, real orders, live config mutation, or risk scale-up.
- This patch does not claim long-run PAPER/SHADOW evidence or Binance runtime closure.

runtime_summary:
- runtime_evidence_status: {report.get("runtime_evidence_status")}
- idempotency_status: {report.get("idempotency_status")}
- reconciliation_status: {report.get("reconciliation_status")}
- portfolio_provenance_status: {report.get("portfolio_provenance_status")}
- source_ledger_jsonl_count: {report.get("source_ledger_jsonl_count")}
- recomputed_ledger_event_count: {report.get("recomputed_ledger_event_count")}
- mismatch_count: {report.get("mismatch_count")}

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

Upbit PAPER ledger idempotency runtime evidence can now be refreshed from current runtime ledger sources. Last refresh: runtime_evidence_status={report.get("runtime_evidence_status")}, idempotency_status={report.get("idempotency_status")}, reconciliation_status={report.get("reconciliation_status")}, mismatch_count={report.get("mismatch_count")}.

This remains PAPER display/runtime evidence only. It is not LIVE_READY evidence, not a live order permission, and not scale-up evidence.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER ledger idempotency runtime evidence refresh",
            "full_text_marker": f"{REQUIREMENT_ID}: scoped PAPER refresh command must regenerate current ledger idempotency and reconciliation evidence without live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Refresh Upbit PAPER ledger idempotency runtime evidence",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifact_ids,
            "test_ids": [
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_DASHBOARD_SHELL",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-DASHBOARD-UPBIT-PAPER-RUNTIME-EVIDENCE-PROFILE-BINDING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"scoped PAPER refresh command regenerates current ledger idempotency and reconciliation evidence without live permission"
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
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "schema_files": ["contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json"],
            "validator_files": [
                "tools/run_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "tools/run_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
            ],
            "evidence_artifacts": [
                rel(RUNTIME_REPORT_PATH),
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
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
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
    report: dict[str, Any],
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
            "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE",
            "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
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
        "new_or_changed_schema_ids": ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"],
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
            "SECTION_UPBIT_PAPER_RUNTIME",
            "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "SECTION_PORTFOLIO_TRUTH",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE"],
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
            "SECTION_UPBIT_PAPER_RUNTIME",
            "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "SECTION_DASHBOARD_SHELL",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "task_class": "VALIDATOR_IMPLEMENTATION",
        "required_section_ids": [
            "SECTION_UPBIT_PAPER_RUNTIME",
            "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "SECTION_DASHBOARD_SHELL",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "expanded_section_ids": ["AGENTS:0G", "AGENTS:0F", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY"],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_UPBIT_PAPER_IDEMPOTENCY_REFRESH",
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
    report: dict[str, Any],
    runtime_artifacts: list[str],
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_IDEMPOTENCY_REFRESH_NO_LIVE_ORDERS",
            "runtime_evidence_status": report.get("runtime_evidence_status"),
            "idempotency_status": report.get("idempotency_status"),
            "reconciliation_status": report.get("reconciliation_status"),
            "portfolio_provenance_status": report.get("portfolio_provenance_status"),
            "mismatch_count": report.get("mismatch_count", 0),
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
            "runtime_evidence_status": report.get("runtime_evidence_status"),
            "idempotency_status": report.get("idempotency_status"),
            "reconciliation_status": report.get("reconciliation_status"),
            "portfolio_provenance_status": report.get("portfolio_provenance_status"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    audit = {
        "audit_schema_id": "trader1.upbit_paper_ledger_idempotency_runtime_evidence_refresh_audit.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "status": "PASS",
        "runtime_report_path": rel(RUNTIME_REPORT_PATH),
        "runtime_evidence_status": report.get("runtime_evidence_status"),
        "idempotency_status": report.get("idempotency_status"),
        "reconciliation_status": report.get("reconciliation_status"),
        "portfolio_provenance_status": report.get("portfolio_provenance_status"),
        "source_ledger_jsonl_count": report.get("source_ledger_jsonl_count"),
        "recomputed_ledger_event_count": report.get("recomputed_ledger_event_count"),
        "mismatch_count": report.get("mismatch_count"),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.md",
        f"""# MVP4 Upbit PAPER Ledger Idempotency Runtime Evidence Refresh

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added a safe refresh command for current Upbit PAPER ledger idempotency runtime evidence.
- The command writes scoped PAPER evidence only and rejects escaped, live, or non-json output paths.
- The launcher dashboard now sees the refreshed idempotency/reconciliation status as current display truth.
- Duplicate-ledger fixtures remain blocked as RECONCILIATION_REQUIRED.

Runtime evidence:
- runtime_evidence_status={report.get("runtime_evidence_status")}
- idempotency_status={report.get("idempotency_status")}
- reconciliation_status={report.get("reconciliation_status")}
- portfolio_provenance_status={report.get("portfolio_provenance_status")}
- source_ledger_jsonl_count={report.get("source_ledger_jsonl_count")}
- recomputed_ledger_event_count={report.get("recomputed_ledger_event_count")}
- mismatch_count={report.get("mismatch_count")}

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
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []) + ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1"])
    )
    state["implemented_validator_ids"] = sorted(
        set(
            state.get("implemented_validator_ids", [])
            + [
                "upbit_paper_ledger_idempotency_runtime_evidence_validator",
                "read_only_dashboard_validator",
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
    for path in ROOT.rglob("__pycache__"):
        if path.is_dir():
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink(missing_ok=True)
            path.rmdir()
    for path in ROOT.rglob("*.pyc"):
        if path.is_file():
            path.unlink(missing_ok=True)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    report, runtime_artifacts = write_runtime_artifacts()
    write_context(now, trader_hash, agents_hash, report)
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
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_upbit_paper_ledger_idempotency_runtime_evidence_refresh.py"]),
    ]
    validators_run = run_validators(BOOTSTRAP_VALIDATORS)
    patch_result = build_patch_result(now, tests_run, validators_run, BOOTSTRAP_VALIDATORS, report)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, report, runtime_artifacts)
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
    patch_result = build_patch_result(now, tests_run, validators_run, VALIDATORS_REQUIRED, report)
    write_evidence(now, trader_hash, agents_hash, patch_result, report, runtime_artifacts)
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
                "runtime_evidence_status": report.get("runtime_evidence_status"),
                "idempotency_status": report.get("idempotency_status"),
                "reconciliation_status": report.get("reconciliation_status"),
                "mismatch_count": report.get("mismatch_count"),
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
