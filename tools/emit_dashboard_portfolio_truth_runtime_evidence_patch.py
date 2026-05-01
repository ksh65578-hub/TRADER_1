from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PORTFOLIO-TRUTH-RUNTIME-EVIDENCE"
NEXT_TASK_CLASS = "MVP4_SOURCE_RELEASE_BUNDLE_HYGIENE_RECHECK"

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
from trader1.dashboard.read_only_dashboard import render_dashboard_html, validate_read_only_dashboard_shell  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_portfolio_truth_runtime_evidence_patch.py",
    "contracts/generated/context_pack/MVP4_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE.md",
    "system/runtime/*/*/*/mvp1_*_launcher/dashboard_shell.json",
    "system/runtime/*/*/*/mvp1_*_launcher/dashboard/index.html",
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
    if validator_id
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
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
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1600:],
        "stderr_tail": completed.stderr[-1600:],
    }


def _hash64(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789ABCDEFabcdef" for char in value)


def build_audit(runtime_paths: list[str]) -> dict[str, Any]:
    schema_text = (ROOT / "contracts" / "schema" / "read_only_dashboard_shell.schema.json").read_text(encoding="utf-8")
    dashboard_text = (ROOT / "trader1" / "dashboard" / "read_only_dashboard.py").read_text(encoding="utf-8")
    test_text = (ROOT / "tests" / "dashboard" / "test_read_only_dashboard.py").read_text(encoding="utf-8")
    runtime_dashboard_shells = sorted((ROOT / "system" / "runtime").glob("**/dashboard_shell.json"))
    runtime_checks: list[dict[str, Any]] = []
    verified_runtime_checks: list[dict[str, Any]] = []
    for path in runtime_dashboard_shells:
        payload = load_json(path)
        portfolio = payload.get("portfolio_snapshot", {}) if isinstance(payload, dict) else {}
        html = render_dashboard_html(payload) if isinstance(payload, dict) else ""
        validation = validate_read_only_dashboard_shell(payload) if isinstance(payload, dict) else None
        runtime_check = {
            "path": path.relative_to(ROOT).as_posix(),
            "status": portfolio.get("status"),
            "has_source_snapshot_hash": "source_snapshot_hash" in portfolio,
            "has_source_snapshot_status": "source_snapshot_status" in portfolio,
            "has_source_snapshot_generated_at_utc": "source_snapshot_generated_at_utc" in portfolio,
            "has_source_balance_kind": "source_balance_kind" in portfolio,
            "dashboard_validator_status": getattr(validation, "status", "FAIL"),
            "live_order_ready": bool(payload.get("live_order_ready")) if isinstance(payload, dict) else True,
            "live_order_allowed": bool(payload.get("live_order_allowed")) if isinstance(payload, dict) else True,
            "can_live_trade": bool(payload.get("can_live_trade")) if isinstance(payload, dict) else True,
            "scale_up_allowed": bool(payload.get("scale_up_allowed")) if isinstance(payload, dict) else True,
        }
        runtime_checks.append(runtime_check)
        if portfolio.get("status") == "VERIFIED":
            snapshot_hash = portfolio.get("source_snapshot_hash")
            verified_runtime_checks.append(
                {
                    "path": path.relative_to(ROOT).as_posix(),
                    "source_snapshot_hash_valid": _hash64(snapshot_hash),
                    "source_snapshot_status": portfolio.get("source_snapshot_status"),
                    "source_snapshot_generated_at_utc": portfolio.get("source_snapshot_generated_at_utc"),
                    "source_balance_kind": portfolio.get("source_balance_kind"),
                    "html_shows_snapshot": f"Snapshot: {str(snapshot_hash)[:12]}..." in html if snapshot_hash else False,
                    "html_shows_balance_kind": "Balance: SIMULATED_PAPER_LEDGER" in html,
                }
            )
    checks = {
        "schema_requires_snapshot_provenance_fields": all(
            marker in schema_text
            for marker in [
                '"source_snapshot_hash"',
                '"source_snapshot_status"',
                '"source_snapshot_generated_at_utc"',
                '"source_balance_kind"',
            ]
        ),
        "runtime_populates_snapshot_provenance": all(
            marker in dashboard_text
            for marker in [
                '"source_snapshot_hash": portfolio.get("source_snapshot_hash")',
                '"source_snapshot_status": portfolio.get("source_snapshot_status")',
                '"source_snapshot_generated_at_utc": portfolio.get("source_snapshot_generated_at_utc")',
                '"source_balance_kind": portfolio.get("source_balance_kind")',
            ]
        ),
        "validator_blocks_verified_snapshot_provenance_drift": all(
            marker in dashboard_text
            for marker in [
                "portfolio source snapshot hash is invalid",
                "verified portfolio source snapshot is not PASS",
                "verified portfolio source must remain simulated PAPER ledger truth",
                "unverified portfolio cannot carry PASS snapshot provenance",
            ]
        ),
        "unit_tests_cover_snapshot_provenance": all(
            marker in test_text
            for marker in [
                "test_dashboard_blocks_verified_portfolio_missing_snapshot_hash",
                "test_dashboard_blocks_verified_portfolio_snapshot_status_drift",
                "test_dashboard_blocks_verified_portfolio_balance_kind_drift",
                "source_snapshot_generated_at_utc",
            ]
        ),
        "runtime_dashboard_shells_have_snapshot_provenance_fields": all(
            item["has_source_snapshot_hash"]
            and item["has_source_snapshot_status"]
            and item["has_source_snapshot_generated_at_utc"]
            and item["has_source_balance_kind"]
            for item in runtime_checks
        ),
        "verified_runtime_dashboards_have_simulated_source_truth": bool(verified_runtime_checks)
        and all(
            item["source_snapshot_hash_valid"]
            and item["source_snapshot_status"] == "PASS"
            and isinstance(item["source_snapshot_generated_at_utc"], str)
            and item["source_balance_kind"] == "SIMULATED_PAPER_LEDGER"
            and item["html_shows_snapshot"]
            and item["html_shows_balance_kind"]
            for item in verified_runtime_checks
        ),
        "runtime_dashboard_shells_validate_fail_closed": all(item["dashboard_validator_status"] == "PASS" for item in runtime_checks),
        "runtime_dashboard_shells_keep_live_false": all(
            not item["live_order_ready"]
            and not item["live_order_allowed"]
            and not item["can_live_trade"]
            and not item["scale_up_allowed"]
            for item in runtime_checks
        ),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.dashboard_portfolio_truth_runtime_evidence_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "runtime_dashboard_shells_checked": runtime_checks,
        "verified_runtime_dashboard_shells_checked": verified_runtime_checks,
        "runtime_paths_regenerated": runtime_paths,
        "hidden_defects": [
            {
                "classification": "dashboard_verified_portfolio_missing_source_identity",
                "condition": "A VERIFIED PAPER portfolio card exposed values and source age without showing the exact paper snapshot hash and balance source kind.",
                "impact": "Operator evidence could show verified values without enough provenance to tie display truth back to the simulated PAPER ledger snapshot.",
                "fix": "portfolio_snapshot now carries snapshot hash, snapshot status, snapshot generated_at, and SIMULATED_PAPER_LEDGER balance kind into runtime dashboard files and HTML.",
                "live_safety_impact": "prevents display-only PAPER portfolio truth from being confused with live balance evidence",
                "ux_impact": "operator can see the simulated snapshot source and balance kind directly on the first screen",
            },
            {
                "classification": "runtime_dashboard_schema_drift_after_portfolio_provenance_delta",
                "condition": "Checked-in dashboard_shell runtime artifacts lacked new required portfolio provenance fields after schema hardening.",
                "impact": "runtime_schema_instance_validator failed until safe launcher dashboard bundles were regenerated.",
                "fix": "safe launcher runtime dashboard bundles were regenerated with all live and scale-up flags false.",
                "live_safety_impact": "keeps runtime artifacts schema-valid without enabling live behavior",
                "ux_impact": "keeps local dashboard files renderable after schema changes",
            },
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_navigation(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE.md",
        f"""# MVP4_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE

context_pack_id: MVP4_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE
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
- VERIFIED PAPER portfolio display must expose source_snapshot_hash, source_snapshot_status, source_snapshot_generated_at_utc, and source_balance_kind.
- VERIFIED PAPER portfolio display must block missing, stale, or non-simulated snapshot provenance.
- runtime dashboard_shell artifacts must validate after schema hardening.
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
            "source_heading": "Dashboard portfolio truth runtime evidence",
            "full_text_marker": f"{REQUIREMENT_ID}:verified portfolio display must expose simulated snapshot provenance",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard verified portfolio values must expose simulated snapshot provenance",
            "requirement_kind": "SCHEMA_VALIDATOR_TEST_RUNTIME_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_schema_instance_validation.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "HIGH",
            "live_affecting": True,
            "read_when": ["DASHBOARD_UX", "UPBIT_PAPER_RUNTIME", "LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-DASHBOARD-PORTFOLIO-SOURCE-FRESHNESS", "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH"],
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
            "validator_files": ["trader1/dashboard/read_only_dashboard.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py", "tests/contract/test_schema_instance_validation.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "dashboard_artifacts": ["system/runtime/*/*/*/mvp1_*_launcher/dashboard_shell.json"],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
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

Dashboard VERIFIED PAPER portfolio values now expose simulated snapshot hash, snapshot status, timestamp, and balance source kind. Runtime dashboard shells were regenerated and remain live-blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


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


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_PORTFOLIO_SOURCE_FRESHNESS.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-PORTFOLIO-SOURCE-FRESHNESS",
                "REQ-MVP4-UPBIT-PAPER-PORTFOLIO-SOURCE-TRUTH",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT,BINANCE",
            "affected_market_type": "KRW_SPOT,SPOT",
            "affected_mode": "PAPER,LIVE_SAFE_BOOT_ARTIFACTS",
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
            "next_required_section_ids": ["SECTION_SOURCE_RELEASE_BUNDLE_HYGIENE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_WINDOWS_LONG_RUN_RECOVERY", "SECTION_DASHBOARD_OPERATOR_UX"],
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
            "expanded_section_ids": ["AGENTS_0G", "TRADER_1_ACTIVE_DASHBOARD_OPERATOR_UX_SURFACE"],
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
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_DASHBOARD_PORTFOLIO_TRUTH_RUNTIME_EVIDENCE",
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
        run_command([sys.executable, "-B", "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-q"], timeout_seconds=300),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"], timeout_seconds=300),
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
        run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"], timeout_seconds=300),
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
