from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.mvp0_validators import run_validators


def main() -> int:
    validator_results = run_validators(["runtime_resource_pressure_validator"])
    status = "PASS" if all(result["status"] == "PASS" for result in validator_results) else "FAIL"
    print(
        json.dumps(
            {
                "status": status,
                "validators": validator_results,
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
