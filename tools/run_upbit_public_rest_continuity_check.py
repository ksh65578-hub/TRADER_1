from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.paper.upbit_public_rest_continuity import (  # noqa: E402
    build_upbit_public_rest_continuity_report,
    validate_upbit_public_rest_continuity_report,
    write_upbit_public_rest_continuity_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe Upbit public REST PAPER-only continuity check.")
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    parser.add_argument("--symbol", default="KRW-BTC")
    parser.add_argument("--continuity-id", default="upbit-public-rest-continuity")
    parser.add_argument("--sample-count", type=int, default=2)
    parser.add_argument("--min-required-pass-samples", type=int, default=2)
    parser.add_argument("--interval-seconds", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=float, default=2.5)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()

    report = build_upbit_public_rest_continuity_report(
        continuity_id=args.continuity_id,
        session_id=args.session_id,
        symbol=args.symbol,
        sample_count=args.sample_count,
        min_required_pass_samples=args.min_required_pass_samples,
        interval_seconds=args.interval_seconds,
        attempt_network=not args.no_network,
        timeout_seconds=args.timeout_seconds,
    )
    result = validate_upbit_public_rest_continuity_report(report)
    path = write_upbit_public_rest_continuity_report(root=ROOT, report=report)
    print(
        json.dumps(
            {
                "status": "PASS" if result.status in {"PASS", "BLOCKED"} else "FAIL",
                "continuity_status": result.status,
                "blocker_code": result.blocker_code,
                "report_path": path.relative_to(ROOT).as_posix(),
                "evidence_role": report["evidence_role"],
                "sample_count_completed": report["sample_count_completed"],
                "pass_sample_count": report["pass_sample_count"],
                "observed_span_seconds": report["observed_span_seconds"],
                "duplicate_latest_event_time_detected": report["duplicate_latest_event_time_detected"],
                "non_advancing_sample_detected": report["non_advancing_sample_detected"],
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
