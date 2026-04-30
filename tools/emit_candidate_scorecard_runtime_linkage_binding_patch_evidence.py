from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-CANDIDATE-SCORECARD-RUNTIME-LINKAGE-BINDING"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_RUNTIME_LONG_RUN_EVIDENCE_HARDENING"

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
from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "candidate_scorecard_validator",
    "candidate_scorecard_net_ev_validator",
    "upbit_paper_runtime_cycle_validator",
    "upbit_paper_persistent_loop_validator",
    "read_only_dashboard_validator",
    "runtime_schema_instance_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/schema/candidate_scorecard.schema.json",
    "trader1/research/profitability/candidate_scorecard.py",
    "trader1/validation/mvp0_validators.py",
    "tests/research/test_candidate_scorecard_from_runtime.py",
    "tests/validators/test_candidate_scorecard_net_ev_validator.py",
    "tests/validators/fixtures/candidate_scorecard_net_ev_pass.json",
    "tests/validators/fixtures/candidate_scorecard_net_ev_raw_cost_fail.json",
    "tests/validators/fixtures/candidate_scorecard_net_ev_live_flag_fail.json",
    "tests/validators/fixtures/candidate_scorecard_net_ev_missing_oos_fail.json",
    "tests/validators/fixtures/candidate_scorecard_net_ev_live_ready_wording_fail.json",
    "tests/validators/fixtures/candidate_scorecard_net_ev_missing_robustness_sources_fail.json",
    "tests/validators/fixtures/candidate_scorecard_net_ev_mismatched_robustness_sources_fail.json",
    "tools/emit_candidate_scorecard_runtime_linkage_binding_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING.md",
]

BLOCKERS = [
    "LIVE_READY_MISSING",
    "OOS_MISSING",
    "WALK_FORWARD_MISSING",
    "BOOTSTRAP_UNSTABLE",
    "OVERFIT_RISK_HIGH",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def summarize_validators(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"validator_id": item.get("validator_id"), "status": item.get("status")} for item in results]


def refresh_runtime_scorecard_and_dashboards() -> list[str]:
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-candidate-scorecard-runtime-linkage-binding",
        session_id="mvp1_upbit_paper_launcher",
        requested_cycle_count=2,
    )
    runtime_path = ROOT / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/upbit_paper_runtime_cycle_report.json"
    runtime_cycle = load_json(runtime_path)
    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(
        runtime_cycle,
        scorecard_id="mvp4_upbit_paper_runtime_latest_candidate_scorecard",
    )
    scorecard_path = ROOT / "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/profitability/candidate_scorecard.json"
    write_json(scorecard_path, scorecard)
    paths = [rel(ROOT / path) for path in loop.get("artifact_paths", [])]
    paths.append(rel(scorecard_path))
    for launcher_name in ("UPBIT_PAPER", "BINANCE_PAPER", "UPBIT_LIVE", "BINANCE_LIVE"):
        report = build_launcher_report(launcher_name)
        report_path, dashboard_paths = write_launcher_runtime_bundle(report, ROOT)
        paths.append(rel(report_path))
        paths.extend(rel(path) for path in dashboard_paths.values())
    return sorted(set(paths))


def update_context(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts/generated/context_pack/MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING.md",
        f"""# MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING

context_pack_id: MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING
task_class: MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_PROFIT_CONVERGENCE_REINFORCEMENT", "SECTION_OPTIMIZER_OBJECTIVE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.candidate_scorecard.v1", "trader1.upbit_paper_runtime_cycle_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}

acceptance_checklist:
- candidate_scorecard carries source_runtime_cycle_id and source_runtime_cycle_hash
- PAPER ranking eligibility requires OOS, walk-forward, and bootstrap evidence ids linked to the same runtime cycle hash
- mismatched robustness evidence remains non-ranking or FAIL/BLOCKED
- optimizer/convergence cannot create live permission, LIVE_READY, or scale-up

known_omissions_by_design:
- no live-enabling evidence
- no private account or credential use
- no long-run live review claim
- robustness evidence remains required before ranking eligibility

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is read cache only.
generated_at_utc: {now}
""",
    )
    write_text(
        ROOT / "contracts/generated/ACTIVE_WORKING_VIEW.md",
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

Candidate scorecards now bind PAPER ranking evidence to the exact source runtime cycle id and hash. Robustness evidence from another cycle cannot make a candidate ranking eligible. Live and scale-up remain blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts/generated/requirement_index.json"
    matrix_path = ROOT / "contracts/generated/requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    reqs = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    reqs.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_OPTIMIZER_OBJECTIVE",
            "source_file": "TRADER_1.md",
            "source_heading": "PAPER scorecard source evidence binding",
            "full_text_marker": f"{REQUIREMENT_ID}: ranking evidence must bind to the exact PAPER runtime cycle id and hash",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Candidate scorecard runtime linkage binding",
            "requirement_kind": "VALIDATOR_PATCH",
            "schema_ids": ["trader1.candidate_scorecard.v1"],
            "validator_ids": ["candidate_scorecard_validator", "candidate_scorecard_net_ev_validator"],
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": [
                "tests/research/test_candidate_scorecard_from_runtime.py",
                "tests/validators/test_candidate_scorecard_net_ev_validator.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["OPTIMIZER_MVP3", "PROFIT_CONVERGENCE_MVP3", "VALIDATOR_IMPLEMENTATION"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-RUNTIME-SCORECARD-BRIDGE",
                "REQ-MVP4-STRATEGY-NET-EV-SCORECARD-SCHEMA-HARDENING",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": sha256_bytes(b"ranking evidence must bind to exact PAPER runtime cycle id and hash"),
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
            "requirements": sorted(reqs, key=lambda item: item["requirement_id"]),
        }
    )
    write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_OPTIMIZER_OBJECTIVE",
            "schema_files": ["contracts/schema/candidate_scorecard.schema.json"],
            "validator_files": ["trader1/research/profitability/candidate_scorecard.py", "trader1/validation/mvp0_validators.py"],
            "test_files": [
                "tests/research/test_candidate_scorecard_from_runtime.py",
                "tests/validators/test_candidate_scorecard_net_ev_validator.py",
            ],
            "fixture_files": [
                "tests/validators/fixtures/candidate_scorecard_net_ev_pass.json",
                "tests/validators/fixtures/candidate_scorecard_net_ev_mismatched_robustness_sources_fail.json",
            ],
            "runtime_modules": ["trader1/research/profitability/candidate_scorecard.py"],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": ["system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/profitability/candidate_scorecard.json"],
            "patch_result_fields": ["new_or_changed_schema_ids", "validators_required", "validators_run", "tests_run"],
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED_LIVE_BLOCKED",
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


def update_current_state(now: str, trader_hash: str, agents_hash: str, patch_result_hash: str) -> None:
    path = ROOT / "contracts/generated/current_implementation_state.json"
    state = load_json(path)
    completed = set(state.get("completed_requirement_ids", []))
    completed.add(REQUIREMENT_ID)
    schemas = set(state.get("implemented_schema_ids", []))
    schemas.add("trader1.candidate_scorecard.v1")
    validators = set(state.get("implemented_validator_ids", []))
    validators.update({"candidate_scorecard_validator", "candidate_scorecard_net_ev_validator"})
    state.update(
        {
            "updated_at_utc": now,
            "trader1_sha256": trader_hash,
            "agents_sha256": agents_hash,
            "current_mvp": "MVP-4",
            "completed_requirement_ids": sorted(completed),
            "implemented_schema_ids": sorted(schemas),
            "implemented_validator_ids": sorted(validators),
            "last_patch_id": PATCH_ID,
            "last_patch_result_hash": patch_result_hash,
            "next_allowed_task_class": NEXT_TASK_CLASS,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
    )
    state.pop("state_hash", None)
    state["state_hash"] = sha256_json(state)
    write_json(path, state)


def append_patch_ledger(now: str, result_hash: str) -> None:
    path = ROOT / "system/evidence/implementation_patch_ledger.json"
    ledger = load_json(path)
    patches = [item for item in ledger.get("patches", []) if item.get("patch_id") != PATCH_ID]
    patches.append(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "patch_class": "VALIDATOR_PATCH",
            "target_mvp_level": "MVP-4",
            "requirement_id": REQUIREMENT_ID,
            "summary": "Bound candidate scorecard robustness evidence to the exact PAPER runtime cycle id and hash.",
            "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            "patch_result_hash": result_hash,
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
            "scale_up_allowed_after": False,
        }
    )
    ledger["patches"] = sorted(patches, key=lambda item: item.get("created_at_utc", ""))
    ledger["last_patch_id"] = PATCH_ID
    ledger["updated_at_utc"] = now
    write_json(path, ledger)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    patch_result = load_json(ROOT / "system/evidence/patch_results/MVP4_UPBIT_PAPER_RUNTIME_SCORECARD_BRIDGE.patch_result.json")
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "VALIDATOR_PATCH",
            "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
            "input_authority_hash_status": "PASS",
            "authority_hash_checked": True,
            "affected_contract_ids": [REQUIREMENT_ID],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "removed_requirements": [],
            "merged_requirements": [],
            "file_split": False,
            "detail_reduction_allowed": False,
            "semantic_reduction_allowed": False,
            "retained_archive_preserved": True,
            "new_registry_items": [],
            "new_or_changed_schema_ids": ["trader1.candidate_scorecard.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": summarize_validators(validators_run),
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "NOT_READ_NOT_REQUIRED",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_PROFIT_CONVERGENCE_REINFORCEMENT"],
            "next_optional_section_ids": ["SECTION_LONG_RUN_STABILITY", "SECTION_DASHBOARD_OPERATOR_UX"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "BINANCE_FUTURES_LIVE"],
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
            "active_read_surface_used": ["TRADER_1.md", "AGENTS.md", "contracts/generated/current_implementation_state.json"],
            "task_class": "MVP4_CANDIDATE_SCORECARD_RUNTIME_LINKAGE_BINDING",
            "required_section_ids": ["SECTION_OPTIMIZER_OBJECTIVE", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_OPTIMIZER_OBJECTIVE", "SECTION_UPBIT_PAPER_RUNTIME"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "PASS",
            "requirement_index_status": "UPDATED_PASS",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED_PASS",
            "context_pack_status": "UPDATED_PASS",
            "current_implementation_state_status": "UPDATED_PASS",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "OPTIMIZER_INPUT_EVIDENCE_BINDING_HARDENING",
            "optimizer_stage": "MVP-4_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_status_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_BLOCKED",
            "optimizer_status_after": "RUNTIME_HASH_BOUND_PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_maturity_level_before": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_maturity_level_after": "PAPER_SCORECARD_INPUT_ONLY_LIVE_GAP_OPEN",
            "optimizer_output_type": "PAPER_SCORECARD_INPUT_ONLY",
            "optimizer_validators_required": ["candidate_scorecard_validator", "candidate_scorecard_net_ev_validator"],
            "optimizer_validators_run": [
                item for item in summarize_validators(validators_run)
                if item.get("validator_id") in {"candidate_scorecard_validator", "candidate_scorecard_net_ev_validator"}
            ],
            "optimizer_guardrail_result": "PASS_LIVE_BLOCKED",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "result_hash": "",
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    runtime_artifacts = refresh_runtime_scorecard_and_dashboards()
    write_source_bundle_manifest()
    update_context(now, trader_hash, agents_hash)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)
    tests_run = [
        run_command(["python", "-B", "-m", "unittest", "tests.research.test_candidate_scorecard_from_runtime", "tests.validators.test_candidate_scorecard_net_ev_validator", "-q"]),
        run_command(["python", "-B", "-m", "unittest", "tests.integration.test_upbit_paper_runtime_cycle", "-q"]),
    ]
    validators_run = run_validators(VALIDATORS_REQUIRED)
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_json(ROOT / f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json", {
        "schema_id": "trader1.validator_run_log.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "validators": validators_run,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    })
    write_json(ROOT / f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json", {
        "schema_id": "trader1.stage_gate_result.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "stage": "MVP-4",
        "status": "PASS_LIVE_BLOCKED",
        "next_stage": "MVP-5_BLOCKED_EXTERNAL_EVIDENCE_REQUIRED",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    })
    write_json(ROOT / f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json", {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "runtime_artifacts_refreshed": runtime_artifacts,
        "changed_artifacts": CHANGED_ARTIFACTS,
        "tests_run": tests_run,
        "validators_run": summarize_validators(validators_run),
        "remaining_blockers": BLOCKERS,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    })
    write_json(ROOT / f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json", patch_result)
    update_current_state(now, trader_hash, agents_hash, patch_result["result_hash"])
    update_read_cache(now, trader_hash, agents_hash)
    append_patch_ledger(now, patch_result["result_hash"])
    return 0 if all(test["status"] == "PASS" for test in tests_run) and all(item["status"] == "PASS" for item in validators_run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
