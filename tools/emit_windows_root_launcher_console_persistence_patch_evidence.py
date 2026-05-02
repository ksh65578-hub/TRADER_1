from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_windows_console_safe_monitor_default_patch_evidence as base  # noqa: E402


ROOT_LAUNCHER_FILES = [
    "UPBIT_PAPER.py",
    "UPBIT_LIVE.py",
    "BINANCE_PAPER.py",
    "BINANCE_LIVE.py",
]
CHANGED_ARTIFACTS = sorted(
    {
        *ROOT_LAUNCHER_FILES,
        "trader1/runtime/boot/safe_launcher.py",
        "tests/contract/test_root_launchers.py",
        "tests/runtime/test_safe_launcher.py",
        "tools/emit_windows_console_safe_monitor_default_patch_evidence.py",
        "tools/emit_windows_root_launcher_console_persistence_patch_evidence.py",
        f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
    }
)
VALIDATORS_REQUIRED = [
    "root_launcher_guard_validator",
    "root_launcher_surface_validator",
    "heartbeat_validator",
    "read_only_dashboard_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
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


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.BLOCKERS = BLOCKERS


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_MVP1_HEARTBEAT", "SECTION_MVP1_SAFE_BOOT_SEQUENCE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP1-HEARTBEAT", "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL", "REQ-MVP0-LIVE-BLOCKED-TEST"]
included_schema_ids: ["trader1.root_launcher_report.v1", "trader1.heartbeat.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- root launchers enter operator SAFE_MONITOR by default so a Windows console does not close after one heartbeat
- automation can bound root launcher execution with TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS and TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS
- root launcher guard still exposes exactly four allowed launchers
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- this is not a persistent trading engine
- this does not create PAPER portfolio verification, LIVE_READY, live order permission, credentials, or scale-up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
generated_at_utc: {now}
""",
    )
    state = base.load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    base.write_text(
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

The four root launchers now route through a root operator entrypoint that holds the console in SAFE_MONITOR by default. Automation can bound the heartbeat loop with TRADER1_ROOT_OPERATOR_HEARTBEAT_TICKS and TRADER1_ROOT_OPERATOR_HEARTBEAT_INTERVAL_SECONDS. No live order, credential, LIVE_READY, live config mutation, or scale-up path is introduced.
""",
    )


_base_write_launcher_artifacts = base.write_launcher_artifacts
_base_build_patch_result = base.build_patch_result
_base_write_evidence = base.write_evidence


def write_launcher_artifacts() -> list[str]:
    return sorted({*_base_write_launcher_artifacts(), *CHANGED_ARTIFACTS})


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    artifacts: list[str],
) -> dict[str, Any]:
    patch_result = _base_build_patch_result(now, tests_run, validators_run, sorted({*artifacts, *CHANGED_ARTIFACTS}))
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                "REQ-MVP1-ROOT-LAUNCHER-SURFACE",
                "REQ-MVP1-HEARTBEAT",
                "REQ-MVP1-READ-ONLY-DASHBOARD-SHELL",
                "REQ-MVP0-LIVE-BLOCKED-TEST",
            ],
            "new_registry_items": sorted({*patch_result.get("new_registry_items", []), *CHANGED_ARTIFACTS}),
            "new_or_changed_schema_ids": [],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "next_task_class": "MVP4_UPBIT_PAPER_PERSISTENT_RUNTIME_RECOVERY",
            "next_required_section_ids": [
                "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
                "SECTION_MVP1_HEARTBEAT",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_DASHBOARD_SHELL"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "BINANCE_FUTURES_LIVE", "LIVE_CONFIG_MUTATION"],
            "remaining_blockers": BLOCKERS,
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
                "SECTION_MVP1_HEARTBEAT",
                "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_WINDOWS_ROOT_LAUNCHER_CONSOLE_PERSISTENCE",
            "required_section_ids": [
                "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
                "SECTION_MVP1_HEARTBEAT",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_MVP1_ROOT_LAUNCHER_SCOPE",
                "SECTION_MVP1_HEARTBEAT",
                "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
            ],
        }
    )
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = base.sha256_json(
        {key: value for key, value in patch_result.items() if key != "result_hash"}
    )
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    _base_write_evidence(now, trader_hash, agents_hash, patch_result)
    manifest_path = ROOT / patch_result["evidence_manifest_path"]
    manifest = base.load_json(manifest_path)
    manifest["artifact_paths"] = sorted({*manifest.get("artifact_paths", []), *CHANGED_ARTIFACTS})
    manifest["live_order_ready"] = False
    manifest["live_order_allowed"] = False
    manifest["can_live_trade"] = False
    manifest["scale_up_allowed"] = False
    base.write_json(manifest_path, manifest)


def main() -> int:
    configure_base()
    base.update_context = update_context
    base.write_launcher_artifacts = write_launcher_artifacts
    base.build_patch_result = build_patch_result
    base.write_evidence = write_evidence
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
