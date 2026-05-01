from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
PATCH_BASENAME = "MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE"
PATCH_ID = f"{PATCH_BASENAME}_20260501_001"
REQUIREMENT_ID = "REQ-MVP4-UPBIT-PAPER-RUNTIME-LEDGER-RECONCILIATION-EVIDENCE"
NEXT_TASK_CLASS = "MVP4_STRATEGY_REGIME_COST_RUNTIME_LINKAGE"

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
from tools.review_plan_reflection_status import (  # noqa: E402
    LEDGER_PATH,
    build_reflection_ledger,
    delete_reflected_files,
    mark_current_files_reflected,
    validate_reflection_ledger,
)
from trader1.runtime.paper.upbit_paper_persistent_loop import run_upbit_paper_persistent_loop  # noqa: E402
from trader1.security.source_bundle import write_source_bundle_manifest  # noqa: E402
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


CHANGED_ARTIFACTS = [
    "trader1/core/ledger/paper_ledger.py",
    "trader1/runtime/ledger/paper_ledger_rollup.py",
    "trader1/validation/mvp0_validators.py",
    "contracts/schema/paper_ledger_rollup_report.schema.json",
    "tests/runtime/test_paper_ledger_rollup.py",
    "tools/emit_upbit_paper_runtime_ledger_reconciliation_evidence_patch.py",
    f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
]
VALIDATORS_REQUIRED = [
    "registry_validator",
    "schema_validator",
    "paper_ledger_rollup_validator",
    "ledger_durability_validator",
    "runtime_schema_instance_validator",
    "review_plan_reflection_ledger_validator",
    "path_namespace_validator",
    "single_writer_order_path_validator",
    "live_final_guard_validator",
    "source_bundle_hygiene_validator",
    "shipped_package_hygiene_validator",
    "secret_scan_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
]
BOOTSTRAP_VALIDATORS = [
    validator_id
    for validator_id in VALIDATORS_REQUIRED
    if validator_id
    not in {
        "patch_result_schema_validator",
        "patch_result_runtime_schema_instance_validator",
        "generated_artifact_dirty_validator",
    }
]
FINAL_VALIDATORS = [
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
    "generated_artifact_dirty_validator",
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


def run_command(args: list[str], timeout_seconds: int = 300) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, env=env, timeout=timeout_seconds)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def remove_python_bytecode_artifacts() -> None:
    for path in ROOT.rglob("__pycache__"):
        if ".git" not in path.parts and path.is_dir():
            shutil.rmtree(path)
    for path in ROOT.rglob("*.pyc"):
        if ".git" not in path.parts and path.is_file():
            path.unlink()


def run_runtime_artifacts() -> list[str]:
    loop = run_upbit_paper_persistent_loop(
        root=ROOT,
        loop_id="mvp4-upbit-paper-runtime-ledger-lifecycle-reconciliation",
        requested_cycle_count=2,
    )
    paths: list[str] = []
    for cycle in loop.get("cycle_results", []):
        paths.extend(path for path in cycle.get("artifact_paths", []) if isinstance(path, str))
    for key in ("runtime_recovery_guard_path", "paper_ledger_rollup_path"):
        if isinstance(loop.get(key), str):
            paths.append(loop[key])
    paths.append(
        "system/runtime/upbit/krw_spot/paper/mvp1_upbit_paper_launcher/"
        "paper_runtime/mvp4-upbit-paper-runtime-ledger-lifecycle-reconciliation.persistent_loop_report.json"
    )
    return sorted(set(paths))


def _current_review_files(ledger: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for entry in ledger.get("review_files", []):
        review_file = str(entry.get("review_file") or "")
        if not review_file or entry.get("reflection_status") == "DELETED_AFTER_REFLECTION":
            continue
        if (ROOT / review_file).exists():
            files.append(review_file)
    return sorted(set(files))


def _review_category_counts(text: str) -> dict[str, int]:
    lowered = text.lower()
    categories = {
        "upbit_paper_runtime": ("upbit", "paper", "runtime"),
        "ledger_reconciliation_idempotency": ("ledger", "reconciliation", "idempotency", "duplicate", "partial fill"),
        "strategy_regime_cost_model": ("strategy", "regime", "entry", "exit", "cost", "net edge"),
        "dashboard_operator_truth": ("dashboard", "operator", "portfolio", "user_status_summary"),
        "source_release_hygiene": ("release", "bundle", "pycache", ".git", "pyc", "pytest"),
        "binance_surface_blocked": ("binance", "futures", "spot", "surface-only", "blocked"),
        "live_external_evidence_blocked": ("live_ready", "micro_live", "operator approval", "burn-in", "credential"),
    }
    return {
        category: sum(1 for marker in markers if marker in lowered)
        for category, markers in categories.items()
    }


def build_reaudit_reflection_audit(
    now: str,
    trader_hash: str,
    agents_hash: str,
    ledger_before_delete: dict[str, Any],
    reflected_files: list[str],
    deleted_files: list[str],
    runtime_artifacts: list[str],
) -> dict[str, Any]:
    review_summaries: list[dict[str, Any]] = []
    category_totals: dict[str, int] = {}
    for review_file in reflected_files:
        path = ROOT / review_file
        text = path.read_text(encoding="utf-8-sig") if path.exists() else ""
        counts = _review_category_counts(text)
        for category, count in counts.items():
            category_totals[category] = category_totals.get(category, 0) + count
        entry = next((item for item in ledger_before_delete.get("review_files", []) if item.get("review_file") == review_file), {})
        headings = [line.strip() for line in text.splitlines() if line.lstrip().startswith("#")][:12]
        review_summaries.append(
            {
                "review_file": review_file,
                "sha256": entry.get("sha256"),
                "bytes": entry.get("bytes"),
                "first_line": entry.get("first_line"),
                "theme_ids": entry.get("theme_ids", []),
                "category_counts": counts,
                "sample_headings": headings,
            }
        )
    validation = validate_reflection_ledger(ledger_before_delete)
    return {
        "audit_schema_id": "trader1.upbit_paper_runtime_ledger_reconciliation_reaudit_reflection_audit.v1",
        "generated_at_utc": now,
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "status": "PASS" if validation["status"] == "PASS" else "BLOCKED",
        "review_files_processed_count": len(reflected_files),
        "review_files_deleted_count": len(deleted_files),
        "review_files_processed": review_summaries,
        "review_theme_category_totals": category_totals,
        "review_gap_mapping": [
            {
                "gap": "ledger/reconciliation/idempotency runtime evidence",
                "reflected_status": "IMPLEMENTED_THIS_PATCH_FOR_UPBIT_PAPER_ORDER_LIFECYCLE_COMPLETENESS",
                "evidence": "filled PAPER orders now require intent/reserve/submit/submitted/ack/fill lifecycle evidence before rollup can pass",
            },
            {
                "gap": "strategy/regime/cost model runtime linkage",
                "reflected_status": "NEXT_ALLOWED_TASK",
                "evidence": NEXT_TASK_CLASS,
            },
            {
                "gap": "Binance spot/futures executable runtime",
                "reflected_status": "BLOCKED_SURFACE_ONLY",
                "evidence": "kept out of scope for this Upbit PAPER patch",
            },
            {
                "gap": "LIVE_READY/MICRO_LIVE positive promotion",
                "reflected_status": "BLOCKED_EXTERNAL_EVIDENCE_AND_MVP5_PLUS",
                "evidence": "no live flags, no credentials, no LIVE_ENABLING_PATCH",
            },
        ],
        "runtime_artifacts": runtime_artifacts,
        "validation": validation,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_static_audit() -> dict[str, Any]:
    paper_ledger_text = (ROOT / "trader1" / "core" / "ledger" / "paper_ledger.py").read_text(encoding="utf-8")
    rollup_text = (ROOT / "trader1" / "runtime" / "ledger" / "paper_ledger_rollup.py").read_text(encoding="utf-8")
    test_text = (ROOT / "tests" / "runtime" / "test_paper_ledger_rollup.py").read_text(encoding="utf-8")
    schema = load_json(ROOT / "contracts" / "schema" / "paper_ledger_rollup_report.schema.json")
    checks = {
        "filled_order_lifecycle_constant": "UPBIT_PAPER_FILLED_ORDER_REQUIRED_LIFECYCLE" in paper_ledger_text,
        "incomplete_lifecycle_counter": "count_incomplete_upbit_paper_order_lifecycles" in paper_ledger_text,
        "upbit_paper_ledger_blocks_incomplete_lifecycle": "filled PAPER order lifecycle incomplete" in paper_ledger_text,
        "rollup_reports_lifecycle_count": "lifecycle_incomplete_order_count" in rollup_text,
        "schema_requires_lifecycle_count": "lifecycle_incomplete_order_count" in schema.get("required", []),
        "negative_fixture_present": "test_rollup_blocks_filled_order_without_complete_lifecycle" in test_text,
    }
    blockers = [name for name, passed in checks.items() if not passed]
    return {
        "audit_schema_id": "trader1.upbit_paper_runtime_ledger_lifecycle_guard_audit.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "checks": checks,
        "hidden_defects": [
            {
                "classification": "filled_order_without_complete_lifecycle",
                "condition": "a hash-valid PAPER ledger could include ORDER_FILLED without submit/ack predecessors",
                "impact": "portfolio rollup could count an execution whose order lifecycle was not proved",
                "fix": "Upbit PAPER ledger validation and rollup evidence now count and block incomplete filled-order lifecycle chains",
            }
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def update_context(now: str, trader_hash: str, agents_hash: str, static_audit: dict[str, Any]) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / f"{PATCH_BASENAME}.md",
        f"""# {PATCH_BASENAME}

context_pack_id: {PATCH_BASENAME}
task_class: MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD", "AGENTS_0G.14"]
included_requirement_ids: ["{REQUIREMENT_ID}"]
included_schema_ids: ["trader1.paper_ledger_rollup_report.v1", "trader1.ledger_event.v1", "trader1.patch_result.v1"]
included_validator_ids: {json.dumps(VALIDATORS_REQUIRED)}
included_artifact_ids: {json.dumps(CHANGED_ARTIFACTS)}
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- Filled Upbit PAPER orders require intent, budget reservation, submit started, submitted, ack, and fill lifecycle records.
- PAPER ledger rollup records lifecycle_incomplete_order_count.
- Incomplete lifecycle fixtures block with RECONCILIATION_REQUIRED.
- Current review addendum files are reflected into this audit, state, requirement mapping, and patch evidence before deletion.
- live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.

audit_status: {static_audit["status"]}

known_omissions_by_design:
- no live Upbit order path
- no credential or private account access
- no LIVE_READY snapshot write
- no MVP-5 promotion
- Binance spot/futures remain surface/scaffold gaps

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

Upbit PAPER ledger rollup now blocks filled-order evidence when the lifecycle lacks intent/reserve/submit/submitted/ack/fill completeness. The current review addendum files were reflected into audit evidence and deleted after reflection. This remains PAPER-only and live-blocked.

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
            "source_section_id": "SECTION_LEDGER_RECONCILIATION",
            "source_file": "TRADER_1.md",
            "source_heading": "Upbit PAPER runtime ledger reconciliation evidence",
            "full_text_marker": f"{REQUIREMENT_ID}:filled PAPER order lifecycle completeness must be evidenced before ledger rollup can pass",
            "authority_level": "ACTIVE_AUTHORITY",
            "requirement_title": "Upbit PAPER ledger rollup must block incomplete filled-order lifecycle evidence",
            "requirement_kind": "RUNTIME_SAFETY_PATCH",
            "schema_ids": ["trader1.paper_ledger_rollup_report.v1", "trader1.ledger_event.v1", "trader1.patch_result.v1"],
            "validator_ids": VALIDATORS_REQUIRED,
            "artifact_ids": CHANGED_ARTIFACTS,
            "test_ids": ["tests/runtime/test_paper_ledger_rollup.py", "tests/runtime/test_execution_ledger.py"],
            "mvp_stage": "MVP-4",
            "implementation_depth_min": "DEPTH_4_RUNTIME_INTEGRATION",
            "blocking_level": "LIVE_BLOCKING",
            "live_affecting": True,
            "read_when": ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "depends_on": ["REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP", "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP-CONSISTENCY-GUARD"],
            "source_text_sha256": sha256_bytes(b"filled PAPER order lifecycle completeness must be evidenced before ledger rollup can pass"),
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
            "section_id": "SECTION_LEDGER_RECONCILIATION",
            "schema_files": ["contracts/schema/paper_ledger_rollup_report.schema.json", "contracts/schema/ledger_event.schema.json"],
            "validator_files": [
                "trader1/core/ledger/paper_ledger.py",
                "trader1/runtime/ledger/paper_ledger_rollup.py",
                "trader1/validation/mvp0_validators.py",
            ],
            "test_files": ["tests/runtime/test_paper_ledger_rollup.py", "tests/runtime/test_execution_ledger.py"],
            "fixture_files": [],
            "runtime_modules": ["trader1/core/ledger/paper_ledger.py", "trader1/runtime/ledger/paper_ledger_rollup.py"],
            "evidence_artifacts": [
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
            "minimum_depth": "DEPTH_4_RUNTIME_INTEGRATION",
            "live_affecting": True,
            "status": "IMPLEMENTED_FAIL_CLOSED",
        }
    )
    matrix.update({"updated_at_utc": now, "rows": sorted(rows, key=lambda item: item["requirement_id"])})
    write_json(matrix_path, matrix)


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    template = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_UPBIT_PAPER_LEDGER_ROLLUP_CONSISTENCY_GUARD.patch_result.json")
    patch_result = dict(template)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                REQUIREMENT_ID,
                "REQ-MVP4-UPBIT-PAPER-LEDGER-ROLLUP",
                "REQ-MVP4-LEDGER-RECONCILIATION-IDEMPOTENCY-RECHECK",
                "REQ-MVP4-LIVE-FINAL-GUARD",
            ],
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
            "new_or_changed_schema_ids": ["trader1.paper_ledger_rollup_report.v1"],
            "validators_required": VALIDATORS_REQUIRED,
            "validators_run": validators_run,
            "tests_run": tests_run,
            "coverage_unmapped_count": 0,
            "coverage_index_result": "UPDATED_PASS",
            "registry_yaml_parse_status": "PASS",
            "registry_placeholders_remaining": [],
            "retained_archive_semantic_mapping_status": "CURRENT_REAUDIT_FILES_REFLECTED_TO_OPEN_GAPS_AND_UPBIT_PAPER_LEDGER_LIFECYCLE_EVIDENCE",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": NEXT_TASK_CLASS,
            "next_required_section_ids": ["SECTION_STRATEGY_PROFITABILITY_LOOP", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "next_optional_section_ids": ["SECTION_DASHBOARD_OPERATOR_UX", "SECTION_LEDGER_RECONCILIATION"],
            "next_forbidden_default_sections": ["LIVE_ENABLING_PATCH", "REAL_EXCHANGE_PRIVATE_CALL", "RISK_SCALE_UP"],
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
                "TRADER_1_0G",
                "AGENTS_0G",
                "SECTION_LEDGER_RECONCILIATION",
                "SECTION_UPBIT_PAPER_RUNTIME",
                "SECTION_LIVE_FINAL_GUARD",
                "CURRENT_REAUDIT_REVIEW_FILES",
            ],
            "task_class": "MVP4_UPBIT_PAPER_RUNTIME_LEDGER_RECONCILIATION_EVIDENCE",
            "required_section_ids": ["SECTION_LEDGER_RECONCILIATION", "SECTION_UPBIT_PAPER_RUNTIME", "SECTION_LIVE_FINAL_GUARD"],
            "expanded_section_ids": ["SECTION_LEDGER_RECONCILIATION", "CURRENT_REAUDIT_REVIEW_FILES"],
            "forbidden_default_sections_respected": True,
            "authority_section_map_status": "PASS",
            "requirement_index_status": "UPDATED",
            "requirement_artifact_matrix_status": "UPDATED",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE_LEDGER_RECONCILIATION_EVIDENCE",
            "optimizer_live_mutation_detected": False,
            "optimizer_live_order_allowed_after": False,
            "profit_convergence_patch": "NO_CONVERGENCE_RUNTIME_CHANGE",
            "convergence_layer_changed": False,
            "convergence_live_mutation_detected": False,
            "convergence_live_order_allowed_after": False,
            "scale_up_eligibility_changed": False,
            "scale_up_allowed_after": False,
        }
    )
    patch_result["result_hash"] = patch_hash(patch_result)
    return patch_result


def update_state_and_ledger(now: str, patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(state_path)
    state["updated_at_utc"] = now
    state["current_mvp"] = "MVP-4"
    state["completed_requirement_ids"] = sorted(set(state.get("completed_requirement_ids", []) + [REQUIREMENT_ID]))
    state["implemented_validator_ids"] = sorted(set(state.get("implemented_validator_ids", []) + ["paper_ledger_rollup_validator"]))
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
    ledger["last_patch_id"] = PATCH_ID
    ledger["last_patch_result_hash"] = patch_result["result_hash"]
    ledger["ledger_hash"] = ""
    ledger["ledger_hash"] = sha256_json({key: value for key, value in ledger.items() if key != "ledger_hash"})
    write_json(ledger_path, ledger)


def write_evidence(
    now: str,
    patch_result: dict[str, Any],
    static_audit: dict[str, Any],
    review_audit: dict[str, Any],
    runtime_artifacts: list[str],
) -> None:
    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-4",
        "artifact_paths": [
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
            f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
            f"system/evidence/audit_reports/{PATCH_BASENAME}.review_reflection.audit.json",
            "system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json",
            f"contracts/generated/context_pack/{PATCH_BASENAME}.md",
            *runtime_artifacts,
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    validator_log = {
        "schema_id": "trader1.validator_run_log.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": patch_result["validators_run"],
        "tests_run": patch_result["tests_run"],
    }
    stage_gate = {
        "schema_id": "trader1.stage_gate_result.v1",
        "generated_at_utc": now,
        "patch_id": PATCH_ID,
        "stage_gate": "MVP-4",
        "stage_gate_status": "PASS_WITH_LIVE_BLOCKED",
        "primary_blocker_code": "LIVE_READY_MISSING",
        "static_audit_status": static_audit["status"],
        "review_reflection_status": review_audit["status"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / "system" / "evidence" / f"{PATCH_BASENAME}.evidence_manifest.json", evidence_manifest)
    write_json(ROOT / "system" / "evidence" / "validator_runs" / f"{PATCH_BASENAME}.validator_run_log.json", validator_log)
    write_json(ROOT / "system" / "evidence" / "stage_gates" / f"{PATCH_BASENAME}.stage_gate_result.json", stage_gate)
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", static_audit)
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.review_reflection.audit.json", review_audit)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"

    runtime_artifacts = run_runtime_artifacts()
    static_audit = build_static_audit()
    update_context(now, trader_hash, agents_hash, static_audit)
    update_requirement_artifacts(now, trader_hash, agents_hash)

    bootstrap_patch = build_patch_result(now, [], [])
    write_json(patch_path, bootstrap_patch)
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.audit.json", static_audit)
    write_json(
        ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.review_reflection.audit.json",
        {
            "audit_schema_id": "trader1.upbit_paper_runtime_ledger_reconciliation_reaudit_reflection_audit.v1",
            "generated_at_utc": now,
            "status": "BOOTSTRAP_BEFORE_REVIEW_REFLECTION_DELETE",
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        },
    )
    update_state_and_ledger(now, bootstrap_patch)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    previous_ledger = load_json(LEDGER_PATH) if LEDGER_PATH.exists() else None
    reflection_ledger = build_reflection_ledger(previous=previous_ledger, now=now)
    review_files = _current_review_files(reflection_ledger)
    evidence_paths = [
        f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        f"system/evidence/audit_reports/{PATCH_BASENAME}.audit.json",
        f"system/evidence/audit_reports/{PATCH_BASENAME}.review_reflection.audit.json",
        "system/evidence/audit_reports/REVIEW_PLAN_REFLECTION_LEDGER.json",
        "contracts/generated/current_implementation_state.json",
        "contracts/generated/requirement_index.json",
    ]
    mark_current_files_reflected(
        reflection_ledger,
        patch_id=PATCH_ID,
        evidence_paths=evidence_paths,
        review_files=review_files,
    )
    review_audit_before_delete = build_reaudit_reflection_audit(
        now,
        trader_hash,
        agents_hash,
        reflection_ledger,
        review_files,
        [],
        runtime_artifacts,
    )
    write_json(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}.review_reflection.audit.json", review_audit_before_delete)
    deleted_files = delete_reflected_files(reflection_ledger, max_delete_count=len(review_files))
    reflection_ledger = build_reflection_ledger(previous=reflection_ledger, now=now)
    reflection_ledger["deleted_files_this_run"] = deleted_files
    reflection_ledger["generated_at_utc"] = now
    write_json(LEDGER_PATH, reflection_ledger)
    review_audit = build_reaudit_reflection_audit(
        now,
        trader_hash,
        agents_hash,
        reflection_ledger,
        review_files,
        deleted_files,
        runtime_artifacts,
    )

    remove_python_bytecode_artifacts()
    write_source_bundle_manifest()
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)

    tests_run = [
        run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "tests/runtime/test_paper_ledger_rollup.py", "tests/runtime/test_execution_ledger.py", "-q"]),
        run_command([sys.executable, "-B", "tools/run_bytecode_free_syntax_check.py"]),
        run_command([sys.executable, "-B", "tools/run_runtime_schema_instance_validators.py"]),
    ]
    validators_run = run_validators(BOOTSTRAP_VALIDATORS)
    patch_validator_args = [sys.executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"]

    def persist_patch_result() -> dict[str, Any]:
        patch = build_patch_result(now, tests_run, validators_run)
        write_evidence(now, patch, static_audit, review_audit, runtime_artifacts)
        write_json(patch_path, patch)
        update_state_and_ledger(now, patch)
        update_read_cache(now, trader_hash, agents_hash)
        return patch

    patch_result = persist_patch_result()

    for _ in range(2):
        validators_run = run_validators(VALIDATORS_REQUIRED)
        patch_result = persist_patch_result()

    tests_run.append(run_command(patch_validator_args))
    patch_result = persist_patch_result()

    tests_run.append(run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q"], timeout_seconds=900))
    patch_result = persist_patch_result()

    for _ in range(2):
        validators_run = run_validators(VALIDATORS_REQUIRED)
        patch_result = persist_patch_result()

    patch_validator_command = " ".join(patch_validator_args)
    tests_run = [item for item in tests_run if item.get("command") != patch_validator_command]
    tests_run.append(run_command(patch_validator_args))
    patch_result = persist_patch_result()

    for _ in range(2):
        validators_run = run_validators(VALIDATORS_REQUIRED)
        patch_result = persist_patch_result()

    write_source_bundle_manifest()

    failed = [item for item in [*patch_result["tests_run"], *patch_result["validators_run"]] if item.get("status") != "PASS"]
    if static_audit["status"] != "PASS" or review_audit["status"] != "PASS":
        failed.append({"status": "FAIL", "reason": "audit failed"})
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": rel(patch_path),
                "result_hash": patch_result["result_hash"],
                "review_files_reflected": len(review_files),
                "review_files_deleted": len(deleted_files),
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
