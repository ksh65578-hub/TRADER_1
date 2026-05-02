from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.runtime.paper.upbit_paper_ledger_idempotency_runtime_evidence import (
    UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult,
    build_upbit_paper_ledger_idempotency_runtime_evidence_report,
    validate_upbit_paper_ledger_idempotency_runtime_evidence_report,
    write_upbit_paper_ledger_idempotency_runtime_evidence_report,
)
from trader1.runtime.paper.upbit_public_collector import durable_atomic_write_json


DEFAULT_SESSION_ID = "mvp1_upbit_paper_launcher"


@dataclass(frozen=True)
class RefreshResult:
    report: dict[str, Any]
    output_path: Path
    validation: UpbitPaperLedgerIdempotencyRuntimeEvidenceValidationResult


def _resolve_under_root(root: Path, path: Path) -> Path:
    root = root.resolve()
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"output path escapes root: {path}") from exc
    normalized = resolved.as_posix()
    if "/.git/" in normalized or "/live/" in normalized or not normalized.endswith(".json"):
        raise ValueError(f"unsafe evidence output path: {path}")
    return resolved


def refresh_upbit_paper_ledger_idempotency_runtime_evidence(
    *,
    root: Path = ROOT,
    session_id: str = DEFAULT_SESSION_ID,
    evidence_id: str = "upbit-paper-ledger-idempotency-runtime-evidence-refresh",
    source_rollup_path: Path | None = None,
    output_path: Path | None = None,
) -> RefreshResult:
    root = Path(root).resolve()
    source_path = None
    if source_rollup_path is not None:
        source_path = _resolve_under_root(root, Path(source_rollup_path))
    report = build_upbit_paper_ledger_idempotency_runtime_evidence_report(
        root=root,
        session_id=session_id,
        evidence_id=evidence_id,
        source_rollup_path=source_path,
    )
    validation = validate_upbit_paper_ledger_idempotency_runtime_evidence_report(report)
    if output_path is None:
        written_path = write_upbit_paper_ledger_idempotency_runtime_evidence_report(root=root, report=report)
    else:
        written_path = _resolve_under_root(root, Path(output_path))
        durable_atomic_write_json(written_path, report)
    return RefreshResult(report=report, output_path=written_path, validation=validation)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Refresh current Upbit PAPER ledger idempotency runtime evidence without live access."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository/runtime root.")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID, help="PAPER session id.")
    parser.add_argument("--evidence-id", default="upbit-paper-ledger-idempotency-runtime-evidence-refresh")
    parser.add_argument("--source-rollup", type=Path, default=None, help="Optional source rollup path under root.")
    parser.add_argument("--output", type=Path, default=None, help="Optional output path under root.")
    parser.add_argument(
        "--allow-blocked",
        action="store_true",
        help="Return success for a BLOCKED report so reconciliation blockers can be inspected as evidence.",
    )
    args = parser.parse_args()

    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    result = refresh_upbit_paper_ledger_idempotency_runtime_evidence(
        root=args.root,
        session_id=args.session_id,
        evidence_id=args.evidence_id,
        source_rollup_path=args.source_rollup,
        output_path=args.output,
    )
    print(
        json.dumps(
            {
                "status": result.validation.status,
                "blocker_code": result.validation.blocker_code,
                "output_path": result.output_path.as_posix(),
                "runtime_evidence_status": result.report.get("runtime_evidence_status"),
                "idempotency_status": result.report.get("idempotency_status"),
                "reconciliation_status": result.report.get("reconciliation_status"),
                "mismatch_count": result.report.get("mismatch_count"),
                "live_order_allowed": result.report.get("live_order_allowed"),
                "can_live_trade": result.report.get("can_live_trade"),
                "scale_up_allowed": result.report.get("scale_up_allowed"),
            },
            indent=2,
        )
    )
    if result.validation.status == "PASS" or (args.allow_blocked and result.validation.status == "BLOCKED"):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
