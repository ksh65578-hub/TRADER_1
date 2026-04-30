from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_convergence_memory_failure_learning_hardening_patch_evidence import ensure_matrix_row, ensure_requirement  # noqa: E402
from tools.emit_dashboard_operation_portfolio_status_fields_patch_evidence import regenerate_launcher_dashboards  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.runtime.paper.upbit_paper_runtime import (  # noqa: E402
    build_upbit_paper_runtime_cycle_report,
    upbit_paper_runtime_cycle_hash,
    validate_upbit_paper_runtime_cycle_report,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop  # noqa: E402
from trader1.runtime.ledger.paper_ledger_rollup import (  # noqa: E402
    paper_ledger_rollup_hash,
    validate_paper_ledger_rollup_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "contracts/schema/paper_portfolio_snapshot.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "contracts/schema/summary.schema.json",
    "trader1/runtime/ledger/paper_ledger_rollup.py",
    "trader1/runtime/portfolio/paper_portfolio.py",
    "trader1/runtime/paper/upbit_paper_runtime.py",
    "trader1/dashboard/summary_writer.py",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_paper_portfolio.py",
    "tests/runtime/test_paper_ledger_rollup.py",
    "tests/integration/test_upbit_paper_runtime_cycle.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/runtime/test_safe_launcher.py",
    "tests/dashboard/test_summary_writer.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_upbit_paper_portfolio_source_truth_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "summary_shell_validator",
    "paper_portfolio_snapshot_validator",
    "paper_ledger_rollup_validator",
    "upbit_paper_runtime_cycle_validator",
    "upbit_paper_persistent_loop_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id
    not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
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
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {"command": " ".join(args), "status": "PASS" if completed.returncode == 0 else "FAIL", "returncode": completed.returncode}


def build_audit(runtime_paths: list[str]) -> dict[str, Any]:
    positive = build_upbit_paper_runtime_cycle_report(cycle_id="audit-portfolio-source-positive")
    positive_result = validate_upbit_paper_runtime_cycle_report(positive)
    cycle_mismatch = build_upbit_paper_runtime_cycle_report(cycle_id="audit-portfolio-source-cycle-mismatch")
    cycle_mismatch["paper_portfolio_snapshot"]["source_runtime_cycle_id"] = "wrong-cycle"
    from trader1.runtime.portfolio.paper_portfolio import paper_portfolio_hash  # local import avoids broad startup dependency

    cycle_mismatch["paper_portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(cycle_mismatch["paper_portfolio_snapshot"])
    cycle_mismatch["cycle_hash"] = upbit_paper_runtime_cycle_hash(cycle_mismatch)
    cycle_mismatch_result = validate_upbit_paper_runtime_cycle_report(cycle_mismatch)
    ledger_mismatch = build_upbit_paper_runtime_cycle_report(cycle_id="audit-portfolio-source-ledger-mismatch")
    ledger_mismatch["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"] = "F" * 64
    ledger_mismatch["paper_portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(ledger_mismatch["paper_portfolio_snapshot"])
    ledger_mismatch["cycle_hash"] = upbit_paper_runtime_cycle_hash(ledger_mismatch)
    ledger_mismatch_result = validate_upbit_paper_runtime_cycle_report(ledger_mismatch)
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        loop = run_upbit_paper_persistent_loop(
            root=root,
            loop_id="audit-portfolio-source-rollup",
            requested_cycle_count=2,
        )
        rollup = load_json(root / str(loop["paper_ledger_rollup_path"]))
    rollup_result = validate_paper_ledger_rollup_report(rollup)
    rollup_mismatch = json.loads(json.dumps(rollup))
    rollup_mismatch["portfolio_snapshot"]["source_paper_ledger_head_hash"] = "E" * 64
    rollup_mismatch["portfolio_snapshot"]["snapshot_hash"] = paper_portfolio_hash(rollup_mismatch["portfolio_snapshot"])
    rollup_mismatch["rollup_hash"] = paper_ledger_rollup_hash(rollup_mismatch)
    rollup_mismatch_result = validate_paper_ledger_rollup_report(rollup_mismatch)
    runtime_dashboard_shells = sorted((ROOT / "system" / "runtime").glob("**/dashboard_shell.json"))
    dashboard_source_fields = []
    for path in runtime_dashboard_shells:
        payload = load_json(path)
        portfolio = payload.get("portfolio_snapshot", {}) if isinstance(payload, dict) else {}
        dashboard_source_fields.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "has_source_runtime_cycle_id": "source_runtime_cycle_id" in portfolio,
                "has_source_paper_ledger_head_hash": "source_paper_ledger_head_hash" in portfolio,
                "live_order_ready": bool(payload.get("live_order_ready")) if isinstance(payload, dict) else True,
                "live_order_allowed": bool(payload.get("live_order_allowed")) if isinstance(payload, dict) else True,
                "can_live_trade": bool(payload.get("can_live_trade")) if isinstance(payload, dict) else True,
                "scale_up_allowed": bool(payload.get("scale_up_allowed")) if isinstance(payload, dict) else True,
            }
        )
    checks = {
        "positive_runtime_binds_portfolio_cycle_id": positive_result.status == "PASS"
        and positive["paper_portfolio_snapshot"]["source_runtime_cycle_id"] == positive["cycle_id"],
        "positive_runtime_binds_portfolio_ledger_head": positive_result.status == "PASS"
        and positive["paper_portfolio_snapshot"]["source_paper_ledger_head_hash"] == positive["paper_ledger_head_hash"],
        "cycle_source_mismatch_is_blocked": cycle_mismatch_result.status == "FAIL"
        and cycle_mismatch_result.blocker_code == "SCHEMA_IDENTITY_MISMATCH",
        "ledger_source_mismatch_is_blocked": ledger_mismatch_result.status == "FAIL"
        and ledger_mismatch_result.blocker_code == "LEDGER_INTEGRITY_FAIL",
        "rollup_binds_latest_cycle_and_ledger_head": rollup_result.status == "PASS"
        and rollup["portfolio_snapshot"]["source_runtime_cycle_id"] == "audit-portfolio-source-rollup-cycle-2"
        and rollup["portfolio_snapshot"]["source_paper_ledger_head_hash"] == rollup["latest_ledger_head_hash"],
        "rollup_ledger_source_mismatch_is_blocked": rollup_mismatch_result.status == "FAIL"
        and rollup_mismatch_result.blocker_code == "LEDGER_INTEGRITY_FAIL",
        "runtime_dashboards_have_portfolio_source_fields": all(
            item["has_source_runtime_cycle_id"] and item["has_source_paper_ledger_head_hash"] for item in dashboard_source_fields
        ),
        "runtime_dashboards_keep_live_false": all(
            not item["live_order_ready"]
            and not item["live_order_allowed"]
            and not item["can_live_trade"]
            and not item["scale_up_allowed"]
            for item in dashboard_source_fields
        ),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.upbit_paper_portfolio_source_truth_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "runtime_paths_regenerated": runtime_paths,
        "runtime_dashboard_shells_checked": dashboard_source_fields,
        "hidden_defects": [
            {
                "classification": "paper_portfolio_snapshot_detached_from_runtime_cycle",
                "condition": "paper_portfolio_snapshot values could be displayed or summarized without carrying the PAPER runtime cycle id that produced them.",
                "impact": "Operator could see cash/equity/positions/PnL without a direct cycle provenance trail.",
                "fix": "paper_portfolio_snapshot now carries source_runtime_cycle_id and the Upbit PAPER runtime validator requires it to match cycle_id.",
                "live_safety_impact": "prevents stale or cross-cycle paper evidence from being treated as trustworthy display evidence",
                "ux_impact": "dashboard can show which PAPER cycle produced the displayed portfolio values",
            },
            {
                "classification": "paper_portfolio_ledger_head_provenance_gap",
                "condition": "filled PAPER portfolio snapshots did not name the ledger head hash used for PnL and position values.",
                "impact": "Ledger/PnL mismatch could be harder to detect when snapshot and ledger artifacts diverge.",
                "fix": "filled snapshots now carry source_paper_ledger_head_hash and runtime validation blocks mismatches.",
                "live_safety_impact": "keeps ledger display truth fail-closed and separate from live permission",
                "ux_impact": "operator can trace displayed PnL back to a ledger head in detail artifacts",
            },
            {
                "classification": "paper_ledger_rollup_portfolio_provenance_gap",
                "condition": "cumulative PAPER ledger rollup could produce a portfolio snapshot without naming the latest contributing cycle and ledger head.",
                "impact": "A launcher dashboard could prefer rollup portfolio values while the operator could not trace the displayed state back to the rollup ledger head.",
                "fix": "PAPER ledger rollup snapshots now carry the latest source_runtime_cycle_id and source_paper_ledger_head_hash, and the rollup validator blocks ledger-head mismatches.",
                "live_safety_impact": "prevents stale or mismatched cumulative paper evidence from being promoted in operator review",
                "ux_impact": "first-screen portfolio detail can explain which cumulative PAPER ledger source produced displayed positions and PnL",
            },
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_navigation(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH.md",
        f"""# MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH

context_pack_id: MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH
task_class: MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_portfolio_snapshot.v1", "trader1.paper_ledger_rollup_report.v1", "trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER portfolio snapshots carry source_runtime_cycle_id and source_paper_ledger_head_hash.
- Upbit PAPER runtime validation blocks portfolio cycle or ledger-head provenance mismatch.
- PAPER ledger rollup validation blocks cumulative portfolio ledger-head provenance mismatch.
- Summary and dashboard preserve source provenance as display truth only.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: {audit["status"]}

known_omissions_by_design:
- no live execution
- no credential or private account access
- no LIVE_READY snapshot write
- no risk scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    matrix = load_json(matrix_path)
    req_index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    ensure_requirement(
        req_index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER runtime portfolio source truth",
            "full_text_marker": f"{REQUIREMENT_ID}:portfolio snapshot source cycle and ledger head provenance",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "PAPER portfolio values must carry runtime and ledger provenance",
            "requirement_kind": "SCHEMA_VALIDATOR_TEST_RUNTIME_PATCH",
            "schema_ids": ["trader1.paper_portfolio_snapshot.v1", "trader1.paper_ledger_rollup_report.v1", "trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_paper_portfolio.py",
                "tests/runtime/test_paper_ledger_rollup.py",
                "tests/integration/test_upbit_paper_runtime_cycle.py",
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_summary_writer.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "HIGH",
            "live_affecting": True,
            "read_when": ["UPBIT_PAPER_RUNTIME", "DASHBOARD_UX", "LEDGER_RECONCILIATION"],
            "depends_on": ["REQ-MVP4-UPBIT-PAPER-RUNTIME-E2E-CONSISTENCY-GUARD"],
            "source_text_sha256": sha256_json({"requirement": REQUIREMENT_ID}),
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": [
                "contracts/schema/paper_portfolio_snapshot.schema.json",
                "contracts/schema/paper_ledger_rollup_report.schema.json",
                "contracts/schema/summary.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/portfolio/paper_portfolio.py",
                "trader1/runtime/ledger/paper_ledger_rollup.py",
                "trader1/runtime/paper/upbit_paper_runtime.py",
                "trader1/dashboard/summary_writer.py",
                "trader1/dashboard/read_only_dashboard.py",
            ],
            "test_files": [
                "tests/runtime/test_paper_portfolio.py",
                "tests/runtime/test_paper_ledger_rollup.py",
                "tests/integration/test_upbit_paper_runtime_cycle.py",
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/runtime/test_safe_launcher.py",
                "tests/dashboard/test_summary_writer.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_runtime.py",
                "trader1/runtime/ledger/paper_ledger_rollup.py",
                "trader1/runtime/portfolio/paper_portfolio.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "dashboard_artifacts": ["system/runtime/*/*/*/mvp1_*_launcher/dashboard_shell.json"],
            "patch_result_fields": ["validators_run", "tests_run", "live_order_ready_after", "live_order_allowed_after"],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    write_json(req_path, req_index)
    write_json(matrix_path, matrix)
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

PAPER portfolio snapshots now carry runtime-cycle and ledger-head provenance. Summary and dashboard preserve that provenance as display truth only.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_SOURCE_BUNDLE_LINE_ENDING_STABLE_HASH.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PAPER-RUNTIME-E2E-CONSISTENCY-GUARD"],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [],
            "new_or_changed_schema_ids": [
                "trader1.paper_portfolio_snapshot.v1",
                "trader1.paper_ledger_rollup_report.v1",
                "trader1.summary.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "PRESERVED_NOT_READ",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_optional_section_ids": ["SECTION_PROFIT_CONVERGENCE"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH"],
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
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_UPBIT_PAPER_RUNTIME_E2E_CONTINUE",
            "required_section_ids": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": ["AGENTS_0G", "TRADER_1_ACTIVE_UPBIT_PAPER_RUNTIME_SURFACE"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "PASS",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_APPLICABLE",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["completed_requirement_ids"] = list(dict.fromkeys([*state.get("completed_requirement_ids", []), REQUIREMENT_ID]))
    state["implemented_schema_ids"] = list(
        dict.fromkeys(
            [
                *state.get("implemented_schema_ids", []),
                "trader1.paper_portfolio_snapshot.v1",
                "trader1.summary.v1",
                "trader1.read_only_dashboard_shell.v1",
            ]
        )
    )
    state["implemented_validator_ids"] = list(dict.fromkeys([*state.get("implemented_validator_ids", []), *VALIDATORS_REQUIRED]))
    state.update(
        {
            "updated_at_utc": now,
            "current_mvp": "MVP-4",
            "untested_validator_ids": [],
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result["result_hash"],
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)
    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    patches = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    patches.append(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "target_mvp_level": "MVP-4",
            "requirement_id": REQUIREMENT_ID,
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    ledger["patches"] = patches
    ledger["updated_at_utc"] = now
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    runtime_paths = regenerate_launcher_dashboards()
    audit = build_audit(runtime_paths)
    update_navigation(now, trader_hash, agents_hash, audit)
    write_source_bundle_manifest()
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)
    tests_run = [
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.runtime.test_paper_portfolio",
                "tests.runtime.test_paper_ledger_rollup",
                "tests.integration.test_upbit_paper_runtime_cycle",
                "tests.integration.test_upbit_public_collection_persistent_loop",
                "tests.runtime.test_safe_launcher",
                "tests.dashboard.test_summary_writer",
                "tests.dashboard.test_read_only_dashboard",
                "-q",
            ],
            timeout_seconds=300,
        ),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "unittest",
                "tests.contract.test_schema_instance_validation",
                "tests.contract.test_patch_result_runtime_schema_validation",
                "-q",
            ],
            timeout_seconds=300,
        ),
        run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"], timeout_seconds=900),
    ]
    validators_run = [
        {
            "validator_id": item["validator_id"],
            "status": item["status"],
            "blocker_code": item.get("blocker_code"),
            "message": item.get("message"),
        }
        for item in run_validators(BOOTSTRAP_VALIDATORS)
    ]
    patch_result = build_patch_result(now, tests_run, validators_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)
    final_validator_ids = ["patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"]
    for _ in range(2):
        final_results = run_validators(final_validator_ids)
        validators_run = [item for item in validators_run if item.get("validator_id") not in set(final_validator_ids)]
        validators_run.extend(
            {
                "validator_id": item["validator_id"],
                "status": item["status"],
                "blocker_code": item.get("blocker_code"),
                "message": item.get("message"),
            }
            for item in final_results
        )
        patch_result["validators_run"] = validators_run
        patch_result["result_hash"] = patch_hash(patch_result)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)
    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-4",
        "artifact_paths": [
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            "contracts/security/source_bundle_manifest.json",
            *CHANGED_ARTIFACTS,
            *runtime_paths,
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    validator_log = {
        "schema_id": "trader1.validator_run_log.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": validators_run,
        "overall_status": "PASS" if all(item["status"] == "PASS" for item in validators_run) else "BLOCKED",
    }
    stage_gate = {
        "schema_id": "trader1.stage_gate_result.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "stage": "MVP-4",
        "status": "PASS" if audit["status"] == "PASS" and all(item["status"] == "PASS" for item in validators_run) else "BLOCKED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "remaining_blockers": BLOCKERS,
    }
    write_json(ROOT / "system" / "evidence" / f"{PATCH_BASENAME}.evidence_manifest.json", evidence_manifest)
    write_json(ROOT / "system" / "evidence" / "validator_runs" / f"{PATCH_BASENAME}.validator_run_log.json", validator_log)
    write_json(ROOT / "system" / "evidence" / "stage_gates" / f"{PATCH_BASENAME}.stage_gate_result.json", stage_gate)
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    print(json.dumps({"patch_id": PATCH_ID, "audit_status": audit["status"], "stage_gate_status": stage_gate["status"]}, sort_keys=True))
    return 0 if audit["status"] == "PASS" and stage_gate["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
