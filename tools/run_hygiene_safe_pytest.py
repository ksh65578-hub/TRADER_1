from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json


FORBIDDEN_DIRECTORY_NAMES = frozenset({"__pycache__", ".pytest_cache"})
FORBIDDEN_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def scan_cache_artifacts(root: Path = ROOT) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for path in root.rglob("*"):
        try:
            relative_parts = path.resolve().relative_to(root.resolve()).parts
        except ValueError:
            continue
        if ".git" in relative_parts:
            continue
        if path.is_dir() and path.name in FORBIDDEN_DIRECTORY_NAMES:
            findings.append({"path": rel(path), "reason": f"forbidden_directory:{path.name}"})
        elif path.is_file() and path.suffix.lower() in FORBIDDEN_FILE_SUFFIXES:
            findings.append({"path": rel(path), "reason": f"forbidden_suffix:{path.suffix.lower()}"})
    return sorted(findings, key=lambda item: item["path"])


def has_no_cacheprovider(args: list[str]) -> bool:
    for index, token in enumerate(args):
        if token == "-p" and index + 1 < len(args) and args[index + 1] == "no:cacheprovider":
            return True
        if token in {"-pno:cacheprovider", "--disable-plugin=cacheprovider"}:
            return True
    return False


def normalize_pytest_args(args: list[str]) -> list[str]:
    normalized = list(args) if args else ["-q"]
    if not has_no_cacheprovider(normalized):
        normalized.extend(["-p", "no:cacheprovider"])
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Run pytest without leaving source/release-forbidden cache artifacts.")
    parser.add_argument("--report", help="Optional JSON report path.")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Arguments passed to pytest. Use -- before pytest args when needed.")
    args = parser.parse_args()

    pytest_args = args.pytest_args
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    pytest_args = normalize_pytest_args(pytest_args)
    before_findings = scan_cache_artifacts()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-m", "pytest", *pytest_args]
    completed = subprocess.run(command, cwd=ROOT, text=True, env=env)
    after_findings = scan_cache_artifacts()
    status = "PASS" if completed.returncode == 0 and not before_findings and not after_findings else "FAIL"
    report = {
        "schema_id": "trader1.hygiene_safe_pytest_report.v1",
        "created_at_utc": utc_now(),
        "status": status,
        "command": " ".join(command),
        "returncode": completed.returncode,
        "preexisting_cache_artifact_count": len(before_findings),
        "post_run_cache_artifact_count": len(after_findings),
        "preexisting_cache_artifacts": before_findings[:20],
        "post_run_cache_artifacts": after_findings[:20],
        "pythondontwritebytecode": env["PYTHONDONTWRITEBYTECODE"],
        "pytest_cacheprovider_disabled": has_no_cacheprovider(pytest_args),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    if args.report:
        write_json(ROOT / args.report, report)
    print(json.dumps(report, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
