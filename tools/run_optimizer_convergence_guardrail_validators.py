from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.mvp0_validators import OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS, run_validators


EXPECTED_STATUSES = {
    "optimizer_no_live_mutation_validator": "PASS",
    "exploration_exploitation_policy_validator": "PASS",
    "exploration_to_exploitation_validator": "PASS",
    "candidate_cooldown_validator": "PASS",
    "rolling_window_default_validator": "PASS",
    "parameter_narrowing_validator": "PASS",
    "optimizer_guardrail_validator": "PASS",
    "convergence_assessment_validator": "PASS",
    "scale_up_eligibility_validator": "BLOCKED",
}


def main() -> int:
    results = run_validators(OPTIMIZER_CONVERGENCE_GUARDRAIL_VALIDATORS)
    statuses = {result["validator_id"]: result["status"] for result in results}
    status = "PASS" if statuses == EXPECTED_STATUSES else "FAIL"
    print(
        json.dumps(
            {
                "status": status,
                "expected_statuses": EXPECTED_STATUSES,
                "validators": results,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
