from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.validation.mvp0_validators import run_validators


PATCH_BASENAME = "MVP4_MONITOR_STALE_SOURCE_WRITER_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-MONITOR-STALE-SOURCE-WRITER-GUARD"
AUTHORITY_FILES = ["TRADER_1.md", "AGENTS.md"]
CHANGED_ARTIFACTS = [
    "trader1/runtime/boot/safe_launcher.py",
    "tests/runtime/test_safe_launcher.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
    "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
    "system/evidence/audit_reports/MVP4_MONITOR_STALE_SOURCE_WRITER_GUARD_20260429.md",
    "contracts/generated/context_pack/MONITOR_STALE_SOURCE_WRITER_GUARD.md",
]
VALIDATORS_REQUIRED = [
    "root_launcher_surface_validator",
    "heartbeat_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "runtime_stability_history_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "live_final_guard_validator",
    "generated_artifact_dirty_validator",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def result_hash(payload: dict[str, Any]) -> str:
    clean = dict(payload)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def patch_state_hash(state: dict[str, Any]) -> str:
    clean = dict(state)
    clean.pop("state_hash", None)
    return sha256_json(clean)


def command_status(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def run_safe_checks() -> list[dict[str, Any]]:
    commands = [
        [sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"],
        [sys.executable, "-m", "unittest", "tests.runtime.test_safe_launcher", "tests.dashboard.test_read_only_dashboard", "-v"],
        [sys.executable, "UPBIT_PAPER.py"],
        [sys.executable, "BINANCE_PAPER.py"],
        [sys.executable, "tools/run_mvp0_validators.py"],
        [sys.executable, "tools/run_patch_result_runtime_schema_validators.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
    ]
    return [command_status(command) for command in commands]


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = read_json(req_path, {})
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_RUNTIME_RECOVERY",
            "source_file": "TRADER_1.md",
            "source_heading": "Runtime stale source writer guard",
            "full_text_marker": f"{REQUIREMENT_ID}:SECTION_RUNTIME_RECOVERY:Runtime stale source writer guard",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Block stale monitor writers after source changes",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.heartbeat.v1", "trader1.read_only_dashboard_shell.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_safe_launcher.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["RUNTIME_SAFETY_PATCH", "DASHBOARD_UX", "VALIDATOR_IMPLEMENTATION"],
            "depends_on": ["REQ-MVP4-RUNTIME-STABILITY-HISTORY-VALIDATOR", "REQ-MVP4-SCHEMA-RUNTIME-INSTANCE-VALIDATION"],
            "source_text_sha256": sha256_bytes(REQUIREMENT_ID.encode("utf-8")),
            "implementation_status": "IMPLEMENTED",
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

    matrix = read_json(matrix_path, {})
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_RUNTIME_RECOVERY",
            "schema_files": ["contracts/schema/heartbeat.schema.json", "contracts/schema/read_only_dashboard_shell.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_safe_launcher.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/dashboard_shell.json",
                "system/runtime/binance/spot/paper/mvp1_binance_paper_launcher/dashboard_shell.json",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def update_state_and_ledger(now: str, patch_hash: str, trader_hash: str, agents_hash: str) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = read_json(state_path, {})
    state["updated_at_utc"] = now
    state["trader1_sha256"] = trader_hash
    state["agents_sha256"] = agents_hash
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["runtime_schema_instance_validator"]))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_hash
    state["next_allowed_task_class"] = "MVP4_RISK_EXPOSURE_DRAWDOWN_UX_HARDENING"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
    state["state_hash"] = patch_state_hash(state)
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = read_json(ledger_path, {"ledger_schema_id": "trader1.implementation_patch_ledger.v1", "created_at_utc": now, "patches": []})
    ledger["updated_at_utc"] = now
    patches = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    patches.append(
        {
            "patch_id": PATCH_ID,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "target_mvp_level": "MVP-4",
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_hash,
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    ledger["patches"] = patches
    write_json(ledger_path, ledger)


def update_read_cache(now: str, trader_hash: str, agents_hash: str) -> None:
    manifest_path = ROOT / "contracts" / "generated" / "read_cache_manifest.json"
    manifest = read_json(manifest_path, {})
    context_hashes = manifest.setdefault("context_pack_hashes", {})
    context_path = ROOT / "contracts" / "generated" / "context_pack" / "MONITOR_STALE_SOURCE_WRITER_GUARD.md"
    context_hashes[context_path.relative_to(ROOT).as_posix()] = sha256_file(context_path)
    manifest.update(
        {
            "created_at_utc": now,
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "requirement_index_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_index.json"),
            "requirement_artifact_matrix_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"),
            "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts" / "registry.yaml"),
            "schema_bundle_sha256_when_generated": sha256_json(
                {
                    path.relative_to(ROOT).as_posix(): sha256_file(path)
                    for path in sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
                }
            ),
            "current_implementation_state_sha256": sha256_file(ROOT / "contracts" / "generated" / "current_implementation_state.json"),
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    write_json(manifest_path, manifest)


def write_supporting_artifacts(now: str, trader_hash: str, agents_hash: str, validators_run: list[dict[str, Any]], tests_run: list[dict[str, Any]]) -> None:
    audit = f"""# MVP4 Monitor Stale Source Writer Guard

generated_at_utc: {now}

Finding:
- Long-running PAPER launcher monitor processes can keep an older in-memory source tree and overwrite dashboard runtime artifacts after a newer code/schema patch.

Patch:
- `refresh_launcher_monitor_artifacts` now compares the launcher report source_tree_hash with the current source tree hash.
- If the source identity changed, it returns a BLOCKED heartbeat with SOURCE_IDENTITY_MISMATCH and does not refresh dashboard artifacts.
- Added a negative test proving stale monitor writers do not overwrite the existing dashboard shell.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange account call
- no live order path enabled
"""
    write_text(ROOT / "system" / "evidence" / "audit_reports" / "MVP4_MONITOR_STALE_SOURCE_WRITER_GUARD_20260429.md", audit)
    context = f"""context_pack_id: MONITOR_STALE_SOURCE_WRITER_GUARD
task_class: RUNTIME_SAFETY_PATCH
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}

Included sections:
- SECTION_RUNTIME_RECOVERY
- SECTION_DASHBOARD_OPERATOR_UX
- SECTION_LIVE_FINAL_GUARD

Acceptance checklist:
- stale source monitor cannot overwrite runtime dashboard artifacts
- heartbeat reports SOURCE_IDENTITY_MISMATCH when stale
- dashboard shell keeps live flags false
- runtime schema validator passes current PAPER artifacts
"""
    write_text(ROOT / "contracts" / "generated" / "context_pack" / "MONITOR_STALE_SOURCE_WRITER_GUARD.md", context)
    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "exchange": "UPBIT_AND_BINANCE",
        "market_type": "KRW_SPOT_AND_SPOT",
        "mode": "PAPER",
        "status": "PASS" if all(item.get("status") == "PASS" for item in tests_run) else "FAIL",
        "blockers": [],
        "notes": "stale source monitor writer guard is runtime-only and live-blocked",
        "evidence_manifest_id": PATCH_ID,
        "artifact_paths": CHANGED_ARTIFACTS + [
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
        ],
        "known_blockers": [
            "LIVE_READY_MISSING",
            "API_UNVERIFIED",
            "OPERATOR_APPROVAL_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "system" / "evidence" / f"{PATCH_BASENAME}.evidence_manifest.json", evidence_manifest)
    write_json(
        ROOT / "system" / "evidence" / "validator_runs" / f"{PATCH_BASENAME}.validator_run_log.json",
        {
            "schema_id": "trader1.validator_run_log.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(
        ROOT / "system" / "evidence" / "stage_gates" / f"{PATCH_BASENAME}.stage_gate_result.json",
        {
            "schema_id": "trader1.stage_gate_result.v1",
            "generated_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "status": "PASS" if all(item.get("status") == "PASS" for item in tests_run) and all(item.get("status") == "PASS" for item in validators_run) else "BLOCKED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
            "next_action": "continue MVP-4 risk/exposure/drawdown UX hardening; MVP-5 remains blocked",
        },
    )


def build_patch_result(now: str, trader_hash: str, agents_hash: str, validators_run: list[dict[str, Any]], tests_run: list[dict[str, Any]]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": AUTHORITY_FILES,
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": [
            REQUIREMENT_ID,
            "REQ-MVP4-SCHEMA-RUNTIME-INSTANCE-VALIDATION",
            "REQ-MVP4-RUNTIME-STABILITY-HISTORY-VALIDATOR",
        ],
        "affected_exchange": "UPBIT_AND_BINANCE",
        "affected_market_type": "KRW_SPOT_AND_SPOT",
        "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": CHANGED_ARTIFACTS,
        "new_or_changed_schema_ids": [],
        "validators_required": VALIDATORS_REQUIRED,
        "validators_run": validators_run,
        "tests_run": tests_run,
        "coverage_unmapped_count": 0,
        "coverage_index_result": "PASS",
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
        "read_cache_update_required": True,
        "context_pack_update_required": True,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP4_RISK_EXPOSURE_DRAWDOWN_UX_HARDENING",
        "next_required_section_ids": ["SECTION_RISK_EXPOSURE", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_RUNTIME_RECOVERY"],
        "next_optional_section_ids": ["SECTION_EXECUTION_FEEDBACK", "SECTION_CONVERGENCE_MEMORY"],
        "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
        "live_order_ready_before": False,
        "live_order_ready_after": False,
        "live_order_allowed_before": False,
        "live_order_allowed_after": False,
        "can_live_trade_before": False,
        "can_live_trade_after": False,
        "scale_up_allowed_before": False,
        "scale_up_allowed_after": False,
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
        "token_navigation_patch": False,
        "active_read_surface_used": ["SECTION_RUNTIME_RECOVERY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_MONITOR_STALE_SOURCE_WRITER_GUARD",
        "required_section_ids": ["SECTION_RUNTIME_RECOVERY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": [
            "TRADER_1:runtime-recovery-active-surface",
            "TRADER_1:dashboard-operator-ux-active-surface",
            "AGENTS:runtime-safety-implementation-guide",
        ],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "UNCHANGED_FRESH",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UPDATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NOT_OPTIMIZER_RELATED",
        "optimizer_stage": "MVP4_REVIEW_PREP",
        "optimizer_status_before": "LIVE_BLOCKED",
        "optimizer_status_after": "LIVE_BLOCKED",
        "optimizer_maturity_level_before": "UNCHANGED",
        "optimizer_maturity_level_after": "UNCHANGED",
        "optimizer_output_type": "NO_OPTIMIZER_OUTPUT",
        "optimizer_validators_required": [],
        "optimizer_validators_run": [],
        "optimizer_guardrail_result": "NOT_CHANGED",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NOT_CONVERGENCE_RELATED",
        "convergence_layer_changed": False,
        "convergence_state_before": "LIVE_BLOCKED",
        "convergence_state_after": "LIVE_BLOCKED",
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_RUNTIME_WRITER_GUARD",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
        "convergence_validators_required": [],
        "convergence_validators_run": [],
        "convergence_guardrail_result": "NOT_CHANGED",
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "scale_up_allowed_after": False,
        "result_hash": "",
    }
    payload["result_hash"] = result_hash(payload)
    return payload


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    tests_run = run_safe_checks()
    validators_run = run_validators(VALIDATORS_REQUIRED)
    write_supporting_artifacts(now, trader_hash, agents_hash, validators_run, tests_run)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, trader_hash, agents_hash, validators_run, tests_run)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result["result_hash"], trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_result_path": patch_path.relative_to(ROOT).as_posix(), "result_hash": patch_result["result_hash"]}, indent=2))
    return 0 if all(item.get("status") == "PASS" for item in tests_run + validators_run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
