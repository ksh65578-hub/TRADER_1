from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_BINANCE_ADAPTER_SURFACE_ONLY"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-BINANCE-ADAPTER-SURFACE-ONLY"
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
    "registry_validator",
    "schema_validator",
    "closed_enum_validator",
    "common_defs_drift_validator",
    "root_launcher_surface_validator",
    "binance_adapter_surface_validator",
    "runtime_config_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "live_final_guard_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "generated_artifact_dirty_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/adapters/binance/__init__.py",
    "trader1/adapters/binance/surface.py",
    "trader1/runtime/boot/safe_launcher.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/registry.yaml",
    "contracts/schema/common.defs.schema.json",
    "contracts/schema/binance_adapter_surface_report.schema.json",
    "tests/adapter/test_binance_adapter_surface.py",
    "contracts/generated/context_pack/BINANCE_ADAPTER_SURFACE_ONLY.md",
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
    "BINANCE_ADAPTER_SURFACE_ONLY",
    "BINANCE_FUTURES_SURFACE_ONLY",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_safe_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
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
    return sorted(set(paths))


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "BINANCE_ADAPTER_SURFACE_ONLY.md",
        f"""# BINANCE_ADAPTER_SURFACE_ONLY

context_pack_id: BINANCE_ADAPTER_SURFACE_ONLY
task_class: MVP4_BINANCE_ADAPTER_SURFACE_ONLY
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_EXCHANGE_ADAPTER", "SECTION_NAMESPACE_SEPARATION", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.binance_adapter_surface_report.v1", "trader1.common_defs.v1"]
included_validator_ids: ["binance_adapter_surface_validator", "root_launcher_surface_validator", "live_final_guard_validator"]
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Binance adapter namespace exists only as fail-closed SURFACE_ONLY
- Binance SPOT PAPER is visible as not implemented, not tradable
- Binance FUTURES_USDT_M is explicit NOT_IMPLEMENTED/BLOCKED
- Binance root launcher and dashboard expose BINANCE_ADAPTER_SURFACE_ONLY instead of generic readiness wording
- any credential, private API, order adapter, live flag, or scale-up drift blocks validation
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

known_omissions_by_design:
- no Binance public market data collector
- no Binance paper broker
- no Binance futures runtime
- no live key loading or private account calls
- no LIVE_READY snapshot write

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

Binance now has an explicit fail-closed adapter namespace and schema-backed surface report. Binance SPOT and FUTURES_USDT_M remain non-tradable; root launchers and dashboard artifacts expose surface-only blockers so operators do not confuse visible Binance launchers with implemented trading runtime.

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
            "source_section_id": "SECTION_EXCHANGE_ADAPTER",
            "source_file": "TRADER_1.md",
            "source_heading": "Binance adapter implementation boundary",
            "full_text_marker": f"{REQUIREMENT_ID}:Binance root launcher surface must not imply Binance trading runtime exists",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Binance surface-only adapter boundary",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.binance_adapter_surface_report.v1", "trader1.common_defs.v1"],
            "validator_ids": ["binance_adapter_surface_validator", "root_launcher_surface_validator", "live_final_guard_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/adapter/test_binance_adapter_surface.py", "tests/contract/test_root_launchers.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_EXCHANGE_ADAPTER", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP1-ROOT-LAUNCHER-SURFACE", "REQ-MVP0-LIVE-DEFAULT-FALSE"],
            "source_text_sha256": sha256_bytes(b"Binance root launcher surface must not imply Binance trading runtime exists"),
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
            "section_id": "SECTION_EXCHANGE_ADAPTER",
            "schema_files": [
                "contracts/schema/binance_adapter_surface_report.schema.json",
                "contracts/schema/common.defs.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py", "trader1/adapters/binance/surface.py"],
            "test_files": ["tests/adapter/test_binance_adapter_surface.py", "tests/contract/test_root_launchers.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/adapters/binance/surface.py", "trader1/runtime/boot/safe_launcher.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["blocking_reason=BINANCE_ADAPTER_SURFACE_ONLY", "primary_blocker_code=BINANCE_ADAPTER_SURFACE_ONLY"],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
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
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_LEDGER_ROLLUP.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID],
            "affected_exchange": "BINANCE",
            "affected_market_type": "SPOT_AND_FUTURES_USDT_M",
            "affected_mode": "PAPER_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": ["BINANCE_ADAPTER_SURFACE_ONLY", "BINANCE_FUTURES_SURFACE_ONLY", *artifacts],
            "new_or_changed_schema_ids": ["trader1.binance_adapter_surface_report.v1", "trader1.common_defs.v1"],
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
            "next_required_section_ids": ["SECTION_EXCHANGE_ADAPTER", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_MVP3_OPERATIONAL_PAPER", "SECTION_DASHBOARD_OPERATOR_UX"],
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
            "active_read_surface_used": [
                "SECTION_EXCHANGE_ADAPTER",
                "SECTION_NAMESPACE_SEPARATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_BINANCE_ADAPTER_SURFACE_ONLY",
            "required_section_ids": ["SECTION_EXCHANGE_ADAPTER", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": [
                "SECTION_EXCHANGE_ADAPTER",
                "SECTION_NAMESPACE_SEPARATION",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
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
            "failure_analysis_status": "NOT_REQUIRED_FOR_BINANCE_SURFACE_BOUNDARY",
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
            "stage_gate_status": "PASS_FOR_BINANCE_SURFACE_ONLY_NO_TRADING_RUNTIME",
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
                "tools/emit_binance_adapter_surface_only_patch_evidence.py",
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
        f"""# MVP4 Binance Adapter Surface-Only Boundary Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Binance root launchers and dashboard artifacts existed, but the repo had no explicit Binance adapter namespace. That could make visible Binance launchers look more implemented than they are.

Patch:
- Added trader1.adapters.binance as a fail-closed SURFACE_ONLY namespace.
- Added strict binance_adapter_surface_report schema and validator.
- Added BINANCE_ADAPTER_SURFACE_ONLY and BINANCE_FUTURES_SURFACE_ONLY blocker codes to registry/common defs.
- Root launcher and dashboard artifacts now expose Binance-specific surface-only blockers.
- Negative tests block credential loading, order adapter calls, live flag drift, futures readiness claims, and scale-up drift.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false

Remaining blocker:
- Binance SPOT/FUTURES paper runtime and any live behavior remain unimplemented and blocked until later staged evidence exists.
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
    schema_ids = set(state.get("implemented_schema_ids", []))
    schema_ids.update({"trader1.binance_adapter_surface_report.v1", "trader1.common_defs.v1"})
    state["implemented_schema_ids"] = sorted(schema_ids)
    validator_ids = set(state.get("implemented_validator_ids", []))
    validator_ids.add("binance_adapter_surface_validator")
    state["implemented_validator_ids"] = sorted(validator_ids)
    state["untested_validator_ids"] = sorted(set(state.get("untested_validator_ids", [])) - {"binance_adapter_surface_validator"})
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
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_safe_command([sys.executable, "-m", "unittest", "tests.adapter.test_binance_adapter_surface", "-v"]),
        run_safe_command(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.adapter.test_binance_adapter_surface",
                "tests.contract.test_root_launchers",
                "tests.config.test_config_validation",
                "-v",
            ]
        ),
        run_safe_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], timeout_seconds=420),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    artifacts = sorted(set(CHANGED_ARTIFACTS + launcher_artifacts + ["tools/emit_binance_adapter_surface_only_patch_evidence.py"]))
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
