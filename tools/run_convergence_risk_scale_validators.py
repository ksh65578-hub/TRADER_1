from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.mvp0_validators import CONVERGENCE_RISK_SCALE_VALIDATORS, run_validators


EXPECTED_STATUSES = {
    "risk_scaling_decision_validator": "BLOCKED",
    "live_burn_in_feedback_validator": "BLOCKED",
    "paper_live_parity_validator": "BLOCKED",
    "execution_quality_measurement_validator": "BLOCKED",
    "survival_layer_validator": "BLOCKED",
}


def main() -> int:
    results = run_validators(CONVERGENCE_RISK_SCALE_VALIDATORS)
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
