from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.research.shadow.evidence_accumulator import (
    build_paper_shadow_evidence_accumulation_from_runtime_artifacts,
)
from trader1.research.shadow.evidence_refresh_policy import choose_paper_shadow_evidence_refresh_report
from trader1.research.shadow.paper_shadow_harness_binding import (
    build_paper_shadow_harness_binding_report,
    validate_paper_shadow_harness_binding_report,
)
from trader1.research.shadow.shadow_observation_runtime_orchestration import (
    build_shadow_observation_runtime_orchestration_report,
    validate_shadow_observation_runtime_orchestration_report,
)
from trader1.research.shadow.shadow_runner import validate_paper_shadow_evidence_accumulation_report


PAPER_SESSION_ROOT = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "paper" / "mvp1_upbit_paper_launcher"
SHADOW_SESSION_ROOT = ROOT / "system" / "runtime" / "upbit" / "krw_spot" / "shadow" / "mvp1_upbit_paper_launcher"
SCORECARD_PATH = PAPER_SESSION_ROOT / "profitability" / "candidate_scorecard.json"
OVERFIT_PATH = PAPER_SESSION_ROOT / "profitability" / "overfit_diagnostic_report.json"
SAMPLE_HISTORY_PATH = PAPER_SESSION_ROOT / "paper_runtime" / "upbit_paper_runtime_sample_history.json"
SHADOW_HARNESS_PATH = SHADOW_SESSION_ROOT / "actual_runtime_harness_report.json"
SHADOW_PERSISTENT_RUNTIME_PATH = (
    SHADOW_SESSION_ROOT / "shadow_observation" / "shadow_observation_persistent_runtime_report.json"
)
SHADOW_RUNTIME_SAMPLE_HISTORY_PATH = SHADOW_SESSION_ROOT / "shadow_runtime_sample_history.json"
ORCHESTRATION_PATH = SHADOW_SESSION_ROOT / "runtime_orchestration_report.json"
EVIDENCE_PATH = PAPER_SESSION_ROOT / "paper_shadow_evidence_accumulation_report.json"
BINDING_PATH = SHADOW_SESSION_ROOT / "paper_shadow_harness_binding_report.json"


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> int:
    missing = [
        path
        for path in (
            SCORECARD_PATH,
            OVERFIT_PATH,
            SAMPLE_HISTORY_PATH,
            SHADOW_HARNESS_PATH,
            SHADOW_PERSISTENT_RUNTIME_PATH,
        )
        if not path.is_file()
    ]
    if missing:
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "blocker_code": "MEASUREMENT_MISSING",
                    "missing_inputs": [rel(path) for path in missing],
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                indent=2,
            )
        )
        return 1

    scorecard = load_json(SCORECARD_PATH)
    overfit = load_json(OVERFIT_PATH)
    sample_history = load_json(SAMPLE_HISTORY_PATH)
    shadow_harness = load_json(SHADOW_HARNESS_PATH)
    shadow_persistent_runtime = load_json(SHADOW_PERSISTENT_RUNTIME_PATH)
    shadow_runtime_sample_history = (
        load_json(SHADOW_RUNTIME_SAMPLE_HISTORY_PATH) if SHADOW_RUNTIME_SAMPLE_HISTORY_PATH.is_file() else None
    )
    orchestration = build_shadow_observation_runtime_orchestration_report(
        orchestration_id="mvp1_upbit_paper_launcher",
        persistent_runtime_report=shadow_persistent_runtime,
        actual_runtime_harness_report=shadow_harness,
    )
    orchestration_result = validate_shadow_observation_runtime_orchestration_report(orchestration)
    if orchestration_result.status != "PASS":
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "blocker_code": orchestration_result.blocker_code,
                    "message": orchestration_result.message,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                indent=2,
            )
        )
        return 1

    evidence_id = f"paper-shadow-runtime-evidence:{scorecard.get('source_runtime_cycle_id', 'current')}"
    evidence = build_paper_shadow_evidence_accumulation_from_runtime_artifacts(
        evidence_report_id=evidence_id,
        candidate_scorecard=scorecard,
        overfit_diagnostic_report=overfit,
        paper_sample_history=sample_history,
        shadow_runtime_harness_report=shadow_harness,
        shadow_runtime_sample_history=shadow_runtime_sample_history,
    )
    evidence_result = validate_paper_shadow_evidence_accumulation_report(evidence)
    if evidence_result.status == "FAIL":
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "blocker_code": evidence_result.blocker_code,
                    "message": evidence_result.message,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                indent=2,
            )
        )
        return 1

    existing_evidence = load_json(EVIDENCE_PATH) if EVIDENCE_PATH.is_file() else None
    existing_evidence_result = (
        validate_paper_shadow_evidence_accumulation_report(existing_evidence)
        if isinstance(existing_evidence, dict)
        else None
    )
    existing_binding = load_json(BINDING_PATH) if BINDING_PATH.is_file() else None
    existing_binding_result = (
        validate_paper_shadow_harness_binding_report(existing_binding)
        if isinstance(existing_binding, dict)
        else None
    )
    refresh_decision = choose_paper_shadow_evidence_refresh_report(
        existing_report=existing_evidence,
        existing_validation_result=existing_evidence_result,
        existing_binding_report=existing_binding,
        existing_binding_validation_result=existing_binding_result,
        latest_report=evidence,
        latest_validation_result=evidence_result,
    )
    selected_evidence = refresh_decision.selected_report
    selected_evidence_result = validate_paper_shadow_evidence_accumulation_report(selected_evidence)
    if refresh_decision.selected_source == "existing":
        binding = existing_binding
        binding_result = existing_binding_result
    else:
        binding = build_paper_shadow_harness_binding_report(
            binding_report_id="mvp1_upbit_paper_launcher",
            shadow_runtime_harness_report=shadow_harness,
            paper_shadow_evidence_accumulation_report=selected_evidence,
        )
        binding_result = validate_paper_shadow_harness_binding_report(binding)
    if binding_result.status not in {"PASS", "BLOCKED"} or binding_result.blocker_code in {
        "LIVE_FINAL_GUARD_FAILED",
        "SNAPSHOT_SCOPE_MISMATCH",
        "SCHEMA_IDENTITY_MISMATCH",
    }:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "blocker_code": binding_result.blocker_code,
                    "message": binding_result.message,
                    "live_order_ready": False,
                    "live_order_allowed": False,
                    "can_live_trade": False,
                    "scale_up_allowed": False,
                },
                indent=2,
            )
        )
        return 1

    if refresh_decision.selected_source != "existing":
        write_json(EVIDENCE_PATH, selected_evidence)
    write_json(ORCHESTRATION_PATH, orchestration)
    if refresh_decision.selected_source != "existing":
        write_json(BINDING_PATH, binding)
    print(
        json.dumps(
            {
                "status": "PASS",
                "evidence_path": rel(EVIDENCE_PATH),
                "orchestration_path": rel(ORCHESTRATION_PATH),
                "binding_path": rel(BINDING_PATH),
                "evidence_refresh_action": refresh_decision.evidence_refresh_action,
                "evidence_refresh_reason_code": refresh_decision.evidence_refresh_reason_code,
                "evidence_refresh_selected_source": refresh_decision.selected_source,
                "orchestration_validation_status": orchestration_result.status,
                "orchestration_status": orchestration.get("orchestration_status"),
                "orchestration_decision": orchestration.get("orchestration_decision"),
                "orchestration_blocker_code": orchestration.get("primary_blocker_code"),
                "observed_actual_runtime_seconds": orchestration.get("observed_actual_runtime_seconds"),
                "observed_actual_cycle_count": orchestration.get("observed_actual_cycle_count"),
                "latest_evidence_validation_status": refresh_decision.latest_validation_status,
                "latest_evidence_blocker_code": refresh_decision.latest_blocker_code,
                "latest_paper_sample_count": evidence.get("paper_sample_count"),
                "latest_shadow_sample_count": evidence.get("shadow_sample_count"),
                "latest_shadow_runtime_span_seconds": evidence.get("shadow_runtime_span_seconds"),
                "latest_evidence_window_count": evidence.get("evidence_window_count"),
                "shadow_runtime_history_path": rel(SHADOW_RUNTIME_SAMPLE_HISTORY_PATH)
                if SHADOW_RUNTIME_SAMPLE_HISTORY_PATH.is_file()
                else None,
                "shadow_runtime_history_cycle_count": (
                    shadow_runtime_sample_history.get("accepted_cycle_sample_count")
                    if isinstance(shadow_runtime_sample_history, dict)
                    else 0
                ),
                "shadow_runtime_history_span_seconds": (
                    shadow_runtime_sample_history.get("observed_span_seconds")
                    if isinstance(shadow_runtime_sample_history, dict)
                    else 0
                ),
                "evidence_validation_status": selected_evidence_result.status,
                "evidence_blocker_code": selected_evidence_result.blocker_code,
                "binding_status": binding.get("binding_status"),
                "paper_sample_count": selected_evidence.get("paper_sample_count"),
                "shadow_sample_count": selected_evidence.get("shadow_sample_count"),
                "shadow_sample_deficit": selected_evidence.get("shadow_sample_deficit"),
                "evidence_actionability_status": selected_evidence.get("evidence_actionability_status"),
                "primary_collection_deficit_code": selected_evidence.get("primary_collection_deficit_code"),
                "long_run_evidence_eligible": False,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
