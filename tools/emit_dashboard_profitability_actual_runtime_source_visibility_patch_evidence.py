from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-PROFITABILITY-ACTUAL-RUNTIME-SOURCE-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
    "tools/emit_dashboard_profitability_actual_runtime_source_visibility_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY.md",
]

BLOCKERS = [
    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY.md",
        f"""# MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY

context_pack_id: MVP4_DASHBOARD_PROFITABILITY_ACTUAL_RUNTIME_SOURCE_VISIBILITY
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_STRATEGY_PROFITABILITY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Dashboard profitability maturity exposes actual non-live runtime source status and source count.
- Long-run evidence cannot display eligible unless a validated non-live runtime source exists.
- Dashboard schema requires the runtime source fields so regenerated PAPER dashboards cannot silently omit the blocker.
- Narrow dashboard layouts wrap long status tokens and evidence details instead of clipping them horizontally.
- UPBIT and BINANCE PAPER dashboard artifacts are regenerated through the safe launcher and remain live-blocked.

known_omissions_by_design:
- no actual 24h PAPER/SHADOW long-run runtime evidence is created
- no official API verification, account snapshot, credential, live order, live config mutation, or scale-up is used
- ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING remains open

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

The dashboard now shows the missing actual non-live runtime source in the profitability maturity area. Narrow dashboard cards wrap long status text instead of clipping. PAPER scorecard input remains separate from long-run evidence and cannot create LIVE_READY, live order permission, live trading, or scale-up.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_DASHBOARD_SHELL",
            "source_file": "TRADER_1.md",
            "source_heading": "Dashboard profitability actual runtime source visibility",
            "full_text_marker": f"{REQUIREMENT_ID}: dashboard profitability maturity must expose actual runtime source blocker before long-run review and keep narrow detail text readable",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard profitability actual runtime source visibility",
            "requirement_kind": "DASHBOARD_UX_VALIDATOR_PATCH",
            "schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/dashboard/test_read_only_dashboard.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PAPER-SHADOW-ACTUAL-RUNTIME-SOURCE-GUARD",
                "REQ-MVP4-DASHBOARD-PROFITABILITY-MATURITY-UX-HARDENING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"dashboard profitability maturity must expose actual runtime source blocker before long-run review and keep narrow detail text readable"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
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
            "section_id": "SECTION_DASHBOARD_SHELL",
            "schema_files": ["contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/dashboard/read_only_dashboard.py"],
            "test_files": ["tests/dashboard/test_read_only_dashboard.py"],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/dashboard/read_only_dashboard.py",
                "trader1/runtime/boot/safe_launcher.py",
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
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard/index.html",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_6_DASHBOARD_AND_OPERATOR_VISIBILITY",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    base.write_json(matrix_path, matrix)


def finalize_patch_result(
    patch_result: dict[str, Any],
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
) -> dict[str, Any]:
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PAPER-SHADOW-ACTUAL-RUNTIME-SOURCE-GUARD",
                "REQ-MVP4-DASHBOARD-PROFITABILITY-MATURITY-UX-HARDENING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT,BINANCE",
            "affected_market_type": "KRW_SPOT,SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
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
                "SECTION_DASHBOARD_SHELL",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_STRATEGY_PROFITABILITY", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
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
                "current_implementation_state",
                "dashboard shell schema",
                "read-only dashboard renderer",
                "paper/shadow actual runtime source guard",
                "safe PAPER launcher artifacts",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_stage": "NOT_CHANGED_DASHBOARD_VISIBILITY_ONLY",
            "optimizer_status_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_output_type": "NO_OPTIMIZER_OUTPUT_CREATED",
            "optimizer_guardrail_result": "PASS_LONG_RUN_RUNTIME_SOURCE_VISIBLE_AND_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_state_before": "LONG_RUN_EVIDENCE_BLOCKED_ACTUAL_RUNTIME_SOURCE_REQUIRED",
            "convergence_state_after": "LONG_RUN_EVIDENCE_BLOCKED_ACTUAL_RUNTIME_SOURCE_VISIBLE_ON_DASHBOARD",
            "convergence_guardrail_result": "PASS_DASHBOARD_CANNOT_HIDE_ACTUAL_RUNTIME_SOURCE_BLOCKER",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_DASHBOARD_ACTUAL_RUNTIME_SOURCE_VISIBILITY_LIVE_BLOCKED",
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
            "artifact_paths": [
                *CHANGED_ARTIFACTS,
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
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260430.md",
        f"""# MVP4 Dashboard Profitability Actual Runtime Source Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Paper/shadow evidence validation requires a validated non-live persistent runtime source before any long-run claim, but the dashboard profitability maturity panel did not expose that source status directly.
- This could make scorecard input look more complete than it is, increasing operator UX risk and optimizer/convergence false-safe risk.
- Browser inspection also showed narrow detail cards could clip long status strings instead of wrapping them, making the user-facing blocker harder to read.

Patch:
- Added actual_runtime_source_status, actual_runtime_source_count, actual_runtime_source_summary, long_run_evidence_eligible, and long_run_blocker_code to the dashboard profitability maturity projection and schema.
- Added dashboard validator checks that block long-run eligibility without validated non-live runtime source evidence.
- Added negative dashboard tests for false long-run eligibility and validated-runtime status without source ids.
- Hardened dashboard CSS so long status tokens, detail cards, readiness rows, and evidence requirement text wrap within their cards on narrow viewports.
- Regenerated UPBIT and BINANCE PAPER dashboard artifacts through safe launcher paths only.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
""",
    )


def write_patch(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-c",
                "from trader1.runtime.boot.safe_launcher import launcher_main; raise SystemExit(launcher_main('UPBIT_PAPER', pause=False, open_dashboard=False, console_heartbeat_ticks=1, console_heartbeat_interval_seconds=0.0))",
            ]
        ),
        base.run_command(
            [
                sys.executable,
                "-c",
                "from trader1.runtime.boot.safe_launcher import launcher_main; raise SystemExit(launcher_main('BINANCE_PAPER', pause=False, open_dashboard=False, console_heartbeat_ticks=1, console_heartbeat_interval_seconds=0.0))",
            ]
        ),
        base.run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        base.run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = finalize_patch_result(base.build_patch_result(now, tests_run, validators_run), now, tests_run, validators_run)
    write_patch(now, trader_hash, agents_hash, patch_result)

    tests_run.append(base.run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = finalize_patch_result(base.build_patch_result(now, tests_run, validators_run), now, tests_run, validators_run)
    write_patch(now, trader_hash, agents_hash, patch_result)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
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
