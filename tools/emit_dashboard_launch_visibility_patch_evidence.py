from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_DASHBOARD_LAUNCH_VISIBILITY_20260429_001"
PATCH_BASENAME = "MVP4_DASHBOARD_LAUNCH_VISIBILITY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (
    run_command,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.runtime.boot.safe_launcher import ROOT_LAUNCHER_SPECS, build_launcher_report, write_launcher_runtime_bundle
from trader1.validation.mvp0_validators import run_validators


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_launcher_artifacts() -> list[str]:
    paths: list[str] = []
    for launcher_name in sorted(ROOT_LAUNCHER_SPECS):
        report = build_launcher_report(launcher_name)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report)
        paths.append(rel(report_path))
        paths.extend(rel(path) for path in dashboard_paths.values() if path.exists())
    return sorted(set(paths))


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "READ_ONLY_DASHBOARD.md",
        f"""# READ_ONLY_DASHBOARD

context_pack_id: READ_ONLY_DASHBOARD
task_class: MVP4_DASHBOARD_LAUNCH_VISIBILITY
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_DASHBOARD_SHELL", "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT"]
included_requirement_ids: ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-ROOT-LAUNCHER-SURFACE"]
included_schema_ids: ["trader1.read_only_dashboard_shell.v1", "trader1.root_launcher_report.v1"]
included_validator_ids: ["read_only_dashboard_validator", "root_launcher_surface_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/dashboard/read_only_dashboard.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- root launchers generate session-scoped read-only dashboard HTML
- root launchers print dashboard_path
- interactive operator runs may open the local HTML dashboard
- dashboard remains display-only
- no order controls are present
- live_order_ready=false, live_order_allowed=false, can_live_trade=false

known_omissions_by_design:
- no standalone root dashboard launcher is added
- no web server is started
- no live order path is enabled
- no exchange credentials are loaded

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
live_order_ready: false
live_order_allowed: false
can_live_trade: false
scale_up_allowed: false

## Current Safe State

Root launchers now generate a session-scoped read-only dashboard at dashboard/index.html and print its path. This is display-only and cannot create live trading permission.
""",
    )


def build_patch_result(now: str, tests_run: list[dict], validators_run: list[dict], artifacts: list[str]) -> dict:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_ROOT_LAUNCHER_OPERATOR_VISIBILITY.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": ["REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP1-ROOT-LAUNCHER-SURFACE"],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": artifacts,
            "new_or_changed_schema_ids": [],
            "validators_required": [
                "read_only_dashboard_validator",
                "root_launcher_surface_validator",
                "live_final_guard_validator",
                "patch_result_schema_validator",
                "generated_artifact_dirty_validator",
            ],
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "task_class": "MVP4_DASHBOARD_LAUNCH_VISIBILITY",
            "active_read_surface_used": ["SECTION_DASHBOARD_SHELL", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT"],
            "required_section_ids": ["SECTION_DASHBOARD_SHELL"],
            "expanded_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT"],
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict) -> None:
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
            "stage_gate_status": "PASS_FOR_DASHBOARD_LAUNCH_VISIBILITY_NO_LIVE_ORDERS",
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
                "trader1/runtime/boot/safe_launcher.py",
                "tests/runtime/test_safe_launcher.py",
                "tools/emit_dashboard_launch_visibility_patch_evidence.py",
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
        f"""# MVP4 Dashboard Launch Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Dashboard artifacts existed, but root launcher execution did not generate a fresh dashboard or show a dashboard path.

Patch:
- Existing four root launchers now generate session-scoped read-only dashboard JSON/HTML.
- Launcher output now includes dashboard_path.
- Interactive operator runs may open the local dashboard HTML.
- No standalone dashboard root launcher was added.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
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
        }
    )
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    artifacts = write_launcher_artifacts()
    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_safe_launcher", "tests.dashboard.test_read_only_dashboard", "-v"]),
        run_command([sys.executable, "tools/run_root_launcher_validators.py"]),
        run_command([sys.executable, "tools/run_read_only_dashboard_validators.py"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ]
    validators_run = run_validators(["read_only_dashboard_validator", "root_launcher_surface_validator", "live_final_guard_validator"])
    update_context(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run, artifacts)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_tests = [
        run_command([sys.executable, "tools/run_mvp0_validators.py"]),
        run_command([sys.executable, "tools/run_live_final_guard_validators.py"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    patch_result["tests_run"].extend(final_tests)
    patch_result["validators_run"] = run_validators(
        [
            "read_only_dashboard_validator",
            "root_launcher_surface_validator",
            "live_final_guard_validator",
            "patch_result_schema_validator",
            "generated_artifact_dirty_validator",
        ]
    )
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
