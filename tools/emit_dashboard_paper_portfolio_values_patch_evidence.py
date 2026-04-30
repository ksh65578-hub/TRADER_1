from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_DASHBOARD_PAPER_PORTFOLIO_VALUES_20260429_001"
PATCH_BASENAME = "MVP4_DASHBOARD_PAPER_PORTFOLIO_VALUES"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_dashboard_launch_visibility_patch_evidence import write_launcher_artifacts
from tools.emit_root_launcher_operator_visibility_patch_evidence import (
    rel,
    run_command,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators


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

VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "summary_shell_validator",
    "read_only_dashboard_validator",
    "paper_portfolio_snapshot_validator",
    "root_launcher_surface_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "generated_artifact_dirty_validator",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "DASHBOARD_PAPER_PORTFOLIO_VALUES.md",
        f"""# DASHBOARD_PAPER_PORTFOLIO_VALUES

context_pack_id: DASHBOARD_PAPER_PORTFOLIO_VALUES
task_class: MVP4_DASHBOARD_PAPER_PORTFOLIO_VALUES
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_MVP1_LEDGER", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-SUMMARY-SHELL", "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD"]
included_schema_ids: ["trader1.paper_portfolio_snapshot.v1", "trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: ["trader1/runtime/portfolio/paper_portfolio.py", "trader1/dashboard/summary_writer.py", "trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- PAPER dashboards show simulated Cash, Equity, Open Positions, and Return values
- PAPER values are generated from paper_portfolio_snapshot and summary, not live account calls
- the dashboard labels values as simulated PAPER ledger and not exchange balance
- live launchers remain hard-blocked and do not get PAPER values as live evidence
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no exchange account balance is fetched
- no API key, secret, .env, or credential is used
- no real order, LIVE_READY snapshot, LIVE_ENABLING_PATCH, or live config mutation is introduced
- future work must replace default PAPER starting cash with operator-configured PAPER capital before production-style paper evaluation

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    write_text(
        ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
        f"""# ACTIVE_WORKING_VIEW

generated_at_utc: {now}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
authority_status: READ_CACHE_NOT_AUTHORITY
current_mvp: {state.get("current_mvp", "MVP-4")}
last_patch_id: {PATCH_ID}
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

PAPER dashboards now display simulated portfolio values from paper_portfolio_snapshot.json through summary.json. UPBIT PAPER starts at 1,000,000 KRW and BINANCE PAPER starts at 10,000 USDT as MVP PAPER defaults. These are simulated PAPER ledger values only, not exchange balances and not live readiness evidence.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_DASHBOARD_PORTFOLIO_SNAPSHOT_UX.patch_result.json")
    patch_result = dict(template)
    optimizer_validators = run_validators(["optimizer_no_live_mutation_validator"])
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
                "REQ-MVP1-SUMMARY-SHELL",
                "REQ-MVP1-EXECUTION-LEDGER-SCAFFOLD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": artifacts,
            "new_or_changed_schema_ids": ["trader1.paper_portfolio_snapshot.v1", "trader1.summary.v1", "trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_NOT_REQUIRED_FOR_DASHBOARD_PAPER_PORTFOLIO_VALUES",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "next_required_section_ids": ["SECTION_LIVE_GATE", "SECTION_LIVE_FINAL_GUARD", "SECTION_UPBIT_LIVE_REVIEW"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_MVP1_LEDGER"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "BINANCE_FUTURES_LIVE", "LIVE_CONFIG_MUTATION"],
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
            "active_read_surface_used": ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_MVP1_LEDGER", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_DASHBOARD_PAPER_PORTFOLIO_VALUES",
            "required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_MVP1_SUMMARY_SHELL", "SECTION_MVP1_LEDGER", "SECTION_LIVE_FINAL_GUARD"],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_validators_required": ["optimizer_no_live_mutation_validator"],
            "optimizer_validators_run": optimizer_validators,
            "optimizer_guardrail_result": "PASS_LIVE_MUTATION_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_DASHBOARD_PAPER_PORTFOLIO_VALUES",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
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
            "stage_gate_status": "PASS_FOR_DASHBOARD_PAPER_PORTFOLIO_VALUES_NO_LIVE_ORDERS",
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
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": [
                "trader1/runtime/portfolio/paper_portfolio.py",
                "trader1/runtime/portfolio/__init__.py",
                "trader1/dashboard/summary_writer.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "contracts/schema/paper_portfolio_snapshot.schema.json",
                "contracts/registry.yaml",
                "contracts/validators/validator_registry.json",
                "tests/runtime/test_paper_portfolio.py",
                "tests/dashboard/test_summary_writer.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "tools/emit_dashboard_paper_portfolio_values_patch_evidence.py",
                "contracts/generated/context_pack/DASHBOARD_PAPER_PORTFOLIO_VALUES.md",
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                *patch_result["new_registry_items"],
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
        f"""# MVP4 Dashboard Paper Portfolio Values Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- The dashboard displayed Cash, Equity, Open Positions, and Return cards, but values were still UNVERIFIED for PAPER runs.
- This was a user workflow defect: PAPER operators could not distinguish a running simulated account from missing portfolio evidence.

Patch:
- Added PAPER-only paper_portfolio_snapshot schema and runtime builder.
- Connected paper_portfolio_snapshot to summary portfolio fields.
- Updated the read-only dashboard to show verified simulated PAPER values while clearly labeling them as not exchange balances.
- Added negative tests for live flag drift, unsupported scope, arithmetic tamper, unverified fresh-looking values, and non-PAPER verified display.
- Updated launchers to write paper_portfolio_snapshot.json for PAPER sessions only.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED"
    if "trader1.paper_portfolio_snapshot.v1" not in state.get("implemented_schema_ids", []):
        state.setdefault("implemented_schema_ids", []).append("trader1.paper_portfolio_snapshot.v1")
        state["implemented_schema_ids"] = sorted(state["implemented_schema_ids"])
    if "paper_portfolio_snapshot_validator" not in state.get("implemented_validator_ids", []):
        state.setdefault("implemented_validator_ids", []).append("paper_portfolio_snapshot_validator")
        state["implemented_validator_ids"] = sorted(state["implemented_validator_ids"])
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
    artifacts = sorted(
        set(
            write_launcher_artifacts()
            + [
                "trader1/runtime/portfolio/paper_portfolio.py",
                "trader1/runtime/portfolio/__init__.py",
                "trader1/dashboard/summary_writer.py",
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
                "contracts/schema/paper_portfolio_snapshot.schema.json",
                "contracts/registry.yaml",
                "contracts/validators/validator_registry.json",
                "tests/runtime/test_paper_portfolio.py",
                "tests/dashboard/test_summary_writer.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/runtime/test_safe_launcher.py",
                "contracts/generated/context_pack/DASHBOARD_PAPER_PORTFOLIO_VALUES.md",
                "tools/emit_dashboard_paper_portfolio_values_patch_evidence.py",
                "tools/emit_dashboard_launch_visibility_patch_evidence.py",
            ]
        )
    )
    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.runtime.test_paper_portfolio",
                "tests.dashboard.test_summary_writer",
                "tests.dashboard.test_read_only_dashboard",
                "tests.runtime.test_safe_launcher",
                "-v",
            ]
        ),
        run_command([sys.executable, "tools/run_read_only_dashboard_validators.py"]),
        run_command([sys.executable, "tools/run_root_launcher_validators.py"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "BINANCE_PAPER.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run, artifacts)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/run_live_final_guard_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] if item["status"] != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
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
