from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.mvp0_validators import run_validators


VALIDATORS = [
    "schema_validator",
    "shadow_observation_runtime_validator",
    "shadow_observation_stream_validator",
    "shadow_observation_scheduler_guard_validator",
    "shadow_observation_persistent_runtime_validator",
    "shadow_observation_actual_runtime_blocker_validator",
    "shadow_observation_actual_runtime_harness_validator",
    "shadow_observation_artifact_writer_validator",
    "paper_shadow_evidence_accumulation_validator",
    "upbit_operational_paper_gate_validator",
    "candidate_scorecard_net_ev_validator",
    "execution_feedback_loop_validator",
    "failure_analysis_validator",
    "profitability_optimizer_evidence_gap_validator",
    "optimizer_guardrail_validator",
    "convergence_assessment_validator",
    "live_final_guard_validator",
]


def main() -> int:
    results = run_validators(VALIDATORS)
    non_pass = [result for result in results if result.get("status") != "PASS"]
    print(
        json.dumps(
            {
                "status": "PASS" if not non_pass else "FAIL",
                "validators_run": results,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not non_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
