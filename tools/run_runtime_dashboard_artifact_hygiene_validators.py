from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.artifact_hygiene import (  # noqa: E402
    build_runtime_dashboard_artifact_hygiene_report,
    validate_runtime_dashboard_artifact_hygiene_report,
)
from trader1.validation.mvp0_validators import run_validators  # noqa: E402


VALIDATORS = [
    "runtime_dashboard_artifact_hygiene_validator",
    "schema_validator",
    "live_final_guard_validator",
]


def main() -> int:
    report = build_runtime_dashboard_artifact_hygiene_report(ROOT)
    hygiene_result = validate_runtime_dashboard_artifact_hygiene_report(report)
    validator_results = run_validators(VALIDATORS)
    payload = {
        "schema_id": "trader1.runtime_dashboard_artifact_hygiene_validator_run.v1",
        "runtime_dashboard_artifact_hygiene_status": hygiene_result.status,
        "runtime_dashboard_artifact_hygiene_message": hygiene_result.message,
        "runtime_dashboard_artifact_hygiene_blocking_reasons": list(hygiene_result.blocking_reasons),
        "validators_run": validator_results,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if hygiene_result.status != "PASS":
        return 1
    if any(result.get("status") != "PASS" for result in validator_results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
