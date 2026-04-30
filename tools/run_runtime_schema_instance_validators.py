from __future__ import annotations

import json
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.mvp0_validators import run_validators


VALIDATORS = [
    "schema_validator",
    "closed_enum_validator",
    "common_defs_drift_validator",
    "runtime_schema_instance_validator",
    "read_only_dashboard_validator",
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
