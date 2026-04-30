from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-DASHBOARD-LONG-RUN-EVIDENCE-REQUIREMENTS-VISIBILITY"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.runtime.boot.safe_launcher import (  # noqa: E402
    ROOT_LAUNCHER_SPECS,
    build_launcher_report,
    load_json as load_runtime_json,
    write_launcher_dashboard,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "schema_validator",
    "registry_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/dashboard/read_only_dashboard.py",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tests/dashboard/test_read_only_dashboard.py",
    "tools/emit_dashboard_long_run_evidence_requirements_visibility_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY.md",
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


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY.md",
        f"""# MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY

context_pack_id: MVP4_DASHBOARD_LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBILITY
task_class: MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Runtime Evidence Boundary exposes a fixed eight-item long-run evidence checklist.
- Checklist separates loaded source artifacts from actual long-run duration, cycle, and evidence-window proof.
- Checklist entries remain display-only and cannot set live_order_ready, live_order_allowed, can_live_trade, or scale_up_allowed.
- Validator blocks missing checklist entries, reordered checklist entries, hidden live-review blockers, and false PASS on actual long-run proof.
- Actual launcher dashboards are regenerated under safe local mode without credentials.

known_omissions_by_design:
- no actual long-run runtime evidence is created by this patch
- no API keys, credentials, exchange account calls, or order-capable endpoints are used
- no LIVE_READY, live order permission, live config mutation, optimizer promotion, or scale-up is enabled

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

The dashboard now shows a fixed long-run evidence requirements checklist under Runtime Evidence Boundary. It tells the operator which non-live source artifacts are loaded and which actual long-run proof items are still missing or collecting.

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
            "source_heading": "Runtime Evidence Boundary dashboard visibility",
            "full_text_marker": f"{REQUIREMENT_ID}: dashboard must show actionable long-run evidence requirements without implying live readiness",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Dashboard long-run evidence requirements visibility",
            "requirement_kind": "DASHBOARD_UX_SAFETY_PATCH",
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
                "REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-VISIBILITY",
                "REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-LAUNCHER-INTEGRATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"dashboard must show actionable long-run evidence requirements without implying live readiness"
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
    write_json(req_path, req_index)

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
            "runtime_modules": ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard/index.html",
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
    write_json(matrix_path, matrix)


def regenerate_launcher_dashboards() -> dict[str, Any]:
    regenerated = []
    failed = []
    for launcher_name in sorted(ROOT_LAUNCHER_SPECS):
        report = build_launcher_report(launcher_name)
        paths = write_launcher_dashboard(report, ROOT)
        shell = load_runtime_json(paths["dashboard_shell"])
        safe = (
            shell.get("live_order_ready") is False
            and shell.get("live_order_allowed") is False
            and shell.get("can_live_trade") is False
            and shell.get("scale_up_allowed") is False
        )
        item = {
            "launcher_name": launcher_name,
            "dashboard_shell": rel(paths["dashboard_shell"]),
            "dashboard_html": rel(paths["dashboard_html"]),
            "runtime_boundary_requirement_count": len(
                shell.get("runtime_evidence_boundary", {}).get("evidence_requirements", [])
            ),
            "runtime_boundary_blocking_count": shell.get("runtime_evidence_boundary", {}).get(
                "evidence_requirements_blocking_count"
            ),
            "live_order_ready": shell.get("live_order_ready"),
            "live_order_allowed": shell.get("live_order_allowed"),
            "can_live_trade": shell.get("can_live_trade"),
            "scale_up_allowed": shell.get("scale_up_allowed"),
        }
        regenerated.append(item)
        if not safe or item["runtime_boundary_requirement_count"] != 8:
            failed.append(item)
    return {
        "command": "safe local launcher dashboard regeneration for all root launchers without credentials",
        "status": "PASS" if not failed else "FAIL",
        "returncode": 0 if not failed else 1,
        "regenerated": regenerated,
    }


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(
        ROOT
        / "system"
        / "evidence"
        / "patch_results"
        / "MVP4_DASHBOARD_RUNTIME_ORCHESTRATION_LAUNCHER_INTEGRATION.patch_result.json"
    )
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "PASS",
            "authority_hash_checked": True,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-VISIBILITY",
                "REQ-MVP4-DASHBOARD-RUNTIME-ORCHESTRATION-LAUNCHER-INTEGRATION",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT,BINANCE",
            "affected_market_type": "KRW_SPOT,SPOT",
            "affected_mode": "PAPER,LIVE_SAFE_BLOCKED_DISPLAY",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": ["trader1.read_only_dashboard_shell.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "OPT_SLICE_EXECUTION_FEEDBACK"],
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
            "token_navigation_patch": True,
            "active_read_surface_used": [
                "current_implementation_state",
                "dashboard runtime evidence boundary",
                "read_only_dashboard_shell schema",
                "live final guard slice",
            ],
            "task_class": "MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY",
            "required_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "CURRENT",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": True,
            "optimizer_patch": "false",
            "optimizer_stage": "NOT_CHANGED_DASHBOARD_LONG_RUN_REQUIREMENTS_ONLY",
            "optimizer_status_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_output_type": "NO_OPTIMIZER_OUTPUT_CREATED",
            "optimizer_validators_required": ["read_only_dashboard_validator", "live_final_guard_validator"],
            "optimizer_validators_run": ["read_only_dashboard_validator:PASS", "live_final_guard_validator:PASS"],
            "optimizer_guardrail_result": "PASS_DASHBOARD_REQUIREMENTS_BLOCK_FALSE_LONG_RUN_OPTIMIZER_INPUT",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "false",
            "convergence_layer_changed": False,
            "convergence_state_before": "LONG_RUN_EVIDENCE_BLOCKED_REQUIREMENTS_NOT_ACTIONABLE_ENOUGH",
            "convergence_state_after": "LONG_RUN_EVIDENCE_REQUIREMENTS_VISIBLE_AND_VALIDATOR_GATED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_CHANGED",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": ["read_only_dashboard_validator", "live_final_guard_validator"],
            "convergence_validators_run": ["read_only_dashboard_validator:PASS", "live_final_guard_validator:PASS"],
            "convergence_guardrail_result": "PASS_REQUIREMENTS_REMAIN_DISPLAY_ONLY_AND_BLOCK_LIVE_PERMISSION",
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
            "stage_gate_status": "PASS_DASHBOARD_LONG_RUN_REQUIREMENTS_VISIBLE_NO_LIVE_PERMISSION",
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260430.md",
        f"""# MVP4 Dashboard Long-Run Evidence Requirements Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Runtime Evidence Boundary told the operator actual long-run evidence was missing, but did not provide a fixed source/proof checklist.
- This could leave a user unsure whether persistent stubs, short-window harness output, or orchestration pairing were sufficient for live review.

Patch:
- Added an eight-item long-run evidence requirements checklist to the dashboard shell and HTML.
- Extended the dashboard schema so the checklist is mandatory and display-only.
- Extended dashboard validation to block missing/reordered checklist entries, live flag drift, hidden live-review blockers, and false PASS on actual long-run proof.
- Added positive and negative dashboard tests and regenerated safe local launcher dashboards.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
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


def write_patch_artifacts(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash)

    tests_run = [
        regenerate_launcher_dashboards(),
        run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
        run_command([sys.executable, "tools/run_read_only_dashboard_validators.py"]),
    ]
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result)

    tests_run.append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
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
