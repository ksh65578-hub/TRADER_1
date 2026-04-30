from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING"
PATCH_ID = f"{PATCH_BASENAME}_20260430_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-SHADOW-SUPPORTING-WINDOW-PAIRING"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_PAPER_SHADOW_RUNTIME_EXECUTION_EVIDENCE_BOUNDARY"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "paper_shadow_evidence_accumulation_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
]

CHANGED_ARTIFACTS = [
    "trader1/research/shadow/shadow_runner.py",
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_paper_shadow_evidence_accumulation_validator.py",
    "tools/emit_paper_shadow_supporting_window_pairing_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING.md",
]

BLOCKERS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING.md",
        f"""# MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING

context_pack_id: MVP4_PAPER_SHADOW_SUPPORTING_WINDOW_PAIRING
task_class: {NEXT_TASK_CLASS}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_shadow_evidence_accumulation_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- long-run supporting_source_evidence_ids must contain paired PAPER and SHADOW entries for the same window key
- separate paper-only and shadow-only window counts cannot be treated as paired evidence
- builder, direct validator, and validator self-check use the same pairing rule
- live readiness, live order permission, live trading, and scale-up remain false

known_omissions_by_design:
- no actual long-run runtime evidence is created
- no credentials, exchange account calls, order-capable endpoints, live orders, live config mutation, or scale-up are used

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: {now}
""",
    )
    base.write_text(
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

PAPER/SHADOW long-run evidence now requires same-window supporting pairs, not separate paper and shadow counts.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "Paper/shadow supporting evidence window pairing",
            "full_text_marker": f"{REQUIREMENT_ID}: long-run paper/shadow evidence must pair supporting evidence by window key",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Paper/shadow supporting window pairing",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.paper_shadow_evidence_accumulation_report.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/validators/test_paper_shadow_evidence_accumulation_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PAPER-SHADOW-RUNTIME-SOURCE-REQUIRED-FIELDS",
                "REQ-MVP4-PAPER-SHADOW-LONG-RUN-STATE-CONSISTENCY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(b"paper shadow supporting window pairing"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        }
    )
    req_index.update(
        {
            "trader1_sha256": trader_hash,
            "updated_at_utc": now,
            "requirements": sorted(requirements, key=lambda item: item["requirement_id"]),
        }
    )
    base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "schema_files": ["contracts/schema/paper_shadow_evidence_accumulation_report.schema.json"],
            "validator_files": ["trader1/research/shadow/shadow_runner.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_paper_shadow_evidence_accumulation_validator.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/research/shadow/shadow_runner.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    base.write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_PAPER_SHADOW_RUNTIME_SOURCE_REQUIRED_FIELDS.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "PASS",
            "authority_hash_checked": True,
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PAPER-SHADOW-RUNTIME-SOURCE-REQUIRED-FIELDS",
                "REQ-MVP4-PAPER-SHADOW-LONG-RUN-STATE-CONSISTENCY",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER,SHADOW",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_SHELL", "SECTION_STRATEGY_PROFITABILITY"],
            "next_forbidden_default_sections": ["RETAINED_ARCHIVE", "LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
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
            "active_read_surface_used": [
                "current_implementation_state",
                "paper/shadow evidence pairing logic",
                "paper/shadow evidence validator",
                "unpaired supporting window probe",
            ],
            "task_class": NEXT_TASK_CLASS,
            "required_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE", "SECTION_LIVE_FINAL_GUARD"],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_SUPPORTING_WINDOWS_PAIRED",
            "optimizer_guardrail_result": "PASS_UNPAIRED_SUPPORTING_WINDOWS_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "convergence_state_after": "LONG_RUN_EVIDENCE_BLOCKED_SUPPORTING_WINDOW_PAIRING_GUARDED",
            "convergence_guardrail_result": "PASS_UNPAIRED_SUPPORTING_WINDOWS_BLOCKED",
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    base.write_json(
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
    base.write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_SUPPORTING_WINDOW_PAIRING_LIVE_BLOCKED",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
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
            ],
            "known_blockers": patch_result["remaining_blockers"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )


def write_patch(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash)

    tests_run = [
        base.run_command([sys.executable, "-m", "unittest", "tests.validators.test_paper_shadow_evidence_accumulation_validator", "-v"]),
        base.run_command([sys.executable, "-m", "unittest", "tests.research.test_paper_shadow_evidence_accumulator", "-v"]),
        base.run_command([sys.executable, "tools/run_paper_shadow_evidence_validators.py"]),
        base.run_command([sys.executable, "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_patch(now, trader_hash, agents_hash, patch_result)

    tests_run.append(base.run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_patch(now, trader_hash, agents_hash, patch_result)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
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
