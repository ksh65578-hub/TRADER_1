from __future__ import annotations

import hashlib
import json
import tokenize
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


BYTECODE_FREE_SYNTAX_SCHEMA_ID = "trader1.bytecode_free_syntax_report.v1"
DEFAULT_SCAN_PATHS = ("trader1", "tools", "tests")
SKIPPED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
        "env",
        "node_modules",
        "venv",
    }
)


@dataclass(frozen=True)
class BytecodeFreeSyntaxValidationResult:
    status: str
    message: str
    blocker_code: str | None = None


def bytecode_free_syntax_hash(report: dict[str, Any]) -> str:
    clean = dict(report)
    clean.pop("report_hash", None)
    payload = json.dumps(clean, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest().upper()


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _is_skipped(path: Path) -> bool:
    return any(part in SKIPPED_DIRECTORY_NAMES for part in path.parts)


def iter_python_files(root: Path, scan_paths: Iterable[str] = DEFAULT_SCAN_PATHS) -> list[Path]:
    files: list[Path] = []
    for scan_path in scan_paths:
        base = (root / scan_path).resolve()
        if not base.exists():
            continue
        if base.is_file():
            if base.suffix == ".py" and not _is_skipped(base.relative_to(root.resolve())):
                files.append(base)
            continue
        for path in base.rglob("*.py"):
            relative = path.resolve().relative_to(root.resolve())
            if _is_skipped(relative):
                continue
            files.append(path.resolve())
    return sorted(set(files))


def _syntax_error_payload(path: Path, root: Path, exc: BaseException) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "path": path.relative_to(root).as_posix(),
        "error_type": type(exc).__name__,
        "message": str(exc),
    }
    if isinstance(exc, SyntaxError):
        payload["line"] = exc.lineno
        payload["offset"] = exc.offset
    return payload


def build_bytecode_free_syntax_report(
    *,
    root: Path | None = None,
    scan_paths: Iterable[str] = DEFAULT_SCAN_PATHS,
) -> dict[str, Any]:
    root_path = (root or Path(__file__).resolve().parents[2]).resolve()
    files = iter_python_files(root_path, scan_paths)
    errors: list[dict[str, Any]] = []
    for path in files:
        try:
            with tokenize.open(path) as handle:
                source = handle.read()
            compile(source, str(path), "exec", dont_inherit=True)
        except (OSError, SyntaxError, UnicodeError) as exc:
            errors.append(_syntax_error_payload(path, root_path, exc))

    report = {
        "schema_id": BYTECODE_FREE_SYNTAX_SCHEMA_ID,
        "generated_at_utc": _utc_now(),
        "project_id": "TRADER_1",
        "status": "PASS" if not errors else "FAIL",
        "execution_mode": "READ_ONLY_SOURCE_COMPILE_NO_BYTECODE_WRITE",
        "scan_paths": list(scan_paths),
        "skipped_directory_names": sorted(SKIPPED_DIRECTORY_NAMES),
        "files_checked": len(files),
        "syntax_error_count": len(errors),
        "syntax_errors": errors,
        "bytecode_write_attempted": False,
        "pycache_write_attempted": False,
        "external_calls_attempted": False,
        "credential_load_attempted": False,
        "live_order_api_attempted": False,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "blocker_code": None if not errors else "SYNTAX_CHECK_FAILED",
        "report_hash": "",
    }
    report["report_hash"] = bytecode_free_syntax_hash(report)
    return report


def validate_bytecode_free_syntax_report(report: dict[str, Any]) -> BytecodeFreeSyntaxValidationResult:
    if report.get("schema_id") != BYTECODE_FREE_SYNTAX_SCHEMA_ID:
        return BytecodeFreeSyntaxValidationResult("FAIL", "bytecode-free syntax report schema_id mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("report_hash") != bytecode_free_syntax_hash(report):
        return BytecodeFreeSyntaxValidationResult("FAIL", "bytecode-free syntax report hash mismatch", "SCHEMA_IDENTITY_MISMATCH")
    if report.get("execution_mode") != "READ_ONLY_SOURCE_COMPILE_NO_BYTECODE_WRITE":
        return BytecodeFreeSyntaxValidationResult("FAIL", "bytecode-free syntax report used an unsafe execution mode", "RUNTIME_REPRODUCIBILITY_GAP")
    for field in (
        "bytecode_write_attempted",
        "pycache_write_attempted",
        "external_calls_attempted",
        "credential_load_attempted",
        "live_order_api_attempted",
        "live_order_ready",
        "live_order_allowed",
        "can_live_trade",
        "scale_up_allowed",
    ):
        if report.get(field) is not False:
            return BytecodeFreeSyntaxValidationResult("FAIL", f"bytecode-free syntax report attempted forbidden behavior: {field}", "LIVE_FINAL_GUARD_FAILED")
    if int(report.get("files_checked", 0)) <= 0:
        return BytecodeFreeSyntaxValidationResult("FAIL", "bytecode-free syntax report did not check any Python files", "RUNTIME_REPRODUCIBILITY_GAP")
    if report.get("status") != "PASS" or int(report.get("syntax_error_count", 0)) != 0 or report.get("syntax_errors"):
        return BytecodeFreeSyntaxValidationResult("FAIL", "bytecode-free syntax report found syntax errors", "SYNTAX_CHECK_FAILED")
    return BytecodeFreeSyntaxValidationResult("PASS", f"bytecode-free syntax check passed for {report.get('files_checked')} Python files")
