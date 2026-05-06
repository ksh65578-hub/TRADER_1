from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.research.profitability.candidate_scorecard import candidate_scorecard_from_upbit_paper_runtime_cycle
from trader1.research.profitability.overfit_diagnostic import (
    overfit_diagnostic_from_upbit_paper_runtime,
    write_overfit_diagnostic_report,
)
from trader1.runtime.paper.upbit_paper_runtime import validate_upbit_paper_runtime_cycle_report
from trader1.runtime.paper.upbit_paper_runtime_sample_history import (
    build_upbit_paper_runtime_sample_history,
    validate_upbit_paper_runtime_sample_history,
    write_upbit_paper_runtime_sample_history,
)
from trader1.validation.mvp0_validators import _overfit_diagnostic_errors


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _blocked_result(message: str, blocker_code: str) -> dict:
    return {
        "status": "BLOCKED",
        "message": message,
        "blocker_code": blocker_code,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def build_current_upbit_paper_overfit_diagnostic(*, root: Path, session_id: str) -> dict:
    root = Path(root).resolve()
    history = build_upbit_paper_runtime_sample_history(root=root, session_id=session_id)
    history_result = validate_upbit_paper_runtime_sample_history(history)
    if history_result.status != "PASS":
        return _blocked_result(history_result.message, history_result.blocker_code or "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")
    if not history.get("samples"):
        return _blocked_result("no PAPER runtime samples are available for overfit diagnostic input", "ACTUAL_PERSISTENT_RUNTIME_EXECUTION_MISSING")

    latest_sample = history["samples"][-1]
    runtime_path = root / latest_sample["source_runtime_cycle_path"]
    runtime = _load_json(runtime_path)
    runtime_result = validate_upbit_paper_runtime_cycle_report(runtime)
    if runtime_result.status != "PASS":
        return _blocked_result(runtime_result.message, runtime_result.blocker_code or "SCHEMA_IDENTITY_MISMATCH")

    scorecard = candidate_scorecard_from_upbit_paper_runtime_cycle(runtime)
    diagnostic = overfit_diagnostic_from_upbit_paper_runtime(
        candidate_scorecard=scorecard,
        runtime_sample_history=history,
        root=root,
    )
    diagnostic_errors = _overfit_diagnostic_errors(diagnostic)
    if diagnostic_errors:
        return {
            **_blocked_result("overfit diagnostic failed contract validation", "SCHEMA_IDENTITY_MISMATCH"),
            "diagnostic_errors": diagnostic_errors,
        }

    history_path = write_upbit_paper_runtime_sample_history(root=root, history=history)
    diagnostic_path = write_overfit_diagnostic_report(root=root, report=diagnostic)
    return {
        "status": "PASS",
        "message": "Upbit PAPER overfit diagnostic was written from ledger-bound runtime samples",
        "session_id": session_id,
        "runtime_sample_history_path": str(history_path.relative_to(root)).replace("\\", "/"),
        "overfit_diagnostic_path": str(diagnostic_path.relative_to(root)).replace("\\", "/"),
        "diagnostic_status": diagnostic["diagnostic_status"],
        "robustness_eligible": diagnostic["robustness_eligible"],
        "sample_count": diagnostic["sample_count"],
        "min_required_sample_count": diagnostic["min_required_sample_count"],
        "blocker_codes": [blocker["code"] for blocker in diagnostic["blockers"]],
        "source_runtime_cycle_hash": runtime["cycle_hash"],
        "diagnostic_hash": diagnostic["diagnostic_hash"],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the non-live Upbit PAPER overfit diagnostic from current runtime samples.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--session-id", default="mvp1_upbit_paper_launcher")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_current_upbit_paper_overfit_diagnostic(root=args.root, session_id=args.session_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
