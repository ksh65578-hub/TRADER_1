from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.boot.launcher_guard import inspect_root_launchers
from trader1.validation.mvp0_validators import run_validators


def main() -> int:
    validator_results = run_validators(["root_launcher_guard_validator", "root_launcher_surface_validator"])
    launcher_guard = inspect_root_launchers(ROOT).as_dict()
    status = "PASS" if all(result["status"] == "PASS" for result in validator_results) else "FAIL"
    print(
        json.dumps(
            {
                "status": status,
                "validators": validator_results,
                "launcher_guard": launcher_guard,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
            },
            indent=2,
        )
    )
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
