from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_actual_long_run_runtime_evidence_collection_depth_recheck_patch_evidence as base


PATCH_BASENAME = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-IMPLEMENTATION-DEPTH-RECHECK"
NEXT_TASK_CLASS = "MVP4_PATCH_RESULT_VALIDATOR_RUN_GAP_IMPLEMENTATION_DEPTH_RECHECK"
CONTRACT_GAP_ID = base.CONTRACT_GAP_ID
PREVIOUS_COLLECTION_DEPTH_REQUIREMENT_ID = "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-COLLECTION-DEPTH-RECHECK"
PER_MODE_BLOCKER = "LONG_RUN_PAPER_SHADOW_PROFITABILITY_EVIDENCE_MISSING"

base.PATCH_BASENAME = PATCH_BASENAME
base.PATCH_ID = PATCH_ID
base.REQUIREMENT_ID = REQUIREMENT_ID
base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
base.CHANGED_ARTIFACTS = [
    "contracts/schema/upbit_paper_runtime_evidence_collection_profile_report.schema.json",
    "contracts/schema/read_only_dashboard_shell.schema.json",
    "tools/run_upbit_paper_runtime_evidence_collection_profile.py",
    "trader1/dashboard/read_only_dashboard.py",
    "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
    "tests/dashboard/test_read_only_dashboard.py",
    "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
    "tests/contract/test_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck.py",
    base.rel(base.REPORT_PATH),
    f"tools/emit_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
base.BLOCKERS = [
    CONTRACT_GAP_ID,
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "LONG_RUN_PAPER_RUNTIME_EVIDENCE_INSUFFICIENT",
    PER_MODE_BLOCKER,
    "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]

_ORIGINAL_BUILD_AUDIT = base.build_audit
_ORIGINAL_BUILD_PATCH_RESULT = base.build_patch_result
_ORIGINAL_UPDATE_REQUIREMENT_ARTIFACTS = base.update_requirement_artifacts
_ORIGINAL_WRITE_EVIDENCE = base.write_evidence


def _mode_depth(report: dict[str, Any]) -> dict[str, Any]:
    depth = report.get("long_run_collection_depth") if isinstance(report.get("long_run_collection_depth"), dict) else {}
    evidence = depth.get("runtime_mode_depth_evidence") if isinstance(depth.get("runtime_mode_depth_evidence"), dict) else {}
    return evidence


def build_audit(report: dict[str, Any]) -> dict[str, Any]:
    audit = _ORIGINAL_BUILD_AUDIT(report)
    evidence = _mode_depth(report)
    mode_depths = evidence.get("mode_depths") if isinstance(evidence.get("mode_depths"), dict) else {}
    paper = mode_depths.get("paper") if isinstance(mode_depths.get("paper"), dict) else {}
    shadow = mode_depths.get("shadow") if isinstance(mode_depths.get("shadow"), dict) else {}
    checks = dict(audit.get("checks", {}))
    per_mode_checks = {
        "per_mode_depth_status_blocked": evidence.get("status") == "BLOCKED_FOR_PER_MODE_LONG_RUN_DEPTH",
        "per_mode_blocker_visible": evidence.get("blocker_code") == PER_MODE_BLOCKER,
        "paper_and_shadow_missing_long_run_modes_visible": evidence.get("missing_long_run_modes") == ["PAPER", "SHADOW"],
        "missing_mode_count_exact": evidence.get("missing_long_run_mode_count") == 2,
        "paper_mode_bounded_not_long_run": paper.get("source_status") == "PRESENT_BOUNDED_NOT_LONG_RUN",
        "shadow_mode_present_not_long_run": shadow.get("source_status") == "PRESENT_BLOCKER_ONLY_NOT_LONG_RUN",
        "paper_mode_does_not_count_as_actual_long_run": paper.get("counts_as_actual_long_run_evidence") is False,
        "shadow_mode_does_not_count_as_actual_long_run": shadow.get("counts_as_actual_long_run_evidence") is False,
        "all_required_modes_not_validated": evidence.get("all_required_modes_long_run_validated") is False,
        "per_mode_live_and_scale_false": all(
            evidence.get(field) is False and paper.get(field) is False and shadow.get(field) is False
            for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
        ),
    }
    checks.update(per_mode_checks)
    audit.update(
        {
            "audit_id": f"{PATCH_BASENAME}_AUDIT",
            "patch_id": PATCH_ID,
            "requirement_id": REQUIREMENT_ID,
            "checks": checks,
            "status": "PASS" if all(checks.values()) else "FAIL",
            "per_mode_depth_status": evidence.get("status"),
            "per_mode_blocker_code": evidence.get("blocker_code"),
            "missing_long_run_modes": evidence.get("missing_long_run_modes"),
            "missing_long_run_mode_count": evidence.get("missing_long_run_mode_count"),
            "paper_mode_source_status": paper.get("source_status"),
            "paper_mode_missing_span_seconds": paper.get("missing_span_seconds"),
            "paper_mode_missing_cycle_count": paper.get("missing_cycle_count"),
            "shadow_mode_source_status": shadow.get("source_status"),
            "shadow_mode_missing_span_seconds": shadow.get("missing_span_seconds"),
            "shadow_mode_missing_cycle_count": shadow.get("missing_cycle_count"),
            "finding": "Actual long-run boundary evidence needed per-mode PAPER and SHADOW depth so bounded PAPER evidence cannot mask missing actual SHADOW runtime.",
            "fix": "Runtime profile, schema, dashboard, and tests now expose per-mode PAPER/SHADOW long-run depth deficits as a first-class live-blocking boundary.",
        }
    )
    return audit


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    base.write_text(
        base.ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LONG_RUN_RUNTIME_EVIDENCE", "SECTION_PAPER_SHADOW_EVIDENCE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_COLLECTION_DEPTH_REQUIREMENT_ID}", "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK"]
included_schema_ids: ["trader1.upbit_paper_runtime_evidence_collection_profile_report.v1", "trader1.read_only_dashboard_shell.v1"]
included_validator_ids: {json.dumps(base.VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(base.CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Per-mode PAPER and SHADOW long-run depth evidence is present in the bounded runtime profile.
- Both PAPER and SHADOW remain listed in missing_long_run_modes until actual per-mode long-run floors pass.
- Bounded PAPER and orchestration-only SHADOW evidence cannot count as actual long-run evidence.
- Dashboard shows per-mode missing span/cycle deficits and blocks hidden per-mode gaps.
- {CONTRACT_GAP_ID} remains OPEN and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_snapshot:
- audit_status: {audit["status"]}
- per_mode_depth_status: {audit["per_mode_depth_status"]}
- missing_long_run_modes: {json.dumps(audit["missing_long_run_modes"])}
- paper_missing_span_seconds: {audit["paper_mode_missing_span_seconds"]}
- paper_missing_cycle_count: {audit["paper_mode_missing_cycle_count"]}
- shadow_missing_span_seconds: {audit["shadow_mode_missing_span_seconds"]}
- shadow_missing_cycle_count: {audit["shadow_mode_missing_cycle_count"]}

known_omissions_by_design:
- this patch does not create actual 24h PAPER/SHADOW long-run evidence
- this patch does not close {CONTRACT_GAP_ID}
- this patch does not use credentials, call private endpoints, place live orders, mutate live config, or scale up

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    base.write_text(
        base.ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md",
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

Actual long-run runtime evidence remains missing and live-blocking. The bounded Upbit PAPER runtime profile now exposes per-mode missing long-run depth for PAPER and SHADOW; both are blocked from counting as actual long-run evidence.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    _ORIGINAL_UPDATE_REQUIREMENT_ARTIFACTS(now, trader_hash, agents_hash)
    req_path = base.ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = base.ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = base.load_json(req_path)
    for item in req_index.get("requirements", []):
        if item.get("requirement_id") == REQUIREMENT_ID:
            item.update(
                {
                    "source_heading": "Actual long-run runtime evidence boundary implementation depth recheck",
                    "full_text_marker": f"{REQUIREMENT_ID}: per-mode PAPER and SHADOW long-run runtime depth must remain explicit, missing, and live-blocking until actual long-run evidence exists",
                    "requirement_title": "Actual long-run runtime evidence boundary implementation depth recheck",
                    "requirement_kind": "RUNTIME_EVIDENCE_BOUNDARY_PATCH",
                    "artifact_ids": base.CHANGED_ARTIFACTS,
                    "test_ids": [
                        "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                        "tests/dashboard/test_read_only_dashboard.py",
                        "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
                        "tests/contract/test_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck.py",
                    ],
                    "depends_on": [
                        PREVIOUS_COLLECTION_DEPTH_REQUIREMENT_ID,
                        "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
                        "REQ-MVP4-LIVE-FINAL-GUARD",
                    ],
                    "source_text_sha256": base.sha256_bytes(
                        b"per-mode PAPER and SHADOW actual long-run runtime depth remains missing and live-blocking"
                    ),
                }
            )
    base.write_json(req_path, req_index)

    matrix = base.load_json(matrix_path)
    for row in matrix.get("rows", []):
        if row.get("requirement_id") == REQUIREMENT_ID:
            row.update(
                {
                    "test_files": [
                        "tests/runtime/test_upbit_paper_runtime_evidence_collection_profile.py",
                        "tests/dashboard/test_read_only_dashboard.py",
                        "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
                        "tests/contract/test_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck.py",
                    ],
                    "evidence_artifacts": [
                        f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                        f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                        f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                        f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
                    ],
                    "patch_result_fields": [
                        "upbit_paper_runtime_evidence_profile_status",
                        "live_order_ready_after",
                        "live_order_allowed_after",
                        "can_live_trade_after",
                        "scale_up_allowed_after",
                    ],
                }
            )
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    audit: dict[str, Any],
) -> dict[str, Any]:
    patch_result = _ORIGINAL_BUILD_PATCH_RESULT(now, tests_run, validators_run, validators_required, audit)
    patch_result.update(
        {
            "affected_contract_ids": [
                REQUIREMENT_ID,
                PREVIOUS_COLLECTION_DEPTH_REQUIREMENT_ID,
                "REQ-MVP4-ACTUAL-LONG-RUN-RUNTIME-EVIDENCE-BOUNDARY-STATE-SYNC-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [
                REQUIREMENT_ID,
                f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            ],
            "remaining_blockers": base.BLOCKERS,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_PATCH_RESULT_VALIDATION",
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_UPBIT_PAPER_RUNTIME"],
            "task_class": "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_IMPLEMENTATION_DEPTH_RECHECK",
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any], audit: dict[str, Any]) -> None:
    _ORIGINAL_WRITE_EVIDENCE(now, trader_hash, agents_hash, patch_result, audit)
    manifest_path = base.ROOT / patch_result["evidence_manifest_path"]
    manifest = base.load_json(manifest_path)
    manifest.update(
        {
            "missing_long_run_modes": audit["missing_long_run_modes"],
            "per_mode_depth_status": audit["per_mode_depth_status"],
            "per_mode_blocker_code": audit["per_mode_blocker_code"],
            "paper_mode_missing_span_seconds": audit["paper_mode_missing_span_seconds"],
            "paper_mode_missing_cycle_count": audit["paper_mode_missing_cycle_count"],
            "shadow_mode_missing_span_seconds": audit["shadow_mode_missing_span_seconds"],
            "shadow_mode_missing_cycle_count": audit["shadow_mode_missing_cycle_count"],
        }
    )
    base.write_json(manifest_path, manifest)
    base.write_text(
        base.ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260504.md",
        f"""# Actual Long-Run Runtime Evidence Boundary Implementation Depth Recheck

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added per-mode PAPER and SHADOW long-run depth evidence to the bounded Upbit PAPER runtime profile.
- Dashboard now shows both modes as missing actual long-run depth with separate span/cycle deficits.
- Validation blocks hidden per-mode gaps and false bounded-profile actual long-run claims.

Audit:
- status: {audit['status']}
- per_mode_depth_status: {audit['per_mode_depth_status']}
- missing_long_run_modes: {json.dumps(audit['missing_long_run_modes'])}
- paper_mode_missing_span_seconds: {audit['paper_mode_missing_span_seconds']}
- paper_mode_missing_cycle_count: {audit['paper_mode_missing_cycle_count']}
- shadow_mode_missing_span_seconds: {audit['shadow_mode_missing_span_seconds']}
- shadow_mode_missing_cycle_count: {audit['shadow_mode_missing_cycle_count']}

Safety:
- actual long-run evidence gap remains OPEN
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentials, private endpoints, live orders, live config mutation, or scale-up
""",
    )


base.build_audit = build_audit
base.update_context = update_context
base.update_requirement_artifacts = update_requirement_artifacts
base.build_patch_result = build_patch_result
base.write_evidence = write_evidence


def run_command(args: list[str], timeout_seconds: int = 900) -> dict[str, Any]:
    return base.run_command(args, timeout_seconds=timeout_seconds)


def main() -> int:
    now = base.utc_now()
    trader_hash = base.sha256_file(base.ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(base.ROOT / "AGENTS.md")
    base.update_authority_manifest(now)
    base.write_source_bundle_manifest()
    report = base.write_profile_report()
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
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_projects_paper_runtime_evidence_profile_pass_display_only",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_runtime_evidence_profile_hidden_per_mode_depth",
                "tests/dashboard/test_read_only_dashboard.py::ReadOnlyDashboardTest::test_dashboard_blocks_paper_runtime_evidence_profile_per_mode_false_long_run_claim",
            ]
        ),
        run_command([sys.executable, "-B", "tools/run_upbit_paper_runtime_evidence_collection_profile.py"]),
    ]
    audit = build_audit(base.load_json(base.REPORT_PATH))
    patch_path = base.ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, base.run_validators(base.BOOTSTRAP_VALIDATORS), base.BOOTSTRAP_VALIDATORS, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/contract/test_actual_long_run_runtime_evidence_collection_depth_recheck.py",
                    "tests/contract/test_actual_long_run_runtime_evidence_boundary_implementation_depth_recheck.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_bundle_security_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"], timeout_seconds=1800),
        ]
    )
    audit = build_audit(base.load_json(base.REPORT_PATH))
    patch_result = build_patch_result(now, tests_run, base.run_validators(base.VALIDATORS_REQUIRED), base.VALIDATORS_REQUIRED, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed", "audit": audit})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "missing_long_run_modes": audit["missing_long_run_modes"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
                "tests_non_pass": failed,
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
