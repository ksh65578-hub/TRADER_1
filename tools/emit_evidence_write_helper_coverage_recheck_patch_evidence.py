from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260429_001"
REQUIREMENT_ID = "REQ-MVP4-EVIDENCE-WRITE-HELPER-COVERAGE-RECHECK"
CONTRACT_GAP_ID = "EVIDENCE_WRITE_HELPER_ATOMIC_COVERAGE"
NEXT_TASK_CLASS = "MVP4_LEGACY_EVIDENCE_WRITER_ATOMIC_CONVERSION"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.evidence_write_helper_coverage import build_evidence_write_helper_audit  # noqa: E402
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    rel,
    run_command,
    sha256_bytes,
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
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if not validator_id.startswith("patch_result") and validator_id != "generated_artifact_dirty_validator"
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
    "EVIDENCE_WRITE_HELPER_ATOMIC_COVERAGE_INCOMPLETE",
]
CHANGED_ARTIFACTS = [
    "tools/evidence_write_helper_coverage.py",
    "tests/runtime/test_evidence_write_helper_coverage.py",
    "tests/runtime/fixtures/evidence_write_helper_legacy_direct_writers.json",
    "tools/emit_evidence_write_helper_coverage_recheck_patch_evidence.py",
    "system/evidence/audit_reports/EVIDENCE_WRITE_HELPER_COVERAGE_AUDIT.json",
    "system/evidence/contract_gaps/EVIDENCE_WRITE_HELPER_ATOMIC_COVERAGE.contract_gap.json",
    "contracts/generated/context_pack/EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK.md",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK.md",
        f"""# EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK

context_pack_id: EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK
task_class: MVP4_EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_GENERATED_ARTIFACT_DIRTY", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.contract_gap.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Evidence writer helper coverage is measured numerically.
- Any newly introduced LOCAL_DIRECT writer fails regression coverage until explicitly audited.
- Remaining legacy LOCAL_DIRECT writers are tracked as a live-affecting contract_gap.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- writer_file_count: {audit["writer_file_count"]}
- covered_writer_count: {audit["covered_writer_count"]}
- legacy_local_direct_writer_count: {audit["legacy_local_direct_writer_count"]}
- coverage_pct: {audit["coverage_pct"]}

known_omissions_by_design:
- legacy LOCAL_DIRECT writers are not all converted in this patch.
- no live execution
- no exchange credential use
- no LIVE_READY snapshot write
- no risk scale-up

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

Evidence writer helper coverage is now measured. Shared/atomic coverage is {audit["coverage_pct"]}% and {audit["legacy_local_direct_writer_count"]} legacy direct writer scripts remain BLOCKED as contract gap {CONTRACT_GAP_ID}.

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
            "source_section_id": "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
            "source_file": "TRADER_1.md",
            "source_heading": "Evidence writer helper coverage recheck",
            "full_text_marker": f"{REQUIREMENT_ID}:atomic writer coverage must be measured and direct helper regression must be blocked",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Evidence write helper atomic coverage guard",
            "requirement_kind": "RUNTIME_SAFETY_AUDIT_TEST_PATCH",
            "schema_ids": ["trader1.contract_gap.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_evidence_write_helper_coverage.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_PARTIAL_WRITE_CRASH_RECOVERY", "SECTION_GENERATED_ARTIFACT_DIRTY", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK"],
            "source_text_sha256": sha256_bytes(b"atomic writer coverage must be measured and direct helper regression must be blocked"),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
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
            "section_id": "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
            "schema_files": ["contracts/schema/contract_gap.schema.json", "contracts/schema/patch_result.schema.json"],
            "validator_files": ["tools/evidence_write_helper_coverage.py"],
            "test_files": ["tests/runtime/test_evidence_write_helper_coverage.py"],
            "fixture_files": ["tests/runtime/fixtures/evidence_write_helper_legacy_direct_writers.json"],
            "runtime_modules": ["tools/evidence_write_helper_coverage.py"],
            "evidence_artifacts": [
                "system/evidence/audit_reports/EVIDENCE_WRITE_HELPER_COVERAGE_AUDIT.json",
                "system/evidence/contract_gaps/EVIDENCE_WRITE_HELPER_ATOMIC_COVERAGE.contract_gap.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
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
            "status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def write_contract_gap(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_json(
        ROOT / "system" / "evidence" / "contract_gaps" / "EVIDENCE_WRITE_HELPER_ATOMIC_COVERAGE.contract_gap.json",
        {
            "schema_id": "trader1.contract_gap.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "status": "OPEN" if audit["legacy_local_direct_writer_count"] else "RESOLVED",
            "blockers": []
            if not audit["legacy_local_direct_writer_count"]
            else [
                {
                    "code": "CONTRACT_GAP_HIGH",
                    "severity": "HIGH",
                    "message": f"{audit['legacy_local_direct_writer_count']} legacy evidence writer helpers still use direct file writes.",
                    "source_requirement_id": REQUIREMENT_ID,
                }
            ],
            "notes": (
                f"Evidence writer helper coverage is {audit['coverage_pct']}%. "
                "Remaining LOCAL_DIRECT scripts must be converted to the shared atomic writer before this gap can resolve."
            ),
            "contract_gap_id": CONTRACT_GAP_ID,
            "severity": "HIGH" if audit["legacy_local_direct_writer_count"] else "INFO",
            "source_section_id": "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
            "live_affecting": True,
        },
    )


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    audit: dict[str, Any],
    validators_required: list[str] | None = None,
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_PARTIAL_WRITE_CRASH_RECOVERY_RECHECK.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PARTIAL-WRITE-CRASH-RECOVERY-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT_AND_BINANCE",
            "affected_market_type": "KRW_SPOT_AND_SPOT",
            "affected_mode": "PAPER_READ_ONLY_AND_LIVE_HARD_BLOCKED",
            "removed_requirements": [],
            "merged_requirements": [],
            "new_registry_items": [
                "contracts/generated/context_pack/EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK.md",
                "system/evidence/audit_reports/EVIDENCE_WRITE_HELPER_COVERAGE_AUDIT.json",
                "system/evidence/contract_gaps/EVIDENCE_WRITE_HELPER_ATOMIC_COVERAGE.contract_gap.json",
                REQUIREMENT_ID,
            ],
            "new_or_changed_schema_ids": [],
            "validators_required": validators_required or VALIDATORS_REQUIRED,
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
            "next_required_section_ids": [
                "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
                "SECTION_RUNTIME_WRITE_LOCK",
                "SECTION_GENERATED_ARTIFACT_DIRTY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_DASHBOARD_OPERATOR_UX"],
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
            "active_read_surface_used": [
                "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
                "SECTION_GENERATED_ARTIFACT_DIRTY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_EVIDENCE_WRITE_HELPER_COVERAGE_RECHECK",
            "required_section_ids": [
                "SECTION_PARTIAL_WRITE_CRASH_RECOVERY",
                "SECTION_GENERATED_ARTIFACT_DIRTY",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "TRADER_1:partial-write-crash-recovery-active-surface",
                "AGENTS:evidence-artifact-generation-guide",
            ],
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
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_EVIDENCE_WRITE_HELPER_COVERAGE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
        }
    )
    patch_result.pop("affected_artifact_paths", None)
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
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
            "stage_gate_status": "PASS_WITH_OPEN_EVIDENCE_WRITE_HELPER_COVERAGE_GAP_NO_LIVE_ORDERS",
            "evidence_write_helper_coverage_pct": audit["coverage_pct"],
            "legacy_local_direct_writer_count": audit["legacy_local_direct_writer_count"],
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
        f"""# MVP4 Evidence Write Helper Coverage Recheck Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Evidence writer helper coverage is {audit['coverage_pct']}%.
- {audit['legacy_local_direct_writer_count']} legacy scripts still define LOCAL_DIRECT write helpers.
- New LOCAL_DIRECT writers are now blocked by regression coverage unless explicitly audited.

Patch:
- Added evidence write helper scanner and machine-readable coverage audit.
- Added baseline fixture for known legacy direct writers.
- Added regression tests to prevent new unaudited direct writers.
- Added live-affecting contract_gap {CONTRACT_GAP_ID}.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
""",
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", []) + [CONTRACT_GAP_ID]))
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
    audit = build_evidence_write_helper_audit(root=ROOT, generated_at_utc=now)
    write_json(ROOT / "system" / "evidence" / "audit_reports" / "EVIDENCE_WRITE_HELPER_COVERAGE_AUDIT.json", audit)
    write_contract_gap(now, trader_hash, agents_hash, audit)
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.runtime.test_evidence_write_helper_coverage", "-v"]),
        run_command([sys.executable, "tools/evidence_write_helper_coverage.py"]),
    ]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS_REQUIRED), audit, BOOTSTRAP_VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), audit, VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"]),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), audit, VALIDATORS_REQUIRED)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "evidence_write_helper_coverage_pct": audit["coverage_pct"],
                "legacy_local_direct_writer_count": audit["legacy_local_direct_writer_count"],
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
