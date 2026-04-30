from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_ROOT_LAUNCHER_OPERATOR_VISIBILITY_20260429_001"
PATCH_BASENAME = "MVP4_ROOT_LAUNCHER_OPERATOR_VISIBILITY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.boot.safe_launcher import ROOT_LAUNCHER_SPECS, build_launcher_report, write_launcher_report
from trader1.validation.mvp0_validators import run_validators


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text_file_canonical(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return sha256_bytes(normalized.encode("utf-8"))


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{time.time_ns()}.tmp")
    try:
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def write_json(path: Path, value: Any) -> None:
    _atomic_write_text(path, json.dumps(value, indent=2) + "\n")


def write_text(path: Path, value: str) -> None:
    _atomic_write_text(path, value)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def schema_bundle_hash() -> str:
    return sha256_json({rel(path): sha256_file(path) for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))})


def source_tree_hash() -> str:
    paths = sorted((ROOT / "trader1").rglob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return sha256_json({rel(path): sha256_file(path) for path in paths if "__pycache__" not in path.parts})


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["validator_bundle_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "validators" / "validator_registry.json")
    manifest["source_tree_hash_when_generated"] = source_tree_hash()
    manifest["updated_at_utc"] = now
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def write_all_launcher_reports() -> list[str]:
    paths: list[str] = []
    for launcher_name in sorted(ROOT_LAUNCHER_SPECS):
        report = build_launcher_report(launcher_name)
        paths.append(rel(write_launcher_report(report)))
    return paths


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "ROOT_LAUNCHER_SURFACE.md",
        f"""# ROOT_LAUNCHER_SURFACE

context_pack_id: ROOT_LAUNCHER_SURFACE
task_class: MVP4_ROOT_LAUNCHER_OPERATOR_VISIBILITY_GUARD
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MVP1_ROOT_LAUNCHER_SCOPE", "SECTION_MVP1_ROOT_LAUNCHER_FOUR", "SECTION_MVP1_SAFE_BOOT_SEQUENCE", "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT", "SECTION_AGENTS_MVP1_ROOT_LAUNCHERS"]
included_requirement_ids: ["REQ-MVP1-ROOT-LAUNCHER-SURFACE"]
included_schema_ids: ["trader1.root_launcher_report.v1"]
included_validator_ids: ["root_launcher_guard_validator", "root_launcher_surface_validator", "live_final_guard_validator"]
included_artifact_ids: ["UPBIT_PAPER.py", "UPBIT_LIVE.py", "BINANCE_PAPER.py", "BINANCE_LIVE.py", "trader1/runtime/boot/safe_launcher.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- root launchers write operator-visible reports
- interactive console execution pauses before closing
- non-interactive automation does not pause
- live launchers remain hard-blocked
- live_order_ready=false, live_order_allowed=false, can_live_trade=false

known_omissions_by_design:
- no live key loading
- no live order API
- no exchange account access
- no LIVE_READY snapshot write
- no MVP-5 live-enabling behavior

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

Root launchers now leave operator-visible reports and pause only for interactive console execution. This is a safety/visibility patch only; all live paths remain blocked.
""",
    )


def update_read_cache(now: str, trader_hash: str, agents_hash: str) -> None:
    context_dir = ROOT / "contracts" / "generated" / "context_pack"
    manifest = {
        "manifest_schema_id": "trader1.read_cache_manifest.v1",
        "created_at_utc": now,
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "authority_section_map_sha256": sha256_text_file_canonical(ROOT / "contracts" / "generated" / "authority_section_map.json"),
        "requirement_index_sha256": sha256_text_file_canonical(ROOT / "contracts" / "generated" / "requirement_index.json"),
        "requirement_artifact_matrix_sha256": sha256_text_file_canonical(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"),
        "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts" / "registry.yaml"),
        "schema_bundle_sha256_when_generated": schema_bundle_hash(),
        "context_pack_hashes": {rel(path): sha256_text_file_canonical(path) for path in sorted(context_dir.glob("*.md"))},
        "active_working_view_sha256": sha256_text_file_canonical(ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md"),
        "current_implementation_state_sha256": sha256_text_file_canonical(ROOT / "contracts" / "generated" / "current_implementation_state.json"),
        "valid_until_authority_hash_changes": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / "contracts" / "generated" / "read_cache_manifest.json", manifest)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]], launcher_reports: list[str]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_LIVE_REVIEW_DISPLAY_TRUTH_GUARD.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": ["REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP0-ROOT-LAUNCHER-GUARD"],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "new_registry_items": [],
            "new_or_changed_schema_ids": [],
            "validators_required": [
                "root_launcher_guard_validator",
                "root_launcher_surface_validator",
                "live_final_guard_validator",
                "patch_result_schema_validator",
                "generated_artifact_dirty_validator",
            ],
            "validators_run": validators_run,
            "tests_run": tests_run,
            "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "next_required_section_ids": ["SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT", "SECTION_MVP1_ROOT_LAUNCHER_FOUR"],
            "next_optional_section_ids": ["SECTION_MVP1_SAFE_BOOT_SEQUENCE"],
            "remaining_blockers": [
                "LIVE_READY_MISSING",
                "API_UNVERIFIED",
                "EXTERNAL_CREDENTIAL_REQUIRED",
                "MANUAL_ORDER_TEST_MISSING",
                "OPERATOR_APPROVAL_MISSING",
                "READ_ONLY_BURN_IN_MISSING",
                "LIVE_ENABLING_EVIDENCE_MISSING",
                "SCALE_UP_NOT_ELIGIBLE",
            ],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
                "SECTION_MVP1_ROOT_LAUNCHER_FOUR",
                "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
            ],
            "task_class": "MVP4_ROOT_LAUNCHER_OPERATOR_VISIBILITY_GUARD",
            "required_section_ids": ["SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT"],
            "expanded_section_ids": [
                "SECTION_AGENTS_ROOT_LAUNCHER_CONTRACT",
                "SECTION_MVP1_ROOT_LAUNCHER_FOUR",
                "SECTION_MVP1_SAFE_BOOT_SEQUENCE",
            ],
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UNCHANGED_FRESH",
            "requirement_artifact_matrix_status": "UNCHANGED_FRESH",
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
    patch_result["new_registry_items"] = launcher_reports
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
            "stage_gate_status": "PASS_FOR_OPERATOR_VISIBILITY_NO_LIVE_ORDERS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "remaining_external_blockers": patch_result["remaining_blockers"],
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
                "tools/emit_root_launcher_operator_visibility_patch_evidence.py",
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
        f"""# MVP4 Root Launcher Operator Visibility Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Root launchers returned immediately after printing JSON. In a double-click console this looked like the program closed without explanation.

Patch:
- Root launchers now write a namespaced root_launcher_report.json.
- Interactive console runs pause before closing.
- Non-interactive automation remains non-blocking.
- Live launchers still hard-block live order paths.

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
    launcher_reports = write_all_launcher_reports()
    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.contract.test_root_launchers", "tests.runtime.test_safe_launcher", "-v"]),
        run_command([sys.executable, "tools/run_root_launcher_validators.py"]),
        run_command([sys.executable, "UPBIT_PAPER.py"]),
        run_command([sys.executable, "UPBIT_LIVE.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ]
    validators_run = run_validators(["root_launcher_guard_validator", "root_launcher_surface_validator", "live_final_guard_validator"])
    update_context(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run, launcher_reports)
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
            "root_launcher_guard_validator",
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
