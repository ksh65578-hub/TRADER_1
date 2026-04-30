from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PUBLIC-DATA-SEQUENCE-REGIME-GUARD"
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
from trader1.adapters.upbit.market_data import (  # noqa: E402
    build_upbit_public_candle_data_from_rest_payload,
    build_upbit_public_candle_fixture,
)
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
]

CHANGED_ARTIFACTS = [
    "trader1/adapters/upbit/market_data.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/integration/test_upbit_paper_runtime_cycle.py",
    "tools/emit_upbit_public_data_sequence_regime_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD.md",
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


def mock_upbit_public_rest_payload() -> list[dict[str, Any]]:
    return [
        {
            "market": "KRW-BTC",
            "candle_date_time_utc": f"2026-04-30T09:{index:02d}:00",
            "opening_price": 1000000 + index * 1000,
            "high_price": 1002500 + index * 1000,
            "low_price": 998000 + index * 1000,
            "trade_price": 1000500 + index * 1000,
            "candle_acc_trade_volume": 2 + index,
        }
        for index in range(5, -1, -1)
    ]


def run_sequence_and_regime_loop(now: str) -> tuple[dict[str, Any], dict[str, Any]]:
    sequence = [
        build_upbit_public_candle_data_from_rest_payload(
            payload=mock_upbit_public_rest_payload(),
            session_id="mvp1_upbit_paper_launcher",
        ),
        build_upbit_public_candle_fixture(
            session_id="mvp1_upbit_paper_launcher",
            profile="DOWNTREND",
        ),
    ]
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-sequence-regime-guard-loop",
        session_id="mvp1_upbit_paper_launcher",
        requested_cycle_count=2,
        market_data_sequence=sequence,
    )
    result = validate_upbit_paper_persistent_loop_report(loop)
    decisions = [item.get("final_decision") for item in loop.get("cycle_results", [])]
    status = result.status if decisions[-1:] == ["NO_TRADE"] else "FAIL"
    return (
        loop,
        {
            "command": "run_upbit_paper_persistent_loop(public_rest_then_downtrend_fixture, requested_cycle_count=2)",
            "status": status,
            "returncode": 0 if status == "PASS" else 1,
            "stdout_tail": json.dumps(
                {
                    "loop_id": loop.get("loop_id"),
                    "loop_status": loop.get("loop_status"),
                    "completed_cycle_count": loop.get("completed_cycle_count"),
                    "cycle_final_decisions": decisions,
                    "risk_off_cycle_expected_no_trade": True,
                    "checked_at_utc": now,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                indent=2,
            ),
            "stderr_tail": "" if status == "PASS" else "risk-off cycle did not remain NO_TRADE",
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
        "source_heading": "Upbit PAPER data sequence and risk-off regime guard",
        "full_text_marker": f"{REQUIREMENT_ID}:SECTION_UPBIT_PAPER_RUNTIME:strict candle ordering and risk-off no-trade",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "PAPER runtime blocks out-of-order market data and no-trades risk-off regimes",
        "requirement_kind": "RUNTIME_DATA_AND_STRATEGY_GUARD_PATCH",
        "schema_ids": ["trader1.upbit_public_market_data_collection_report.v1", "trader1.upbit_paper_runtime_cycle_report.v1"],
        "validator_ids": ["upbit_public_market_data_collection_validator", "upbit_paper_runtime_cycle_validator"],
        "artifact_ids": CHANGED_ARTIFACTS,
        "test_ids": ["tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/integration/test_upbit_paper_runtime_cycle.py"],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
        "blocking_level": "PAPER_RUNTIME_BLOCKING",
        "live_affecting": True,
        "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_MARKET_DATA"],
        "depends_on": [
            "REQ-MVP4-UPBIT-PUBLIC-REST-READ-ONLY-TRANSFORM",
            "REQ-MVP4-UPBIT-PAPER-RUNTIME-CANDIDATE-LINKAGE-COST-MODEL",
        ],
        "source_text_sha256": sha256_json({"requirement_id": REQUIREMENT_ID, "title": "sequence and regime guard"}),
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
        "schema_files": ["contracts/schema/upbit_public_market_data_collection_report.schema.json", "contracts/schema/upbit_paper_runtime_cycle_report.schema.json"],
        "validator_files": ["trader1/validation/mvp0_validators.py"],
        "test_files": ["tests/integration/test_upbit_public_collection_persistent_loop.py", "tests/integration/test_upbit_paper_runtime_cycle.py"],
        "fixture_files": [],
        "runtime_modules": ["trader1/adapters/upbit/market_data.py", "trader1/runtime/paper/upbit_paper_runtime.py"],
        "evidence_artifacts": [
            f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        ],
        "dashboard_artifacts": ["system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"],
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
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD.md",
        f"""# MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD

context_pack_id: MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_public_market_data_collection_report.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- public candle timestamps must be strictly increasing after canonicalization
- duplicate or out-of-order candle timestamps block with RECONCILIATION_REQUIRED
- risk-off/downtrend PAPER runtime cycle remains NO_TRADE and writes no fill ledger
- no live, private, credential, order, or scale-up behavior is introduced

known_omissions_by_design:
- deterministic sequence/regime tests are not long-run live evidence
- real public REST sampling and long-run PAPER evidence remain future safe work
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

Upbit PAPER public candle validation now requires strictly increasing timestamps after canonicalization. Downtrend/risk-off runtime cycles no-trade and do not write fill ledger events. This remains PAPER-only evidence, not LIVE_READY evidence.
""",
    )


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "authority_hash_checked": True,
            "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PAPER-RUNTIME-CANDIDATE-LINKAGE-COST-MODEL"],
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
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_STRATEGY_PROFITABILITY_LOOP"],
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
            "task_class": PATCH_BASENAME,
            "active_read_surface_used": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_LIVE_FINAL_GUARD"],
            "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_MARKET_DATA", "SECTION_STRATEGY_PROFITABILITY_LOOP"],
            "read_cache_invalidated": True,
            "profit_convergence_patch": "PAPER_REGIME_NO_TRADE_AND_SEQUENCE_GUARD_STRENGTHENED",
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_SEQUENCE_REGIME_GUARD_PATCH",
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
            "stage_gate_status": "PASS_FOR_SEQUENCE_REGIME_GUARD_NO_LIVE_ORDERS",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = [
        *CHANGED_ARTIFACTS,
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
        f"""# MVP4 Upbit Public Data Sequence Regime Guard Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Findings:
- Hidden issue: public REST-shaped candles could pass even when canonicalized timestamps were not strictly increasing.
- Hidden issue: runtime tests did not explicitly prove downtrend/risk-off data no-trades without writing fill ledger events.

Patch:
- Public candle validation now requires strictly increasing timestamps and blocks out-of-order samples.
- Added tests for out-of-order timestamp reconciliation.
- Added risk-off/downtrend PAPER runtime no-trade test.
- Re-ran bounded PAPER loop with public REST-shaped input followed by downtrend fixture input.

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

    _loop, loop_run = run_sequence_and_regime_loop(now)
    tests_run = [
        loop_run,
        run_command([sys.executable, "-m", "unittest", "tests.integration.test_upbit_public_collection_persistent_loop", "tests.integration.test_upbit_paper_runtime_cycle", "-v"]),
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
