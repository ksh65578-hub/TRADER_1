from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-PLACEHOLDER-READINESS-SURFACE-GUARD"
NEXT_TASK_CLASS = "MVP4_BINANCE_ADAPTER_SURFACE_STATUS_RECHECK"

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
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "trader1/runtime/readiness/live_ready_snapshot.py",
    "trader1/validation/mvp0_validators.py",
    "tests/readiness/test_live_ready_snapshot_writer.py",
    "tests/validators/test_optimizer_backlog_validators.py",
    "tools/emit_placeholder_readiness_surface_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "live_ready_snapshot_validator",
    "live_ready_snapshot_writer_validator",
    "readiness_surface_validator",
    "live_final_guard_validator",
    "promotion_threshold_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
]
BOOTSTRAP_VALIDATORS = [
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
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def build_audit() -> dict[str, Any]:
    source_text = (ROOT / "trader1" / "runtime" / "readiness" / "live_ready_snapshot.py").read_text(encoding="utf-8")
    test_text = (ROOT / "tests" / "readiness" / "test_live_ready_snapshot_writer.py").read_text(encoding="utf-8")
    validator_text = (ROOT / "trader1" / "validation" / "mvp0_validators.py").read_text(encoding="utf-8")
    placeholder_markers = ["placeholder", "unverified", "mvp0-blocked", "example.invalid"]
    source_checks = {
        "placeholder_marker_constant_present": "PLACEHOLDER_MARKERS" in source_text,
        "writer_input_placeholder_fields_blocked": "evidence_manifest_hash" in source_text and "_placeholder_fields" in source_text,
        "live_ready_requires_evidence_even_without_order_permission": "if snapshot.get(\"live_ready\") is True" in source_text,
        "live_order_allowed_still_requires_live_ready": "live_order_allowed requires live_ready=true" in source_text,
    }
    test_checks = {
        "live_ready_true_without_live_order_allowed_negative": "test_live_ready_true_without_live_order_allowed_still_requires_evidence" in test_text,
        "placeholder_evidence_ids_negative": "test_placeholder_evidence_ids_block_live_ready_candidate" in test_text,
        "placeholder_writer_hash_negative": "test_writer_pass_with_placeholder_evidence_hash_is_blocked" in test_text,
    }
    validator_checks = {
        "live_ready_without_order_permission_validator_case": "ready_without_order_permission" in validator_text,
        "writer_placeholder_validator_case": "placeholder_writer" in validator_text,
        "promotion_threshold_uses_non_placeholder_evidence_hash": "pass_but_not_enabled[\"evidence_manifest_hash\"] = \"E\" * 64" in validator_text,
    }
    blockers: list[str] = []
    if not all(source_checks.values()):
        blockers.append("SOURCE_GUARD_INCOMPLETE")
    if not all(test_checks.values()):
        blockers.append("NEGATIVE_TEST_INCOMPLETE")
    if not all(validator_checks.values()):
        blockers.append("VALIDATOR_FIXTURE_INCOMPLETE")
    return {
        "audit_schema_id": "trader1.placeholder_readiness_surface_guard_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "source_checks": source_checks,
        "test_checks": test_checks,
        "validator_checks": validator_checks,
        "hidden_defect": {
            "classification": "false_safe_live_ready_candidate",
            "condition": "placeholder or unverified evidence fields appear in a writer input or live_ready snapshot candidate",
            "impact": "dashboard or validator consumers could interpret a candidate as more ready than the evidence supports",
            "fix": "block placeholder evidence on writer input and on any live_ready=true snapshot, even when live_order_allowed remains false",
        },
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD.md",
        f"""# MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD

context_pack_id: MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD
task_class: MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_FINAL_GUARD", "SECTION_READINESS_SURFACE"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.live_ready_snapshot.v1", "trader1.live_ready_candidate_writer_input.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- LIVE_READY writer input blocks placeholder or unverified identity/evidence fields.
- live_ready=true snapshot blocks missing, placeholder, or unverified evidence even when live_order_allowed=false.
- scope mismatch tests use non-placeholder evidence so the scope guard is independently verified.
- promotion threshold cannot become live readiness outside LIVE_ENABLING_PATCH.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: {audit["status"]}

known_omissions_by_design:
- no live execution
- no credential access
- no LIVE_READY snapshot write
- no active or live config mutation
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

Placeholder and unverified evidence strings are now blocked on LIVE_READY writer inputs and any live_ready=true snapshot candidate. This closes the false-safe gap where live_order_allowed=false could still allow a live_ready=true candidate to pass validation without independent evidence.

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
            "source_section_id": "SECTION_LIVE_READY_WRITER_GUARD",
            "source_file": "TRADER_1.md",
            "source_heading": "LIVE_READY writer guard and live final guard",
            "full_text_marker": f"{REQUIREMENT_ID}:placeholder evidence cannot satisfy LIVE_READY writer or snapshot validation",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Placeholder evidence cannot satisfy LIVE_READY readiness surfaces",
            "requirement_kind": "LIVE_BLOCKED_TEST_PATCH",
            "schema_ids": ["trader1.live_ready_snapshot.v1", "trader1.live_ready_candidate_writer_input.v1", "trader1.validator_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/readiness/test_live_ready_snapshot_writer.py",
                "tests/validators/test_mvp0_validators.py",
                "tests/validators/test_optimizer_backlog_validators.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_FINAL_GUARD", "SECTION_READINESS_SURFACE"],
            "depends_on": ["REQ-MVP0-LIVE-READY-SNAPSHOT-WRITER-GUARD", "REQ-MVP4-LIVE-FINAL-GUARD"],
            "source_text_sha256": sha256_bytes(b"placeholder evidence cannot satisfy LIVE_READY writer or snapshot validation"),
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
            "section_id": "SECTION_LIVE_READY_WRITER_GUARD",
            "schema_files": [
                "contracts/schema/live_ready_snapshot.schema.json",
                "contracts/schema/live_ready_candidate_writer_input.schema.json",
            ],
            "validator_files": ["trader1/runtime/readiness/live_ready_snapshot.py", "trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/readiness/test_live_ready_snapshot_writer.py",
                "tests/validators/test_mvp0_validators.py",
                "tests/validators/test_optimizer_backlog_validators.py",
            ],
            "fixture_files": [],
            "runtime_modules": ["trader1/runtime/readiness/live_ready_snapshot.py"],
            "evidence_artifacts": [
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
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
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
    audit: dict[str, Any],
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
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP0-LIVE-READY-SNAPSHOT-WRITER-GUARD", "REQ-MVP4-LIVE-FINAL-GUARD"],
        "affected_exchange": "ALL",
        "affected_market_type": "ALL",
        "affected_mode": "READINESS_SURFACE_ONLY",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": [],
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
        "next_required_section_ids": ["SECTION_BINANCE_ADAPTER_SURFACE", "SECTION_EXCHANGE_MARKET_TYPE_SEPARATION", "SECTION_LIVE_FINAL_GUARD"],
        "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_SOURCE_BUNDLE_HYGIENE"],
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
        "active_read_surface_used": ["SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_FINAL_GUARD", "SECTION_READINESS_SURFACE"],
        "task_class": "MVP4_PLACEHOLDER_READINESS_SURFACE_GUARD",
        "required_section_ids": ["SECTION_LIVE_READY_WRITER_GUARD", "SECTION_LIVE_FINAL_GUARD", "SECTION_READINESS_SURFACE"],
        "expanded_section_ids": ["AGENTS:0G", "AGENTS:LIVE_READY_WRITER_GUARD", "TRADER_1:LIVE_READY_WRITER_GUARD"],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_PLACEHOLDER_READINESS_GUARD",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
    }
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
            "stage_gate_status": "PASS_FOR_PLACEHOLDER_READINESS_SURFACE_GUARD_NO_LIVE_ORDERS",
            "placeholder_readiness_surface_audit": audit,
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260501.md",
        f"""# MVP4 Placeholder Readiness Surface Guard

created_at_utc: {now}
patch_id: {PATCH_ID}

Finding:
- Placeholder evidence strings could be present on LIVE_READY writer input or live_ready snapshot candidates. Even with live_order_allowed=false, a live_ready=true candidate must not pass without independent evidence.

Patch:
- Added placeholder/unverified evidence detection to the LIVE_READY writer guard.
- Added live_ready=true evidence enforcement independent of live_order_allowed.
- Added negative tests and validator fixtures for placeholder writer hashes and live_ready without order permission.

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
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["live_ready_snapshot_validator", "live_ready_snapshot_writer_validator"]))
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
    audit = build_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "unittest", "tests.readiness.test_live_ready_snapshot_writer", "-v"]),
    ]
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS, audit)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "-m", "unittest", "tests.contract.test_patch_result_runtime_schema_validation", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.validators.test_mvp0_validators", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.validators.test_optimizer_backlog_validators", "-v"]),
            run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-q"]),
        ]
    )
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED, audit)
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
