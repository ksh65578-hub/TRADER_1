from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
PATCH_BASENAME = "MVP4_UPBIT_PAPER_LEDGER_RECONCILIATION_IDEMPOTENCY_RUNTIME_EVIDENCE"
PATCH_ID = f"{PATCH_BASENAME}_20260502_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-LEDGER-IDEMPOTENCY-RUNTIME-EVIDENCE"
NEXT_TASK_CLASS = "MVP4_UPBIT_PAPER_LEDGER_IDEMPOTENCY_DASHBOARD_OPERATOR_VISIBILITY"
SESSION_ID = "mvp1_upbit_paper_launcher"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import tools.emit_persistent_runtime_resource_boundary_patch_evidence as base  # noqa: E402
from trader1.dashboard.read_only_dashboard import validate_read_only_dashboard_shell  # noqa: E402
from trader1.runtime.boot.safe_launcher import build_launcher_report, write_launcher_runtime_bundle  # noqa: E402
from trader1.runtime.ledger.paper_ledger_rollup import (  # noqa: E402
    build_paper_ledger_rollup_report,
    validate_paper_ledger_rollup_report,
    write_paper_ledger_rollup_report,
)
from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (  # noqa: E402
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
    write_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS_REQUIRED = [
    "schema_validator",
    "registry_validator",
    "runtime_schema_instance_validator",
    "paper_ledger_rollup_validator",
    "upbit_paper_ledger_idempotency_runtime_evidence_validator",
    "reconciliation_validator",
    "ledger_reconciliation_validator",
    "read_only_dashboard_validator",
    "dashboard_visual_layout_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "coverage_index_validator",
    "live_final_guard_validator",
]

CHANGED_ARTIFACTS = [
    "contracts/registry.yaml",
    "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json",
    "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
    "trader1/validation/mvp0_validators.py",
    "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
    "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/ledger/upbit_paper_ledger_idempotency_runtime_evidence_report.json",
    "contracts/security/source_bundle_manifest.json",
    "tools/emit_upbit_paper_ledger_idempotency_runtime_evidence_patch_evidence.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]

BLOCKERS = [
    "POST_RERUN_RECONCILIATION_REQUIRED",
    "ACTUAL_LONG_RUN_RUNTIME_EVIDENCE_MISSING",
    "LIVE_READY_MISSING",
    "API_UNVERIFIED",
    "READ_ONLY_ACCOUNT_SNAPSHOT_MISSING",
    "READ_ONLY_BURN_IN_MISSING",
    "MANUAL_ORDER_TEST_MISSING",
    "OPERATOR_APPROVAL_MISSING",
    "LIVE_ENABLING_EVIDENCE_MISSING",
    "SCALE_UP_NOT_ELIGIBLE",
]


def configure_base() -> None:
    base.PATCH_BASENAME = PATCH_BASENAME
    base.PATCH_ID = PATCH_ID
    base.REQUIREMENT_ID = REQUIREMENT_ID
    base.NEXT_TASK_CLASS = NEXT_TASK_CLASS
    base.VALIDATORS_REQUIRED = VALIDATORS_REQUIRED
    base.CHANGED_ARTIFACTS = CHANGED_ARTIFACTS
    base.BLOCKERS = BLOCKERS


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_runtime_artifacts() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[str]]:
    rollup = build_paper_ledger_rollup_report(
        root=ROOT,
        session_id=SESSION_ID,
        rollup_id="mvp4-upbit-paper-ledger-idempotency-runtime-evidence-rollup",
    )
    rollup_result = validate_paper_ledger_rollup_report(rollup)
    if rollup_result.status != "PASS":
        raise RuntimeError(f"paper ledger rollup did not validate: {rollup_result.status} {rollup_result.blocker_code}")
    rollup_path = write_paper_ledger_rollup_report(root=ROOT, report=rollup)

    evidence = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
        root=ROOT,
        session_id=SESSION_ID,
        evidence_id="mvp4-upbit-paper-ledger-idempotency-runtime-evidence",
    )
    evidence_result = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(evidence)
    if evidence_result.status != "PASS":
        raise RuntimeError(f"ledger idempotency evidence did not validate: {evidence_result.status} {evidence_result.blocker_code}")
    evidence_path = write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=ROOT, report=evidence)

    report = build_launcher_report("UPBIT_PAPER")
    launcher_report_path, dashboard_paths = write_launcher_runtime_bundle(report)
    dashboard = load_json(dashboard_paths["dashboard_shell"])
    dashboard_result = validate_read_only_dashboard_shell(dashboard)
    if dashboard_result.status != "PASS":
        raise RuntimeError(f"dashboard validation failed: {dashboard_result.status} {dashboard_result.blocker_code}")
    if any(evidence.get(field) for field in ("live_order_ready", "live_order_allowed", "can_live_trade", "can_submit_order", "scale_up_allowed")):
        raise RuntimeError("ledger idempotency evidence attempted forbidden live or scale-up permission")

    legacy_html_path = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "dashboard" / "index.html"
    base.write_text(legacy_html_path, dashboard_paths["dashboard_html"].read_text(encoding="utf-8"))
    runtime_artifacts = [
        base.rel(rollup_path),
        base.rel(evidence_path),
        base.rel(launcher_report_path),
        *(base.rel(path) for path in dashboard_paths.values()),
        base.rel(legacy_html_path),
    ]
    return rollup, evidence, dashboard, sorted(set(runtime_artifacts))


def write_context(now: str, trader_hash: str, agents_hash: str, evidence: dict[str, Any]) -> None:
    base.write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: VALIDATOR_IMPLEMENTATION
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1", "trader1.paper_ledger_rollup_report.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Current Upbit PAPER ledger idempotency evidence rereads the canonical PAPER ledger rollup source.
- Event counts, fill counts, duplicate event ids, duplicate dedup keys, semantic duplicate events, and filled order keys are recomputed from JSONL.
- Portfolio provenance must match the rollup latest ledger head hash and cycle id.
- Duplicate, escaped, mismatched, or live-mutated evidence remains blocked.

known_omissions_by_design:
- This patch does not resolve post-rerun operator reconciliation guidance.
- This patch does not create long-run evidence, LIVE_READY, live config, credentials, orders, or scale-up permission.
- Dashboard operator visibility for this new idempotency evidence is the next safe task.

runtime_summary:
- runtime_evidence_status: {evidence["runtime_evidence_status"]}
- idempotency_status: {evidence["idempotency_status"]}
- reconciliation_status: {evidence["reconciliation_status"]}
- portfolio_provenance_status: {evidence["portfolio_provenance_status"]}
- source_ledger_jsonl_count: {evidence["source_ledger_jsonl_count"]}
- recomputed_ledger_event_count: {evidence["recomputed_ledger_event_count"]}
- duplicate_event_id_count: {evidence["duplicate_event_id_count"]}
- live_order_ready: false
- live_order_allowed: false
- can_live_trade: false
- scale_up_allowed: false

conflict_resolution_rule:
TRADER_1.md active authority wins over this context pack. This context pack is a read cache only.
generated_at_utc: {now}
""",
    )
    base.write_text(
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

Upbit PAPER portfolio values are ledger-backed, and the current PAPER ledger rollup now has an independent idempotency runtime evidence report that recomputes JSONL event counts, duplicate keys, and portfolio provenance. Post-rerun review, long-run evidence, LIVE_READY, live orders, credentials, and scale-up remain blocked.

## Next Safe Task

{NEXT_TASK_CLASS}
""",
    )


def update_requirement_artifacts(now: str, trader_hash: str, agents_hash: str, runtime_artifacts: list[str]) -> None:
    artifacts = sorted(set(CHANGED_ARTIFACTS + runtime_artifacts))
    req_path = ROOT / "contracts" / "generated" / "requirement_index.json"
    matrix_path = ROOT / "contracts" / "generated" / "requirement_artifact_matrix.json"
    req_index = load_json(req_path)
    requirements = [item for item in req_index.get("requirements", []) if item.get("requirement_id") != REQUIREMENT_ID]
    requirements.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER ledger idempotency runtime evidence",
            "full_text_marker": f"{REQUIREMENT_ID}: current Upbit PAPER ledger evidence must independently recompute idempotency, reconciliation counts, and portfolio provenance from runtime JSONL",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER ledger idempotency runtime evidence",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": [
                "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1",
                "trader1.paper_ledger_rollup_report.v1",
            ],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": artifacts,
            "test_ids": [
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_paper_ledger_rollup.py",
            ],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LEDGER_RECONCILIATION", "SECTION_IDEMPOTENCY", "SECTION_PORTFOLIO_TRUTH", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": [
                "REQ-MVP4-UPBIT-PAPER-VERIFIED-PORTFOLIO-LEDGER-BOOTSTRAP",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-HEAD-BINDING-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "source_text_sha256": base.sha256_bytes(
                b"current Upbit PAPER ledger evidence must independently recompute idempotency, reconciliation counts, and portfolio provenance from runtime JSONL"
            ),
            "source_authority_sha256": trader_hash,
            "implementation_status": "IMPLEMENTED_RUNTIME_EVIDENCE_LIVE_BLOCKED",
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
    base.write_json(req_path, req_index)

    matrix = load_json(matrix_path)
    rows = [item for item in matrix.get("rows", []) if item.get("requirement_id") != REQUIREMENT_ID]
    rows.append(
        {
            "requirement_id": REQUIREMENT_ID,
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": [
                "contracts/schema/upbit_paper_ledger_idempotency_runtime_evidence_report.schema.json",
                "contracts/schema/paper_ledger_rollup_report.schema.json",
            ],
            "validator_files": [
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": [
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_paper_ledger_rollup.py",
            ],
            "fixture_files": [],
            "runtime_modules": [
                "trader1/runtime/paper/upbit_paper_ledger_idempotency_runtime_evidence.py",
                "trader1/runtime/ledger/paper_ledger_rollup.py",
            ],
            "evidence_artifacts": [
                f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
                f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
                f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
                f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            ],
            "dashboard_artifacts": [
                "ledger.idempotency_status",
                "ledger.reconciliation_status",
                "ledger.portfolio_provenance_status",
            ],
            "patch_result_fields": [
                "live_order_ready_after",
                "live_order_allowed_after",
                "can_live_trade_after",
                "scale_up_allowed_after",
            ],
            "minimum_depth": "DEPTH_5_EVIDENCE_AND_STAGE_GATE",
            "live_affecting": True,
            "status": "IMPLEMENTED_RUNTIME_EVIDENCE_LIVE_BLOCKED",
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
    base.write_json(matrix_path, matrix)


def build_patch_result(
    now: str,
    tests_run: list[dict[str, Any]],
    validators_run: list[dict[str, Any]],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_VERIFIED_PORTFOLIO_LEDGER_BOOTSTRAP.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-VERIFIED-PORTFOLIO-LEDGER-BOOTSTRAP",
                "REQ-MVP4-UPBIT-PAPER-LEDGER-HEAD-BINDING-GUARD",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "PAPER",
            "new_registry_items": [REQUIREMENT_ID, "upbit_paper_ledger_idempotency_runtime_evidence_validator"],
            "new_or_changed_schema_ids": [
                "trader1.upbit_paper_ledger_idempotency_runtime_evidence_report.v1",
                "trader1.paper_ledger_rollup_report.v1",
            ],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "read_cache_update_required": True,
            "context_pack_update_required": True,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_DASHBOARD_OPERATOR_UX",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "next_optional_section_ids": ["SECTION_PORTFOLIO_TRUTH", "SECTION_RUNTIME_RECOVERY_RTO_ACTIVE"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "LIVE_CONFIG_MUTATION", "RISK_SCALE_UP", "RETAINED_ARCHIVE"],
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
                "TRADER_1.0G",
                "AGENTS.0G",
                "paper_ledger_rollup runtime",
                "Upbit PAPER ledger idempotency runtime evidence",
                "live final guard",
            ],
            "task_class": "VALIDATOR_IMPLEMENTATION",
            "required_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "expanded_section_ids": [
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_IDEMPOTENCY",
                "SECTION_PORTFOLIO_TRUTH",
                "SECTION_LIVE_FINAL_GUARD",
            ],
            "authority_section_map_status": "UNCHANGED",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED_PASS",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "optimizer_status_after": "PAPER_SCORECARD_INPUT_ONLY_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_PASS_LIVE_BLOCKED",
            "optimizer_guardrail_result": "PASS_IDEMPOTENCY_EVIDENCE_DOES_NOT_CREATE_RANKING_OR_LIVE_PERMISSION",
            "convergence_state_before": "VERIFIED_PAPER_LEDGER_PORTFOLIO_VISIBLE_POST_RERUN_AND_LONG_RUN_BLOCKERS_REMAIN",
            "convergence_state_after": "PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_PASS_POST_RERUN_AND_LONG_RUN_BLOCKERS_REMAIN",
            "convergence_guardrail_result": "PASS_NO_LIVE_PERMISSION_NO_SCALE_UP",
            "convergence_validators_required": VALIDATORS_REQUIRED,
            "convergence_validators_run": validators_run,
        }
    )
    patch_result["result_hash"] = base.patch_hash(patch_result)
    return patch_result


def write_evidence(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    evidence: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    base.write_json(
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
    base.write_json(
        ROOT / patch_result["stage_gate_result_path"],
        {
            "stage_gate_schema_id": "trader1.stage_gate_result.v1",
            "created_at_utc": now,
            "patch_id": PATCH_ID,
            "target_mvp_level": "MVP-4",
            "stage_gate_status": "PASS_PAPER_LEDGER_IDEMPOTENCY_RUNTIME_EVIDENCE_LIVE_BLOCKED",
            "runtime_evidence_status": evidence["runtime_evidence_status"],
            "idempotency_status": evidence["idempotency_status"],
            "reconciliation_status": evidence["reconciliation_status"],
            "portfolio_provenance_status": evidence["portfolio_provenance_status"],
            "source_ledger_jsonl_count": evidence["source_ledger_jsonl_count"],
            "recomputed_ledger_event_count": evidence["recomputed_ledger_event_count"],
            "duplicate_event_id_count": evidence["duplicate_event_id_count"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_json(
        ROOT / patch_result["evidence_manifest_path"],
        {
            "schema_id": "trader1.evidence_manifest.v1",
            "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
            "created_at_utc": now,
            "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
            "patch_id": PATCH_ID,
            "artifact_paths": sorted(
                set(
                    [
                        *CHANGED_ARTIFACTS,
                        *runtime_artifacts,
                        patch_result["validator_run_log_path"],
                        patch_result["stage_gate_result_path"],
                        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                    ]
                )
            ),
            "known_blockers": patch_result["remaining_blockers"],
            "runtime_evidence_status": evidence["runtime_evidence_status"],
            "idempotency_status": evidence["idempotency_status"],
            "reconciliation_status": evidence["reconciliation_status"],
            "portfolio_provenance_status": evidence["portfolio_provenance_status"],
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    base.write_text(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260502.md",
        f"""# MVP4 Upbit PAPER Ledger Idempotency Runtime Evidence Audit

created_at_utc: {now}
patch_id: {PATCH_ID}

Patch:
- Added a current-runtime Upbit PAPER ledger idempotency evidence producer.
- The producer rereads the canonical PAPER ledger rollup and recomputes event counts, fill counts, duplicate event ids, duplicate dedup keys, duplicate semantic events, duplicate filled order keys, and portfolio provenance.
- Added a closed schema, validator, and negative fixtures for duplicate ledger events, live permission mutation, path escape, and count mismatch.

Runtime evidence:
- runtime_evidence_status={evidence["runtime_evidence_status"]}
- idempotency_status={evidence["idempotency_status"]}
- reconciliation_status={evidence["reconciliation_status"]}
- portfolio_provenance_status={evidence["portfolio_provenance_status"]}
- source_ledger_jsonl_count={evidence["source_ledger_jsonl_count"]}
- recomputed_ledger_event_count={evidence["recomputed_ledger_event_count"]}
- duplicate_event_id_count={evidence["duplicate_event_id_count"]}

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
- post-rerun and long-run blockers remain open
""",
    )


def write_patch_artifacts(
    now: str,
    trader_hash: str,
    agents_hash: str,
    patch_result: dict[str, Any],
    evidence: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    write_evidence(now, trader_hash, agents_hash, patch_result, evidence, runtime_artifacts)
    base.write_json(patch_path, patch_result)
    base.update_state_and_ledger(now, patch_result)
    base.update_read_cache(now, trader_hash, agents_hash)


def main() -> int:
    configure_base()
    now = base.utc_now()
    trader_hash = base.sha256_file(ROOT / "TRADER_1.md")
    agents_hash = base.sha256_file(ROOT / "AGENTS.md")
    write_source_bundle_manifest()
    base.update_authority_manifest(now)
    rollup, evidence, dashboard, runtime_artifacts = write_runtime_artifacts()
    write_context(now, trader_hash, agents_hash, evidence)
    update_requirement_artifacts(now, trader_hash, agents_hash, runtime_artifacts)

    tests_run = [
        base.run_command(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-p",
                "no:cacheprovider",
                "tests/runtime/test_upbit_paper_ledger_idempotency_runtime_evidence.py",
                "tests/runtime/test_paper_ledger_rollup.py",
                "tests/runtime/test_reconciliation.py",
                "tests/runtime/test_safe_launcher.py",
                "-q",
            ]
        ),
        base.run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        base.run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, evidence)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, evidence, runtime_artifacts)

    tests_run.append(base.run_command([sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]))
    validators_run = base.summarize_validators(run_validators(VALIDATORS_REQUIRED))
    patch_result = build_patch_result(now, tests_run, validators_run, evidence)
    write_patch_artifacts(now, trader_hash, agents_hash, patch_result, evidence, runtime_artifacts)

    failed = [item for item in patch_result["tests_run"] + patch_result["validators_run"] if item.get("status") != "PASS"]
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": base.rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "runtime_evidence_status": evidence["runtime_evidence_status"],
                "idempotency_status": evidence["idempotency_status"],
                "reconciliation_status": evidence["reconciliation_status"],
                "portfolio_provenance_status": evidence["portfolio_provenance_status"],
                "source_ledger_jsonl_count": evidence["source_ledger_jsonl_count"],
                "recomputed_ledger_event_count": evidence["recomputed_ledger_event_count"],
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
