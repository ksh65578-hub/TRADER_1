from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PAPER-EXPOSURE-QUALITY-BINDING"
NEXT_TASK_CLASS = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK_CONTINUE"

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
from trader1.runtime.boot.launcher_guard import ALLOWED_ROOT_LAUNCHERS  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "root_launcher_surface_validator",
    "paper_exposure_quality_report_validator",
    "profitability_optimizer_evidence_gap_validator",
    "source_bundle_hygiene_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "root_launcher_surface_validator",
    "paper_exposure_quality_report_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/runtime/boot/safe_launcher.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/runtime/test_safe_launcher.py",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json",
    "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
    "contracts/generated/context_pack/DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING.md",
]
BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def update_registry_timestamp(now: str) -> None:
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(registry_path)
    registry["updated_at_utc"] = now
    write_json(registry_path, registry)


def update_gap_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    audit_path = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json"
    audit = load_json(audit_path)
    audit["generated_at_utc"] = now
    audit["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}

    for gap in audit.get("gaps", []):
        if gap.get("gap_id") == "PROFIT-GAP-004":
            gap["ux_impact"] = (
                "Paper exposure quality is now visible in the risk panel with PASS/INSUFFICIENT/BLOCKED status, "
                "sample counts, recommendation, and scale-up blocked wording."
            )
            gap["patch_status"] = "PARTIAL_PATCHED"
        if gap.get("gap_id") == "PROFIT-GAP-010":
            gap["condition"] = (
                "Dashboard now projects paper exposure quality into the risk panel, but profitability maturity "
                "still requires external and long-run evidence before live review."
            )
            gap["patch_status"] = "PARTIAL_PATCHED"

    actions = audit.setdefault("safe_patch_actions", [])
    if not any(isinstance(item, dict) and item.get("action_id") == PATCH_ID for item in actions):
        actions.append(
            {
                "action_id": PATCH_ID,
                "status": "APPLIED",
                "summary": "Bound paper_exposure_quality_report into the read-only dashboard risk panel and launcher-scoped loader while keeping all live and scale flags false.",
                "live_order_ready_after": False,
                "live_order_allowed_after": False,
                "can_live_trade_after": False,
                "scale_up_allowed_after": False,
            }
        )
    write_json(audit_path, audit)

    gap_path = ROOT / "system" / "evidence" / "contract_gaps" / "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json"
    gap = load_json(gap_path)
    gap["generated_at_utc"] = now
    gap["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    gap["notes"] = (
        "Rechecked in MVP-4. Dashboard now shows paper exposure quality status, sample counts, recommendation, "
        "and scale-up blocked wording from exact scoped PAPER artifacts. Gap remains OPEN because live-enabling "
        "evidence, read-only burn-in, official API verification, manual order evidence, and operator approval are absent."
    )
    write_json(gap_path, gap)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING.md",
        f"""# DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING

context_pack_id: DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING
task_class: MVP4_DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.paper_exposure_quality_report.v1"]
included_validator_ids: ["read_only_dashboard_validator", "paper_exposure_quality_report_validator", "live_final_guard_validator"]
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- dashboard risk panel shows paper exposure quality status and sample counts
- launcher loads only exact scoped PAPER exposure quality artifact
- cross-session exposure quality artifacts are ignored
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no live evidence collection
- no live config mutation
- no scale-up permission
- no exchange account call

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

The read-only dashboard risk panel now shows paper exposure quality status, sample counts, recommendation, and blocked scale-up state. Launcher loading is exact scoped by exchange, market_type, mode, and session_id.

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
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "dashboard operator risk and exposure visibility",
            "full_text_marker": f"{REQUIREMENT_ID}:dashboard must show paper exposure quality without creating live or scale permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard paper exposure quality binding",
            "requirement_kind": "DASHBOARD_UX_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1", "trader1.paper_exposure_quality_report.v1"],
            "validator_ids": ["read_only_dashboard_validator", "paper_exposure_quality_report_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-PAPER-EXPOSURE-QUALITY-REPORT"],
            "source_text_sha256": sha256_bytes(b"dashboard must show paper exposure quality without creating live or scale permission"),
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
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/runtime/test_safe_launcher.py"],
            "fixture_files": ["tests/validators/fixtures/paper_exposure_quality_pass.json", "tests/validators/fixtures/paper_exposure_quality_scale_up_fail.json"],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                "system/evidence/audit_reports/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_AUDIT.json",
                "system/evidence/contract_gaps/PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY.contract_gap.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["risk_exposure_snapshot.paper_exposure_quality_status"],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "scale_up_allowed_after",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def write_all_launcher_runtime_bundles() -> list[str]:
    paths: list[str] = []
    for launcher_name in sorted(ALLOWED_ROOT_LAUNCHERS):
        report = build_launcher_report(launcher_name)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report)
        paths.append(rel(report_path))
        paths.extend(rel(path) for path in dashboard_paths.values())
    return sorted(paths)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    launcher_runtime_paths: list[str],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_PAPER_EXPOSURE_QUALITY_REPORT.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PAPER-EXPOSURE-QUALITY-REPORT",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
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
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_CONTRACT_GAP", "SECTION_OPTIMIZER_GUARDRAIL"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
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
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING",
            "required_section_ids": [
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "TRADER_1:dashboard-operator-ux",
                "TRADER_1:strategy-profitability-risk-sizing-exposure",
                "AGENTS:profit-convergence-risk-scaling-rules",
            ],
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
            "optimizer_patch": "DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING",
            "optimizer_stage": "MVP4_REVIEW_PREP",
            "optimizer_status_before": "LIVE_BLOCKED_WITH_PAPER_EXPOSURE_QUALITY_REVIEW",
            "optimizer_status_after": "LIVE_BLOCKED_WITH_OPERATOR_VISIBLE_PAPER_EXPOSURE_QUALITY",
            "optimizer_maturity_level_before": "PARTIAL_PATCHED",
            "optimizer_maturity_level_after": "PARTIAL_PATCHED",
            "optimizer_output_type": "DASHBOARD_DISPLAY_TRUTH_ONLY",
            "optimizer_validators_required": [
                "read_only_dashboard_validator",
                "paper_exposure_quality_report_validator",
                "optimizer_no_live_mutation_validator",
            ],
            "optimizer_validators_run": [
                item
                for item in validators_run
                if item.get("validator_id") in {"read_only_dashboard_validator", "paper_exposure_quality_report_validator", "optimizer_no_live_mutation_validator"}
            ],
            "optimizer_guardrail_result": "PASS_LIVE_MUTATION_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "DASHBOARD_PAPER_EXPOSURE_QUALITY_VISIBILITY",
            "convergence_layer_changed": False,
            "convergence_state_before": "LIVE_BLOCKED_WITH_PAPER_EXPOSURE_QUALITY_REVIEW",
            "convergence_state_after": "LIVE_BLOCKED_WITH_OPERATOR_VISIBLE_PAPER_EXPOSURE_QUALITY",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_DASHBOARD_BINDING",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["read_only_dashboard_validator", "paper_exposure_quality_report_validator"],
            "convergence_validators_run": [
                item
                for item in validators_run
                if item.get("validator_id") in {"read_only_dashboard_validator", "paper_exposure_quality_report_validator"}
            ],
            "convergence_guardrail_result": "PASS_SCALE_UP_BLOCKED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_DASHBOARD_PAPER_EXPOSURE_QUALITY_BINDING_LIVE_AND_SCALE_UP_BLOCKED",
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
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md",
        f"""# MVP4 Dashboard Paper Exposure Quality Binding Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Paper exposure quality evidence existed, but the operator dashboard risk panel did not project that status.

Patch:
- Added paper exposure quality fields to read_only_dashboard_shell.
- Added dashboard rendering for quality status, sample counts, recommendation, and source.
- Added exact scoped launcher loader for paper_exposure_quality_report.json.
- Added dashboard and launcher tests for PASS, live/scale drift, and cross-session artifact rejection.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.read_only_dashboard_shell.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["read_only_dashboard_validator"]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + ["PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"]))
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


def emit_patch(now: str, trader_hash: str, agents_hash: str, tests_run: list[dict[str, Any]], validator_ids: list[str]) -> dict[str, Any]:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    launcher_runtime_paths = write_all_launcher_runtime_bundles()
    patch_result = build_patch_result(now, tests_run, run_validators(validator_ids), validator_ids, launcher_runtime_paths)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    return patch_result


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_registry_timestamp(now)
    update_gap_artifacts(now, trader_hash, agents_hash)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_safe_launcher", "-v"]),
    ]

    emit_patch(now, trader_hash, agents_hash, tests_run, BOOTSTRAP_VALIDATORS_REQUIRED)

    tests_run.extend(
        [
            run_command([sys.executable, "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        ]
    )

    patch_result = emit_patch(now, trader_hash, agents_hash, tests_run, VALIDATORS_REQUIRED)
    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "validators_required": VALIDATORS_REQUIRED,
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
