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
from trader1.runtime.paper.upbit_public_rest_continuity_history import (  # noqa: E402
    append_upbit_public_rest_continuity_history,
    validate_upbit_public_rest_continuity_history_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a safe Upbit public REST PAPER-only continuity attempt to history.")
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    parser.add_argument("--symbol", default="KRW-BTC")
    parser.add_argument("--continuity-id", default="upbit-public-rest-continuity-history-attempt")
    parser.add_argument("--history-id", default="upbit-public-rest-continuity-history")
    parser.add_argument("--sample-count", type=int, default=2)
    parser.add_argument("--min-required-pass-samples", type=int, default=2)
    parser.add_argument("--interval-seconds", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=float, default=2.5)
    parser.add_argument("--max-attempts", type=int, default=50)
    parser.add_argument("--no-network", action="store_true")
    args = parser.parse_args()

    continuity = build_upbit_public_rest_continuity_report(
        continuity_id=args.continuity_id,
        session_id=args.session_id,
        symbol=args.symbol,
        sample_count=args.sample_count,
        min_required_pass_samples=args.min_required_pass_samples,
        interval_seconds=args.interval_seconds,
        attempt_network=not args.no_network,
        timeout_seconds=args.timeout_seconds,
    )
    continuity_result = validate_upbit_public_rest_continuity_report(continuity)
    continuity_path = write_upbit_public_rest_continuity_report(root=ROOT, report=continuity)
    history_path, history = append_upbit_public_rest_continuity_history(
        root=ROOT,
        continuity_report=continuity,
        history_id=args.history_id,
        max_attempts=args.max_attempts,
    )
    history_result = validate_upbit_public_rest_continuity_history_report(history)
    print(
        json.dumps(
            {
                "status": "PASS" if history_result.status in {"PASS", "BLOCKED"} else "FAIL",
                "continuity_status": continuity_result.status,
                "continuity_blocker_code": continuity_result.blocker_code,
                "history_status": history_result.status,
                "history_blocker_code": history_result.blocker_code,
                "continuity_report_path": continuity_path.relative_to(ROOT).as_posix(),
                "history_report_path": history_path.relative_to(ROOT).as_posix(),
                "total_attempt_count": history["total_attempt_count"],
                "pass_attempt_count": history["pass_attempt_count"],
                "blocked_attempt_count": history["blocked_attempt_count"],
                "duplicate_latest_event_block_count": history["duplicate_latest_event_block_count"],
                "non_advancing_block_count": history["non_advancing_block_count"],
                "data_unavailable_block_count": history["data_unavailable_block_count"],
                "evidence_role": history["evidence_role"],
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if history_result.status in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
