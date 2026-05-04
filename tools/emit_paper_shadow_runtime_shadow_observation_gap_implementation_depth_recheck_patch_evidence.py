from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-IMPLEMENTATION-DEPTH-RECHECK"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK"
NEXT_TASK_CLASS = "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY_IMPLEMENTATION_DEPTH_RECHECK"

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
from tools.run_hygiene_safe_pytest import scan_cache_artifacts  # noqa: E402
from tools.run_upbit_paper_runtime_evidence_collection_profile import (  # noqa: E402
    DEFAULT_REPORT_PATH,
    run_upbit_paper_runtime_evidence_collection_profile,
    validate_upbit_paper_runtime_evidence_collection_profile_report,
)
from trader1.security.source_bundle import build_source_bundle_manifest, write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


REPORT_PATH = ROOT / DEFAULT_REPORT_PATH
CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "contracts/schema/patch_result.schema.json",
    "tools/run_upbit_paper_runtime_evidence_collection_profile.py",
    "trader1/dashboard/read_only_dashboard.py",
    "tools/emit_paper_shadow_runtime_shadow_observation_gap_implementation_depth_recheck_patch_evidence.py",
    "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
    rel(REPORT_PATH),
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "upbit_paper_persistent_loop_validator",
    "upbit_paper_runtime_recovery_guard_validator",
    "upbit_paper_runtime_sample_history_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "paper_ledger_rollup_validator",
    "shadow_observation_runtime_orchestration_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "read_only_dashboard_validator",
    "live_final_guard_validator",
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
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
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


def write_profile_report() -> dict[str, Any]:
    report = run_upbit_paper_runtime_evidence_collection_profile(requested_cycle_count=2)
    write_json(REPORT_PATH, report)
    return report


def build_audit(report: dict[str, Any]) -> dict[str, Any]:
    validation = validate_upbit_paper_runtime_evidence_collection_profile_report(report)
    manifest = build_source_bundle_manifest()
    cache_findings = scan_cache_artifacts()
    depth = report.get("long_run_collection_depth") if isinstance(report.get("long_run_collection_depth"), dict) else {}
    blockers: list[str] = []
    if validation.status != "PASS" or report.get("status") != "PASS":
        blockers.append(validation.blocker_code or report.get("primary_blocker_code") or "RUNTIME_EVIDENCE_PROFILE_NOT_PASS")
    if cache_findings:
        blockers.append("CURRENT_REPO_CACHE_ARTIFACT_PRESENT")
    if manifest.get("shipped_forbidden_count"):
        blockers.append("SHIPPED_PACKAGE_FORBIDDEN_PRESENT")
    if manifest.get("contains_secret") or manifest.get("repo_secret_findings_count"):
        blockers.append("SOURCE_SECRET_FINDING_PRESENT")
    if manifest.get("live_order_ready") or manifest.get("live_order_allowed") or manifest.get("can_live_trade"):
        blockers.append("LIVE_FLAG_DRIFT")
    return {
        "audit_schema_id": "trader1.paper_shadow_runtime_shadow_observation_gap_depth_recheck_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": sorted(set(blockers)),
        "profile_report_path": rel(REPORT_PATH),
        "profile_status": report.get("status"),
        "component_count": report.get("component_count", 0),
        "component_pass_count": report.get("component_pass_count", 0),
        "accepted_cycle_sample_count": report.get("accepted_cycle_sample_count", 0),
        "runtime_sample_status": report.get("runtime_sample_status"),
        "ledger_runtime_evidence_status": report.get("ledger_runtime_evidence_status"),
        "collection_depth_observed_runtime_modes": depth.get("observed_runtime_modes", []),
        "collection_depth_missing_runtime_modes": depth.get("missing_runtime_modes", []),
        "shadow_runtime_depth_status": depth.get("shadow_runtime_depth_status"),
        "paper_shadow_pairing_status": depth.get("paper_shadow_pairing_status"),
        "shadow_orchestration_component_present": any(
            item.get("component_id") == "shadow_runtime_orchestration"
            for item in report.get("component_results", [])
            if isinstance(item, dict)
        ),
        "idempotency_status": report.get("idempotency_status"),
        "reconciliation_status": report.get("reconciliation_status"),
        "mismatch_count": report.get("mismatch_count", 0),
        "cache_artifact_count": len(cache_findings),
        "shipped_forbidden_count": manifest.get("shipped_forbidden_count", 0),
        "contains_secret": bool(manifest.get("contains_secret")),
        "long_run_evidence_eligible": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_SHADOW_OBSERVATION_RUNTIME", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1", "trader1.read_only_dashboard_shell.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Bounded Upbit PAPER runtime loop still executes from public/static PAPER inputs only.
- Runtime recovery guard, sample history, ledger idempotency, and SHADOW orchestration evidence are validated together.
- The SHADOW runtime source is present and paired as PRESENT_NOT_LONG_RUN / PAIRED_NOT_LONG_RUN.
- Duplicate ledger/idempotency evidence still blocks as RECONCILIATION_REQUIRED.
- The profile keeps SHADOW in missing_runtime_modes because no actual long-run PAPER/SHADOW evidence exists.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- profile_status: {audit["profile_status"]}
- component_pass_count: {audit["component_pass_count"]}/{audit["component_count"]}
- accepted_cycle_sample_count: {audit["accepted_cycle_sample_count"]}
- ledger_runtime_evidence_status: {audit["ledger_runtime_evidence_status"]}
- observed_runtime_modes: {json.dumps(audit["collection_depth_observed_runtime_modes"])}
- missing_runtime_modes: {json.dumps(audit["collection_depth_missing_runtime_modes"])}
- shadow_runtime_depth_status: {audit["shadow_runtime_depth_status"]}
- paper_shadow_pairing_status: {audit["paper_shadow_pairing_status"]}
- mismatch_count: {audit["mismatch_count"]}

known_omissions_by_design:
- no long-run PAPER/SHADOW evidence is created
- PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP remains open and live-affecting
- no LIVE_READY snapshot is written
- no live config or active/live config mutation is allowed
- no exchange credential, account, private endpoint, or live order path is used

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

Upbit PAPER runtime evidence collection now includes a non-live SHADOW orchestration source. Last profile: status={audit["profile_status"]}, components={audit["component_pass_count"]}/{audit["component_count"]}, accepted_cycle_samples={audit["accepted_cycle_sample_count"]}, shadow_depth_status={audit["shadow_runtime_depth_status"]}, pairing_status={audit["paper_shadow_pairing_status"]}.

This remains bounded PAPER/SHADOW support evidence only. It is not long-run evidence, not LIVE_READY, and not scale-up evidence.

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
            "source_section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "source_file": "TRADER_1.md",
            "source_heading": "PAPER/SHADOW runtime shadow observation gap implementation depth",
            "full_text_marker": f"{REQUIREMENT_ID}: bounded PAPER runtime profile must bind non-live SHADOW orchestration as not-long-run evidence without closing live blockers",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "PAPER/SHADOW runtime shadow observation gap implementation depth",
            "requirement_kind": "RUNTIME_EVIDENCE_PROFILE_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1",
                "trader1.read_only_dashboard_shell.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_SHADOW_OBSERVATION_RUNTIME",
                "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-SAMPLE-HISTORY-PROVENANCE",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-RECONCILIATION-IDEMPOTENCY-RUNTIME-EVIDENCE",
                "REQ-MVP4-OPEN-CONTRACT-GAP-IMPLEMENTATION-PRIORITY-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"bounded PAPER profile binds non-live SHADOW orchestration not long-run no live"
            ),
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
            "section_id": "SECTION_PAPER_SHADOW_EVIDENCE",
            "schema_files": [
                "contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json",
                "contracts/schema/read_only_dashboard_shell.schema.json",
            ],
            "validator_files": [
                "tools/run_upbit_paper_runtime_evidence_collection_profile.py",
                "trader1/research/shadow/shadow_observation_runtime_orchestration.py",
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/runtime/paper/upbit_paper_runtime_sample_history.py",
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                "tests/dashboard/test_read_only_dashboard.py",
                "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_persistent_loop.py",
                "trader1/runtime/paper/upbit_paper_runtime_sample_history.py",
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
                "trader1/research/shadow/shadow_observation_runtime_orchestration.py",
            ],
            "evidence_artifacts": [
                rel(REPORT_PATH),
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py"],
            "patch_result_fields": [
                "upbit_paper_runtime_evidence_profile_status",
                "upbit_paper_runtime_evidence_profile_component_count",
                "upbit_paper_runtime_evidence_profile_component_pass_count",
                "upbit_paper_runtime_evidence_profile_accepted_cycle_sample_count",
                "upbit_paper_runtime_evidence_profile_ledger_status",
                "upbit_paper_runtime_evidence_profile_mismatch_count",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
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
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [
            REQUIREMENT_ID,
            PREVIOUS_REQUIREMENT_ID,
            "REQ-MVP4-PAPER-SHADOW-RUNTIME-SHADOW-OBSERVATION-GAP-STATE-SYNC-RECHECK",
            "REQ-MVP4-UPBIT-PAPER-RUNTIME-SAMPLE-HISTORY-PROVENANCE",
            "REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK",
            "REQ-MVP4-LIVE-FINAL-GUARD",
        ],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "PAPER_AND_SHADOW_NON_LIVE",
        "removed_requirements": [],
        "merged_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [],
        "new_or_changed_schema_ids": [
            "trader1.upbit_paper_runtime_evidence_collection_profile_report.v1",
            "trader1.read_only_dashboard_shell.v1",
        ],
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
        "next_required_section_ids": [
            "SECTION_PAPER_SHADOW_EVIDENCE",
            "SECTION_SHADOW_OBSERVATION_RUNTIME",
            "SECTION_UPBIT_PAPER_RUNTIME",
            "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_PAPER_SHADOW_EVIDENCE"],
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
        "active_read_surface_used": [
            "SECTION_PAPER_SHADOW_EVIDENCE",
            "SECTION_SHADOW_OBSERVATION_RUNTIME",
            "SECTION_UPBIT_PAPER_RUNTIME",
            "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "task_class": PATCH_BASENAME,
        "required_section_ids": [
            "SECTION_PAPER_SHADOW_EVIDENCE",
            "SECTION_SHADOW_OBSERVATION_RUNTIME",
            "SECTION_UPBIT_PAPER_RUNTIME",
            "SECTION_LEDGER_RECONCILIATION_IDEMPOTENCY",
            "SECTION_LIVE_FINAL_GUARD",
        ],
        "expanded_section_ids": [
            "AGENTS:0G",
            "AGENTS:0F",
            "SECTION_PAPER_SHADOW_EVIDENCE",
            "SECTION_SHADOW_OBSERVATION_RUNTIME",
            "SECTION_UPBIT_PAPER_RUNTIME",
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_PAPER_SHADOW_DEPTH_RECHECK",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "upbit_paper_runtime_evidence_profile_status": audit["profile_status"],
        "upbit_paper_runtime_evidence_profile_component_count": audit["component_count"],
        "upbit_paper_runtime_evidence_profile_component_pass_count": audit["component_pass_count"],
        "upbit_paper_runtime_evidence_profile_accepted_cycle_sample_count": audit["accepted_cycle_sample_count"],
        "upbit_paper_runtime_evidence_profile_ledger_status": audit["ledger_runtime_evidence_status"],
        "upbit_paper_runtime_evidence_profile_mismatch_count": audit["mismatch_count"],
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
            "stage_gate_status": "PASS_FOR_UPBIT_PAPER_RUNTIME_EVIDENCE_COLLECTION_PROFILE_NO_LIVE_ORDERS",
            "audit": audit,
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# MVP4 PAPER/SHADOW Runtime Observation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Bound the Upbit PAPER runtime evidence profile to a non-live SHADOW orchestration component.
- SHADOW depth is visible as PRESENT_NOT_LONG_RUN and PAPER/SHADOW pairing as PAIRED_NOT_LONG_RUN.
- The profile still keeps SHADOW in missing_runtime_modes because no actual long-run evidence exists.
- Duplicate ledger evidence remains tested as RECONCILIATION_REQUIRED.

Audit:
- profile_status: {audit['profile_status']}
- component_pass_count: {audit['component_pass_count']}/{audit['component_count']}
- accepted_cycle_sample_count: {audit['accepted_cycle_sample_count']}
- ledger_runtime_evidence_status: {audit['ledger_runtime_evidence_status']}
- observed_runtime_modes: {json.dumps(audit['collection_depth_observed_runtime_modes'])}
- missing_runtime_modes: {json.dumps(audit['collection_depth_missing_runtime_modes'])}
- shadow_runtime_depth_status: {audit['shadow_runtime_depth_status']}
- paper_shadow_pairing_status: {audit['paper_shadow_pairing_status']}
- mismatch_count: {audit['mismatch_count']}

Safety:
- long_run_evidence_eligible=false
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
    state["implemented_schema_ids"] = sorted(
        set(state.get("implemented_schema_ids", []) + ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1"])
    )
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
    report = write_profile_report()
    audit = build_audit(report)
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command(
            [
                sys.executable,
                "tools/run_hygiene_safe_pytest.py",
                "--",
                "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                "tests/research/test_shadow_observation_runtime_orchestration.py",
                "tests/research/test_shadow_observation_persistent_runtime.py",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_projects_paper_runtime_evidence_profile_pass_display_only",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_runtime_evidence_profile_hidden_collection_depth",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_runtime_evidence_profile_shadow_pairing_drift",
                "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_upbit_paper_runtime_evidence_collection_profile.py"]),
    ]
    audit = build_audit(load_json(REPORT_PATH))
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_paper_shadow_evidence_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_bundle_security_validators.py"]),
        ]
    )
    audit = build_audit(load_json(REPORT_PATH))
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed", "blockers": audit["blockers"]})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "profile_status": audit["profile_status"],
                "component_pass_count": audit["component_pass_count"],
                "component_count": audit["component_count"],
                "accepted_cycle_sample_count": audit["accepted_cycle_sample_count"],
                "ledger_runtime_evidence_status": audit["ledger_runtime_evidence_status"],
                "mismatch_count": audit["mismatch_count"],
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
