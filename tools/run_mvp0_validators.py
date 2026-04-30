from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.mvp0_validators import run_validators


def main() -> int:
    results = run_validators()
    status = "PASS" if all(result["status"] == "PASS" for result in results) else "FAIL"
    print(json.dumps({"status": status, "validators": results}, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
