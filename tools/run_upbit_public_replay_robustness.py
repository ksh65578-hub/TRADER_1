from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.adapters.upbit.market_data import fetch_upbit_public_candle_history_read_only
from trader1.research.replay.replay_runner import (
    build_public_replay_robustness_report,
    validate_public_replay_robustness_report,
    write_public_replay_robustness_report,
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _scorecard_path(root: Path, session_id: str) -> Path:
    return (
        root
        / "system"
        / "runtime"
        / "upbit"
        / "krw_spot"
        / "paper"
        / session_id
        / "profitability"
        / "candidate_scorecard.json"
    )


def build_and_write_public_replay_robustness(
    *,
    root: Path,
    session_id: str,
    target_count: int,
    page_size: int,
    timeout_seconds: float,
    max_replay_windows: int,
) -> dict[str, Any]:
    root = Path(root).resolve()
    scorecard = _load_json(_scorecard_path(root, session_id))
    market_data = fetch_upbit_public_candle_history_read_only(
        symbol=str(scorecard["symbol"]),
        session_id=session_id,
        target_count=target_count,
        page_size=page_size,
        timeout_seconds=timeout_seconds,
    )
    report = build_public_replay_robustness_report(
        candidate_scorecard=scorecard,
        market_data=market_data,
        max_replay_windows=max_replay_windows,
    )
    validation = validate_public_replay_robustness_report(report, candidate_scorecard=scorecard)
    report_path = write_public_replay_robustness_report(root=root, report=report)
    return {
        "status": validation.status,
        "message": validation.message,
        "blocker_code": validation.blocker_code,
        "session_id": session_id,
        "candidate_id": report["candidate_id"],
        "symbol": report["symbol"],
        "report_path": _relative_path(report_path, root),
        "replay_status": report["replay_status"],
        "sample_count": report["sample_count"],
        "min_required_sample_count": report["min_required_sample_count"],
        "public_market_data_source": report["public_market_data_source"],
        "public_market_data_hash": report["public_market_data_hash"],
        "primary_blocker_code": report["primary_blocker_code"],
        "blocker_codes": [blocker["code"] for blocker in report["blockers"]],
        "credential_load_attempted": False,
        "private_endpoint_called": False,
        "order_endpoint_called": False,
        "order_adapter_called": False,
        "live_key_loaded": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build non-live public Upbit replay robustness evidence for the current PAPER scorecard candidate."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    parser.add_argument("--target-count", type=int, default=420)
    parser.add_argument("--page-size", type=int, default=200)
    parser.add_argument("--timeout-seconds", type=float, default=3.0)
    parser.add_argument("--max-replay-windows", type=int, default=420)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_and_write_public_replay_robustness(
        root=args.root,
        session_id=args.session_id,
        target_count=args.target_count,
        page_size=args.page_size,
        timeout_seconds=args.timeout_seconds,
        max_replay_windows=args.max_replay_windows,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
