from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.run_upbit_paper_candidate_scorecard import build_current_upbit_paper_candidate_scorecard
from trader1.runtime.paper.upbit_paper_persistent_loop import (
    DEFAULT_MAX_CYCLE_COUNT,
    run_upbit_paper_persistent_loop,
    validate_upbit_paper_persistent_loop_report,
)
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history,
)


DEFAULT_TARGET_SAMPLE_COUNT = 300
DEFAULT_MAX_NEW_CYCLES = 20
MAX_ACCUMULATOR_NEW_CYCLES = 200


def utc_now_compact() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y%m%dT%H%M%SZ")


def _blocked_result(message: str, blocker_code: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": "BLOCKED",
        "accumulation_status": "BLOCKED",
        "message": message,
        "blocker_code": blocker_code,
        **extra,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def _robustness_sample_progress(
    *,
    accepted_sample_count: int,
    scorecard_result: dict[str, Any],
    fallback_min_required_sample_count: int,
) -> dict[str, Any]:
    min_required_sample_count = int(scorecard_result.get("min_required_sample_count") or fallback_min_required_sample_count)
    missing_required_sample_count = max(0, min_required_sample_count - accepted_sample_count)
    return {
        "min_required_sample_count": min_required_sample_count,
        "missing_robustness_sample_count": missing_required_sample_count,
        "robustness_sample_floor_met": missing_required_sample_count == 0,
    }


def _history_counts(*, root: Path, session_id: str) -> tuple[dict[str, Any], Any]:
    history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
    return history, validate_upbit_paper_runtime_sample_history(history)


def build_upbit_paper_robustness_sample_accumulation(
    *,
    root: Path,
    session_id: str = "mvp1_upbit_paper_launcher",
    target_sample_count: int = DEFAULT_TARGET_SAMPLE_COUNT,
    max_new_cycles: int = DEFAULT_MAX_NEW_CYCLES,
    cycles_per_loop: int = DEFAULT_MAX_CYCLE_COUNT,
    loop_id_prefix: str | None = None,
) -> dict[str, Any]:
    root = Path(root).resolve()
    target_sample_count = int(target_sample_count)
    max_new_cycles = int(max_new_cycles)
    cycles_per_loop = int(cycles_per_loop)
    if target_sample_count < 1:
        return _blocked_result("target_sample_count must be at least 1", "SAMPLE_ACCUMULATION_INVALID_TARGET")
    if max_new_cycles < 0 or max_new_cycles > MAX_ACCUMULATOR_NEW_CYCLES:
        return _blocked_result("max_new_cycles is outside the safe accumulator range", "RUNTIME_BUDGET_EXCEEDED")
    if cycles_per_loop < 1 or cycles_per_loop > DEFAULT_MAX_CYCLE_COUNT:
        return _blocked_result("cycles_per_loop must stay within the bounded PAPER loop budget", "RUNTIME_BUDGET_EXCEEDED")

    before_history, before_result = _history_counts(root=root, session_id=session_id)
    if before_result.status not in {"PASS"}:
        return _blocked_result(
            before_result.message,
            before_result.blocker_code or "RECONCILIATION_REQUIRED",
            before_sample_count=int(before_history.get("accepted_cycle_sample_count") or 0),
            before_invalid_source_count=int(before_history.get("invalid_source_count") or 0),
        )
    before_count = int(before_history.get("accepted_cycle_sample_count") or 0)
    missing_before = max(0, target_sample_count - before_count)
    cycles_to_run = min(max_new_cycles, missing_before)
    loop_reports: list[dict[str, Any]] = []
    loop_prefix = loop_id_prefix or f"robustness-sample-accumulator-{utc_now_compact()}"

    for index in range(math.ceil(cycles_to_run / cycles_per_loop)):
        requested = min(cycles_per_loop, cycles_to_run - (index * cycles_per_loop))
        if requested <= 0:
            break
        loop_id = f"{loop_prefix}-loop-{index + 1}"
        loop = run_upbit_paper_persistent_loop(
            root=root,
            loop_id=loop_id,
            session_id=session_id,
            requested_cycle_count=requested,
        )
        loop_result = validate_upbit_paper_persistent_loop_report(loop)
        loop_reports.append(
            {
                "loop_id": loop.get("loop_id"),
                "requested_cycle_count": loop.get("requested_cycle_count"),
                "completed_cycle_count": loop.get("completed_cycle_count"),
                "loop_status": loop.get("loop_status"),
                "validation_status": loop_result.status,
                "blocker_code": loop_result.blocker_code,
                "live_order_ready": False,
                "live_order_allowed": False,
                "can_live_trade": False,
                "scale_up_allowed": False,
            }
        )
        if loop_result.status != "PASS":
            after_history, after_result = _history_counts(root=root, session_id=session_id)
            after_count = int(after_history.get("accepted_cycle_sample_count") or 0)
            scorecard_result = build_current_upbit_paper_candidate_scorecard(root=root, session_id=session_id)
            sample_progress = _robustness_sample_progress(
                accepted_sample_count=after_count,
                scorecard_result=scorecard_result,
                fallback_min_required_sample_count=target_sample_count,
            )
            return _blocked_result(
                loop_result.message,
                loop_result.blocker_code or "RECONCILIATION_REQUIRED",
                before_sample_count=before_count,
                after_sample_count=after_count,
                accepted_new_sample_count=max(0, after_count - before_count),
                requested_new_cycle_count=cycles_to_run,
                after_history_validation_status=after_result.status,
                loop_reports=loop_reports,
                scorecard_status=scorecard_result.get("status"),
                candidate_scorecard_path=scorecard_result.get("candidate_scorecard_path"),
                overfit_diagnostic_path=scorecard_result.get("overfit_diagnostic_path"),
                ranking_eligible=bool(scorecard_result.get("ranking_eligible")),
                scorecard_scope=scorecard_result.get("scorecard_scope"),
                diagnostic_status=scorecard_result.get("diagnostic_status"),
                robustness_eligible=bool(scorecard_result.get("robustness_eligible")),
                sample_count=int(scorecard_result.get("sample_count") or after_count),
                min_required_sample_count=sample_progress["min_required_sample_count"],
                missing_robustness_sample_count=sample_progress["missing_robustness_sample_count"],
                robustness_sample_floor_met=sample_progress["robustness_sample_floor_met"],
                scorecard_blocker_codes=scorecard_result.get("scorecard_blocker_codes") or [],
                overfit_blocker_codes=scorecard_result.get("overfit_blocker_codes") or [],
            )

    scorecard_result = build_current_upbit_paper_candidate_scorecard(root=root, session_id=session_id)
    after_history, after_result = _history_counts(root=root, session_id=session_id)
    after_count = int(after_history.get("accepted_cycle_sample_count") or 0)
    new_sample_count = max(0, after_count - before_count)
    if after_result.status != "PASS":
        return _blocked_result(
            after_result.message,
            after_result.blocker_code or "RECONCILIATION_REQUIRED",
            before_sample_count=before_count,
            after_sample_count=after_count,
            loop_reports=loop_reports,
            scorecard_result_status=scorecard_result.get("status"),
        )
    if cycles_to_run and new_sample_count < cycles_to_run:
        return _blocked_result(
            "bounded PAPER loops completed but accepted sample history did not advance as requested",
            "SAMPLE_ACCUMULATION_NO_PROGRESS",
            before_sample_count=before_count,
            after_sample_count=after_count,
            requested_new_cycle_count=cycles_to_run,
            accepted_new_sample_count=new_sample_count,
            loop_reports=loop_reports,
            scorecard_result_status=scorecard_result.get("status"),
        )
    if scorecard_result.get("status") != "PASS":
        return _blocked_result(
            str(scorecard_result.get("message") or "candidate scorecard refresh failed"),
            str(scorecard_result.get("blocker_code") or "SCORECARD_SCHEMA_INVALID"),
            before_sample_count=before_count,
            after_sample_count=after_count,
            loop_reports=loop_reports,
            scorecard_result=scorecard_result,
        )

    missing_after = max(0, target_sample_count - after_count)
    sample_progress = _robustness_sample_progress(
        accepted_sample_count=after_count,
        scorecard_result=scorecard_result,
        fallback_min_required_sample_count=target_sample_count,
    )
    accumulation_status = "TARGET_SAMPLE_COUNT_REACHED" if missing_after == 0 else "COLLECTING"
    blocker_code = None if missing_after == 0 else "SAMPLE_INSUFFICIENT"
    return {
        "status": "PASS",
        "accumulation_status": accumulation_status,
        "message": "bounded Upbit PAPER samples accumulated and candidate scorecard refreshed",
        "session_id": session_id,
        "target_sample_count": target_sample_count,
        "before_sample_count": before_count,
        "after_sample_count": after_count,
        "accepted_new_sample_count": new_sample_count,
        "missing_sample_count": missing_after,
        "missing_target_sample_count": missing_after,
        "missing_robustness_sample_count": sample_progress["missing_robustness_sample_count"],
        "requested_new_cycle_count": cycles_to_run,
        "max_new_cycles": max_new_cycles,
        "cycles_per_loop": cycles_per_loop,
        "loop_reports": loop_reports,
        "loop_report_count": len(loop_reports),
        "invalid_source_count": int(after_history.get("invalid_source_count") or 0),
        "scorecard_status": scorecard_result.get("status"),
        "candidate_scorecard_path": scorecard_result.get("candidate_scorecard_path"),
        "overfit_diagnostic_path": scorecard_result.get("overfit_diagnostic_path"),
        "ranking_eligible": bool(scorecard_result.get("ranking_eligible")),
        "scorecard_scope": scorecard_result.get("scorecard_scope"),
        "diagnostic_status": scorecard_result.get("diagnostic_status"),
        "robustness_eligible": bool(scorecard_result.get("robustness_eligible")),
        "sample_count": int(scorecard_result.get("sample_count") or after_count),
        "min_required_sample_count": sample_progress["min_required_sample_count"],
        "robustness_sample_floor_met": sample_progress["robustness_sample_floor_met"],
        "scorecard_blocker_codes": scorecard_result.get("scorecard_blocker_codes") or [],
        "overfit_blocker_codes": scorecard_result.get("overfit_blocker_codes") or [],
        "blocker_code": blocker_code,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Accumulate bounded non-live Upbit PAPER samples and refresh robustness-gated scorecard evidence."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    parser.add_argument("--target-sample-count", type=int, default=DEFAULT_TARGET_SAMPLE_COUNT)
    parser.add_argument("--max-new-cycles", type=int, default=DEFAULT_MAX_NEW_CYCLES)
    parser.add_argument("--cycles-per-loop", type=int, default=DEFAULT_MAX_CYCLE_COUNT)
    parser.add_argument("--loop-id-prefix", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_upbit_paper_robustness_sample_accumulation(
        root=args.root,
        session_id=args.session_id,
        target_sample_count=args.target_sample_count,
        max_new_cycles=args.max_new_cycles,
        cycles_per_loop=args.cycles_per_loop,
        loop_id_prefix=args.loop_id_prefix,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
