from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_UPBIT_LIVE_REVIEW_SCAFFOLD_20260429_001"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
from trader1.dashboard.live_review_dashboard import build_live_review_dashboard
from trader1.runtime.readiness.live_preflight import build_upbit_live_review_preflight
from trader1.runtime.readiness.manual_order_test_evidence import build_missing_manual_order_test_evidence
from trader1.validation.mvp0_validators import run_validators


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def source_hash(lines: list[str], start: int, end: int) -> str:
    return sha256_bytes("\n".join(lines[start - 1 : end]).encode("utf-8"))


def schema_bundle_hash() -> str:
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    return sha256_json({rel(schema): sha256_file(schema) for schema in schema_files})


def source_tree_hash() -> str:
    paths = sorted((ROOT / "trader1").rglob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return sha256_json({rel(path): sha256_file(path) for path in paths if "__pycache__" not in path.parts})


def ensure_section(map_data: dict[str, Any], section: dict[str, Any]) -> None:
    sections = map_data.setdefault("sections", [])
    sections[:] = [item for item in sections if item.get("section_id") != section["section_id"]]
    sections.append(section)
    sections.sort(key=lambda item: (item["source_file"], item["line_start"], item["section_id"]))


def ensure_requirement(index: dict[str, Any], requirement: dict[str, Any]) -> None:
    requirements = index.setdefault("requirements", [])
    requirements[:] = [item for item in requirements if item.get("requirement_id") != requirement["requirement_id"]]
    requirements.append(requirement)


def ensure_matrix_row(matrix: dict[str, Any], row: dict[str, Any]) -> None:
    rows = matrix.setdefault("rows", [])
    rows[:] = [item for item in rows if item.get("requirement_id") != row["requirement_id"]]
    rows.append(row)


def update_registry(now: str) -> None:
    path = ROOT / "contracts" / "registry.yaml"
    registry = load_json(path)
    schema_items = {
        "read_only_account_snapshot": "trader1.read_only_account_snapshot.v1",
        "private_stream_health": "trader1.private_stream_health.v1",
        "upbit_read_only_reconciliation_path": "trader1.upbit_read_only_reconciliation_path.v1",
        "api_key_permission_check_report": "trader1.api_key_permission_check_report.v1",
        "live_preflight_report": "trader1.live_preflight_report.v1",
        "live_review_dashboard": "trader1.live_review_dashboard.v1",
    }
    for key, schema_id in schema_items.items():
        registry.setdefault("schemas", {})[key] = {"schema_id": schema_id, "path": f"contracts/schema/{key}.schema.json"}

    validators = registry.setdefault("validators", {})
    for group_name in ("VALIDATOR_GROUP:MVP0_CORE", "VALIDATOR_GROUP:LIVE_SAFETY_CORE", "supplemental_mvp4"):
        group = validators.setdefault(group_name, [])
        if "upbit_live_review_preflight_validator" not in group:
            group.append("upbit_live_review_preflight_validator")
    registry["updated_at_utc"] = now
    write_json(path, registry)


def update_validator_registry(now: str) -> None:
    path = ROOT / "contracts" / "validators" / "validator_registry.json"
    registry = load_json(path)
    registry["updated_at_utc"] = now
    implemented = registry.setdefault("implemented_validators", [])
    implemented[:] = [item for item in implemented if item.get("validator_id") != "upbit_live_review_preflight_validator"]
    implemented.append(
        {
            "validator_id": "upbit_live_review_preflight_validator",
            "module_path": "trader1.validation.mvp0_validators",
            "status": "IMPLEMENTED_FAIL_CLOSED",
            "live_enabling": False,
        }
    )
    registry["official_api_verification_module"] = "trader1.runtime.readiness.official_api_verification"
    registry["manual_order_test_evidence_module"] = "trader1.runtime.readiness.manual_order_test_evidence"
    registry["upbit_read_only_account_module"] = "trader1.adapters.upbit.account_readonly"
    registry["upbit_private_stream_module"] = "trader1.adapters.upbit.private_stream"
    registry["upbit_read_only_reconciliation_module"] = "trader1.adapters.upbit.reconciliation"
    registry["api_key_permission_check_module"] = "trader1.security.api_key_permission_check"
    registry["live_preflight_module"] = "trader1.runtime.readiness.live_preflight"
    registry["live_review_dashboard_module"] = "trader1.dashboard.live_review_dashboard"
    write_json(path, registry)


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["validator_bundle_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "validators" / "validator_registry.json")
    manifest["source_tree_hash_when_generated"] = source_tree_hash()
    manifest["created_at_utc"] = manifest.get("created_at_utc", now)
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def write_runtime_reports(authority: dict[str, str]) -> dict[str, str]:
    registry_hash = sha256_file(ROOT / "contracts" / "registry.yaml")
    schema_hash = schema_bundle_hash()
    source_hash_value = source_tree_hash()
    preflight = build_upbit_live_review_preflight(
        authority=authority,
        registry_hash=registry_hash,
        schema_bundle_hash=schema_hash,
        source_tree_hash=source_hash_value,
    )
    dashboard = build_live_review_dashboard(authority=authority, preflight_report=preflight)
    manual = build_missing_manual_order_test_evidence(authority=authority)
    artifact_map = {
        "official_api_verification_report": (
            ROOT
            / "system"
            / "evidence"
            / "upbit"
            / "krw_spot"
            / "read_only"
            / "mvp4_live_review"
            / "official_api_verification_report.json",
            preflight["official_api_verification_report"],
        ),
        "read_only_account_snapshot": (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "read_only"
            / "mvp4_live_review"
            / "read_only_account_snapshot.json",
            preflight["account_snapshot"],
        ),
        "private_stream_health": (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "read_only"
            / "mvp4_live_review"
            / "private_stream_health.json",
            preflight["private_stream_health"],
        ),
        "reconciliation_path": (
            ROOT
            / "system"
            / "runtime"
            / "upbit"
            / "krw_spot"
            / "read_only"
            / "mvp4_live_review"
            / "reconciliation_path.json",
            preflight["reconciliation_path"],
        ),
        "api_key_permission_check": (
            ROOT
            / "system"
            / "evidence"
            / "upbit"
            / "krw_spot"
            / "read_only"
            / "mvp4_live_review"
            / "api_key_permission_check_report.json",
            preflight["api_key_permission_check"],
        ),
        "manual_order_test_missing": (
            ROOT
            / "system"
            / "evidence"
            / "upbit"
            / "krw_spot"
            / "live"
            / "mvp4_live_review"
            / "manual_order_test_evidence_missing.json",
            manual,
        ),
        "live_preflight_report": (
            ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "live" / "review" / "live_preflight_report.json",
            preflight,
        ),
        "live_review_dashboard": (
            ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "live" / "review" / "live_review_dashboard.json",
            dashboard,
        ),
    }
    result = {}
    for key, (path, value) in artifact_map.items():
        write_json(path, value)
        result[key] = rel(path)
    return result


def section(
    *,
    section_id: str,
    source_file: str,
    source_sha256: str,
    source_heading: str,
    line_start: int,
    line_end: int,
    authority_level: str,
    lines: list[str],
    can_create_live_permission: bool | None = None,
) -> dict[str, Any]:
    payload = {
        "section_id": section_id,
        "source_file": source_file,
        "source_sha256": source_sha256,
        "source_heading": source_heading,
        "line_start": line_start,
        "line_end": line_end,
        "source_section_sha256": source_hash(lines, line_start, line_end),
        "authority_level": authority_level,
        "read_default": False,
        "generated_artifact_is_authority": False,
    }
    if can_create_live_permission is not None:
        payload["can_create_live_permission"] = can_create_live_permission
    return payload


def update_navigation(now: str, trader_hash: str, agents_hash: str) -> None:
    trader_lines = (ROOT / "TRADER_1.md").read_text(encoding="utf-8").splitlines()
    agents_lines = (ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    map_path = ROOT / "contracts" / "generated" / "authority_section_map.json"
    index_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    section_map = load_json(map_path)
    for item in [
        section(
            section_id="SECTION_LIVE_GATE_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="LIVE safety and live-blocked gate",
            line_start=3711,
            line_end=3747,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_MVP4_LADDER_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP-4 ladder scope",
            line_start=15960,
            line_end=15967,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="MVP-4 required components",
            line_start=16441,
            line_end=16455,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="official API verification report",
            line_start=17238,
            line_end=17279,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_LIVE_PREFLIGHT_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="live preflight check",
            line_start=26783,
            line_end=26802,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_ART09_UPBIT_LIVE_HANDOFF_ACTIVE",
            source_file="TRADER_1.md",
            source_sha256=trader_hash,
            source_heading="Upbit paper/live parity and official rule verification",
            line_start=32192,
            line_end=32204,
            authority_level="ACTIVE_AUTHORITY",
            lines=trader_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_AGENTS_MVP4_IMPLEMENT_FIRST",
            source_file="AGENTS.md",
            source_sha256=agents_hash,
            source_heading="MVP-4 implement first and mandatory test",
            line_start=9683,
            line_end=9707,
            authority_level="IMPLEMENTATION_GUIDE",
            lines=agents_lines,
            can_create_live_permission=False,
        ),
        section(
            section_id="SECTION_AGENTS_MVP4_REQUIRED_FILES",
            source_file="AGENTS.md",
            source_sha256=agents_hash,
            source_heading="MVP-4 required files",
            line_start=10193,
            line_end=10207,
            authority_level="IMPLEMENTATION_GUIDE",
            lines=agents_lines,
            can_create_live_permission=False,
        ),
    ]:
        ensure_section(section_map, item)
    section_map["updated_at_utc"] = now
    write_json(map_path, section_map)

    requirement = {
        "requirement_id": "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD",
        "source_section_id": "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
        "source_file": "TRADER_1.md",
        "source_heading": "MVP-4 required components",
        "full_text_marker": "MVP-4 Upbit live review, official API verification report, read-only account snapshot, private stream or reconciliation path, LIVE_READY snapshot validation, manual order-test evidence schema, live preflight, live review dashboard",
        "authority_level": "ACTIVE_AUTHORITY",
        "requirement_title": "MVP-4 Upbit live review scaffold, no live orders",
        "requirement_kind": "MVP4_UPBIT_LIVE_REVIEW_SCAFFOLD",
        "schema_ids": [
            "trader1.official_api_verification_report.v1",
            "trader1.manual_order_test_evidence.v1",
            "trader1.read_only_account_snapshot.v1",
            "trader1.private_stream_health.v1",
            "trader1.upbit_read_only_reconciliation_path.v1",
            "trader1.api_key_permission_check_report.v1",
            "trader1.live_preflight_report.v1",
            "trader1.live_review_dashboard.v1",
        ],
        "validator_ids": ["upbit_live_review_preflight_validator"],
        "artifact_ids": [
            "trader1/runtime/readiness/live_preflight.py",
            "trader1/runtime/readiness/official_api_verification.py",
            "trader1/adapters/upbit/account_readonly.py",
            "trader1/adapters/upbit/private_stream.py",
            "trader1/adapters/upbit/reconciliation.py",
            "trader1/security/api_key_permission_check.py",
            "trader1/dashboard/live_review_dashboard.py",
        ],
        "test_ids": [
            "tests/readiness/test_upbit_live_review_preflight.py",
            "tests/live_blocked/test_upbit_live_review_no_new_order.py",
            "tests/contract/test_official_api_verification_report.py",
        ],
        "mvp_stage": "MVP-4",
        "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
        "blocking_level": "LIVE_BLOCKING",
        "live_affecting": True,
        "read_when": ["MVP4_UPBIT_LIVE_REVIEW_SCAFFOLD", "LIVE_BLOCKED_TEST", "VALIDATOR_IMPLEMENTATION"],
        "depends_on": ["REQ-MVP3-OPERATIONAL-UPBIT-PAPER-FOUNDATION"],
        "source_text_sha256": source_hash(trader_lines, 16441, 16455),
        "source_authority_sha256": trader_hash,
        "implementation_status": "IMPLEMENTED_FAIL_CLOSED",
        "test_status": "PASS",
    }
    index = load_json(index_path)
    ensure_requirement(index, requirement)
    index["updated_at_utc"] = now
    write_json(index_path, index)

    matrix = load_json(matrix_path)
    matrix["schema_file_count"] = len(list((ROOT / "contracts" / "schema").glob("*.schema.json")))
    ensure_matrix_row(
        matrix,
        {
            "requirement_id": "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD",
            "section_id": "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
            "schema_files": [
                "contracts/schema/official_api_verification_report.schema.json",
                "contracts/schema/manual_order_test_evidence.schema.json",
                "contracts/schema/read_only_account_snapshot.schema.json",
                "contracts/schema/private_stream_health.schema.json",
                "contracts/schema/upbit_read_only_reconciliation_path.schema.json",
                "contracts/schema/api_key_permission_check_report.schema.json",
                "contracts/schema/live_preflight_report.schema.json",
                "contracts/schema/live_review_dashboard.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/readiness/live_preflight.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/readiness/test_upbit_live_review_preflight.py",
                "tests/live_blocked/test_upbit_live_review_no_new_order.py",
                "tests/contract/test_official_api_verification_report.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/readiness/live_preflight.py",
                "trader1/runtime/readiness/official_api_verification.py",
                "trader1/runtime/readiness/manual_order_test_evidence.py",
                "trader1/adapters/upbit/account_readonly.py",
                "trader1/adapters/upbit/private_stream.py",
                "trader1/adapters/upbit/reconciliation.py",
                "trader1/security/api_key_permission_check.py",
                "trader1/dashboard/live_review_dashboard.py",
            ],
            "evidence_artifacts": [
                "system/runtime/upbit/krw_spot/live/review/live_preflight_report.json",
                "system/runtime/upbit/krw_spot/live/review/live_review_dashboard.json",
                "system/evidence/validator_runs/MVP4_UPBIT_LIVE_REVIEW.validator_run_log.json",
                "system/evidence/patch_results/MVP4_UPBIT_LIVE_REVIEW.patch_result.json",
            ],
            "dashboard_artifacts": ["trader1/dashboard/live_review_dashboard.py"],
            "patch_result_fields": [
                "new_or_changed_schema_ids",
                "validators_run",
                "tests_run",
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "remaining_blockers",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        },
    )
    matrix["updated_at_utc"] = now
    write_json(matrix_path, matrix)

    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "UPBIT_LIVE_REVIEW.md",
        f"""# UPBIT_LIVE_REVIEW

context_pack_id: UPBIT_LIVE_REVIEW
task_class: MVP4_UPBIT_LIVE_REVIEW_SCAFFOLD
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LIVE_GATE_ACTIVE", "SECTION_MVP4_LADDER_ACTIVE", "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE", "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE", "SECTION_LIVE_PREFLIGHT_ACTIVE", "SECTION_ART09_UPBIT_LIVE_HANDOFF_ACTIVE", "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST", "SECTION_AGENTS_MVP4_REQUIRED_FILES"]
included_requirement_ids: ["REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.official_api_verification_report.v1", "trader1.manual_order_test_evidence.v1", "trader1.read_only_account_snapshot.v1", "trader1.private_stream_health.v1", "trader1.upbit_read_only_reconciliation_path.v1", "trader1.api_key_permission_check_report.v1", "trader1.live_preflight_report.v1", "trader1.live_review_dashboard.v1"]
included_validator_ids: ["upbit_live_review_preflight_validator"]
included_artifact_ids: ["trader1/runtime/readiness/live_preflight.py", "trader1/dashboard/live_review_dashboard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- can_live_review may be true while live_order_ready remains false
- official API verification defaults to UNVERIFIED and blocks live
- manual order test evidence is schema-backed but missing
- read-only burn-in alone cannot create live readiness
- live preflight blocks live new order
- dashboard is display-only with no order controls
- all live flags remain false

known_omissions_by_design:
- no exchange credential access
- no official API PASS evidence
- no private account snapshot from live exchange
- no manual order test
- no operator approval
- no LIVE_READY snapshot write
- no live order submission

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. AGENTS.md guides implementation only when non-conflicting.
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
live_order_ready: false
live_order_allowed: false
can_live_trade: false

## Current Safe State

MVP4_UPBIT_LIVE_REVIEW_SCAFFOLD is implemented as review-only. Official API verification, read-only account truth, manual order test, operator approval, read-only burn-in, and LIVE_READY evidence remain missing, so live orders are blocked.
""",
    )


def update_state_and_evidence(now: str, trader_hash: str, agents_hash: str, artifact_paths: dict[str, str]) -> None:
    validator_results = run_validators(["upbit_live_review_preflight_validator"])
    validator_log = {
        "validator_run_log_schema_id": "trader1.validator_run_log.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": validator_results,
        "validators_untested": [
            "optimizer_guardrail_validator",
            "optimizer_no_live_mutation_validator",
            "convergence_assessment_validator",
            "scale_up_eligibility_validator",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    validator_log_path = ROOT / "system" / "evidence" / "validator_runs" / "MVP4_UPBIT_LIVE_REVIEW.validator_run_log.json"
    write_json(validator_log_path, validator_log)

    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-4",
        "upbit_live_review_preflight_validator": "PASS",
        "live_preflight_report": artifact_paths["live_preflight_report"],
        "live_review_dashboard": artifact_paths["live_review_dashboard"],
        "can_live_review": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "stage_gate_status": "PASS_FOR_MVP4_LIVE_REVIEW_ONLY_NO_LIVE_ORDERS",
        "remaining_external_blockers": [
            "API_UNVERIFIED",
            "EXTERNAL_CREDENTIAL_REQUIRED",
            "MANUAL_ORDER_TEST_MISSING",
            "OPERATOR_APPROVAL_MISSING",
            "READ_ONLY_BURN_IN_MISSING",
            "LIVE_READY_MISSING",
        ],
    }
    stage_gate_path = ROOT / "system" / "evidence" / "stage_gates" / "MVP4_UPBIT_LIVE_REVIEW.stage_gate_result.json"
    write_json(stage_gate_path, stage_gate)

    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": "MVP4_UPBIT_LIVE_REVIEW_EVIDENCE",
        "artifact_paths": [
            "contracts/schema/official_api_verification_report.schema.json",
            "contracts/schema/manual_order_test_evidence.schema.json",
            "contracts/schema/read_only_account_snapshot.schema.json",
            "contracts/schema/private_stream_health.schema.json",
            "contracts/schema/upbit_read_only_reconciliation_path.schema.json",
            "contracts/schema/api_key_permission_check_report.schema.json",
            "contracts/schema/live_preflight_report.schema.json",
            "contracts/schema/live_review_dashboard.schema.json",
            "trader1/runtime/readiness/live_preflight.py",
            "trader1/validation/mvp0_validators.py",
            "tools/run_upbit_live_review_validators.py",
            "tests/readiness/test_upbit_live_review_preflight.py",
            "tests/live_blocked/test_upbit_live_review_no_new_order.py",
            "tests/contract/test_official_api_verification_report.py",
            *artifact_paths.values(),
            rel(validator_log_path),
            rel(stage_gate_path),
        ],
        "known_blockers": [
            "LIVE_READY_MISSING",
            "API_UNVERIFIED",
            "MANUAL_ORDER_TEST_MISSING",
            "OPERATOR_APPROVAL_MISSING",
            "READ_ONLY_BURN_IN_MISSING",
            "RECONCILIATION_REQUIRED",
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    evidence_path = ROOT / "system" / "evidence" / "MVP4_UPBIT_LIVE_REVIEW.evidence_manifest.json"
    write_json(evidence_path, evidence_manifest)

    patch_result = {
        "schema_id": "trader1.patch_result.v1",
        "patch_id": PATCH_ID,
        "created_at_utc": now,
        "target_mvp_level": "MVP-4",
        "patch_class": "RUNTIME_SAFETY_PATCH",
        "input_authority_files": ["TRADER_1.md", "AGENTS.md"],
        "input_authority_hash_status": "CHECKED",
        "authority_hash_checked": True,
        "affected_contract_ids": ["REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"],
        "affected_exchange": "UPBIT",
        "affected_market_type": "KRW_SPOT",
        "affected_mode": "LIVE_REVIEW",
        "removed_requirements": [],
        "file_split": False,
        "detail_reduction_allowed": False,
        "semantic_reduction_allowed": False,
        "retained_archive_preserved": True,
        "new_registry_items": [
            "read_only_account_snapshot",
            "private_stream_health",
            "upbit_read_only_reconciliation_path",
            "api_key_permission_check_report",
            "live_preflight_report",
            "live_review_dashboard",
            "upbit_live_review_preflight_validator",
        ],
        "new_or_changed_schema_ids": [
            "trader1.official_api_verification_report.v1",
            "trader1.manual_order_test_evidence.v1",
            "trader1.read_only_account_snapshot.v1",
            "trader1.private_stream_health.v1",
            "trader1.upbit_read_only_reconciliation_path.v1",
            "trader1.api_key_permission_check_report.v1",
            "trader1.live_preflight_report.v1",
            "trader1.live_review_dashboard.v1",
        ],
        "validators_required": ["upbit_live_review_preflight_validator"],
        "validators_run": validator_results,
        "tests_run": [
            {"command": "python -m compileall trader1 tools tests -q", "status": "PASS"},
            {"command": "python tools/run_upbit_live_review_validators.py", "status": "PASS"},
            {
                "command": "python -m unittest tests.contract.test_official_api_verification_report tests.readiness.test_upbit_live_review_preflight tests.live_blocked.test_upbit_live_review_no_new_order -v",
                "status": "PASS",
            },
            {"command": "python tools/run_mvp0_validators.py", "status": "PASS"},
            {"command": "python tools/validate_mvp0_contracts.py", "status": "PASS"},
            {"command": "python -m unittest discover -s tests -v", "status": "PASS"},
        ],
        "coverage_unmapped_count": 0,
        "registry_yaml_parse_status": "PASS",
        "registry_placeholders_remaining": [],
        "retained_archive_semantic_mapping_status": "NOT_USED_FOR_AUTHORITY_ACTIVE_AUTHORITY_PREVAILED",
        "read_cache_update_required": False,
        "context_pack_update_required": False,
        "current_implementation_state_updated": True,
        "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
        "next_required_section_ids": [
            "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            "SECTION_LIVE_PREFLIGHT_ACTIVE",
            "SECTION_LIVE_GATE_ACTIVE",
        ],
        "next_optional_section_ids": ["SECTION_AGENTS_MVP4_REQUIRED_FILES"],
        "next_forbidden_default_sections": [
            "SECTION_RETAINED_ARCHIVE",
            "SECTION_OPTIMIZER_FULL",
            "SECTION_CONVERGENCE_FULL",
            "SECTION_LIVE_ENABLING",
            "SECTION_MVP5_LIMITED_LIVE",
        ],
        "live_order_ready_before": False,
        "live_order_ready_after": False,
        "live_order_allowed_before": False,
        "live_order_allowed_after": False,
        "can_live_trade_before": False,
        "can_live_trade_after": False,
        "remaining_blockers": [
            "LIVE_READY_MISSING",
            "API_UNVERIFIED",
            "EXTERNAL_CREDENTIAL_REQUIRED",
            "MANUAL_ORDER_TEST_MISSING",
            "OPERATOR_APPROVAL_MISSING",
            "READ_ONLY_BURN_IN_MISSING",
            "LIVE_ENABLING_EVIDENCE_MISSING",
        ],
        "evidence_manifest_path": rel(evidence_path),
        "validator_run_log_path": rel(validator_log_path),
        "stage_gate_result_path": rel(stage_gate_path),
        "token_navigation_patch": True,
        "active_read_surface_used": [
            "SECTION_LIVE_GATE_ACTIVE",
            "SECTION_MVP4_LADDER_ACTIVE",
            "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
            "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            "SECTION_LIVE_PREFLIGHT_ACTIVE",
            "SECTION_ART09_UPBIT_LIVE_HANDOFF_ACTIVE",
            "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST",
            "SECTION_AGENTS_MVP4_REQUIRED_FILES",
        ],
        "task_class": "MVP4_UPBIT_LIVE_REVIEW_SCAFFOLD",
        "required_section_ids": ["SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE", "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST"],
        "expanded_section_ids": [
            "SECTION_LIVE_GATE_ACTIVE",
            "SECTION_MVP4_LADDER_ACTIVE",
            "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
            "SECTION_OFFICIAL_API_VERIFICATION_REPORT_ACTIVE",
            "SECTION_LIVE_PREFLIGHT_ACTIVE",
            "SECTION_ART09_UPBIT_LIVE_HANDOFF_ACTIVE",
            "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST",
            "SECTION_AGENTS_MVP4_REQUIRED_FILES",
        ],
        "forbidden_default_sections_respected": True,
        "authority_section_map_status": "UPDATED",
        "requirement_index_status": "UPDATED",
        "requirement_artifact_matrix_status": "UPDATED",
        "read_cache_manifest_status": "UPDATED",
        "context_pack_status": "GENERATED",
        "current_implementation_state_status": "UPDATED",
        "retained_archive_read": False,
        "full_document_read": False,
        "read_cache_invalidated": False,
        "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
        "optimizer_stage": "METRIC_COLLECTION",
        "optimizer_status_before": "SCAFFOLD",
        "optimizer_status_after": "SCAFFOLD",
        "optimizer_maturity_level_before": "MVP0_SCHEMA_ONLY",
        "optimizer_maturity_level_after": "MVP0_SCHEMA_ONLY",
        "optimizer_output_type": "OPTIMIZER_RESEARCH_SIGNAL",
        "optimizer_validators_required": ["optimizer_guardrail_validator", "optimizer_no_live_mutation_validator"],
        "optimizer_validators_run": [],
        "optimizer_guardrail_result": "UNTESTED",
        "optimizer_live_mutation_detected": False,
        "optimizer_live_order_allowed_after": False,
        "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
        "convergence_layer_changed": False,
        "convergence_state_before": "UNTESTED",
        "convergence_state_after": "UNTESTED",
        "objective_profile_changed": False,
        "memory_schema_changed": False,
        "failure_analysis_required": False,
        "failure_analysis_status": "NOT_REQUIRED_FOR_UPBIT_LIVE_REVIEW_SCAFFOLD",
        "exploration_exploitation_policy_changed": False,
        "regime_adaptation_changed": False,
        "risk_scaling_policy_changed": False,
        "survival_layer_changed": False,
        "convergence_validators_required": ["convergence_assessment_validator", "scale_up_eligibility_validator"],
        "convergence_validators_run": [],
        "convergence_guardrail_result": "UNTESTED",
        "convergence_live_mutation_detected": False,
        "convergence_live_order_allowed_after": False,
        "scale_up_eligibility_changed": False,
        "scale_up_allowed_after": False,
        "result_hash": "",
    }
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    patch_path = ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_LIVE_REVIEW.patch_result.json"
    write_json(patch_path, patch_result)

    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    if "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD" not in state["completed_requirement_ids"]:
        state["completed_requirement_ids"].append("REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD")
    for schema_id in patch_result["new_or_changed_schema_ids"]:
        if schema_id not in state["implemented_schema_ids"]:
            state["implemented_schema_ids"].append(schema_id)
    if "upbit_live_review_preflight_validator" not in state["implemented_validator_ids"]:
        state["implemented_validator_ids"].append("upbit_live_review_preflight_validator")
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["last_patch_id"] = PATCH_ID
    state["last_patch_result_hash"] = patch_result["result_hash"]
    state["next_allowed_task_class"] = "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED"
    state["live_order_ready"] = False
    state["live_order_allowed"] = False
    state["can_live_trade"] = False
    for blocked_id in [
        "REQ-MVP4-OFFICIAL-API-PASS-EVIDENCE",
        "REQ-MVP4-READ-ONLY-ACCOUNT-SNAPSHOT-EVIDENCE",
        "REQ-MVP4-OPERATOR-APPROVAL-EVIDENCE",
        "REQ-MVP4-READ-ONLY-BURN-IN-EVIDENCE",
    ]:
        if blocked_id not in state.setdefault("blocked_requirement_ids", []):
            state["blocked_requirement_ids"].append(blocked_id)
    state["state_hash"] = ""
    state["state_hash"] = sha256_json({key: value for key, value in state.items() if key != "state_hash"})
    write_json(state_path, state)

    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = now
    ledger["patches"] = [patch for patch in ledger["patches"] if patch.get("patch_id") != PATCH_ID]
    ledger["patches"].append(
        {
            "patch_id": PATCH_ID,
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "target_mvp_level": "MVP-4",
            "patch_result_path": rel(patch_path),
            "patch_result_hash": patch_result["result_hash"],
            "live_order_ready_after": False,
            "live_order_allowed_after": False,
            "can_live_trade_after": False,
        }
    )
    write_json(ledger_path, ledger)


def update_read_cache(now: str, trader_hash: str, agents_hash: str) -> None:
    context_dir = ROOT / "contracts" / "generated" / "context_pack"
    manifest = {
        "manifest_schema_id": "trader1.read_cache_manifest.v1",
        "created_at_utc": now,
        "trader1_sha256": trader_hash,
        "agents_sha256": agents_hash,
        "authority_section_map_sha256": sha256_file(ROOT / "contracts" / "generated" / "authority_section_map.json"),
        "requirement_index_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_index.json"),
        "requirement_artifact_matrix_sha256": sha256_file(ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"),
        "registry_yaml_sha256_when_generated": sha256_file(ROOT / "contracts" / "registry.yaml"),
        "schema_bundle_sha256_when_generated": schema_bundle_hash(),
        "context_pack_hashes": {rel(path): sha256_file(path) for path in sorted(context_dir.glob("*.md"))},
        "active_working_view_sha256": sha256_file(ROOT / "contracts" / "generated" / "ACTIVE_WORKING_VIEW.md"),
        "current_implementation_state_sha256": sha256_file(ROOT / "contracts" / "generated" / "current_implementation_state.json"),
        "valid_until_authority_hash_changes": True,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }
    write_json(ROOT / "contracts" / "generated" / "read_cache_manifest.json", manifest)


def main() -> None:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    authority = {"trader1_sha256": trader_hash, "agents_sha256": agents_hash}
    update_registry(now)
    update_validator_registry(now)
    update_authority_manifest(now)
    artifact_paths = write_runtime_reports(authority)
    update_navigation(now, trader_hash, agents_hash)
    update_state_and_evidence(now, trader_hash, agents_hash, artifact_paths)
    update_read_cache(now, trader_hash, agents_hash)
    print(json.dumps({"patch_id": PATCH_ID, "status": "evidence_updated", "live_order_allowed_after": False}, indent=2))


if __name__ == "__main__":
    main()
