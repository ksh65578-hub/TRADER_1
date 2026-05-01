from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json

REVIEW_DIR = ROOT / "검토안"
LEDGER_PATH = ROOT / "system" / "evidence" / "audit_reports" / "REVIEW_PLAN_REFLECTION_LEDGER.json"

EXPECTED_REVIEW_NUMBERS = [number for number in range(1, 45) if number != 29]
REVIEW_STATUS_PENDING = "PENDING_REFLECTION"
REVIEW_STATUS_READY = "REFLECTED_DELETE_READY"
REVIEW_STATUS_DELETED = "DELETED_AFTER_REFLECTION"
ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION = False
DEFAULT_MAX_DELETE_COUNT = 1000

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


def _load_previous_if_available(previous: dict[str, Any] | None, *, root: Path, review_dir: Path) -> dict[str, Any] | None:
    if previous is not None:
        return previous
    if root == ROOT and review_dir == REVIEW_DIR and LEDGER_PATH.exists():
        return load_json(LEDGER_PATH)
    return None


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
    previous = _load_previous_if_available(previous, root=root, review_dir=review_dir)
    catalog = catalog_review_files(review_dir, root=root)
    previous_by_file = _previous_entry_by_file(previous)
    current_files = {item["review_file"] for item in catalog}
    review_entries: list[dict[str, Any]] = []
    for item in catalog:
        previous_entry = previous_by_file.get(item["review_file"], {})
        sha_matches = previous_entry.get("sha256") == item["sha256"]
        status = previous_entry.get("reflection_status") if sha_matches else REVIEW_STATUS_PENDING
        if status == REVIEW_STATUS_DELETED:
            status = REVIEW_STATUS_PENDING
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

    for review_file, previous_entry in sorted(previous_by_file.items()):
        if review_file in current_files:
            continue
        if previous_entry.get("reflection_status") != REVIEW_STATUS_DELETED:
            continue
        entry = dict(previous_entry)
        entry["reflection_status"] = REVIEW_STATUS_DELETED
        entry["deletion_allowed"] = False
        entry["delete_reason"] = "deleted after reflection evidence; original source preservation was not required"
        entry["original_review_file_preservation_required_after_reflection"] = ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION
        entry["live_order_ready"] = False
        entry["live_order_allowed"] = False
        entry["can_live_trade"] = False
        entry["scale_up_allowed"] = False
        review_entries.append(entry)

    covered_numbers = {
        entry.get("review_number")
        for entry in review_entries
        if isinstance(entry.get("review_number"), int)
    }
    missing_numbers = [number for number in EXPECTED_REVIEW_NUMBERS if number not in covered_numbers]
    unexpected_numbers = unexpected_review_numbers(catalog)
    delete_ready = [entry["review_file"] for entry in review_entries if entry["deletion_allowed"]]
    pending = [entry["review_file"] for entry in review_entries if not entry["deletion_allowed"] and entry["reflection_status"] != REVIEW_STATUS_DELETED]
    deleted = [entry["review_file"] for entry in review_entries if entry["reflection_status"] == REVIEW_STATUS_DELETED]
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
        "deleted_after_reflection_count": len(deleted),
        "pending_reflection_count": len(pending),
        "delete_ready_files": delete_ready,
        "deleted_after_reflection_files": deleted,
        "review_files": review_entries,
        "deletion_policy": {
            "delete_only_when_reflection_status": REVIEW_STATUS_READY,
            "requires_reflected_by_patch_ids": True,
            "requires_reflection_evidence_paths": True,
            "requires_authority_priority_preserved": True,
            "requires_all_live_flags_false": True,
            "original_review_file_preservation_required_after_reflection": ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION,
            "delete_each_file_individually_tracked": True,
            "batch_delete_allowed_when_each_file_has_reflection_evidence": True,
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
    for entry in files:
        review_path = root / str(entry.get("review_file", ""))
        status = entry.get("reflection_status")
        if status not in {REVIEW_STATUS_PENDING, REVIEW_STATUS_READY, REVIEW_STATUS_DELETED}:
            blockers.append(f"invalid_status:{entry.get('review_file')}")
        if status != REVIEW_STATUS_DELETED and not review_path.exists():
            blockers.append(f"review_file_missing:{entry.get('review_file')}")
        if status == REVIEW_STATUS_DELETED and review_path.exists():
            blockers.append(f"deleted_review_file_still_present:{entry.get('review_file')}")
        if status == REVIEW_STATUS_DELETED:
            if not entry.get("reflected_by_patch_ids"):
                blockers.append(f"deleted_without_patch_id:{entry.get('review_file')}")
            evidence_paths = entry.get("reflection_evidence_paths") or []
            if not evidence_paths:
                blockers.append(f"deleted_without_evidence:{entry.get('review_file')}")
            for evidence_path in evidence_paths:
                if not (root / str(evidence_path)).exists():
                    blockers.append(f"deleted_evidence_missing:{entry.get('review_file')}:{evidence_path}")
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
        "deleted_after_reflection_count": len([entry for entry in files if entry.get("reflection_status") == REVIEW_STATUS_DELETED]),
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


def mark_current_files_reflected(
    ledger: dict[str, Any],
    *,
    patch_id: str,
    evidence_paths: list[str],
    review_files: list[str] | None = None,
    root: Path = ROOT,
) -> list[str]:
    marked: list[str] = []
    target_files = set(review_files or [])
    for entry in ledger.get("review_files", []):
        if target_files and entry.get("review_file") not in target_files:
            continue
        if entry.get("reflection_status") == REVIEW_STATUS_DELETED:
            continue
        review_path = root / str(entry.get("review_file", ""))
        if not review_path.exists():
            continue
        patch_ids = list(dict.fromkeys([*entry.get("reflected_by_patch_ids", []), patch_id]))
        paths = list(dict.fromkeys([*entry.get("reflection_evidence_paths", []), *evidence_paths]))
        entry["reflection_status"] = REVIEW_STATUS_READY
        entry["authority_priority_preserved"] = True
        entry["reflected_by_patch_ids"] = patch_ids
        entry["reflection_evidence_paths"] = paths
        entry["deletion_allowed"] = _delete_allowed(entry, root=root)
        entry["delete_reason"] = (
            "reflected into implementation state, requirement mapping, open blockers, and patch evidence"
            if entry["deletion_allowed"]
            else "reflection evidence incomplete"
        )
        entry["original_review_file_preservation_required_after_reflection"] = (
            ORIGINAL_REVIEW_FILE_PRESERVATION_REQUIRED_AFTER_REFLECTION
        )
        entry["live_order_ready"] = False
        entry["live_order_allowed"] = False
        entry["can_live_trade"] = False
        entry["scale_up_allowed"] = False
        if entry["deletion_allowed"]:
            marked.append(str(entry.get("review_file")))
    ledger["delete_ready_files"] = [entry["review_file"] for entry in ledger.get("review_files", []) if entry.get("deletion_allowed")]
    ledger["delete_ready_count"] = len(ledger["delete_ready_files"])
    ledger["pending_reflection_count"] = len(
        [
            entry
            for entry in ledger.get("review_files", [])
            if not entry.get("deletion_allowed") and entry.get("reflection_status") != REVIEW_STATUS_DELETED
        ]
    )
    return marked


def _configure_stdout_utf8() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="write reflection ledger")
    parser.add_argument("--validate", action="store_true", help="validate current or generated ledger")
    parser.add_argument("--delete-reflected", action="store_true", help="delete files marked safe in the ledger")
    parser.add_argument("--mark-current-reflected", action="store_true", help="mark currently present review files as reflected")
    parser.add_argument("--reflection-patch-id", default="MANUAL_REVIEW_PLAN_REFLECTION", help="patch id used when marking current files reflected")
    parser.add_argument("--reflection-evidence-path", action="append", default=[], help="evidence path required before reflected files can be deleted")
    parser.add_argument("--review-file", action="append", default=[], help="specific review file to mark reflected; defaults to all current review files")
    parser.add_argument("--max-delete-count", type=int, default=DEFAULT_MAX_DELETE_COUNT, help="maximum reflected files to delete in one run")
    args = parser.parse_args()

    previous = load_json(LEDGER_PATH) if LEDGER_PATH.exists() else None
    ledger = build_reflection_ledger(previous=previous)
    if args.mark_current_reflected:
        ledger["marked_reflected_this_run"] = mark_current_files_reflected(
            ledger,
            patch_id=args.reflection_patch_id,
            evidence_paths=args.reflection_evidence_path,
            review_files=args.review_file or None,
        )
    if args.delete_reflected:
        deleted = delete_reflected_files(ledger, max_delete_count=args.max_delete_count)
        ledger["deleted_files_this_run"] = deleted
    validation = validate_reflection_ledger(ledger)
    if args.write or args.delete_reflected:
        write_json(LEDGER_PATH, ledger)
    output = {"ledger": ledger, "validation": validation}
    _configure_stdout_utf8()
    print(json.dumps(output, indent=2, ensure_ascii=False))
    if args.validate and validation["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
