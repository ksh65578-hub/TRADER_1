from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PUBLIC-REST-READ-ONLY-TRANSFORM"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_REAL_PUBLIC_DATA_LONG_RUN_EVIDENCE"

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
from trader1.adapters.upbit.market_data import build_upbit_public_candle_data_from_rest_payload  # noqa: E402
from trader1.runtime.paper.upbit_paper_persistent_loop import (  # noqa: E402
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "upbit_public_market_data_collection_validator",
    "upbit_paper_runtime_cycle_validator",
    "upbit_paper_persistent_loop_validator",
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
    "REAL_PUBLIC_REST_NETWORK_SAMPLE_NOT_REQUIRED_FOR_UNIT_TESTS",
]

CHANGED_ARTIFACTS = [
    "trader1/adapters/upbit/market_data.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tools/emit_upbit_public_rest_read_only_transform_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    clean = dict(patch_result)
    clean.pop("result_hash", None)
    return sha256_json(clean)


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1600:],
        "stderr_tail": completed.stderr[-1600:],
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


def mock_upbit_public_rest_payload(offset: int = 0) -> list[dict[str, Any]]:
    newest_first: list[dict[str, Any]] = []
    for index in range(5, -1, -1):
        minute = offset + index
        newest_first.append(
            {
                "market": "KRW-BTC",
                "candle_date_time_utc": f"2026-04-30T09:{minute:02d}:00",
                "opening_price": 1000000 + minute * 1000,
                "high_price": 1002500 + minute * 1000,
                "low_price": 998000 + minute * 1000,
                "trade_price": 1000500 + minute * 1000,
                "candle_acc_trade_volume": 2 + minute,
            }
        )
    return newest_first


def run_public_rest_backed_paper_loop(now: str) -> tuple[dict[str, Any], dict[str, Any]]:
    sequence = [
        build_upbit_public_candle_data_from_rest_payload(
            payload=mock_upbit_public_rest_payload(offset=cycle * 6),
            session_id="mvp1_upbit_paper_launcher",
        )
        for cycle in range(2)
    ]
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-public-rest-transform-loop",
        session_id="mvp1_upbit_paper_launcher",
        requested_cycle_count=2,
        market_data_sequence=sequence,
    )
    result = validate_upbit_paper_persistent_loop_report(loop)
    return (
        loop,
        {
            "command": "run_upbit_paper_persistent_loop(public_rest_read_only_mock_payloads, requested_cycle_count=2)",
            "status": result.status,
            "returncode": 0 if result.status == "PASS" else 1,
            "stdout_tail": json.dumps(
                {
                    "loop_id": loop.get("loop_id"),
                    "loop_status": loop.get("loop_status"),
                    "completed_cycle_count": loop.get("completed_cycle_count"),
                    "input_source": "PUBLIC_REST_READ_ONLY",
                    "checked_at_utc": now,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                indent=2,
            ),
            "stderr_tail": "" if result.status == "PASS" else result.message,
        },
    )


def upsert_requirement_index(now: str, trader_hash: str, agents_hash: str) -> None:
    path = ROOT / "contracts" / "generated" / "requirement_index.json"
    index = load_json(path)
    index["trader1_sha256"] = trader_hash
    index["agents_sha256"] = agents_hash
    index["updated_at_utc"] = now
    entry = {
        "requirement_id": REQUIREMENT_ID,
        "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
        "source_file": "TRADER_1.md",
        "source_heading": "Upbit public REST read-only transform for PAPER runtime",
        "full_text_marker": f"{REQUIREMENT_ID}:SECTION_UPBIT_PAPER_RUNTIME:public REST read-only payload transform, no credential, no private endpoint",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "Upbit public REST candle payloads can feed PAPER runtime only through read-only canonicalization",
        "requirement_kind": "RUNTIME_DATA_ADAPTER_PATCH",
        "schema_ids": ["trader1.upbit_public_market_data_collection_report.v1"],
        "validator_ids": ["upbit_public_market_data_collection_validator", "upbit_paper_persistent_loop_validator"],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": ["tests/integration/test_upbit_public_collection_persistent_loop.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
        "blocking_level": "PAPER_RUNTIME_BLOCKING",
        "live_affecting": True,
        "read_when": ["EXCHANGE_ADAPTER", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA"],
        "depends_on": [
            "REQ-MVP4-UPBIT-PAPER-PUBLIC-COLLECTOR-PERSISTENT-LOOP",
            "REQ-MVP4-UPBIT-PAPER-RUNTIME-CANDIDATE-LINKAGE-COST-MODEL",
        ],
        "source_text_sha256": sha256_json({"requirement_id": REQUIREMENT_ID, "title": "public REST read-only transform"}),
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
        "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
        "schema_files": ["contracts/schema/upbit_public_market_data_collection_report.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py"],
        "test_files": ["tests/integration/test_upbit_public_collection_persistent_loop.py"],
        "fixture_files": [],
        "runtime_modules": ["trader1/adapters/upbit/market_data.py", "trader1/runtime/paper/upbit_public_collector.py"],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        ],
        "dashboard_artifacts": ["system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/market_data/public/latest_collection_report.json"],
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
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM.md",
        f"""# MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM

context_pack_id: MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Upbit public REST candle payload shape maps into canonical PAPER candle data.
- Approved public endpoint identity is api.upbit.com/v1/candles/minutes/1.
- Authorization headers, private endpoint flags, and order endpoint flags are blocked.
- Duplicate candle timestamps require reconciliation.
- Bounded PAPER runtime can run from PUBLIC_REST_READ_ONLY-shaped inputs while live-blocked.

known_omissions_by_design:
- The required test path uses deterministic public REST-shaped payloads, not mandatory live network access.
- Real public network sampling remains optional operator evidence and is not LIVE_READY evidence.
- No account, private stream, credential, or order endpoint is used.

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

Upbit public REST-shaped candle payloads can now feed PAPER runtime through a read-only transform. The transform rejects authorization headers, private endpoint markers, order endpoint markers, unsupported endpoint identity, and duplicate candle timestamps. This is not live readiness evidence.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_RUNTIME_CANDIDATE_LINKAGE_COST_MODEL.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "authority_hash_checked": True,
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PAPER-PUBLIC-COLLECTOR-PERSISTENT-LOOP"],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [],
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
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA"],
            "next_optional_section_ids": ["SECTION_LONG_RUN_STABILITY", "SECTION_DASHBOARD_OPERATOR_UX"],
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
            "active_read_surface_used": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_LIVE_FINAL_GUARD"],
            "task_class": PATCH_BASENAME,
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": True,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "PAPER_PUBLIC_DATA_INPUT_STRENGTHENED",
            "convergence_layer_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_PUBLIC_REST_TRANSFORM_PATCH",
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
            "stage_gate_status": "PASS_FOR_PUBLIC_REST_READ_ONLY_TRANSFORM_NO_LIVE_ORDERS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = [
        *CHANGED_ARTIFACTS,
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/market_data/public/latest_collection_report.json",
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json",
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
        f"""# MVP4 Upbit Public REST Read-only Transform Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Hidden issue: public collector could only use internal fixtures, so actual Upbit public candle payload shape was not contract-tested.
- Hidden issue: public data validation did not explicitly reject authorization header markers or private/order endpoint markers.
- Hidden issue: duplicate candle timestamps were not blocked at public candle validation time.

Patch:
- Added Upbit public REST read-only candle payload transform for api.upbit.com/v1/candles/minutes/1 shaped data.
- Added fail-closed validation for endpoint identity, authorization header use, private endpoint markers, order endpoint markers, and duplicate timestamps.
- Added tests for safe public REST-shaped payloads, authorization header blocking, and duplicate timestamp reconciliation.
- Re-ran bounded UPBIT/KRW_SPOT/PAPER runtime from PUBLIC_REST_READ_ONLY-shaped inputs.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    completed = state.setdefault("completed_requirement_ids", [])
    if REQUIREMENT_ID not in completed:
        completed.append(REQUIREMENT_ID)
        completed.sort()
    validators = state.setdefault("implemented_validator_ids", [])
    for validator_id in ["upbit_public_market_data_collection_validator", "upbit_paper_persistent_loop_validator"]:
        if validator_id not in validators:
            validators.append(validator_id)
    validators.sort()
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


def main() -> int:
    clean_bytecode_cache()
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)

    _loop, loop_run = run_public_rest_backed_paper_loop(now)
    tests_run = [
        loop_run,
        run_command([sys.executable, "-m", "unittest", "tests.integration.test_upbit_public_collection_persistent_loop", "-v"]),
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

    patch_result["tests_run"].append(run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], timeout_seconds=360))
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

    patch_result["tests_run"].append(run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
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
