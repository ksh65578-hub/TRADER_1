from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time


DEFAULT_RUNTIME_RESOURCE_WARN_BYTES = 500_000_000
DEFAULT_RUNTIME_RESOURCE_FAIL_BYTES = 5_000_000_000


@dataclass(frozen=True)
class RuntimeResourcePressure:
    status: str
    artifact_count: int
    byte_count: int
    temp_file_count: int
    lock_present: bool
    lock_age_seconds: float | None
    message: str
    blocker_code: str | None

    def heartbeat_component_overrides(self) -> dict[str, dict[str, str]]:
        if self.status == "PASS":
            return {
                "disk": {
                    "status": "PASS",
                    "message": self.message,
                },
                "queue_backlog": {
                    "status": "PASS",
                    "message": "Runtime writer lock is clear; no partial write pressure detected",
                },
            }
        disk_status = "FAIL" if self.status == "FAIL" else "WARN"
        queue_status = "FAIL" if self.blocker_code == "RESOURCE_LIMIT_BLOCK" else "WARN"
        return {
            "disk": {
                "status": disk_status,
                "message": self.message,
            },
            "queue_backlog": {
                "status": queue_status,
                "message": "Runtime artifact pressure requires review before operator trading review",
            },
        }


def _is_temp_write_file(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".tmp") or (name.startswith(".") and ".tmp" in name)


def _safe_file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return None


def _audit_history_cycle_count(runtime_dir: Path) -> int:
    cycle_roots = (
        runtime_dir / "paper_runtime" / "cycles",
        runtime_dir / "market_data" / "public" / "collection",
        runtime_dir / "ledger" / "cycles",
    )
    counts: list[int] = []
    for cycle_root in cycle_roots:
        if not cycle_root.exists():
            continue
        try:
            counts.append(sum(1 for path in cycle_root.iterdir() if path.is_file()))
        except OSError:
            continue
    return max(counts, default=0)


def inspect_runtime_resource_pressure(
    runtime_dir: Path,
    *,
    warn_file_count: int = 200,
    fail_file_count: int = 1000,
    hard_file_count: int = 20_000,
    warn_bytes: int = DEFAULT_RUNTIME_RESOURCE_WARN_BYTES,
    fail_bytes: int = DEFAULT_RUNTIME_RESOURCE_FAIL_BYTES,
    stale_lock_seconds: float = 30.0,
) -> RuntimeResourcePressure:
    if not runtime_dir.exists():
        return RuntimeResourcePressure(
            status="PASS",
            artifact_count=0,
            byte_count=0,
            temp_file_count=0,
            lock_present=False,
            lock_age_seconds=None,
            message="Runtime artifact pressure PASS: no runtime directory exists yet",
            blocker_code=None,
        )

    files: list[Path] = []
    byte_count = 0
    for path in runtime_dir.rglob("*"):
        try:
            if not path.is_file():
                continue
        except OSError:
            continue
        size = _safe_file_size(path)
        if size is None:
            continue
        files.append(path)
        byte_count += size
    artifact_count = len(files)
    temp_file_count = sum(1 for path in files if _is_temp_write_file(path))
    audit_cycle_count = _audit_history_cycle_count(runtime_dir)
    audit_history_file_budget = 0
    if audit_cycle_count:
        # PAPER audit history writes roughly 4 files per cycle today. Budget 6 plus a fixed session allowance
        # so normal append-only evidence collection does not look like operational backlog.
        audit_history_file_budget = 500 + audit_cycle_count * 6
        warn_file_count = max(warn_file_count, audit_history_file_budget)
        fail_file_count = max(fail_file_count, audit_history_file_budget * 2)
    lock_path = runtime_dir / ".runtime_write.lock"
    lock_present = lock_path.exists()
    lock_age_seconds = None
    if lock_present:
        try:
            lock_age_seconds = max(0.0, time.time() - lock_path.stat().st_mtime)
        except FileNotFoundError:
            lock_present = False

    status = "PASS"
    blocker_code = None
    reasons: list[str] = []
    if artifact_count >= hard_file_count or byte_count >= fail_bytes:
        status = "FAIL"
        blocker_code = "RESOURCE_LIMIT_BLOCK"
        if artifact_count >= hard_file_count:
            reasons.append("runtime artifact file count crossed hard safety threshold")
        if byte_count >= fail_bytes:
            reasons.append("runtime artifact bytes crossed fail threshold")
    elif artifact_count >= fail_file_count:
        status = "WARN"
        reasons.append("runtime artifact file count crossed review threshold")
    elif artifact_count >= warn_file_count or byte_count >= warn_bytes:
        status = "WARN"
        if artifact_count >= warn_file_count:
            reasons.append("runtime artifact file count crossed warning threshold")
        if byte_count >= warn_bytes:
            reasons.append("runtime artifact bytes crossed warning threshold")

    if temp_file_count:
        if status == "PASS":
            status = "WARN"
        reasons.append("temporary write files are present")

    if lock_age_seconds is not None and lock_age_seconds > stale_lock_seconds:
        status = "FAIL"
        blocker_code = "RESOURCE_LIMIT_BLOCK"
        reasons.append("runtime write lock is stale")

    if not reasons:
        if audit_cycle_count:
            reasons.append(
                "runtime artifact count, disk usage, and writer lock are within safe thresholds "
                f"for {audit_cycle_count} audit cycle(s) with file budget {audit_history_file_budget}"
            )
        else:
            reasons.append("runtime artifact count, disk usage, and writer lock are within safe thresholds")
    message = (
        f"Runtime artifact pressure {status}: files={artifact_count}, bytes={byte_count}, "
        f"temp_files={temp_file_count}, lock_present={str(lock_present).lower()}; " + "; ".join(reasons)
    )
    return RuntimeResourcePressure(
        status=status,
        artifact_count=artifact_count,
        byte_count=byte_count,
        temp_file_count=temp_file_count,
        lock_present=lock_present,
        lock_age_seconds=lock_age_seconds,
        message=message,
        blocker_code=blocker_code,
    )
