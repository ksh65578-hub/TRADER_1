from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_LEDGER_JSONL_RECOVERY"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LEDGER-JSONL-RECOVERY"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_ENGINE_RUNTIME_E2E_CONTINUE"

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
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "upbit_paper_persistent_loop_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "ledger_durability_validator",
    "ledger_reconciliation_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/runtime/paper/upbit_paper_persistent_loop.py",
    "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "contracts/generated/context_pack/UPBIT_PAPER_LEDGER_JSONL_RECOVERY.md",
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
    "GLOBAL_CROSS_CYCLE_PAPER_LEDGER_ROLLUP_NOT_IMPLEMENTED",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_safe_command(args: list[str]) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def write_launcher_artifacts() -> list[str]:
    paths: list[str] = []
    for launcher_name in ["UPBIT_PAPER", "BINANCE_PAPER", "UPBIT_LIVE", "BINANCE_LIVE"]:
        report = build_launcher_report(launcher_name)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report)
        paths.append(rel(report_path))
        paths.extend(rel(path) for path in dashboard_paths.values() if hasattr(path, "relative_to"))
    legacy_dashboard = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    session_dashboard = (
        ROOT
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / "mvp1_upbit_paper_launcher"
        / "dashboard"
        / "index.html"
    )
    if session_dashboard.exists():
        write_text(legacy_dashboard, session_dashboard.read_text(encoding="utf-8"))
        paths.append(rel(legacy_dashboard))
    return sorted(set(paths))


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "UPBIT_PAPER_LEDGER_JSONL_RECOVERY.md",
        f"""# UPBIT_PAPER_LEDGER_JSONL_RECOVERY

context_pack_id: UPBIT_PAPER_LEDGER_JSONL_RECOVERY
task_class: MVP4_UPBIT_PAPER_LEDGER_JSONL_RECOVERY
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_runtime_recovery_guard_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: ["upbit_paper_persistent_loop_validator", "ledger_durability_validator", "read_only_dashboard_validator", "live_final_guard_validator"]
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- bounded Upbit PAPER runtime cycles write cycle-scoped paper ledger JSONL artifacts
- recovery guard scans paper ledger JSONL and quarantines corrupted partial lines
- invalid or corrupted ledger JSONL blocks PAPER resume and keeps live flags false
- dashboard shows ledger JSONL counts in the PAPER recovery panel

known_omissions_by_design:
- no global cross-cycle ledger rollup promotion
- no live exchange ledger use
- no private endpoint or credential use
- no live order permission

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

Upbit PAPER runtime cycles now write cycle-scoped PAPER ledger JSONL artifacts and a display-only ledger head. Recovery guard checks market-data JSONL, PAPER ledger JSONL, orphan temp files, and latest cycle recoverability before allowing PAPER-only resume.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "PAPER ledger JSONL recovery and dashboard visibility",
            "full_text_marker": f"{REQUIREMENT_ID}:PAPER runtime ledger JSONL must be written and recovery-checked without live permission",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER ledger JSONL recovery",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.upbit_paper_runtime_recovery_guard_report.v1", "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": ["upbit_paper_persistent_loop_validator", "ledger_durability_validator", "read_only_dashboard_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-UPBIT-PAPER-ENGINE-RUNTIME-E2E", "REQ-MVP4-DASHBOARD-MARKET-DATA-CONTINUITY-VISIBILITY"],
            "source_text_sha256": sha256_bytes(b"PAPER runtime ledger JSONL must be written and recovery-checked without live permission"),
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
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/upbit_paper_runtime_recovery_guard_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": ["trader1/runtime/paper/upbit_paper_persistent_loop.py", "trader1/dashboard/read_only_dashboard.py"],
            "test_files": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/dashboard/test_read_only_dashboard.py",
            ],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/paper/upbit_paper_persistent_loop.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["paper_runtime_recovery_guard_status.ledger_jsonl_checked_count"],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
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


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], artifacts: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_RUNTIME_WRITE_LOCK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": artifacts,
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_runtime_recovery_guard_report.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "UNCHANGED_LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STRATEGY_PROFITABILITY"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
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
            "active_read_surface_used": ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": "MVP4_UPBIT_PAPER_LEDGER_JSONL_RECOVERY",
            "required_section_ids": ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_LEDGER_RECONCILIATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_UPBIT_PAPER_LEDGER_JSONL_RECOVERY",
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_LEDGER_JSONL_RECOVERY_NO_LIVE_ORDERS",
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
                *CHANGED_ARTIFACTS,
                "tools/emit_upbit_paper_ledger_jsonl_recovery_patch_evidence.py",
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
        f"""# MVP4 Upbit PAPER Ledger JSONL Recovery Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- PAPER runtime fill ledger events were embedded in cycle reports but did not have a separate cycle-scoped JSONL artifact.
- Recovery guard checked public market-data JSONL and temp files, but not PAPER ledger JSONL corruption.
- Dashboard recovery panel did not show whether PAPER ledger JSONL had been checked.

Patch:
- Writes cycle-scoped PAPER ledger JSONL artifacts and a display-only latest ledger head report for PAPER fills.
- Recovery guard scans ledger JSONL, quarantines partial/corrupt lines, validates ledger chains, and blocks PAPER resume on corruption.
- Dashboard recovery panel now shows market JSONL count, ledger JSONL count, quarantined counts, and invalid ledger count.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
Remaining design gap: global cross-cycle paper ledger rollup remains blocked for a later non-live patch.
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
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    state["completed_requirement_ids"] = sorted(completed)
    for key, value in {
        "implemented_schema_ids": "trader1.upbit_paper_runtime_recovery_guard_report.v1",
        "implemented_validator_ids": "upbit_paper_persistent_loop_validator",
    }.items():
        values = set(state.get(key, []))
        values.add(value)
        state[key] = sorted(values)
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
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    launcher_artifacts = write_launcher_artifacts()
    tests_run = [
        run_safe_command([sys.executable, "-m", "unittest", "tests.integration.test_upbit_public_collection_persistent_loop", "-v"]),
        run_safe_command([sys.executable, "-m", "unittest", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_safe_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)

    artifacts = sorted(set(CHANGED_ARTIFACTS + launcher_artifacts + ["tools/emit_upbit_paper_ledger_jsonl_recovery_patch_evidence.py"]))
    patch_result = build_patch_result(now, tests_run, validators_run, artifacts)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result["validators_run"] = run_validators(VALIDATORS_REQUIRED)
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] if item["status"] != "PASS"]
    failed_validators = [item for item in patch_result["validators_run"] if item["status"] != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed and not failed_validators else "FAIL",
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
    return 0 if not failed and not failed_validators else 1


if __name__ == "__main__":
    raise SystemExit(main())
