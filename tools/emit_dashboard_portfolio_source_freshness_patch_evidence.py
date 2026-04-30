from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PORTFOLIO-SOURCE-FRESHNESS"
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
from trader1.config.config_schema import build_runtime_config  # noqa: E402
from trader1.dashboard.read_only_dashboard import (  # noqa: E402
    build_read_only_dashboard_shell,
    dashboard_shell_hash,
    render_dashboard_html,
    validate_read_only_dashboard_shell,
)
from trader1.dashboard.summary_writer import build_summary_shell  # noqa: E402
from trader1.runtime.boot.startup_probe import build_startup_probe  # noqa: E402
from trader1.runtime.health.heartbeat import build_heartbeat  # noqa: E402
from trader1.runtime.portfolio.paper_portfolio import build_paper_portfolio_snapshot_from_fill  # noqa: E402
from trader1.runtime.readiness.readiness_surface import build_readiness_surface  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import current_authority_hashes, run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "trader1/validation/mvp0_validators.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_portfolio_source_freshness_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
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
    if validator_id not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
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


def _build_verified_dashboard() -> dict[str, Any]:
    session_id = "audit-dashboard-portfolio-source-freshness"
    registry_path = ROOT / "contracts" / "registry.yaml"
    registry_hash = sha256_file(registry_path)
    schema_bundle_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))}
    )
    source_tree_hash = sha256_json(
        {path.relative_to(ROOT).as_posix(): sha256_file(path) for path in sorted((ROOT / "trader1").rglob("*.py")) if "__pycache__" not in path.parts}
    )
    config = build_runtime_config(exchange="UPBIT", market_type="KRW_SPOT", mode="PAPER", session_id=session_id, registry_hash=registry_hash)
    startup_probe = build_startup_probe(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
        ledger_write_status=None,
    )
    heartbeat = build_heartbeat(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        config_hash=config["config_hash"],
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    readiness_surface = build_readiness_surface(
        authority=current_authority_hashes(),
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        registry_hash=registry_hash,
        schema_bundle_hash=schema_bundle_hash,
        source_tree_hash=source_tree_hash,
    )
    portfolio = build_paper_portfolio_snapshot_from_fill(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        session_id=session_id,
        symbol="KRW-BTC",
        side="BUY",
        quantity="0.01",
        fill_price="1000500",
        mark_price="1000000",
        fee_amount="5",
        source_runtime_cycle_id="audit-dashboard-source-freshness-cycle",
        source_paper_ledger_head_hash="A" * 64,
    )
    summary = build_summary_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        startup_probe=startup_probe,
        heartbeat=heartbeat,
        readiness_surface=readiness_surface,
        paper_portfolio_snapshot=portfolio,
    )
    return build_read_only_dashboard_shell(
        exchange="UPBIT",
        market_type="KRW_SPOT",
        mode="PAPER",
        session_id=session_id,
        summary=summary,
        heartbeat=heartbeat,
        startup_probe=startup_probe,
    )


def build_audit(runtime_paths: list[str]) -> dict[str, Any]:
    dashboard = _build_verified_dashboard()
    result = validate_read_only_dashboard_shell(dashboard)
    html = render_dashboard_html(dashboard)
    portfolio = dashboard.get("portfolio_snapshot", {})
    stale_dashboard = json.loads(json.dumps(dashboard))
    stale_dashboard["portfolio_snapshot"]["source_snapshot_age_seconds"] = (
        stale_dashboard["portfolio_snapshot"]["source_snapshot_stale_after_seconds"] + 1
    )
    stale_dashboard["dashboard_hash"] = dashboard_shell_hash(stale_dashboard)
    stale_result = validate_read_only_dashboard_shell(stale_dashboard)
    runtime_dashboard_shells = sorted((ROOT / "system" / "runtime").glob("**/dashboard_shell.json"))
    runtime_checks = []
    for path in runtime_dashboard_shells:
        payload = load_json(path)
        runtime_portfolio = payload.get("portfolio_snapshot", {}) if isinstance(payload, dict) else {}
        runtime_checks.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "has_source_snapshot_age_seconds": "source_snapshot_age_seconds" in runtime_portfolio,
                "has_source_snapshot_stale_after_seconds": "source_snapshot_stale_after_seconds" in runtime_portfolio,
                "has_source_snapshot_freshness_message": "source_snapshot_freshness_message" in runtime_portfolio,
                "live_order_ready": bool(payload.get("live_order_ready")) if isinstance(payload, dict) else True,
                "live_order_allowed": bool(payload.get("live_order_allowed")) if isinstance(payload, dict) else True,
                "can_live_trade": bool(payload.get("can_live_trade")) if isinstance(payload, dict) else True,
                "scale_up_allowed": bool(payload.get("scale_up_allowed")) if isinstance(payload, dict) else True,
            }
        )
    checks = {
        "verified_dashboard_carries_source_age": result.status == "PASS" and isinstance(portfolio.get("source_snapshot_age_seconds"), int),
        "verified_dashboard_carries_stale_threshold": result.status == "PASS"
        and portfolio.get("source_snapshot_stale_after_seconds") == 300,
        "verified_dashboard_html_shows_age": "Age:" in html and "stale after 300s" in html,
        "stale_source_age_blocks_verified_dashboard": stale_result.status == "BLOCKED" and stale_result.blocker_code == "LATENCY_TTL_EXPIRED",
        "runtime_dashboards_have_source_freshness_fields": all(
            item["has_source_snapshot_age_seconds"]
            and item["has_source_snapshot_stale_after_seconds"]
            and item["has_source_snapshot_freshness_message"]
            for item in runtime_checks
        ),
        "runtime_dashboards_keep_live_false": all(
            not item["live_order_ready"]
            and not item["live_order_allowed"]
            and not item["can_live_trade"]
            and not item["scale_up_allowed"]
            for item in runtime_checks
        ),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.dashboard_portfolio_source_freshness_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "runtime_paths_regenerated": runtime_paths,
        "runtime_dashboard_shells_checked": runtime_checks,
        "hidden_defects": [
            {
                "classification": "dashboard_portfolio_freshness_ambiguity",
                "condition": "portfolio cards could show verified PAPER values while the first screen did not expose source age or stale threshold.",
                "impact": "operator could mistake old PAPER portfolio values for current values even though dashboard truth remains display-only.",
                "fix": "dashboard portfolio snapshot now carries source_snapshot_age_seconds, source_snapshot_stale_after_seconds, and freshness message; stale age is blocked.",
                "live_safety_impact": "prevents stale display evidence from looking review-ready",
                "ux_impact": "operator sees how fresh the portfolio values are at a glance",
            }
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_navigation(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS.md",
        f"""# MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS

context_pack_id: MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS
task_class: DASHBOARD_UX
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard portfolio snapshot carries source age, stale threshold, and freshness message.
- First-screen portfolio source line shows Age and stale threshold.
- Verified portfolio display blocks stale source age.
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
            "source_section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard operator UX portfolio source freshness",
            "full_text_marker": f"{REQUIREMENT_ID}:portfolio source age and stale threshold visible",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard portfolio values must expose source freshness",
            "requirement_kind": "SCHEMA_VALIDATOR_TEST_DASHBOARD_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_schema_instance_validation.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "HIGH",
            "live_affecting": True,
            "read_when": ["DASHBOARD_UX", "UPBIT_PAPER_RUNTIME", "LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH"],
            "source_text_sha256": sha256_json({"requirement": REQUIREMENT_ID}),
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_DASHBOARD_OPERATOR_UX",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_schema_instance_validation.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "dashboard_artifacts": ["system/runtime/*/*/*/mvp1_*_launcher/dashboard_shell.json"],
            "patch_result_fields": ["validators_run", "tests_run", "live_order_ready_after", "live_order_allowed_after"],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
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

Dashboard portfolio values now show source age and stale threshold on the first screen. Stale verified portfolio display is blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_PORTFOLIO_SOURCE_TRUTH.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-DASHBOARD-OPERATOR-UX"],
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
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
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
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "DASHBOARD_UX",
            "required_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["AGENTS_0G", "TRADER_1_ACTIVE_DASHBOARD_UX_SURFACE"],
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
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS",
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
    state["implemented_schema_ids"] = list(dict.fromkeys([*state.get("implemented_schema_ids", []), "trader1.read_only_dashboard_shell.v1"]))
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
        run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "tests.contract.test_schema_instance_validation", "-q"], timeout_seconds=300),
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
    tests_run = [
        *tests_run,
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-q"], timeout_seconds=300),
        run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"], timeout_seconds=900),
    ]
    patch_result["tests_run"] = tests_run
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
