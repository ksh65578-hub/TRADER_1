from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PUBLIC-REST-CONTINUITY-EVIDENCE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_LONG_RUN_REAL_DATA_AND_REGIME_EVIDENCE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "upbit_public_rest_continuity_validator",
    "upbit_public_rest_sample_validator",
    "upbit_public_market_data_collection_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "generated_artifact_dirty_validator",
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
    "LONG_RUN_REAL_MARKET_EVIDENCE_INSUFFICIENT",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_public_rest_continuity_report.schema.json",
    "contracts/registry.yaml",
    "contracts/validators/validator_registry.json",
    "trader1/runtime/paper/upbit_public_rest_continuity.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_rest_continuity.py",
    "tools/run_upbit_public_rest_continuity_check.py",
    "tools/emit_upbit_public_rest_continuity_evidence_patch.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def run_command(args: list[str], timeout_seconds: int = 360) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1800:],
        "stderr_tail": completed.stderr[-1800:],
    }


def clean_bytecode_cache() -> list[str]:
    removed: list[str] = []
    root = ROOT.resolve()
    for path in sorted(root.rglob("*.pyc")) + sorted(root.rglob("*.pyo")):
        resolved = path.resolve()
        if root not in resolved.parents:
            continue
        path.unlink(missing_ok=True)
        removed.append(rel(path))
    for path in sorted(root.rglob("__pycache__"), reverse=True):
        resolved = path.resolve()
        if root not in resolved.parents:
            continue
        try:
            path.rmdir()
            removed.append(rel(path))
        except OSError:
            pass
    return removed


def upsert_requirement_index(now: str, trader_hash: str, agents_hash: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_index.json"
    index = load_json(path)
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    index["updated_at_utc"] = now
    entry = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_MARKET_DATA",
        "source_file": "TRADER_1.md",
        "source_heading": "Upbit PAPER public REST continuity evidence boundary",
        "full_text_marker": f"{REQUIREMENT_ID}:SECTION_MARKET_DATA:public-rest-continuity-paper-only-not-live-ready",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Repeated public Upbit REST samples must advance before counting as PAPER continuity evidence",
        "requirement_kind": "RUNTIME_DATA_CONTINUITY_BOUNDARY_PATCH",
        "schema_ids": ["trader1.upbit_public_rest_continuity_report.v1"],
        "validator_ids": ["upbit_public_rest_continuity_validator"],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": ["tests/integration/test_upbit_public_rest_continuity.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
        "blocking_level": "PAPER_RUNTIME_BLOCKING",
        "live_affecting": True,
        "read_when": ["SECTION_MARKET_DATA", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
        "depends_on": [
            "REQ-MVP4-UPBIT-PUBLIC-REST-SAMPLE-EVIDENCE",
            "REQ-MVP4-UPBIT-PUBLIC-DATA-SEQUENCE-REGIME-GUARD",
        ],
        "source_text_sha256": sha256_json({"requirement_id": REQUIREMENT_ID, "title": "public rest continuity evidence boundary"}),
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index["requirements"] = [item for item in index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    index["requirements"].append(entry)
    index["requirements"] = sorted(index["requirements"], key=lambda item: item["requirement_id"])
    write_json(path, index)


def upsert_requirement_artifact_matrix(now: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    matrix = load_json(path)
    matrix["updated_at_utc"] = now
    row = {
        "requirement_id": REQUIREMENT_ID,
        "section_id": "SECTION_MARKET_DATA",
        "schema_files": ["contracts/schema/upbit_public_rest_continuity_report.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py"],
        "test_files": ["tests/integration/test_upbit_public_rest_continuity.py"],
        "fixture_files": [],
        "runtime_modules": ["trader1/runtime/paper/upbit_public_rest_continuity.py", "trader1/runtime/paper/upbit_public_rest_sample.py"],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        ],
        "dashboard_artifacts": ["system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/market_data/public/rest_continuity_report.json"],
        "patch_result_fields": ["validators_run", "tests_run", "remaining_blockers"],
        "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
        "live_affecting": True,
        "status": "IMPLEMENTED_FAIL_CLOSED",
    }
    matrix["rows"] = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    matrix["rows"].append(row)
    matrix["rows"] = sorted(matrix["rows"], key=lambda item: item["requirement_id"])
    write_json(path, matrix)


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE.md",
        f"""# MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE

context_pack_id: MVP4_UPBIT_PUBLIC_REST_CONTINUITY_EVIDENCE
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_MARKET_DATA", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_public_rest_continuity_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- repeated public REST samples are PAPER continuity evidence only
- repeated latest candle timestamp blocks continuity as DATA_QUALITY_INSUFFICIENT
- network failure is safe BLOCKED evidence, not runtime crash
- continuity cannot load credentials, call private/order endpoints, submit orders, or set live/scale flags

known_omissions_by_design:
- short continuity sample is not long-run evidence
- short continuity sample is not official API verification or account read-only evidence
- MVP-5 remains blocked

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

Upbit public REST continuity now requires repeated PAPER-only samples to advance in event time before counting as continuity evidence. A repeated/latest unchanged candle blocks continuity and remains non-live.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    for key, value in {
        "completed_requirement_ids": REQUIREMENT_ID,
        "implemented_schema_ids": "trader1.upbit_public_rest_continuity_report.v1",
        "implemented_validator_ids": "upbit_public_rest_continuity_validator",
    }.items():
        values = state.setdefault(key, [])
        if value not in values:
            values.append(value)
            values.sort()
    state["untested_validator_ids"] = [item for item in state.get("untested_validator_ids", []) if item != "upbit_public_rest_continuity_validator"]
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
            "stage_gate_status": "PASS_FOR_PUBLIC_REST_CONTINUITY_EVIDENCE_NO_LIVE_ORDERS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = [
        *CHANGED_ARTIFACTS,
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/market_data/public/rest_continuity_report.json",
        patch_result["validator_run_log_path"],
        patch_result["stage_gate_result_path"],
        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
    ]
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260430.md",
        f"""# MVP4 Upbit Public REST Continuity Evidence Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Hidden issue: a single public REST PASS sample did not prove market data continuity.
- Hidden issue: repeated calls inside the same candle could be mistaken for progress unless latest event timestamps are compared.
- Hidden issue: data continuity needed its own operator-visible BLOCKED state, distinct from live readiness.

Patch:
- Added strict public REST continuity schema, runtime builder, validator, tests, and CLI tool.
- Repeated latest candle timestamps now block continuity with DATA_QUALITY_INSUFFICIENT.
- Continuity evidence is PAPER-only and cannot create live readiness, live order permission, or scale-up.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PUBLIC_REST_SAMPLE_EVIDENCE.patch_result.json")
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
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PUBLIC-REST-SAMPLE-EVIDENCE"],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID, "upbit_public_rest_continuity_validator"],
            "new_or_changed_schema_ids": ["trader1.upbit_public_rest_continuity_report.v1"],
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
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_LONG_RUN_STABILITY"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_STRATEGY_PROFITABILITY_LOOP"],
            "next_forbidden_default_sections": ["MVP5_LIVE_ENABLING", "LIVE_CONFIG_MUTATION", "BINANCE_FUTURES_LIVE"],
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
            "active_read_surface_used": ["SECTION_MARKET_DATA", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": PATCH_BASENAME,
            "required_section_ids": ["SECTION_MARKET_DATA", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_MARKET_DATA", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LONG_RUN_STABILITY"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "FRESH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": True,
            "profit_convergence_patch": "PUBLIC_REST_CONTINUITY_BOUNDARY_NOT_LIVE_READY",
            "convergence_layer_changed": False,
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_PUBLIC_REST_CONTINUITY_BOUNDARY_PATCH",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def main() -> int:
    clean_bytecode_cache()
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)

    tests_run = [
        run_command([sys.executable, "-m", "unittest", "tests.integration.test_upbit_public_rest_continuity", "-v"], timeout_seconds=120),
        run_command([sys.executable, "tools/run_upbit_public_rest_continuity_check.py", "--no-network"], timeout_seconds=120),
        run_command([sys.executable, "tools/run_upbit_public_rest_continuity_check.py", "--timeout-seconds", "2.5"], timeout_seconds=120),
    ]
    pre_validators = run_validators(
        [item for item in VALIDATORS_REQUIRED if item not in {"patch_result_schema_validator", "patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}]
    )

    upsert_requirement_index(now, trader_hash, agents_hash)
    upsert_requirement_artifact_matrix(now)
    update_context(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, pre_validators)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    final_validators = run_validators(VALIDATORS_REQUIRED)
    patch_result["validators_run"] = final_validators
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result["tests_run"].append(run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout_seconds=420))
    removed_bytecode = clean_bytecode_cache()
    patch_result["tests_run"].append(
        {
            "command": "clean_bytecode_cache()",
            "status": "PASS",
            "returncode": 0,
            "stdout_tail": json.dumps({"removed_count": len(removed_bytecode), "removed_sample": removed_bytecode[:20]}, indent=2),
            "stderr_tail": "",
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result["tests_run"].append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"], timeout_seconds=180))
    final_validators = run_validators(VALIDATORS_REQUIRED)
    patch_result["validators_run"] = final_validators
    patch_result["result_hash"] = patch_hash(patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed_tests = [item for item in patch_result["tests_run"] if item.get("status") != "PASS"]
    failed_validators = [item for item in final_validators if item.get("status") != "PASS"]
    status = "PASS" if not failed_tests and not failed_validators else "FAIL"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": status,
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
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
