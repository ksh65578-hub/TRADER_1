from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json
from tools.run_hygiene_safe_pytest import scan_cache_artifacts
from trader1.security.source_bundle import write_source_bundle_manifest


REPORT_SCHEMA_ID = "trader1.source_release_proof_profile_report.v1"
PROFILE_ID = "SOURCE_RELEASE_BUNDLE_PROOF_V1"
DEFAULT_REPORT_PATH = Path("system/evidence/runtime_checks/MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE.report.json")
DEFAULT_HYGIENE_SAFE_PYTEST_REPORT_PATH = Path(
    "system/evidence/runtime_checks/MVP4_SOURCE_RELEASE_BUNDLE_PROOF_PROFILE.hygiene_safe_pytest_report.json"
)
RELEASE_PYTEST_TARGETS = [
    "tests/runtime/test_bytecode_free_syntax_check.py",
    "tests/security/test_source_bundle_security.py",
    "tests/contract/test_patch_result_runtime_schema_validation.py",
    "tests/contract/test_schema_instance_validation.py",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def tail_text(value: str, limit: int = 4000) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def default_release_profile_commands(
    *,
    python_executable: str = sys.executable,
    hygiene_safe_pytest_report_path: Path = DEFAULT_HYGIENE_SAFE_PYTEST_REPORT_PATH,
) -> list[list[str]]:
    return [
        [
            python_executable,
            "tools/run_hygiene_safe_pytest.py",
            "--report",
            hygiene_safe_pytest_report_path.as_posix(),
            "--",
            *RELEASE_PYTEST_TARGETS,
        ],
        [python_executable, "-B", "tools/build_source_bundle_manifest.py"],
        [python_executable, "-B", "tools/run_bundle_security_validators.py"],
        [python_executable, "-B", "tools/run_patch_result_runtime_schema_validators.py"],
        [python_executable, "-B", "tools/run_runtime_schema_instance_validators.py"],
        [python_executable, "-B", "tools/run_live_final_guard_validators.py"],
        [python_executable, "-B", "tools/run_bytecode_free_syntax_check.py"],
    ]


def run_command(args: list[str], *, timeout_seconds: int) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            env=env,
            timeout=timeout_seconds,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        returncode = -1
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        timed_out = True
    duration_ms = int((time.monotonic() - started) * 1000)
    return {
        "command": " ".join(args),
        "status": "PASS" if returncode == 0 and not timed_out else "TIMEOUT" if timed_out else "FAIL",
        "returncode": returncode,
        "duration_ms": duration_ms,
        "stdout_tail": tail_text(stdout),
        "stderr_tail": tail_text(stderr),
    }


def source_bundle_summary() -> dict[str, Any]:
    manifest = write_source_bundle_manifest()
    return {
        "included_count": len(manifest.get("included_files", [])),
        "excluded_count": len(manifest.get("excluded_files", [])),
        "forbidden_count": manifest.get("forbidden_count", 0),
        "shipped_forbidden_count": manifest.get("shipped_forbidden_count", 0),
        "contains_secret": bool(manifest.get("contains_secret")),
        "repo_secret_findings_count": manifest.get("repo_secret_findings_count", 0),
        "live_order_ready": bool(manifest.get("live_order_ready")),
        "live_order_allowed": bool(manifest.get("live_order_allowed")),
        "can_live_trade": bool(manifest.get("can_live_trade")),
    }


def build_source_release_proof_profile_report(
    *,
    command_results: list[dict[str, Any]],
    preexisting_cache_artifacts: list[dict[str, str]],
    post_run_cache_artifacts: list[dict[str, str]],
    manifest_summary: dict[str, Any],
    created_at_utc: str | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    failed_commands = [item for item in command_results if item.get("status") != "PASS"]
    if failed_commands:
        blockers.append("RELEASE_PROOF_COMMAND_FAILED")
    if preexisting_cache_artifacts:
        blockers.append("PREEXISTING_CACHE_ARTIFACTS")
    if post_run_cache_artifacts:
        blockers.append("POST_RUN_CACHE_ARTIFACTS")
    if manifest_summary.get("forbidden_count") or manifest_summary.get("shipped_forbidden_count"):
        blockers.append("SOURCE_OR_SHIPPED_FORBIDDEN_ARTIFACTS")
    if manifest_summary.get("contains_secret") or manifest_summary.get("repo_secret_findings_count"):
        blockers.append("SOURCE_SECRET_FINDINGS")
    if (
        manifest_summary.get("live_order_ready")
        or manifest_summary.get("live_order_allowed")
        or manifest_summary.get("can_live_trade")
    ):
        blockers.append("LIVE_FLAG_DRIFT")

    return {
        "schema_id": REPORT_SCHEMA_ID,
        "created_at_utc": created_at_utc or utc_now(),
        "profile_id": PROFILE_ID,
        "profile_scope": "SOURCE_RELEASE_BUNDLE_PROOF_ONLY_NO_LIVE",
        "status": "PASS" if not blockers else "FAIL",
        "command_count": len(command_results),
        "command_pass_count": len([item for item in command_results if item.get("status") == "PASS"]),
        "command_fail_count": len(failed_commands),
        "commands": command_results,
        "preexisting_cache_artifact_count": len(preexisting_cache_artifacts),
        "post_run_cache_artifact_count": len(post_run_cache_artifacts),
        "preexisting_cache_artifacts": preexisting_cache_artifacts[:20],
        "post_run_cache_artifacts": post_run_cache_artifacts[:20],
        "source_bundle_summary": manifest_summary,
        "blockers": blockers,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def run_source_release_proof_profile(*, timeout_seconds: int = 180) -> dict[str, Any]:
    preexisting_cache_artifacts = scan_cache_artifacts()
    command_results: list[dict[str, Any]] = []
    if not preexisting_cache_artifacts:
        for command in default_release_profile_commands():
            command_results.append(run_command(command, timeout_seconds=timeout_seconds))
    post_run_cache_artifacts = scan_cache_artifacts()
    return build_source_release_proof_profile_report(
        command_results=command_results,
        preexisting_cache_artifacts=preexisting_cache_artifacts,
        post_run_cache_artifacts=post_run_cache_artifacts,
        manifest_summary=source_bundle_summary(),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the bounded TRADER_1 source/release proof profile.")
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH, help="JSON report path.")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="Per-command timeout.")
    args = parser.parse_args()

    report = run_source_release_proof_profile(timeout_seconds=args.timeout_seconds)
    write_json(ROOT / args.output, report)
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
