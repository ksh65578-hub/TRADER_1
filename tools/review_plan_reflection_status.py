from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "검토안"
LEDGER_PATH = ROOT / "system" / "evidence" / "audit_reports" / "REVIEW_PLAN_REFLECTION_LEDGER.json"

EXPECTED_REVIEW_NUMBERS = [number for number in range(1, 45) if number != 29]
REVIEW_STATUS_PENDING = "PENDING_REFLECTION"
REVIEW_STATUS_READY = "REFLECTED_DELETE_READY"
REVIEW_STATUS_DELETED = "DELETED_AFTER_REFLECTION"
ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION = False
DEFAULT_MAX_DELETE_COUNT = 1

THEME_PATTERNS: dict[str, tuple[str, ...]] = {
    "source_package_hygiene": ("pycache", ".pyc", "bundle", "hygiene", "source"),
    "binance_spot_futures_scope": ("binance", "futures", "usd", "spot", "1x", "long/short"),
    "runtime_termination_reproducibility": ("timeout", "pytest", "launcher", "one-shot", "ticks", "reproduc"),
    "upbit_paper_runtime": ("upbit", "paper", "market data", "feature", "runtime", "engine"),
    "dashboard_operator_ux": ("dashboard", "대시", "portfolio", "포트폴리오", "ux", "operator"),
    "portfolio_pnl_truth": ("cash", "equity", "position", "pnl", "realized", "unrealized"),
    "placeholder_readiness_block": ("placeholder", "readiness", "live_ready", "blocked_not_applicable"),
    "authority_manifest_identity": ("authority", "manifest", "hash", "registry", "source identity"),
    "ledger_reconciliation_idempotency": ("ledger", "reconciliation", "idempotency", "duplicate", "partial"),
    "strategy_profitability_loop": ("strategy", "entry", "exit", "regime", "expectancy", "vwap", "breakout"),
    "optimizer_convergence_guardrail": ("optimizer", "convergence", "overfit", "oos", "scorecard"),
    "operations_recovery_24x7": ("daemon", "24/7", "windows", "recovery", "file lock", "shutdown"),
    "live_safety_external_blocker": ("live", "credential", "operator approval", "manual order", "burn-in"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def review_file_number(path: Path) -> int | None:
    try:
        return int(path.stem)
    except ValueError:
        return None


def _first_non_empty_line(text: str) -> str:
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.strip():
            return line.strip()
    return ""


def _theme_ids(text: str) -> list[str]:
    lowered = text.lower()
    return [
        theme_id
        for theme_id, patterns in THEME_PATTERNS.items()
        if any(pattern.lower() in lowered for pattern in patterns)
    ]


def catalog_review_files(review_dir: Path = REVIEW_DIR, *, root: Path = ROOT) -> list[dict[str, Any]]:
    if not review_dir.exists():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(review_dir.glob("*.md"), key=lambda item: (review_file_number(item) is None, review_file_number(item) or 0, item.name)):
        text = path.read_text(encoding="utf-8-sig")
        entries.append(
            {
                "review_file": path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name,
                "review_number": review_file_number(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
                "first_line": _first_non_empty_line(text),
                "theme_ids": _theme_ids(text),
            }
        )
    return entries


def expected_missing_numbers(catalog: list[dict[str, Any]]) -> list[int]:
    present = {entry.get("review_number") for entry in catalog}
    return [number for number in EXPECTED_REVIEW_NUMBERS if number not in present]


def unexpected_review_numbers(catalog: list[dict[str, Any]]) -> list[int]:
    expected = set(EXPECTED_REVIEW_NUMBERS)
    return sorted(
        number
        for number in (entry.get("review_number") for entry in catalog)
        if isinstance(number, int) and number not in expected
    )


def _previous_entry_by_file(previous: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(previous, dict):
        return {}
    return {
        str(entry.get("review_file")): entry
        for entry in previous.get("review_files", [])
        if isinstance(entry, dict) and entry.get("review_file")
    }


def _delete_allowed(entry: dict[str, Any], root: Path = ROOT) -> bool:
    if entry.get("reflection_status") != REVIEW_STATUS_READY:
        return False
    if entry.get("live_order_ready") is True or entry.get("live_order_allowed") is True or entry.get("can_live_trade") is True:
        return False
    if entry.get("scale_up_allowed") is True:
        return False
    if not entry.get("authority_priority_preserved", False):
        return False
    if not entry.get("reflected_by_patch_ids"):
        return False
    evidence_paths = entry.get("reflection_evidence_paths") or []
    if not evidence_paths:
        return False
    return all((root / str(path)).exists() for path in evidence_paths)


def build_reflection_ledger(
    *,
    previous: dict[str, Any] | None = None,
    now: str | None = None,
    root: Path = ROOT,
    review_dir: Path = REVIEW_DIR,
) -> dict[str, Any]:
    catalog = catalog_review_files(review_dir, root=root)
    previous_by_file = _previous_entry_by_file(previous)
    review_entries: list[dict[str, Any]] = []
    for item in catalog:
        previous_entry = previous_by_file.get(item["review_file"], {})
        sha_matches = previous_entry.get("sha256") == item["sha256"]
        status = previous_entry.get("reflection_status") if sha_matches else REVIEW_STATUS_PENDING
        if status not in {REVIEW_STATUS_PENDING, REVIEW_STATUS_READY, REVIEW_STATUS_DELETED}:
            status = REVIEW_STATUS_PENDING
        entry = {
            **item,
            "reflection_status": status,
            "authority_priority_preserved": bool(previous_entry.get("authority_priority_preserved", True)),
            "reflected_by_patch_ids": previous_entry.get("reflected_by_patch_ids", []) if sha_matches else [],
            "reflection_evidence_paths": previous_entry.get("reflection_evidence_paths", []) if sha_matches else [],
            "deletion_allowed": False,
            "delete_reason": "not reflected into authority/contracts/code/tests/artifacts yet",
            "original_review_file_preservation_required_after_reflection": ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION,
            "live_order_ready": False,
            "live_order_allowed": False,
            "can_live_trade": False,
            "scale_up_allowed": False,
        }
        if _delete_allowed(entry, root=root):
            entry["deletion_allowed"] = True
            entry["delete_reason"] = "reflected evidence exists and live flags remain false"
        review_entries.append(entry)
    missing_numbers = expected_missing_numbers(catalog)
    unexpected_numbers = unexpected_review_numbers(catalog)
    delete_ready = [entry["review_file"] for entry in review_entries if entry["deletion_allowed"]]
    pending = [entry["review_file"] for entry in review_entries if not entry["deletion_allowed"] and entry["reflection_status"] != REVIEW_STATUS_DELETED]
    all_theme_ids = sorted({theme_id for entry in review_entries for theme_id in entry.get("theme_ids", [])})
    return {
        "schema_id": "trader1.review_plan_reflection_ledger.v1",
        "generated_at_utc": now,
        "review_directory": review_dir.relative_to(root).as_posix() if review_dir.is_relative_to(root) else str(review_dir),
        "authority_files": ["TRADER_1.md", "AGENTS.md"],
        "authority_priority": "TRADER_1.md > AGENTS.md > review plan addendum > repository code > runtime artifacts",
        "review_files_count": len(review_entries),
        "expected_review_numbers": EXPECTED_REVIEW_NUMBERS,
        "expected_missing_numbers": missing_numbers,
        "unexpected_review_numbers": unexpected_numbers,
        "theme_ids_detected": all_theme_ids,
        "delete_ready_count": len(delete_ready),
        "pending_reflection_count": len(pending),
        "delete_ready_files": delete_ready,
        "review_files": review_entries,
        "deletion_policy": {
            "delete_only_when_reflection_status": REVIEW_STATUS_READY,
            "requires_reflected_by_patch_ids": True,
            "requires_reflection_evidence_paths": True,
            "requires_authority_priority_preserved": True,
            "requires_all_live_flags_false": True,
            "original_review_file_preservation_required_after_reflection": ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION,
            "delete_one_file_at_a_time": True,
        },
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def validate_reflection_ledger(ledger: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    blockers: list[str] = []
    files = ledger.get("review_files", [])
    if not isinstance(files, list):
        blockers.append("review_files_missing")
        files = []
    if ledger.get("live_order_ready") is True or ledger.get("live_order_allowed") is True or ledger.get("can_live_trade") is True:
        blockers.append("live_flag_enabled")
    if ledger.get("scale_up_allowed") is True:
        blockers.append("scale_up_enabled")
    if ledger.get("unexpected_review_numbers"):
        blockers.append("unexpected_review_number")
    missing = ledger.get("expected_missing_numbers", [])
    if missing:
        blockers.append("expected_review_file_missing")
    for entry in files:
        review_path = root / str(entry.get("review_file", ""))
        status = entry.get("reflection_status")
        if status not in {REVIEW_STATUS_PENDING, REVIEW_STATUS_READY, REVIEW_STATUS_DELETED}:
            blockers.append(f"invalid_status:{entry.get('review_file')}")
        if status != REVIEW_STATUS_DELETED and not review_path.exists():
            blockers.append(f"review_file_missing:{entry.get('review_file')}")
        if entry.get("deletion_allowed"):
            if not _delete_allowed(entry, root=root):
                blockers.append(f"unsafe_delete_ready:{entry.get('review_file')}")
        if status == REVIEW_STATUS_READY and not entry.get("deletion_allowed"):
            blockers.append(f"delete_ready_evidence_incomplete:{entry.get('review_file')}")
    return {
        "schema_id": "trader1.review_plan_reflection_validation_result.v1",
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
        "review_files_count": len(files),
        "delete_ready_count": len([entry for entry in files if entry.get("deletion_allowed")]),
        "pending_reflection_count": len([entry for entry in files if entry.get("reflection_status") == REVIEW_STATUS_PENDING]),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def delete_reflected_files(
    ledger: dict[str, Any],
    *,
    root: Path = ROOT,
    max_delete_count: int = DEFAULT_MAX_DELETE_COUNT,
) -> list[str]:
    deleted: list[str] = []
    max_delete_count = max(0, int(max_delete_count))
    validation = validate_reflection_ledger(ledger, root=root)
    if validation["status"] != "PASS":
        return deleted
    for entry in ledger.get("review_files", []):
        if not entry.get("deletion_allowed"):
            continue
        path = root / str(entry["review_file"])
        resolved_root = root.resolve()
        resolved_path = path.resolve()
        if resolved_path.parent != (resolved_root / "검토안"):
            continue
        if path.exists() and path.is_file():
            path.unlink()
            entry["reflection_status"] = REVIEW_STATUS_DELETED
            entry["deletion_allowed"] = False
            entry["delete_reason"] = "deleted after reflection evidence; original source preservation was not required"
            deleted.append(entry["review_file"])
            if len(deleted) >= max_delete_count:
                break
    return deleted


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write reflection ledger")
    parser.add_argument("--validate", action="store_true", help="validate current or generated ledger")
    parser.add_argument("--delete-reflected", action="store_true", help="delete files marked safe in the ledger")
    parser.add_argument("--max-delete-count", type=int, default=DEFAULT_MAX_DELETE_COUNT, help="maximum reflected files to delete in one run")
    args = parser.parse_args()

    previous = load_json(LEDGER_PATH) if LEDGER_PATH.exists() else None
    ledger = build_reflection_ledger(previous=previous)
    if args.delete_reflected:
        deleted = delete_reflected_files(ledger, max_delete_count=args.max_delete_count)
        ledger["deleted_files_this_run"] = deleted
    validation = validate_reflection_ledger(ledger)
    if args.write or args.delete_reflected:
        write_json(LEDGER_PATH, ledger)
    output = {"ledger": ledger, "validation": validation}
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if args.validate and validation["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
