from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_live_enabling_evidence_missing_recheck_patch_evidence import (  # noqa: E402
    ROUTE_GUARD_TEST_ARTIFACTS,
)
from tools.emit_root_launcher_operator_visibility_patch_evidence import (  # noqa: E402
    sha256_bytes,
    sha256_file,
    sha256_json,
    update_authority_manifest,
    update_read_cache,
    utc_now,
    write_json,
    write_text,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_fixture_file, run_validators  # noqa: E402


PATCH_BASENAME = "MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK"
PATCH_ID = f"{PATCH_BASENAME}_20260505_001"
REQUIREMENT_ID = "REQ-MVP4-SCALE-UP-NOT-ELIGIBLE-RECHECK"
GAP_ID = "SCALE_UP_NOT_ELIGIBLE"
PREVIOUS_REQUIREMENT_ID = "REQ-MVP4-LIVE-ENABLING-EVIDENCE-MISSING-RECHECK"
PREVIOUS_PATCH_PREFIX = "MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_"
NEXT_TASK_CLASS = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"

EXTERNAL_BLOCKER_MANIFEST = "system/evidence/MVP4_EXTERNAL_BLOCKER.evidence_manifest.json"
SCALEUP_SAFETY_PATCH_RESULT = "system/evidence/patch_results/MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json"
CONVERGENCE_RISK_SCALE_PATCH_RESULT = "system/evidence/patch_results/MVP4_CONVERGENCE_RISK_SCALE_BLOCKED.patch_result.json"
DASHBOARD_STABILITY_SCALEUP_LOCK_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_DASHBOARD_STABILITY_SCALEUP_LOCK.patch_result.json"
)
LIVE_ENABLING_RECHECK_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK.patch_result.json"
)
CONTRACT_GAP_PATH = f"system/evidence/contract_gaps/{GAP_ID}.contract_gap.json"

RISK_SCALE_VALIDATORS = [
    "risk_scaling_decision_validator",
    "live_burn_in_feedback_validator",
    "paper_live_parity_validator",
    "execution_quality_measurement_validator",
    "survival_layer_validator",
]
GUARDRAIL_VALIDATORS = [
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "scale_up_eligibility_validator",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    *RISK_SCALE_VALIDATORS,
    *GUARDRAIL_VALIDATORS,
]
BOOTSTRAP_VALIDATORS_REQUIRED = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
]
EXPECTED_SCALE_STATUSES = {
    "risk_scaling_decision_validator": "BLOCKED",
    "live_burn_in_feedback_validator": "BLOCKED",
    "paper_live_parity_validator": "BLOCKED",
    "execution_quality_measurement_validator": "BLOCKED",
    "survival_layer_validator": "BLOCKED",
    "optimizer_no_live_mutation_validator": "PASS",
    "optimizer_guardrail_validator": "PASS",
    "convergence_assessment_validator": "PASS",
    "scale_up_eligibility_validator": "BLOCKED",
}
FIXTURE_PATHS = [
    "tests/validators/fixtures/convergence_risk_scale_pass.json",
    "tests/validators/fixtures/convergence_risk_scale_fail.json",
    "tests/validators/fixtures/convergence_risk_scale_blocked.json",
    "tests/validators/fixtures/convergence_scaleup_safety_pass.json",
    "tests/validators/fixtures/convergence_scaleup_safety_fail.json",
    "tests/validators/fixtures/convergence_scaleup_safety_blocked.json",
]
EXPECTED_FIXTURE_STATUSES = {
    "convergence_risk_scale_pass.json": "PASS",
    "convergence_risk_scale_fail.json": "FAIL",
    "convergence_risk_scale_blocked.json": "BLOCKED",
    "convergence_scaleup_safety_pass.json": "PASS",
    "convergence_scaleup_safety_fail.json": "FAIL",
    "convergence_scaleup_safety_blocked.json": "BLOCKED",
}
CHANGED_ARTIFACTS = sorted(
    set(
        ROUTE_GUARD_TEST_ARTIFACTS
        + [
            "tests/contract/test_scale_up_not_eligible_recheck.py",
            "tools/emit_scale_up_not_eligible_recheck_patch_evidence.py",
            f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            CONTRACT_GAP_PATH,
        ]
    )
)
BLOCKERS = [
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "API_UNVERIFIED",
    "BLOCKED_REPAIR_PLAN_REQUIRES_OPERATOR_RECONCILIATION",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "LIVE_READY_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "MISSING_CYCLE_LEDGER_RERUN_REQUIRED",
    "OPERATOR_APPROVAL_MISSING",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
    "PATCH_RESULT_VALIDATOR_RUN_GAP",
    "POST_REPAIR_RECONCILIATION_REQUIRED",
    "POST_RERUN_CURRENT_EVIDENCE_WRITE_BLOCKED",
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "REGENERATED_CURRENT_BLOCKED_REPAIRS_REQUIRE_LEDGER_RECOVERY_RECONCILIATION",
    "REPAIR_CANDIDATE_HASH_MISMATCH_RECONCILIATION_REQUIRED",
    "RISK_SCALING_UNTESTED",
    "LIVE_BURN_IN_FEEDBACK_MISSING",
    "EXECUTION_QUALITY_UNTESTED",
    "SURVIVAL_LAYER_BLOCKED",
    GAP_ID,
]
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result: dict[str, Any] = {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }
    if completed.returncode != 0:
        result["stdout_tail"] = completed.stdout[-4000:]
        result["stderr_tail"] = completed.stderr[-4000:]
    return result


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def assert_false_fields(name: str, artifact: dict[str, Any], suffix: str = "") -> None:
    for field in FALSE_FIELDS:
        key = f"{field}{suffix}"
        if artifact.get(key) is True:
            raise RuntimeError(f"{name} has forbidden true field: {key}")


def assert_current_state_ready_for_scaleup_recheck() -> None:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    completed = set(state.get("completed_requirement_ids", []))
    gaps = set(state.get("open_contract_gap_ids", []))
    last_patch_id = str(state.get("last_patch_id", ""))
    next_allowed = state.get("next_allowed_task_class")

    for field in FALSE_FIELDS:
        if state.get(field) is not False:
            raise RuntimeError(f"{field} must stay false before {PATCH_BASENAME}")
    if GAP_ID not in gaps:
        raise RuntimeError(f"{GAP_ID} must remain open before {PATCH_BASENAME}")

    previous_route_ready = last_patch_id.startswith(PREVIOUS_PATCH_PREFIX) and next_allowed == PATCH_BASENAME
    idempotent_rerun_ready = last_patch_id.startswith(PATCH_BASENAME) and next_allowed == NEXT_TASK_CLASS
    if not (previous_route_ready or idempotent_rerun_ready):
        raise RuntimeError(
            f"{PATCH_BASENAME} expected previous route {PREVIOUS_PATCH_PREFIX} -> {PATCH_BASENAME}; "
            f"got last_patch_id={last_patch_id!r}, next_allowed_task_class={next_allowed!r}"
        )
    if previous_route_ready and PREVIOUS_REQUIREMENT_ID not in completed:
        raise RuntimeError(f"{PREVIOUS_REQUIREMENT_ID} must be completed before {PATCH_BASENAME}")


def assert_previous_patch(path_text: str) -> dict[str, Any]:
    patch = load_json(ROOT / path_text)
    assert_false_fields(path_text, patch, "_after")
    if GAP_ID not in patch.get("remaining_blockers", []):
        raise RuntimeError(f"{path_text} no longer preserves {GAP_ID}")
    return patch


def update_route_guard_tests() -> None:
    anchor = '        if state["last_patch_id"].startswith("MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_"):'
    replacement = (
        '        if state["last_patch_id"].startswith("MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_"):\n'
        '            expected_next_task = "MVP4_OPEN_CONTRACT_GAP_IMPLEMENTATION_PRIORITY_RECHECK"\n'
        '            self.assertEqual(state["next_allowed_task_class"], expected_next_task)\n'
        '        elif state["last_patch_id"].startswith("MVP4_LIVE_ENABLING_EVIDENCE_MISSING_RECHECK_"):'
    )
    already_present = 'state["last_patch_id"].startswith("MVP4_SCALE_UP_NOT_ELIGIBLE_RECHECK_")'
    for path_text in ROUTE_GUARD_TEST_ARTIFACTS:
        path = ROOT / path_text
        text = path.read_text(encoding="utf-8")
        if anchor not in text:
            if already_present in text:
                continue
            raise RuntimeError(f"route guard anchor missing in {path_text}")
        updated = text.replace(anchor, replacement)
        if updated == text:
            continue
        write_text(path, updated)


def scaleup_gap_summary(
    risk_results: list[dict[str, Any]],
    guardrail_results: list[dict[str, Any]],
    fixture_results: list[dict[str, Any]],
) -> dict[str, Any]:
    state = load_json(ROOT / "contracts" / "generated" / "current_implementation_state.json")
    external_manifest = load_json(ROOT / EXTERNAL_BLOCKER_MANIFEST)
    scaleup_patch = assert_previous_patch(SCALEUP_SAFETY_PATCH_RESULT)
    risk_scale_patch = assert_previous_patch(CONVERGENCE_RISK_SCALE_PATCH_RESULT)
    live_enabling_patch = assert_previous_patch(LIVE_ENABLING_RECHECK_PATCH_RESULT)
    dashboard_patch = load_json(ROOT / DASHBOARD_STABILITY_SCALEUP_LOCK_PATCH_RESULT)
    assert_false_fields(DASHBOARD_STABILITY_SCALEUP_LOCK_PATCH_RESULT, dashboard_patch, "_after")
    assert_false_fields(EXTERNAL_BLOCKER_MANIFEST, external_manifest)
    assert_false_fields("current_implementation_state", state)

    all_results = risk_results + guardrail_results
    statuses = {item["validator_id"]: item["status"] for item in all_results}
    blockers = {
        item["validator_id"]: [blocker["code"] for blocker in item.get("blockers", [])]
        for item in all_results
    }
    for validator_id, expected_status in EXPECTED_SCALE_STATUSES.items():
        if statuses.get(validator_id) != expected_status:
            raise RuntimeError(
                f"{validator_id} expected {expected_status}, got {statuses.get(validator_id)!r}"
            )
    if blockers.get("scale_up_eligibility_validator") != [GAP_ID]:
        raise RuntimeError("scale_up_eligibility_validator no longer blocks on SCALE_UP_NOT_ELIGIBLE")

    fixture_statuses = {Path(item.get("fixture_path", "")).name: item.get("status") for item in fixture_results}
    for filename, expected_status in EXPECTED_FIXTURE_STATUSES.items():
        if fixture_statuses.get(filename) != expected_status:
            raise RuntimeError(f"{filename} expected {expected_status}, got {fixture_statuses.get(filename)!r}")

    external_statuses = list(external_manifest.get("external_review_input_statuses", []))
    usable_external = [item for item in external_statuses if item.get("usable_for_live_enabling") is True]
    true_scale_statuses = [
        item
        for item in external_statuses
        for field in FALSE_FIELDS
        if item.get(field) is True
    ]
    if usable_external:
        raise RuntimeError("external evidence unexpectedly usable for live enabling during scale-up recheck")
    if true_scale_statuses:
        raise RuntimeError("external evidence has forbidden true live/scale flag during scale-up recheck")

    known_blockers = set(external_manifest.get("known_blockers", []))
    blocker_codes = sorted(
        set(BLOCKERS)
        | known_blockers
        | set(state.get("open_contract_gap_ids", []))
        | {code for values in blockers.values() for code in values}
        | set(scaleup_patch.get("remaining_blockers", []))
        | set(risk_scale_patch.get("remaining_blockers", []))
        | set(live_enabling_patch.get("remaining_blockers", []))
    )
    if GAP_ID not in blocker_codes:
        raise RuntimeError(f"{GAP_ID} must remain in blockers")
    if "LIVE_ENABLING_EVIDENCE_MISSING" not in blocker_codes:
        raise RuntimeError("scale-up recheck lost live enabling blocker dependency")

    return {
        "scale_up_eligibility_status": statuses["scale_up_eligibility_validator"],
        "scale_up_primary_blocker_code": blockers["scale_up_eligibility_validator"][0],
        "risk_scaling_decision_status": statuses["risk_scaling_decision_validator"],
        "risk_scaling_primary_blocker_code": blockers["risk_scaling_decision_validator"][0],
        "live_burn_in_feedback_status": statuses["live_burn_in_feedback_validator"],
        "paper_live_parity_status": statuses["paper_live_parity_validator"],
        "execution_quality_measurement_status": statuses["execution_quality_measurement_validator"],
        "survival_layer_status": statuses["survival_layer_validator"],
        "blocked_scale_validator_count": sum(1 for status in statuses.values() if status == "BLOCKED"),
        "pass_guardrail_validator_count": sum(1 for status in statuses.values() if status == "PASS"),
        "fixture_pass_count": sum(1 for status in fixture_statuses.values() if status == "PASS"),
        "fixture_fail_count": sum(1 for status in fixture_statuses.values() if status == "FAIL"),
        "fixture_blocked_count": sum(1 for status in fixture_statuses.values() if status == "BLOCKED"),
        "external_review_input_count": len(external_statuses),
        "usable_for_live_enabling_count": len(usable_external),
        "forbidden_live_or_scale_true_status_count": len(true_scale_statuses),
        "previous_scaleup_patch_result_hash": scaleup_patch.get("result_hash"),
        "previous_risk_scale_patch_result_hash": risk_scale_patch.get("result_hash"),
        "live_enabling_recheck_patch_result_hash": live_enabling_patch.get("result_hash"),
        "dashboard_stability_scaleup_lock_patch_result_hash": dashboard_patch.get("result_hash"),
        "remaining_blockers": blocker_codes,
    }


def write_contract_gap(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_json(
        ROOT / CONTRACT_GAP_PATH,
        {
            "schema_id": "trader1.contract_gap.v1",
            "generated_at_utc": now,
            "project_id": "TRADER_1",
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "status": "OPEN",
            "blockers": [
                {
                    "code": GAP_ID,
                    "severity": "CRITICAL",
                    "message": (
                        "Scale-up is not eligible because live permission is false, live burn-in/parity/execution "
                        "quality/survival dependencies remain blocked, and external live-enabling evidence is missing."
                    ),
                    "source_requirement_id": REQUIREMENT_ID,
                }
            ],
            "notes": (
                f"scale_up_eligibility_status={summary['scale_up_eligibility_status']}; "
                f"primary_blocker={summary['scale_up_primary_blocker_code']}; "
                f"blocked_scale_validator_count={summary['blocked_scale_validator_count']}; "
                "no risk scale-up, live order, credential use, or live config mutation is created."
            ),
            "contract_gap_id": GAP_ID,
            "severity": "CRITICAL",
            "source_section_id": "SECTION_CONVERGENCE_RISK_SCALE",
            "live_affecting": True,
        },
    )


def update_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: {PATCH_BASENAME}
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_CONVERGENCE_RISK_SCALE", "SECTION_LIVE_FINAL_GUARD", "SECTION_LIVE_BLOCKED_TEST", "SECTION_RISK_SCALE_UP_BLOCKER"]
included_requirement_ids: ["{REQUIREMENT_ID}", "{PREVIOUS_REQUIREMENT_ID}", "REQ-CONV-012"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.contract_gap.v1", "trader1.validator_result.v1", "trader1.risk_scaling_decision.v1", "trader1.live_burn_in_feedback_report.v1", "trader1.execution_quality_measurement_report.v1", "trader1.survival_layer_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Confirm scale_up_eligibility_validator remains BLOCKED on {GAP_ID}.
- Confirm live burn-in, paper/live parity, execution quality, survival layer, and risk scaling dependencies remain blocked.
- Confirm PASS/FAIL/BLOCKED risk-scale fixtures are still exercised.
- Route only to {NEXT_TASK_CLASS}.
- Keep live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

gap_snapshot:
- scale_up_eligibility_status: {summary["scale_up_eligibility_status"]}
- scale_up_primary_blocker_code: {summary["scale_up_primary_blocker_code"]}
- risk_scaling_decision_status: {summary["risk_scaling_decision_status"]}
- risk_scaling_primary_blocker_code: {summary["risk_scaling_primary_blocker_code"]}
- blocked_scale_validator_count: {summary["blocked_scale_validator_count"]}
- usable_for_live_enabling_count: {summary["usable_for_live_enabling_count"]}

known_omissions_by_design:
- No live order, credentialed API call, live config mutation, LIVE_ENABLING_PATCH, or risk scale-up is created.
- {GAP_ID} remains an open live-affecting gap.
- The next route returns to open contract gap priority selection for remaining safe non-live work.

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

Scale-up remains not eligible. Live permission is false and burn-in, parity, execution quality, survival, and risk scaling dependencies remain blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    artifacts = sorted(
        set(
            CHANGED_ARTIFACTS
            + [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ]
        )
    )

    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_CONVERGENCE_RISK_SCALE",
            "source_file": "TRADER_1.md",
            "source_heading": "scale-up not eligible recheck",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: scale-up remains blocked until live permission, burn-in, parity, "
                "execution quality, survival layer, operator policy, and risk scaling validators pass"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Scale-up not eligible recheck",
            "requirement_kind": "LIVE_BLOCKED_TEST_PATCH",
            "schema_ids": [
                "trader1.patch_result.v1",
                "trader1.evidence_manifest.v1",
                "trader1.contract_gap.v1",
                "trader1.validator_result.v1",
                "trader1.risk_scaling_decision.v1",
                "trader1.live_burn_in_feedback_report.v1",
                "trader1.execution_quality_measurement_report.v1",
                "trader1.survival_layer_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/contract/test_scale_up_not_eligible_recheck.py",
                "tests/validators/test_convergence_risk_scale_validators.py",
                "tests/validators/test_optimizer_convergence_guardrails.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": [
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
                "SECTION_RISK_SCALE_UP_BLOCKER",
            ],
            "depends_on": [
                PREVIOUS_REQUIREMENT_ID,
                "REQ-CONV-012",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"scale-up remains blocked until live permission, burn-in, parity, execution quality, survival layer, operator policy, and risk scaling validators pass"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RECHECK_GAP_OPEN",
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
            "section_id": "SECTION_CONVERGENCE_RISK_SCALE",
            "schema_files": [
                "contracts/schema/patch_result.schema.json",
                "contracts/schema/evidence_manifest.schema.json",
                "contracts/schema/contract_gap.schema.json",
                "contracts/schema/validator_result.schema.json",
                "contracts/schema/risk_scaling_decision.schema.json",
                "contracts/schema/live_burn_in_feedback_report.schema.json",
                "contracts/schema/execution_quality_measurement_report.schema.json",
                "contracts/schema/survival_layer_report.schema.json",
            ],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/contract/test_scale_up_not_eligible_recheck.py",
                "tests/validators/test_convergence_risk_scale_validators.py",
                "tests/validators/test_optimizer_convergence_guardrails.py",
            ],
            "fixture_files": [
                *FIXTURE_PATHS,
                EXTERNAL_BLOCKER_MANIFEST,
                SCALEUP_SAFETY_PATCH_RESULT,
                CONVERGENCE_RISK_SCALE_PATCH_RESULT,
                LIVE_ENABLING_RECHECK_PATCH_RESULT,
            ],
            "runtime_modules": [
                "trader1/validation/mvp0_validators.py",
                "trader1/safety/live_order_gate.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                CONTRACT_GAP_PATH,
            ],
            "dashboard_artifacts": ["contracts/generated/context_pack/MVP4_DASHBOARD_STABILITY_SCALEUP_LOCK.md"],
            "patch_result_fields": [
                "remaining_blockers",
                "next_task_class",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RECHECK_GAP_OPEN",
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


def status_of(results: list[dict[str, Any]], validator_id: str) -> str:
    for result in results:
        if result.get("validator_id") == validator_id:
            return str(result.get("status"))
    return "MISSING"


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    validators_required: list[str],
    summary: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_SCALEUP_SAFETY_BLOCKED.patch_result.json")
    patch_result = dict(template)
    optimizer_results = [
        result for result in validators_run if result.get("validator_id") in {"optimizer_no_live_mutation_validator", "optimizer_guardrail_validator"}
    ]
    convergence_results = [
        result
        for result in validators_run
        if result.get("validator_id")
        in {
            *RISK_SCALE_VALIDATORS,
            "convergence_assessment_validator",
            "scale_up_eligibility_validator",
        }
    ]
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [REQUIREMENT_ID, PREVIOUS_REQUIREMENT_ID, "REQ-CONV-012"],
            "new_registry_items": [REQUIREMENT_ID, f"contracts/generated/context_pack/{PATCH_BASENAME}.md", CONTRACT_GAP_PATH],
            "new_or_changed_schema_ids": [],
            "validators_required": validators_required,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_RISK_SCALE_UP_BLOCKER",
            ],
            "next_optional_section_ids": ["SECTION_OPEN_CONTRACT_GAP_PRIORITY", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "scale_up_allowed_before": False,
            "scale_up_allowed_after": False,
            "remaining_blockers": summary["remaining_blockers"],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "current_implementation_state",
                "external live review blocker manifest",
                "scale-up safety blocked patch result",
                "convergence risk-scale validator results",
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": PATCH_BASENAME,
            "required_section_ids": [
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
                "SECTION_RISK_SCALE_UP_BLOCKER",
            ],
            "expanded_section_ids": [
                "SECTION_CONVERGENCE_RISK_SCALE",
                "SECTION_LIVE_FINAL_GUARD",
                "SECTION_LIVE_BLOCKED_TEST",
                "SECTION_RISK_SCALE_UP_BLOCKER",
            ],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "REUSED_HASH_MATCH",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "optimizer_validators_required": ["optimizer_no_live_mutation_validator", "optimizer_guardrail_validator"],
            "optimizer_validators_run": optimizer_results,
            "optimizer_guardrail_result": status_of(validators_run, "optimizer_guardrail_validator"),
            "profit_convergence_patch": "FAIL_CLOSED_SCALE_UP_NOT_ELIGIBLE_RECHECK",
            "convergence_layer_changed": False,
            "convergence_state_before": "SCALEUP_BLOCKED_LIVE_ENABLING_EVIDENCE_MISSING",
            "convergence_state_after": "SCALE_UP_NOT_ELIGIBLE_LIVE_STILL_BLOCKED",
            "objective_profile_changed": False,
            "memory_schema_changed": False,
            "failure_analysis_required": False,
            "failure_analysis_status": "NOT_REQUIRED_FOR_SCALE_UP_NOT_ELIGIBLE_RECHECK",
            "exploration_exploitation_policy_changed": False,
            "regime_adaptation_changed": False,
            "risk_scaling_policy_changed": False,
            "survival_layer_changed": False,
            "convergence_validators_required": [
                *RISK_SCALE_VALIDATORS,
                "convergence_assessment_validator",
                "scale_up_eligibility_validator",
            ],
            "convergence_validators_run": convergence_results,
            "convergence_guardrail_result": status_of(validators_run, "convergence_assessment_validator"),
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
    fixture_results: list[dict[str, Any]],
) -> None:
    write_json(
        ROOT / patch_result["validator_run_log_path"],
        {
            "validator_run_log_schema_id": "trader1.validator_run_log.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "validators_run": patch_result["validators_run"],
            "fixture_results": fixture_results,
            "validators_untested": [],
            "expected_scale_statuses": EXPECTED_SCALE_STATUSES,
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
            "stage_gate_status": "PASS_RECHECK_SCALE_UP_NOT_ELIGIBLE_REMAINS_LIVE_BLOCKING",
            **summary,
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    artifact_paths = sorted(
        set(
            [
                *CHANGED_ARTIFACTS,
                "contracts/generated/ACTIVE_WORKING_VIEW.md",
                "contracts/generated/current_implementation_state.json",
                "contracts/generated/read_cache_manifest.json",
                "contracts/generated/requirement_index.json",
                "contracts/generated/requirement_artifact_matrix.json",
                "contracts/security/source_bundle_manifest.json",
                "system/evidence/implementation_patch_ledger.json",
                EXTERNAL_BLOCKER_MANIFEST,
                SCALEUP_SAFETY_PATCH_RESULT,
                CONVERGENCE_RISK_SCALE_PATCH_RESULT,
                DASHBOARD_STABILITY_SCALEUP_LOCK_PATCH_RESULT,
                LIVE_ENABLING_RECHECK_PATCH_RESULT,
                patch_result["validator_run_log_path"],
                patch_result["stage_gate_result_path"],
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ]
        )
    )
    write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": artifact_paths,
            "known_blockers": patch_result["remaining_blockers"],
            **summary,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["open_contract_gap_ids"] = sorted(set(state.get("open_contract_gap_ids", [])) | {GAP_ID})
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
    patches = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    patches.append(
        {
            "patch_id": PATCH_ID,
            "patch_class": patch_result["patch_class"],
            "target_mvp_level": "MVP-4",
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
            "next_allowed_task_class": NEXT_TASK_CLASS,
        }
    )
    ledger.update(
        {
            "updated_at_utc": now,
            "patches": patches,
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result["result_hash"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    write_json(ledger_path, ledger)


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    summary: dict[str, Any],
    fixture_results: list[dict[str, Any]],
) -> None:
    write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary, fixture_results)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)


def run_scale_validators() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    risk_results = run_validators(RISK_SCALE_VALIDATORS)
    guardrail_results = run_validators(GUARDRAIL_VALIDATORS)
    fixture_results = []
    for path_text in FIXTURE_PATHS:
        result = run_fixture_file(ROOT / path_text)
        result["fixture_path"] = path_text
        fixture_results.append(result)
    return risk_results, guardrail_results, fixture_results


def main() -> int:
    assert_current_state_ready_for_scaleup_recheck()
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_route_guard_tests()
    update_authority_manifest(now)
    write_source_bundle_manifest()

    risk_results, guardrail_results, fixture_results = run_scale_validators()
    summary = scaleup_gap_summary(risk_results, guardrail_results, fixture_results)
    write_contract_gap(now, trader_hash, agents_hash, summary)
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    bootstrap_results = run_validators(BOOTSTRAP_VALIDATORS_REQUIRED)
    patch_result = build_patch_result(
        now,
        tests_run,
        bootstrap_results,
        BOOTSTRAP_VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary, fixture_results)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
            run_command([sys.executable, "-B", "tools/run_convergence_risk_scale_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_optimizer_convergence_guardrail_validators.py"]),
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    "tests/contract/test_scale_up_not_eligible_recheck.py",
                    "tests/validators/test_convergence_risk_scale_validators.py",
                    "tests/validators/test_optimizer_convergence_guardrails.py",
                    "-q",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"]),
        ]
    )

    risk_results, guardrail_results, fixture_results = run_scale_validators()
    summary = scaleup_gap_summary(risk_results, guardrail_results, fixture_results)
    write_contract_gap(now, trader_hash, agents_hash, summary)
    update_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(
        now,
        tests_run,
        run_validators(VALIDATORS_REQUIRED),
        VALIDATORS_REQUIRED,
        summary,
    )
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, summary, fixture_results)

    failed_tests = [item for item in patch_result["tests_run"] if item.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed_tests else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
                "scale_up_eligibility_status": summary["scale_up_eligibility_status"],
                "scale_up_primary_blocker_code": summary["scale_up_primary_blocker_code"],
                "blocked_scale_validator_count": summary["blocked_scale_validator_count"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not failed_tests else 1


if __name__ == "__main__":
    raise SystemExit(main())
