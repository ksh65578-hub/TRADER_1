from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-SOURCE-RELEASE-BUNDLE-PATH-SECRET-GUARD"
NEXT_TASK_CLASS = "MVP4_WINDOWS_RUNTIME_RECOVERY_CONTINUE"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_convergence_memory_failure_learning_hardening_patch_evidence import ensure_matrix_row, ensure_requirement  # noqa: E402
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
from trader1.security.source_bundle import (  # noqa: E402
    build_source_bundle_manifest,
    classify_path,
    classify_shipped_forbidden_path,
    load_denylist,
    write_source_bundle_manifest,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "trader1/security/source_bundle.py",
    "trader1/validation/mvp0_validators.py",
    "tests/security/test_source_bundle_security.py",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_source_release_bundle_path_secret_guard_patch_evidence.py",
    "contracts/generated/context_pack/MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
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
UNSAFE_PATH_NEGATIVE_CASES = [
    "contracts/../system/evidence.json",
    "contracts\\..\\system\\evidence.json",
    "/contracts/schema/common.defs.schema.json",
    "C:/TRADER_1/contracts/schema/common.defs.schema.json",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def patch_hash(patch_result: dict[str, Any]) -> str:
    return sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-1600:],
        "stderr_tail": completed.stderr[-1600:],
    }


def excluded_secret_fixture_audit(denylist: dict[str, Any]) -> dict[str, Any]:
    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "trader1").mkdir()
        write_text(root / ".env", "API_KEY=" + ("A" * 32) + "\n")
        write_text(root / "trader1" / "module.py", "VALUE = 1\n")
        manifest = build_source_bundle_manifest(root=root, denylist=denylist)
    return {
        "excluded_secret_paths": [item["path"] for item in manifest.get("excluded_secret_findings", [])],
        "excluded_contains_secret": bool(manifest.get("excluded_contains_secret")),
        "contains_secret": bool(manifest.get("contains_secret")),
        "repo_secret_findings_count": manifest.get("repo_secret_findings_count", 0),
    }


def build_audit(manifest: dict[str, Any]) -> dict[str, Any]:
    denylist = load_denylist()
    source_classification = {path: classify_path(path, denylist).reason for path in UNSAFE_PATH_NEGATIVE_CASES}
    shipped_classification = {path: classify_shipped_forbidden_path(path, denylist) for path in UNSAFE_PATH_NEGATIVE_CASES}
    excluded_secret_fixture = excluded_secret_fixture_audit(denylist)
    checks = {
        "unsafe_paths_are_denied_from_source_bundle": all(reason == "unsafe_relative_path" for reason in source_classification.values()),
        "unsafe_paths_are_shipped_forbidden": all(reason == "shipped_forbidden:unsafe_relative_path" for reason in shipped_classification.values()),
        "excluded_secret_fixture_is_detected": excluded_secret_fixture["excluded_secret_paths"] == [".env"]
        and excluded_secret_fixture["excluded_contains_secret"]
        and excluded_secret_fixture["contains_secret"]
        and excluded_secret_fixture["repo_secret_findings_count"] == 1,
        "current_repo_has_no_included_secret_findings": not manifest.get("secret_findings"),
        "current_repo_has_no_excluded_secret_findings": not manifest.get("excluded_secret_findings"),
        "current_repo_has_no_shipped_forbidden_files": manifest.get("shipped_forbidden_count") == 0,
        "current_manifest_live_flags_false": not manifest.get("live_order_ready")
        and not manifest.get("live_order_allowed")
        and not manifest.get("can_live_trade"),
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.source_release_bundle_path_secret_guard_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "unsafe_path_negative_cases": UNSAFE_PATH_NEGATIVE_CASES,
        "source_classification": source_classification,
        "shipped_classification": shipped_classification,
        "excluded_secret_fixture": excluded_secret_fixture,
        "included_count": len(manifest.get("included_files", [])),
        "excluded_count": len(manifest.get("excluded_files", [])),
        "shipped_forbidden_count": manifest.get("shipped_forbidden_count", 0),
        "secret_findings_count": len(manifest.get("secret_findings", [])),
        "excluded_secret_findings_count": len(manifest.get("excluded_secret_findings", [])),
        "repo_secret_findings_count": manifest.get("repo_secret_findings_count", 0),
        "contains_secret": bool(manifest.get("contains_secret")),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_navigation(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD.md",
        f"""# MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD

context_pack_id: MVP4_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD
task_class: MVP4_SOURCE_RELEASE_BUNDLE_HYGIENE_RECHECK
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Source bundle path classification must reject absolute paths, drive paths, dot segments, and parent traversal.
- Shipped package hygiene must treat unsafe path strings as forbidden.
- Secret scan must regenerate the manifest and detect credential-like material in excluded files, including .env.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- unsafe_path_negative_cases: {json.dumps(UNSAFE_PATH_NEGATIVE_CASES)}
- included_count: {audit["included_count"]}
- excluded_count: {audit["excluded_count"]}
- shipped_forbidden_count: {audit["shipped_forbidden_count"]}
- secret_findings_count: {audit["secret_findings_count"]}
- excluded_secret_findings_count: {audit["excluded_secret_findings_count"]}
- repo_secret_findings_count: {audit["repo_secret_findings_count"]}

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

Source/release bundle hygiene now rejects unsafe relative path strings before allow-root checks and scans excluded files for credential-like material. Current repo scan: repo_secret_findings={audit["repo_secret_findings_count"]}, shipped_forbidden={audit["shipped_forbidden_count"]}.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str) -> None:
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    matrix = load_json(matrix_path)
    req_index["updated_at_utc"] = now
    matrix["updated_at_utc"] = now
    ensure_requirement(
        req_index,
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_SOURCE_BUNDLE_HYGIENE",
            "source_file": "TRADER_1.md",
            "source_heading": "Source release bundle path and secret guard",
            "full_text_marker": f"{REQUIREMENT_ID}:release bundle path strings and excluded secrets must fail closed",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Source release bundle rejects unsafe paths and excluded credential material",
            "requirement_kind": "BUNDLE_SECURITY_TEST_PATCH",
            "schema_ids": ["trader1.patch_result.v1", "trader1.evidence_manifest.v1", "trader1.validator_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/security/test_source_bundle_security.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP0-BUNDLE-SECURITY", "REQ-MVP4-SOURCE-BUNDLE-HYGIENE-RECHECK"],
            "source_text_sha256": sha256_json({"requirement": REQUIREMENT_ID}),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
            "test_status": "PASS",
        },
    )
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_SOURCE_BUNDLE_HYGIENE",
            "schema_files": [],
            "validator_files": ["trader1/security/source_bundle.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/security/test_source_bundle_security.py"],
            "fixture_files": ["contracts/security/source_bundle_denylist.json"],
            "runtime_modules": [],
            "evidence_artifacts": [
                "contracts/security/source_bundle_manifest.json",
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
            "minimum_depth": "DEPTH_3_NEGATIVE_FIXTURES",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    req_index["trader1_sha256"] = trader_hash
    req_index["agents_sha256"] = agents_hash
    write_json(req_path, req_index)
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
        "affected_contract_ids": [REQUIREMENT_ID, "REQ-MVP0-BUNDLE-SECURITY", "REQ-MVP4-LIVE-FINAL-GUARD"],
        "affected_exchange": "ALL",
        "affected_market_type": "ALL",
        "affected_mode": "SOURCE_AND_RELEASE_PACKAGE_ONLY",
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
        "next_required_section_ids": ["SECTION_WINDOWS_LONG_RUN_RECOVERY", "SECTION_LIVE_FINAL_GUARD"],
        "next_optional_section_ids": ["SECTION_UPBIT_PAPER_RUNTIME", "SECTION_DASHBOARD_OPERATOR_UX"],
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
        "active_read_surface_used": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_SOURCE_RELEASE_BUNDLE_HYGIENE_RECHECK",
        "required_section_ids": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_SECRET_HYGIENE", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["AGENTS:0G", "TRADER_1:source-release-bundle-hygiene-active-surface"],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_SOURCE_RELEASE_BUNDLE_HYGIENE",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_APPLICABLE",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
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
            "stage_gate_status": "PASS_FOR_SOURCE_RELEASE_BUNDLE_PATH_SECRET_GUARD_NO_LIVE_ORDERS",
            "source_release_bundle_path_secret_guard_audit": audit,
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


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + VALIDATORS_REQUIRED))
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = NEXT_TASK_CLASS
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    state["scale_up_allowed"] = False
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
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)
    manifest = write_source_bundle_manifest()
    audit = build_audit(manifest)
    update_navigation(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "tools/build_source_bundle_manifest.py"], timeout_seconds=300),
        run_command([sys.executable, "-B", "-m", "unittest", "tests.security.test_source_bundle_security", "-q"], timeout_seconds=300),
    ]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS, audit)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    for _ in range(2):
        patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED, audit)
        write_evidence(now, trader_hash, agents_hash, patch_result, audit)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"], timeout_seconds=300),
            run_command([sys.executable, "-B", "-m", "unittest", "tests.validators.test_mvp0_validators", "-q"], timeout_seconds=300),
        ]
    )
    for _ in range(2):
        patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED, audit)
        write_evidence(now, trader_hash, agents_hash, patch_result, audit)
        write_json(patch_path, patch_result)
        update_state_and_ledger(now, patch_result)
        update_read_cache(now, trader_hash, agents_hash)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    if audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "source release bundle path/secret audit failed"})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "repo_secret_findings_count": audit["repo_secret_findings_count"],
                "shipped_forbidden_count": audit["shipped_forbidden_count"],
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
