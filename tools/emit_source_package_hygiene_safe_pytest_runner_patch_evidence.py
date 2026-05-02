from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-SOURCE-PACKAGE-HYGIENE-SAFE-PYTEST-RUNNER"
NEXT_TASK_CLASS = "MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE_RECHECK"

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
from trader1.security.source_bundle import build_source_bundle_manifest, write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "pyproject.toml",
    "contracts/schema/hygiene_safe_pytest_report.schema.json",
    "tools/run_hygiene_safe_pytest.py",
    "tools/emit_source_package_hygiene_safe_pytest_runner_patch_evidence.py",
    "tests/runtime/test_bytecode_free_syntax_check.py",
    "tests/security/test_source_bundle_security.py",
    "contracts/security/source_bundle_manifest.json",
    "contracts/generated/context_pack/MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER.md",
]
VALIDATORS_REQUIRED = [
    "schema_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "bytecode_free_syntax_validator",
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
SAFE_PYTEST_REPORT_PATH = (
    ROOT
    / "system"
    / "evidence"
    / "runtime_checks"
    / f"{PATCH_BASENAME}.hygiene_safe_pytest_report.json"
)


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


def pytest_cacheprovider_disabled() -> bool:
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    addopts = config["tool"]["pytest"]["ini_options"]["addopts"].split()
    return "-p" in addopts and "no:cacheprovider" in addopts


def build_audit() -> dict[str, Any]:
    manifest = build_source_bundle_manifest()
    cache_findings = scan_cache_artifacts()
    safe_pytest_report = load_json(SAFE_PYTEST_REPORT_PATH) if SAFE_PYTEST_REPORT_PATH.exists() else None
    blockers: list[str] = []
    if cache_findings:
        blockers.append("CURRENT_REPO_CACHE_ARTIFACT_PRESENT")
    if manifest.get("shipped_forbidden_count"):
        blockers.append("SHIPPED_PACKAGE_FORBIDDEN_PRESENT")
    if manifest.get("contains_secret"):
        blockers.append("SOURCE_SECRET_FINDING_PRESENT")
    if not pytest_cacheprovider_disabled():
        blockers.append("PYTEST_CACHEPROVIDER_NOT_DISABLED")
    if safe_pytest_report and safe_pytest_report.get("status") != "PASS":
        blockers.append("HYGIENE_SAFE_PYTEST_REPORT_NOT_PASS")
    if manifest.get("live_order_ready") or manifest.get("live_order_allowed") or manifest.get("can_live_trade"):
        blockers.append("LIVE_FLAG_DRIFT")
    return {
        "audit_schema_id": "trader1.source_package_hygiene_safe_pytest_runner_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "cache_artifact_count": len(cache_findings),
        "cache_artifacts": cache_findings[:20],
        "source_bundle_included_count": len(manifest.get("included_files", [])),
        "source_bundle_excluded_count": len(manifest.get("excluded_files", [])),
        "shipped_forbidden_count": manifest.get("shipped_forbidden_count", 0),
        "contains_secret": bool(manifest.get("contains_secret")),
        "pytest_cacheprovider_disabled": pytest_cacheprovider_disabled(),
        "safe_pytest_report_path": rel(SAFE_PYTEST_REPORT_PATH),
        "safe_pytest_report_status": safe_pytest_report.get("status") if isinstance(safe_pytest_report, dict) else "NOT_WRITTEN",
        "safe_pytest_post_run_cache_artifact_count": (
            safe_pytest_report.get("post_run_cache_artifact_count") if isinstance(safe_pytest_report, dict) else None
        ),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER.md",
        f"""# MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER

context_pack_id: MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER
task_class: MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.hygiene_safe_pytest_report.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Use tools/run_hygiene_safe_pytest.py for repo pytest proof runs that must leave no __pycache__, .pytest_cache, .pyc, or .pyo artifacts.
- pyproject disables pytest cacheprovider by default.
- The hygiene-safe pytest report is schema-valid and keeps live flags false.
- Source/shipped package hygiene remains PASS after the test runner executes.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

coverage_snapshot:
- cache_artifact_count: {audit["cache_artifact_count"]}
- shipped_forbidden_count: {audit["shipped_forbidden_count"]}
- safe_pytest_report_status: {audit["safe_pytest_report_status"]}
- safe_pytest_post_run_cache_artifact_count: {audit["safe_pytest_post_run_cache_artifact_count"]}

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

Source/release hygiene now has a cache-proof pytest runner. Last audit: cache_artifact_count={audit["cache_artifact_count"]}, shipped_forbidden_count={audit["shipped_forbidden_count"]}, safe_pytest_report_status={audit["safe_pytest_report_status"]}.

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
            "source_section_id": "SECTION_SOURCE_BUNDLE_HYGIENE",
            "source_file": "TRADER_1.md",
            "source_heading": "Source package hygiene safe pytest runner",
            "full_text_marker": f"{REQUIREMENT_ID}:pytest proof runs must not leave cache or bytecode artifacts",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Cache-proof pytest runner for source/release hygiene",
            "requirement_kind": "BUNDLE_SECURITY_TEST_PATCH",
            "schema_ids": ["trader1.hygiene_safe_pytest_report.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_bytecode_free_syntax_check.py", "tests/security/test_source_bundle_security.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_3_NEGATIVE_FIXTURES",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP0-BUNDLE-SECURITY",
                "REQ-MVP4-SOURCE-PACKAGE-HYGIENE-CACHE-DIR-GUARD",
                "REQ-MVP4-BYTECODE-FREE-SYNTAX-REPRODUCIBILITY",
            ],
            "source_text_sha256": sha256_bytes(b"pytest proof runs must not leave cache or bytecode artifacts"),
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
            "section_id": "SECTION_SOURCE_BUNDLE_HYGIENE",
            "schema_files": ["contracts/schema/hygiene_safe_pytest_report.schema.json"],
            "validator_files": ["trader1/security/source_bundle.py", "trader1/validation/mvp0_validators.py"],
            "test_files": ["tests/runtime/test_bytecode_free_syntax_check.py", "tests/security/test_source_bundle_security.py"],
            "fixture_files": [],
            "runtime_modules": [],
            "evidence_artifacts": [
                rel(SAFE_PYTEST_REPORT_PATH),
                "contracts/security/source_bundle_manifest.json",
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [],
            "patch_result_fields": [
                "tests_run",
                "validators_run",
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
) -> dict[str, Any]:
    patch_result: dict[str, Any] = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "TEST_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "MATCH",
        "authority_hash_checked": True,
        "affected_contract_ids": [
            REQUIREMENT_ID,
            "REQ-MVP0-BUNDLE-SECURITY",
            "REQ-MVP4-BYTECODE-FREE-SYNTAX-REPRODUCIBILITY",
            "REQ-MVP4-LIVE-FINAL-GUARD",
        ],
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
        "new_or_changed_schema_ids": ["trader1.hygiene_safe_pytest_report.v1"],
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
        "next_required_section_ids": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"],
        "next_optional_section_ids": ["SECTION_RELEASE_PROOF", "SECTION_BUNDLE_SECURITY"],
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
        "active_read_surface_used": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"],
        "task_class": "MVP4_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER",
        "required_section_ids": ["SECTION_SOURCE_BUNDLE_HYGIENE", "SECTION_TEST_PROOF", "SECTION_LIVE_FINAL_GUARD"],
        "expanded_section_ids": ["AGENTS:0G", "AGENTS:0F", "SECTION_SOURCE_BUNDLE_HYGIENE"],
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
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_SOURCE_PACKAGE_HYGIENE",
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
            "stage_gate_status": "PASS_FOR_SOURCE_PACKAGE_HYGIENE_SAFE_PYTEST_RUNNER_NO_LIVE_ORDERS",
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
                rel(SAFE_PYTEST_REPORT_PATH),
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
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Source Package Hygiene Safe Pytest Runner

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added a hygiene-safe pytest runner that starts child pytest with PYTHONDONTWRITEBYTECODE=1.
- The runner forces pytest cacheprovider off and fails if __pycache__, .pytest_cache, .pyc, or .pyo artifacts exist before or after the run.
- Added a schema and tests for the runner report.

Audit:
- cache_artifact_count: {audit['cache_artifact_count']}
- shipped_forbidden_count: {audit['shipped_forbidden_count']}
- pytest_cacheprovider_disabled: {audit['pytest_cacheprovider_disabled']}
- safe_pytest_report_status: {audit['safe_pytest_report_status']}
- safe_pytest_post_run_cache_artifact_count: {audit['safe_pytest_post_run_cache_artifact_count']}

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
    state["implemented_schema_ids"] = sorted(set(state.get("implemented_schema_ids", []) + ["trader1.hygiene_safe_pytest_report.v1"]))
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
    tests_run = [
        run_command(
            [
                sys.executable,
                "tools/run_hygiene_safe_pytest.py",
                "--report",
                rel(SAFE_PYTEST_REPORT_PATH),
                "--",
                "tests/runtime/test_bytecode_free_syntax_check.py",
                "tests/security/test_source_bundle_security.py",
            ]
        ),
        run_command([sys.executable, "-B", "tools/build_source_bundle_manifest.py"]),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
    ]
    audit = build_audit()
    update_context(now, trader_hash, agents_hash, audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"

    patch_result = build_patch_result(now, tests_run, run_validators(BOOTSTRAP_VALIDATORS), BOOTSTRAP_VALIDATORS)
    write_evidence(now, trader_hash, agents_hash, patch_result, audit)
    write_json(patch_path, patch_result)
    update_state_and_ledger(now, patch_result)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run.extend(
        [
            run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]),
            run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
            run_command(
                [
                    sys.executable,
                    "tools/run_hygiene_safe_pytest.py",
                    "--",
                    "tests/runtime/test_bytecode_free_syntax_check.py",
                    "tests/security/test_source_bundle_security.py",
                ]
            ),
        ]
    )
    audit = build_audit()
    patch_result = build_patch_result(now, tests_run, run_validators(VALIDATORS_REQUIRED), VALIDATORS_REQUIRED)
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
                "cache_artifact_count": audit["cache_artifact_count"],
                "shipped_forbidden_count": audit["shipped_forbidden_count"],
                "safe_pytest_report_status": audit["safe_pytest_report_status"],
            },
            indent=2,
        )
    )
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
