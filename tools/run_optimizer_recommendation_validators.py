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
    "optimization_state_validator",
    "optimizer_run_report_validator",
    "optimizer_recommendation_validator",
    "optimizer_guardrail_report_validator",
    "optimizer_no_live_mutation_validator",
    "optimizer_guardrail_validator",
    "live_final_guard_validator",
    "patch_result_schema_validator",
    "patch_result_runtime_schema_instance_validator",
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
