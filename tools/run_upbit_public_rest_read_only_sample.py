from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.paper.upbit_public_rest_sample import (  # noqa: E402
    build_upbit_public_rest_sample_report,
    validate_upbit_public_rest_sample_report,
    write_upbit_public_rest_sample_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe Upbit public REST PAPER-only sample.")
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    parser.add_argument("--symbol", default="KRW-BTC")
    parser.add_argument("--sample-id", default="upbit-public-rest-read-only-sample")
    parser.add_argument("--timeout-seconds", type=float, default=2.5)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()

    report = build_upbit_public_rest_sample_report(
        sample_id=args.sample_id,
        session_id=args.session_id,
        symbol=args.symbol,
        attempt_network=not args.no_network,
        timeout_seconds=args.timeout_seconds,
    )
    result = validate_upbit_public_rest_sample_report(report)
    path = write_upbit_public_rest_sample_report(root=ROOT, report=report)
    print(
        json.dumps(
            {
                "status": "PASS" if result.status in {"PASS", "BLOCKED"} else "FAIL",
                "sample_status": result.status,
                "blocker_code": result.blocker_code,
                "report_path": path.relative_to(ROOT).as_posix(),
                "evidence_role": report["evidence_role"],
                "network_call_attempted": report["network_call_attempted"],
                "canonical_event_count": report["canonical_event_count"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if result.status in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
