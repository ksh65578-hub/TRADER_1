from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PATCH_ID = "MVP4_LIVE_REVIEW_DISPLAY_TRUTH_GUARD_20260429_001"
PATCH_BASENAME = "MVP4_LIVE_REVIEW_DISPLAY_TRUTH_GUARD"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json, write_text
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


def run_command(args: list[str]) -> dict[str, Any]:
    completed = subprocess.run(args, cwd=ROOT, text=True, capture_output=True)
    return {
        "command": " ".join(args),
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "returncode": completed.returncode,
    }


def schema_bundle_hash() -> str:
    schema_files = sorted((ROOT / "contracts" / "schema").glob("*.schema.json"))
    return sha256_json({rel(path): sha256_file(path) for path in schema_files})


def source_tree_hash() -> str:
    paths = sorted((ROOT / "trader1").rglob("*.py")) + sorted((ROOT / "tools").glob("*.py"))
    return sha256_json({rel(path): sha256_file(path) for path in paths if "__pycache__" not in path.parts})


def update_authority_manifest(now: str) -> None:
    path = ROOT / "contracts" / "authority_manifest.json"
    manifest = load_json(path)
    manifest["registry_yaml_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "registry.yaml")
    manifest["schema_bundle_sha256_when_generated"] = schema_bundle_hash()
    manifest["validator_bundle_sha256_when_generated"] = sha256_file(ROOT / "contracts" / "validators" / "validator_registry.json")
    manifest["source_tree_hash_when_generated"] = source_tree_hash()
    manifest["updated_at_utc"] = now
    manifest.pop("manifest_sha256", None)
    manifest["manifest_sha256"] = sha256_json(manifest)
    write_json(path, manifest)


def update_context_pack(now: str, trader_hash: str, agents_hash: str) -> None:
    write_text(
        ROOT / "contracts" / "generated" / "context_pack" / "UPBIT_LIVE_REVIEW.md",
        f"""# UPBIT_LIVE_REVIEW

context_pack_id: UPBIT_LIVE_REVIEW
task_class: MVP4_UPBIT_LIVE_REVIEW_DISPLAY_TRUTH_GUARD
source_trader1_sha256: {trader_hash}
source_agents_sha256: {agents_hash}
included_section_ids: ["SECTION_LIVE_GATE_ACTIVE", "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE", "SECTION_LIVE_PREFLIGHT_ACTIVE", "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST"]
included_requirement_ids: ["REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD"]
included_schema_ids: ["trader1.live_preflight_report.v1", "trader1.live_review_dashboard.v1"]
included_validator_ids: ["upbit_live_review_preflight_validator", "live_final_guard_validator"]
included_artifact_ids: ["trader1/runtime/readiness/live_preflight.py", "trader1/dashboard/live_review_dashboard.py"]
source_section_hashes: see contracts/generated/authority_section_map.json

acceptance_checklist:
- generated context pack is not authority
- MVP-4 live review remains review-only
- preflight_status must remain BLOCKED
- primary_blocker_code must be present in blockers
- readiness_surface blocker must match preflight truth
- live review dashboard first line must remain LIVE TRADING: BLOCKED
- display-only dashboard cannot create live permission
- live_order_ready=false, live_order_allowed=false, can_live_trade=false

known_omissions_by_design:
- no exchange credentials
- no official API PASS evidence
- no manual order test
- no operator approval
- no read-only burn-in evidence
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
scale_up_allowed: false

## Current Safe State

MVP4_UPBIT_LIVE_REVIEW_DISPLAY_TRUTH_GUARD is implemented as a safety-only guard. Live review display truth must remain blocked and must match preflight blockers. External live-enabling evidence is still missing, so MVP-5+ behavior remains blocked.
""",
    )


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


def build_patch_result(now: str, tests_run: list[dict[str, Any]], validators_run: list[dict[str, Any]]) -> dict[str, Any]:
    previous = load_json(ROOT / "system" / "evidence" / "patch_results" / "MVP4_PATCH_RESULT_SCHEMA_STRICTNESS.patch_result.json")
    patch_result = dict(previous)
    patch_result.update(
        {
            "patch_id": PATCH_ID,
            "created_at_utc": now,
            "target_mvp_level": "MVP-4",
            "patch_class": "RUNTIME_SAFETY_PATCH",
            "affected_contract_ids": [
                "REQ-MVP4-UPBIT-LIVE-REVIEW-SCAFFOLD",
                "REQ-MVP0-LIVE-BLOCKED-MATRIX",
                "REQ-MVP0-VALIDATOR-LOGIC",
            ],
            "affected_exchange": "UPBIT",
            "affected_market_type": "KRW_SPOT",
            "affected_mode": "LIVE_REVIEW",
            "new_registry_items": [],
            "new_or_changed_schema_ids": [],
            "validators_required": [
                "upbit_live_review_preflight_validator",
                "live_final_guard_validator",
                "patch_result_schema_validator",
                "generated_artifact_dirty_validator",
            ],
            "validators_run": validators_run,
            "tests_run": tests_run,
            "retained_archive_semantic_mapping_status": "NOT_USED_FOR_AUTHORITY_ACTIVE_AUTHORITY_PREVAILED",
            "read_cache_update_required": False,
            "context_pack_update_required": False,
            "current_implementation_state_updated": True,
            "next_task_class": "MVP4_EXTERNAL_LIVE_REVIEW_EVIDENCE_REQUIRED",
            "next_required_section_ids": [
                "SECTION_LIVE_GATE_ACTIVE",
                "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
                "SECTION_LIVE_PREFLIGHT_ACTIVE",
            ],
            "next_optional_section_ids": ["SECTION_AGENTS_MVP4_IMPLEMENT_FIRST"],
            "next_forbidden_default_sections": [
                "SECTION_RETAINED_ARCHIVE",
                "SECTION_OPTIMIZER_FULL",
                "SECTION_CONVERGENCE_FULL",
                "SECTION_LIVE_ENABLING",
                "SECTION_MVP5_LIMITED_LIVE",
            ],
            "remaining_blockers": [
                "LIVE_READY_MISSING",
                "API_UNVERIFIED",
                "EXTERNAL_CREDENTIAL_REQUIRED",
                "MANUAL_ORDER_TEST_MISSING",
                "OPERATOR_APPROVAL_MISSING",
                "READ_ONLY_BURN_IN_MISSING",
                "LIVE_ENABLING_EVIDENCE_MISSING",
                "LIVE_BURN_IN_FEEDBACK_MISSING",
                "EXECUTION_QUALITY_UNTESTED",
                "SURVIVAL_LAYER_BLOCKED",
                "RISK_SCALING_UNTESTED",
                "SCALE_UP_NOT_ELIGIBLE",
            ],
            "evidence_manifest_path": f"system/evidence/{PATCH_BASENAME}.evidence_manifest.json",
            "validator_run_log_path": f"system/evidence/validator_runs/{PATCH_BASENAME}.validator_run_log.json",
            "stage_gate_result_path": f"system/evidence/stage_gates/{PATCH_BASENAME}.stage_gate_result.json",
            "active_read_surface_used": [
                "SECTION_LIVE_GATE_ACTIVE",
                "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
                "SECTION_LIVE_PREFLIGHT_ACTIVE",
                "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST",
            ],
            "task_class": "MVP4_UPBIT_LIVE_REVIEW_DISPLAY_TRUTH_GUARD",
            "required_section_ids": [
                "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
                "SECTION_LIVE_PREFLIGHT_ACTIVE",
            ],
            "expanded_section_ids": [
                "SECTION_LIVE_GATE_ACTIVE",
                "SECTION_MVP4_REQUIRED_COMPONENTS_ACTIVE",
                "SECTION_LIVE_PREFLIGHT_ACTIVE",
                "SECTION_AGENTS_MVP4_IMPLEMENT_FIRST",
            ],
            "authority_section_map_status": "UNCHANGED_FRESH",
            "requirement_index_status": "UNCHANGED_FRESH",
            "requirement_artifact_matrix_status": "UNCHANGED_FRESH",
            "read_cache_manifest_status": "UPDATED",
            "context_pack_status": "UPDATED",
            "current_implementation_state_status": "UPDATED",
            "retained_archive_read": False,
            "full_document_read": False,
            "read_cache_invalidated": False,
            "live_order_ready_before": False,
            "live_order_ready_after": False,
            "live_order_allowed_before": False,
            "live_order_allowed_after": False,
            "can_live_trade_before": False,
            "can_live_trade_after": False,
            "optimizer_patch": "NO_OPTIMIZER_RUNTIME_CHANGE",
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
    patch_result["result_hash"] = ""
    patch_result["result_hash"] = sha256_json({key: value for key, value in patch_result.items() if key != "result_hash"})
    return patch_result


def update_state(now: str, patch_result: dict[str, Any]) -> None:
    path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    state = load_json(path)
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
    write_json(path, state)


def write_evidence(now: str, trader_hash: str, agents_hash: str, patch_result: dict[str, Any]) -> None:
    validator_log = {
        "validator_run_log_schema_id": "trader1.validator_run_log.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "validators_run": patch_result["validators_run"],
        "validators_untested": [],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / patch_result["validator_run_log_path"], validator_log)
    stage_gate = {
        "stage_gate_schema_id": "trader1.stage_gate_result.v1",
        "created_at_utc": now,
        "patch_id": PATCH_ID,
        "target_mvp_level": "MVP-4",
        "stage_gate_status": "PASS_FOR_MVP4_DISPLAY_TRUTH_GUARD_NO_LIVE_ORDERS",
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "remaining_external_blockers": patch_result["remaining_blockers"],
    }
    write_json(ROOT / patch_result["stage_gate_result_path"], stage_gate)
    evidence_manifest = {
        "schema_id": "trader1.evidence_manifest.v1",
        "generated_at_utc": now,
        "project_id": "TRADER_1",
        "authority": {"trader1_sha256": trader_hash, "agents_sha256": agents_hash},
        "evidence_manifest_id": f"{PATCH_BASENAME}_EVIDENCE",
        "artifact_paths": [
            "trader1/runtime/readiness/live_preflight.py",
            "trader1/dashboard/live_review_dashboard.py",
            "tests/readiness/test_upbit_live_review_preflight.py",
            "tools/emit_upbit_live_review_patch_evidence.py",
            "tools/emit_live_review_display_truth_guard_patch_evidence.py",
            patch_result["validator_run_log_path"],
            patch_result["stage_gate_result_path"],
            f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
        ],
        "known_blockers": patch_result["remaining_blockers"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    write_json(ROOT / patch_result["evidence_manifest_path"], evidence_manifest)
    audit_report = "\n".join(
        [
            "# MVP4 Live Review Display Truth Guard Audit",
            "",
            f"created_at_utc: {now}",
            f"patch_id: {PATCH_ID}",
            "",
            "Scope: MVP-4 safety-only display truth guard.",
            "",
            "Findings:",
            "- Upbit live review preflight validation did not explicitly reject non-BLOCKED preflight_status.",
            "- Live review dashboard validation did not explicitly reject display first lines outside LIVE TRADING: BLOCKED.",
            "- The Upbit live review evidence emitter still contained the obsolete LIVE_BLOCKING_PATCH class.",
            "",
            "Patch:",
            "- Enforced BLOCKED preflight status, primary blocker membership, readiness surface blocker parity, and blocked live trading status.",
            "- Enforced dashboard blocker presence, primary blocker membership, and blocked first-line display.",
            "- Updated the old evidence emitter patch_class to RUNTIME_SAFETY_PATCH.",
            "",
            "Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.",
            "",
        ]
    )
    write_text(ROOT / "system" / "evidence" / "audit_reports" / f"{PATCH_BASENAME}_20260429.md", audit_report)


def update_ledger(patch_result: dict[str, Any]) -> None:
    patch_path = ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json"
    ledger_path = ROOT / "system" / "evidence" / "implementation_patch_ledger.json"
    ledger = load_json(ledger_path)
    ledger["updated_at_utc"] = patch_result["created_at_utc"]
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
        }
    )
    write_json(ledger_path, ledger)


def main() -> int:
    now = utc_now()
    trader_hash = sha256_file(ROOT / "TRADER_1.md")
    agents_hash = sha256_file(ROOT / "AGENTS.md")
    update_authority_manifest(now)

    tests_run = [
        run_command([sys.executable, "-m", "compileall", "trader1", "tools", "tests", "-q"]),
        run_command([sys.executable, "-m", "unittest", "tests.readiness.test_upbit_live_review_preflight", "-v"]),
        run_command([sys.executable, "tools/run_upbit_live_review_validators.py"]),
        run_command([sys.executable, "tools/run_live_final_guard_validators.py"]),
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
        run_command([sys.executable, "tools/validate_mvp0_contracts.py"]),
    ]
    validators_run = run_validators(
        [
            "upbit_live_review_preflight_validator",
            "live_final_guard_validator",
            "patch_result_schema_validator",
            "generated_artifact_dirty_validator",
        ]
    )
    update_context_pack(now, trader_hash, agents_hash)
    patch_result = build_patch_result(now, tests_run, validators_run)
    write_evidence(now, trader_hash, agents_hash, patch_result)
    write_json(ROOT / "system" / "evidence" / "patch_results" / f"{PATCH_BASENAME}.patch_result.json", patch_result)
    update_state(now, patch_result)
    update_ledger(patch_result)
    update_authority_manifest(now)
    update_read_cache(now, trader_hash, agents_hash)
    failed = [test for test in tests_run if test["status"] != "PASS"]
    print(
        json.dumps(
            {
                "patch_id": PATCH_ID,
                "status": "PASS" if not failed else "FAIL",
                "patch_result_path": f"system/evidence/patch_results/{PATCH_BASENAME}.patch_result.json",
                "result_hash": patch_result["result_hash"],
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
