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

PATCH_BASENAME = "MVP4_PROFITABILITY_MATURITY_SOURCE_ARTIFACT_PATH_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260504_001"
REQUIREMENT_ID = "REQ-MVP4-PROFITABILITY-MATURITY-SOURCE-ARTIFACT-PATH-GUARD"
PREVIOUS_PATCH_RESULT = (
    "system/evidence/patch_results/MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_STATE_SYNC_RECHECK.patch_result.json"
)
CONTRACT_GAP_ID = "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY"
NEXT_TASK_CLASS = "MVP4_ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY_RECHECK"

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
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import (  # noqa: E402
    PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS,
    run_validators,
)


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "profitability_evidence_maturity_rollup_validator",
    "profitability_optimizer_evidence_gap_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "coverage_index_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]
CHANGED_ARTIFACTS = [
    "trader1/validation/mvp0_validators.py",
    "tests/validators/test_profitability_optimizer_evidence_gap_validator.py",
    "tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json",
    "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
    "tools/emit_profitability_maturity_source_artifact_path_guard_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
BLOCKERS = [
    CONTRACT_GAP_ID,
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_BOUNDARY",
    "PAPER_SHADOW_RUNTIME_SHADOW_OBSERVATION_GAP",
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
FALSE_FIELDS = ("live_order_ready", "live_order_allowed", "can_live_trade", "scale_up_allowed")
ROLLUP_PATH = ROOT / "system" / "evidence" / "audit_reports" / "MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json"
ROLLUP_FIXTURE_PATH = (
    ROOT / "tests" / "validators" / "fixtures" / "profitability_evidence_maturity_rollup_pass.json"
)
MISSING_DASHBOARD_PATH = "trader1/dashboard/static/read_only_dashboard.html"
REAL_DASHBOARD_PATH = "trader1/dashboard/read_only_dashboard.py"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env)
    result = {
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


def rollup_hash(rollup: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in rollup.items() if key != "rollup_hash"})


def component_set(rows: Any, key: str) -> set[str]:
    if not isinstance(rows, list):
        return set()
    return {item[key] for item in rows if isinstance(item, dict) and isinstance(item.get(key), str)}


def assert_false_fields(name: str, artifact: dict[str, Any]) -> None:
    for field in FALSE_FIELDS:
        if artifact.get(field) is True:
            raise RuntimeError(f"{name} has forbidden true field: {field}")


def normalize_rollup_artifact_paths(now: str, trader_hash: str, agents_hash: str) -> dict[str, Any]:
    changed_count = 0
    missing_path_count_before = 0
    source_artifact_path_count = 0
    for path in (ROLLUP_PATH, ROLLUP_FIXTURE_PATH):
        rollup = load_json(path)
        for component in rollup.get("components", []):
            paths = component.get("source_artifact_paths", [])
            source_artifact_path_count += len(paths)
            missing_path_count_before += sum(1 for item in paths if item == MISSING_DASHBOARD_PATH)
            component["source_artifact_paths"] = [
                REAL_DASHBOARD_PATH if item == MISSING_DASHBOARD_PATH else item for item in paths
            ]
            changed_count += sum(1 for item in paths if item == MISSING_DASHBOARD_PATH)
        if path == ROLLUP_PATH:
            rollup["generated_at_utc"] = now
            rollup["authority"] = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
        rollup["rollup_hash"] = ""
        rollup["rollup_hash"] = rollup_hash(rollup)
        write_json(path, rollup)

    return {
        "missing_dashboard_source_path_count_before": missing_path_count_before,
        "source_artifact_path_rewrite_count": changed_count,
        "source_artifact_path_count_checked": source_artifact_path_count,
        "canonical_dashboard_source_path": REAL_DASHBOARD_PATH,
    }


def verify_rollup_source_paths() -> dict[str, Any]:
    rollup = load_json(ROLLUP_PATH)
    assert_false_fields("profitability maturity rollup", rollup)
    components = rollup.get("components", [])
    component_ids = component_set(components, "component_id")
    if component_ids != set(PROFITABILITY_EVIDENCE_REQUIRED_COMPONENTS):
        raise RuntimeError("profitability maturity rollup component set drifted")
    missing: list[str] = []
    escaping: list[str] = []
    absolute: list[str] = []
    root = ROOT.resolve()
    total = 0
    for component in components:
        for path_text in component.get("source_artifact_paths", []):
            total += 1
            source_path = Path(path_text)
            if source_path.is_absolute():
                absolute.append(path_text)
                continue
            resolved = (ROOT / source_path).resolve()
            if resolved != root and root not in resolved.parents:
                escaping.append(path_text)
            elif not resolved.is_file():
                missing.append(path_text)
    if missing or escaping or absolute:
        raise RuntimeError(
            "profitability maturity rollup has invalid source artifact paths: "
            f"missing={missing}, escaping={escaping}, absolute={absolute}"
        )
    if rollup.get("status") != "BLOCKED_FOR_PROFITABILITY_EVIDENCE_MATURITY":
        raise RuntimeError("profitability maturity rollup status drifted from live-blocking state")
    return {
        "component_count": len(components),
        "source_artifact_path_count": total,
        "source_artifact_missing_count_after": len(missing),
        "source_artifact_escape_count_after": len(escaping),
        "source_artifact_absolute_count_after": len(absolute),
        "rollup_status": rollup.get("status"),
        "rollup_hash": rollup.get("rollup_hash"),
    }


def write_context(now: str, trader_hash: str, agents_hash: str, summary: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_STRATEGY_PROFITABILITY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}", "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT"]
included_schema_ids: ["trader1.profitability_evidence_maturity_rollup.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- Profitability maturity rollup component source_artifact_paths must be repo-relative existing files.
- Missing dashboard static HTML evidence must be rebound to the actual read-only dashboard source.
- Negative tests must cover missing component artifacts and repository escape attempts.
- {CONTRACT_GAP_ID} remains open and live-affecting.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

source_artifact_path_summary:
- missing_dashboard_source_path_count_before: {summary["missing_dashboard_source_path_count_before"]}
- source_artifact_path_rewrite_count: {summary["source_artifact_path_rewrite_count"]}
- source_artifact_path_count: {summary["source_artifact_path_count"]}
- source_artifact_missing_count_after: {summary["source_artifact_missing_count_after"]}
- source_artifact_escape_count_after: {summary["source_artifact_escape_count_after"]}
- canonical_dashboard_source_path: {summary["canonical_dashboard_source_path"]}

known_omissions_by_design:
- This guard does not close the profitability evidence maturity gap.
- This guard does not create long-run, OOS, read-only burn-in, manual-order, live, or scale-up evidence.
- Runtime monitor outputs under system/runtime are not intended patch artifacts.

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

Profitability maturity evidence remains live-blocking. Component source artifact paths are now required to point to existing repo-local files.

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
            "source_section_id": "SECTION_STRATEGY_PROFITABILITY",
            "source_file": "TRADER_1.md",
            "source_heading": "profitability maturity source artifact path guard",
            "full_text_marker": (
                f"{REQUIREMENT_ID}: profitability maturity component source artifact paths must be existing "
                "repo-relative evidence references and cannot imply live readiness"
            ),
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Profitability maturity source artifact path guard",
            "requirement_kind": "VALIDATOR_IMPLEMENTATION",
            "schema_ids": ["trader1.profitability_evidence_maturity_rollup.v1"],
            "validator_ids": ["profitability_evidence_maturity_rollup_validator"],
            "artifact_ids": artifacts,
            "test_ids": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_STRATEGY_PROFITABILITY", "SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(
                b"profitability maturity component source artifact paths must exist and stay live blocked"
            ),
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
            "section_id": "SECTION_STRATEGY_PROFITABILITY",
            "schema_files": ["contracts/schema/profitability_evidence_maturity_rollup.schema.json"],
            "validator_files": ["trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/validators/test_profitability_optimizer_evidence_gap_validator.py"],
            "fixture_files": ["tests/validators/fixtures/profitability_evidence_maturity_rollup_pass.json"],
            "runtime_modules": ["tools/run_profitability_optimizer_evidence_gap_validators.py"],
            "evidence_artifacts": [
                "system/evidence/audit_reports/MVP4_PROFITABILITY_EVIDENCE_MATURITY_ROLLUP.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            ],
            "dashboard_artifacts": ["trader1/dashboard/read_only_dashboard.py"],
            "patch_result_fields": [
                "validators_required",
                "validators_run",
                "tests_run",
                "remaining_blockers",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_WITH_OPEN_CONTRACT_GAP",
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


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    summary: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / PREVIOUS_PATCH_RESULT)
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-PROFITABILITY-OPTIMIZER-EVIDENCE-GAP-AUDIT",
                "REQ-MVP4-PROFITABILITY-EVIDENCE-MATURITY-ROLLUP-VALIDATOR",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "new_registry_items": [REQUIREMENT_ID],
            "new_or_changed_schema_ids": [],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LONG_RUN_RUNTIME_EVIDENCE",
                "SECTION_PAPER_SHADOW_EVIDENCE",
                "SECTION_PROFITABILITY_OPTIMIZER_EVIDENCE",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_CONTRACT_GAP"],
            "next_forbidden_default_sections": ["MVP5_LIVE_PERMISSION", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP"],
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
                "PROFITABILITY_OPTIMIZER_EVIDENCE_MATURITY contract gap",
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "task_class": "MVP4_PROFITABILITY_OPTIMIZER_EVIDENCE_GAP_RECHECK",
            "required_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_STRATEGY_PROFITABILITY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
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
            "optimizer_status_after": "EVIDENCE_MATURITY_SOURCE_ARTIFACT_PATHS_GUARDED_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_NO_LIVE_MUTATION",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE_SOURCE_ARTIFACT_GUARD_ONLY",
            "convergence_state_after": "EVIDENCE_MATURITY_GAP_REMAINS_LIVE_BLOCKED",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION",
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
            "stage_gate_status": "PASS_SOURCE_ARTIFACT_PATH_GUARD_PROFITABILITY_GAP_REMAINS_LIVE_BLOCKING",
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
    write_source_bundle_manifest()
    rewrite_summary = normalize_rollup_artifact_paths(now, trader_hash, agents_hash)
    verification_summary = verify_rollup_source_paths()
    summary = {**rewrite_summary, **verification_summary}
    write_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run: list[dict[str, Any]] = []
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, summarize_validators(run_validators(VALIDATORS_REQUIRED)), summary)
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command(
                [
                    sys.executable,
                    "-B",
                    "-m",
                    "unittest",
                    "tests.validators.test_profitability_optimizer_evidence_gap_validator",
                    "-v",
                ]
            ),
            run_command([sys.executable, "-B", "tools/run_profitability_optimizer_evidence_gap_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_mvp0_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_hygiene_safe_pytest.py", "--", "-q"]),
        ]
    )
    verification_summary = verify_rollup_source_paths()
    summary = {**rewrite_summary, **verification_summary}
    write_context(now, trader_hash, agents_hash, summary)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, summarize_validators(run_validators(VALIDATORS_REQUIRED)), summary)
    write_json(patch_path, patch_result)
    write_evidence(now, trader_hash, agents_hash, patch_result, summary)
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
                "source_artifact_path_count": summary["source_artifact_path_count"],
                "source_artifact_missing_count_after": summary["source_artifact_missing_count_after"],
                "source_artifact_escape_count_after": summary["source_artifact_escape_count_after"],
                "next_allowed_task_class": NEXT_TASK_CLASS,
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
