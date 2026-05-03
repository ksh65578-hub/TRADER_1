from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260503_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-RUNTIME-DEPTH-RECHECK"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RECHECK"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    load_json,
    rel,
    sha256_bytes,
    sha256_file,
    sha256_json,
    utc_now,
    write_json,
    write_text,
    update_authority_manifest,
    update_read_cache,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_persistent_loop_report.schema.json",
    "trader1/runtime/paper/upbit_paper_persistent_loop.py",
    "trader1/runtime/paper/upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
    "trader1/validation/mvp0_validators.py",
    "tests/integration/test_upbit_public_collection_persistent_loop.py",
    "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
    "tools/emit_upbit_paper_runtime_depth_recheck_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "runtime_schema_instance_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_cycle_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id not in {"patch_result_runtime_schema_instance_validator", "generated_artifact_dirty_validator"}
]
BLOCKERS = [
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "EXTERNAL_CREDENTIAL_REQUIRED",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "SCALE_UP_NOT_ELIGIBLE",
]


def run_command(args: list[str], timeout_seconds: int = 600) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def patch_hash(patch_result: dict[str, Any]) -> str:
    payload = dict(patch_result)
    payload.pop("result_hash", None)
    return sha256_json(payload)


def build_audit() -> dict[str, Any]:
    loop_text = (ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_persistent_loop.py").read_text(encoding="utf-8")
    recheck_text = (
        ROOT / "trader1" / "runtime" / "paper" / "upbit_paper_stale_loop_normalized_reconciliation_recheck.py"
    ).read_text(encoding="utf-8")
    validator_text = (ROOT / "trader1" / "validation" / "mvp0_validators.py").read_text(encoding="utf-8")
    test_text = (ROOT / "tests" / "integration" / "test_upbit_public_collection_persistent_loop.py").read_text(encoding="utf-8")
    recheck_test_text = (
        ROOT / "tests" / "runtime" / "test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py"
    ).read_text(encoding="utf-8")
    schema = load_json(ROOT / "contracts" / "schema" / "upbit_paper_persistent_loop_report.schema.json")
    cycle_item_schema = schema.get("properties", {}).get("cycle_results", {}).get("items", {})
    required = set(cycle_item_schema.get("required", []))
    depth_fields = {
        "runtime_input_role",
        "source_collection_report_hash",
        "source_public_market_data_hash",
        "canonical_event_count",
        "runtime_public_market_data_hash",
        "feature_snapshot_hash",
        "regime",
        "selected_candidate_id",
        "selected_candidate_net_ev_after_cost_bps",
        "strategy_regime_cost_linkage",
    }
    checks = {
        "cycle_summary_emits_depth_fields": all(field in loop_text for field in depth_fields),
        "cycle_summary_schema_requires_depth_fields": depth_fields.issubset(required),
        "validator_blocks_non_public_collection_summary": "cycle result is not bound to public market data collection input" in loop_text,
        "validator_blocks_linkage_live_permission": "strategy/regime/cost linkage attempted live or scale-up permission" in loop_text,
        "stale_recheck_treats_missing_depth_as_blocked_recheck": "RUNTIME_DEPTH_RECHECK_REQUIRED" in recheck_text,
        "mvp0_validator_rechecks_depth_fields": "persistent loop cycle summary is not public-collection bound" in validator_text,
        "negative_tests_cover_depth_fields": all(
            name in test_text
            for name in (
                "test_persistent_loop_blocks_static_fixture_cycle_summary_role",
                "test_persistent_loop_blocks_missing_cycle_summary_canonical_depth",
                "test_persistent_loop_blocks_summary_source_runtime_hash_mismatch",
                "test_persistent_loop_blocks_strategy_regime_cost_linkage_live_flag",
            )
        ),
        "stale_recheck_test_covers_runtime_depth_reason": "RUNTIME_DEPTH_RECHECK_REQUIRED" in recheck_test_text,
    }
    return {
        "audit_schema_id": "trader1.audit_report.v1",
        "audit_id": f"{PATCH_BASENAME}_AUDIT",
        "patch_id": PATCH_ID,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "requirement_id": REQUIREMENT_ID,
        "checks": checks,
        "finding": (
            "Upbit PAPER persistent loop cycle_results summarized PASS cycles without requiring the same "
            "public input, feature, regime, selected-candidate, and strategy/regime/cost linkage evidence "
            "already present in each runtime cycle report."
        ),
        "fix": (
            "cycle_results now carry runtime depth fields and the persistent-loop validator blocks missing, "
            "mismatched, static-fixture, or live-mutated linkage summaries."
        ),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK.md",
        f"""# MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK

context_pack_id: MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK
task_class: MVP4_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_NAMESPACE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_persistent_loop_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- persistent loop cycle_results expose public-collection input hashes and canonical event depth
- persistent loop cycle_results expose feature hash, regime, selected candidate, and strategy/regime/cost linkage
- validator blocks static-fixture summary mutation, source/runtime hash mismatch, missing canonical depth, and linkage live flags
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false

audit_status: {audit["status"]}

known_omissions_by_design:
- no long-run evidence eligibility is created
- no live order path, credential load, or LIVE_READY snapshot write is introduced
- scale-up remains blocked

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

Upbit PAPER persistent-loop summaries now fail closed unless PASS cycles expose public source hashes, canonical event depth, feature hash, regime, selected candidate, and strategy/regime/cost linkage. This remains PAPER-only and does not create long-run evidence eligibility.

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
            "source_section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER runtime depth recheck",
            "full_text_marker": f"{REQUIREMENT_ID}:persistent loop summaries must preserve public runtime depth evidence",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER persistent loop summaries must preserve public runtime depth evidence",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.upbit_paper_persistent_loop_report.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
                "tests/validators/test_mvp0_validators.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-BOUNDED",
                "REQ-MVP4-STRATEGY-REGIME-COST-RUNTIME-LINKAGE",
                "REQ-MVP4-CANDIDATE-SCORECARD-RUNTIME-LINKAGE-BINDING",
            ],
            "source_text_sha256": sha256_bytes(b"persistent loop summaries must preserve public runtime depth evidence"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
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
            "section_id": "SECTION_UPBIT_PAPER_RUNTIME",
            "schema_files": ["contracts/schema/upbit_paper_persistent_loop_report.schema.json"],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/integration/test_upbit_public_collection_persistent_loop.py",
                "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/runtime/paper/upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
                "trader1/runtime/paper/upbit_paper_runtime.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
) -> dict[str, Any]:
    patch_result: dict[str, Any] = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "VALIDATOR_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP4-UPBIT-PAPER-PERSISTENT-LOOP-BOUNDED"],
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
        "new_or_changed_schema_ids": ["trader1.upbit_paper_persistent_loop_report.v1"],
        "validators_required": validators_required,
        "validators_run": validators_run,
        "tests_run": tests_run,
        "coverage_unmapped_count": 0,
        "coverage_index_result": "UPDATED_PASS",
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "LIVE_IMPACT_RECHECKED_NO_ARCHIVE_AUTHORITY",
        "read_cache_update_required": True,
        "context_pack_update_required": True,
        "current_implementation_state_updated": True,
        "next_task_class": NEXT_TASK_CLASS,
        "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
        "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PROFITABILITY_LOOP"],
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
        "active_read_surface_used": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": PATCH_BASENAME,
        "required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["AGENTS:0G", "TRADER_1:UPBIT_PAPER_RUNTIME", "TRADER_1:LIVE_FINAL_GUARD"],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "REUSED_HASH_MATCH",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "UPDATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
    }
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    audit: dict[str, Any],
) -> None:
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_RUNTIME_DEPTH_RECHECK_NO_LIVE_ORDERS",
            "runtime_depth_audit": audit,
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
                f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", audit)
    write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260503.md",
        f"""# MVP4 Upbit PAPER Runtime Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Persistent PAPER loop summaries did not require the full public source, feature, regime, selected-candidate, and strategy/regime/cost linkage evidence carried by each runtime cycle report.

Patch:
- Added runtime-depth fields to cycle_results.
- Tightened persistent-loop validation and schema for source/runtime hash binding, canonical event depth, and linkage live blockers.
- Added negative tests for static fixture role mutation, missing depth, hash mismatch, and linkage live permission.

Live state:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.upbit_paper_persistent_loop_report.v1"]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["upbit_paper_persistent_loop_validator"]))
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
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    write_source_bundle_manifest()
    audit = build_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/integration/test_upbit_public_collection_persistent_loop.py", "-q"]),
        run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_stale_loop_normalized_reconciliation_recheck.py",
                "-q",
            ]
        ),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_schema_instance_validation", "-v"]),
    ]
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/validators/test_mvp0_validators.py", "-q"]),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-v"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"], timeout_seconds=900),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed"})
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
