from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.smoke import run_safe_smoke
from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run TRADER_1 safe offline smoke checks.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path for the smoke report.")
    parser.add_argument("--skip-validators", action="store_true", help="Only build temporary runtime bundles.")
    args = parser.parse_args()

    report = run_safe_smoke(include_validators=not args.skip_validators)
    if args.output is not None:
        write_json(args.output, report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
