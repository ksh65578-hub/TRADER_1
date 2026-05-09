from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


ALLOWED_ROOT_LAUNCHERS = frozenset(
    {
        "UPBIT_PAPER",
        "UPBIT_LIVE",
        "BINANCE_PAPER",
        "BINANCE_LIVE",
    }
)
ALLOWED_ROOT_CONTROL_LAUNCHERS = frozenset({"STOP_UPBIT_PAPER"})

LAUNCHER_EXTENSIONS = frozenset({".py", ".ps1", ".bat", ".cmd", ".sh"})
LAUNCHER_NAME_MARKERS = frozenset(
    {
        "launcher",
        "launch",
        "start",
        "run",
        "trade",
        "trader",
        "dashboard",
        "debug",
        "test",
        "temp",
        "tmp",
        "experimental",
        "upbit",
        "binance",
        "paper",
        "live",
    }
)
FORBIDDEN_ROOT_MARKERS = frozenset({"dashboard", "debug", "test", "temp", "tmp", "experimental"})
LIVE_ORDER_MARKERS = (
    "submit_live_order",
    "create_order(",
    "place_order(",
    "send_order(",
    "live_order_allowed = true",
    "live_order_allowed=true",
    "can_live_trade = true",
    "can_live_trade=true",
    "live_order_ready = true",
    "live_order_ready=true",
    "load_live_credentials",
    "live_api_key",
)
PAPER_BROKER_MARKERS = ("paper_broker", "paperbroker", "paper execution", "paper_execution")
EXPLICIT_BINANCE_MARKERS = ("market_type", "--market-type", "spot", "futures_usdt_m")
BINANCE_REQUIRED_MARKET_TYPE_MARKERS = ("spot", "futures_usdt_m")
BINANCE_FUTURES_BLOCKED_MARKERS = ("blocked", "not_implemented", "surface_only")


@dataclass(frozen=True)
class RootLauncherFinding:
    path: str
    logical_name: str
    allowed: bool
    issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RootLauncherGuardResult:
    status: str
    message: str
    root_launchers_found: list[str]
    unexpected_root_launchers_found: list[str]
    live_order_path_found: bool
    direct_strategy_to_exchange_call_found: bool
    blockers: list[str]
    findings: list[RootLauncherFinding]
    live_order_ready: bool = False
    live_order_allowed: bool = False
    can_live_trade: bool = False

    @property
    def primary_blocker_code(self) -> str | None:
        return self.blockers[0] if self.blockers else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "root_launchers_found": self.root_launchers_found,
            "unexpected_root_launchers_found": self.unexpected_root_launchers_found,
            "live_order_path_found": self.live_order_path_found,
            "direct_strategy_to_exchange_call_found": self.direct_strategy_to_exchange_call_found,
            "blockers": self.blockers,
            "findings": [
                {
                    "path": finding.path,
                    "logical_name": finding.logical_name,
                    "allowed": finding.allowed,
                    "issues": finding.issues,
                }
                for finding in self.findings
            ],
            "live_order_ready": self.live_order_ready,
            "live_order_allowed": self.live_order_allowed,
            "can_live_trade": self.can_live_trade,
        }


def normalize_launcher_name(path: Path) -> str:
    return path.stem.upper().replace("-", "_").replace(" ", "_")


def _is_launcher_like(path: Path) -> bool:
    if path.suffix.lower() not in LAUNCHER_EXTENSIONS:
        return False
    stem = path.stem.lower().replace("-", "_")
    logical_name = normalize_launcher_name(path)
    return (
        logical_name in ALLOWED_ROOT_LAUNCHERS
        or logical_name in ALLOWED_ROOT_CONTROL_LAUNCHERS
        or any(marker in stem for marker in LAUNCHER_NAME_MARKERS)
    )


def _read_lower(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return ""


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _content_issues(logical_name: str, text: str) -> list[str]:
    issues: list[str] = []
    if "PAPER" in logical_name and any(marker in text for marker in LIVE_ORDER_MARKERS):
        issues.append("paper launcher references live order or live credential path")
    if "LIVE" in logical_name and any(marker in text for marker in PAPER_BROKER_MARKERS):
        issues.append("live launcher references paper broker")
    if "BINANCE" in logical_name and not any(marker in text for marker in EXPLICIT_BINANCE_MARKERS):
        issues.append("binance launcher lacks explicit market_type selection")
    if "BINANCE" in logical_name and not all(marker in text for marker in BINANCE_REQUIRED_MARKET_TYPE_MARKERS):
        issues.append("binance launcher must disclose both SPOT and FUTURES_USDT_M market_type boundary")
    if "BINANCE" in logical_name and "futures_usdt_m" in text and not any(marker in text for marker in BINANCE_FUTURES_BLOCKED_MARKERS):
        issues.append("binance futures market_type lacks blocked/not implemented status")
    if logical_name == "BINANCE_LIVE" and "futures_usdt_m" in text and "default" in text:
        issues.append("binance futures live appears to be an implicit default")
    return issues


def inspect_root_launchers(root: Path | str, *, require_exact_four: bool = False) -> RootLauncherGuardResult:
    root_path = Path(root).resolve()
    blockers: list[str] = []
    findings: list[RootLauncherFinding] = []
    root_launchers_found: list[str] = []
    unexpected: list[str] = []
    live_order_path_found = False
    direct_strategy_to_exchange_call_found = False
    logical_name_counts: dict[str, int] = {}

    if not root_path.exists() or not root_path.is_dir():
        return RootLauncherGuardResult(
            status="FAIL",
            message="repository root cannot be inspected",
            root_launchers_found=[],
            unexpected_root_launchers_found=[],
            live_order_path_found=False,
            direct_strategy_to_exchange_call_found=False,
            blockers=["CONTRACT_GAP_HIGH"],
            findings=[],
        )

    for path in sorted(item for item in root_path.iterdir() if item.is_file()):
        if not _is_launcher_like(path):
            continue
        logical_name = normalize_launcher_name(path)
        text = _read_lower(path)
        issues: list[str] = []
        allowed_trading_launcher = logical_name in ALLOWED_ROOT_LAUNCHERS
        allowed_control_launcher = logical_name in ALLOWED_ROOT_CONTROL_LAUNCHERS
        allowed = allowed_trading_launcher or allowed_control_launcher
        logical_name_counts[logical_name] = logical_name_counts.get(logical_name, 0) + 1

        if allowed_trading_launcher:
            root_launchers_found.append(logical_name)
            issues.extend(_content_issues(logical_name, text))
        elif allowed_control_launcher:
            issues.extend(_content_issues(logical_name, text))
        else:
            unexpected.append(_relative(path, root_path))
            lower_stem = path.stem.lower()
            if any(marker in lower_stem for marker in FORBIDDEN_ROOT_MARKERS):
                issues.append("forbidden root launcher category")
            else:
                issues.append("unexpected root launcher")

        if any(marker in text for marker in LIVE_ORDER_MARKERS):
            live_order_path_found = True
        if "strategy" in text and "exchange" in text and any(marker in text for marker in LIVE_ORDER_MARKERS):
            direct_strategy_to_exchange_call_found = True

        findings.append(
            RootLauncherFinding(
                path=_relative(path, root_path),
                logical_name=logical_name,
                allowed=allowed,
                issues=issues,
            )
        )

    root_launchers_found = sorted(set(root_launchers_found))
    duplicate_allowed = sorted(
        name for name, count in logical_name_counts.items() if name in ALLOWED_ROOT_LAUNCHERS and count > 1
    )
    if duplicate_allowed:
        blockers.append("CONTRACT_GAP_HIGH")
        findings.append(
            RootLauncherFinding(
                path=".",
                logical_name="DUPLICATE_ROOT_LAUNCHER",
                allowed=False,
                issues=[f"duplicate allowed root launcher: {name}" for name in duplicate_allowed],
            )
        )
    if unexpected:
        blockers.append("CONTRACT_GAP_HIGH")
    if root_launchers_found and set(root_launchers_found) != ALLOWED_ROOT_LAUNCHERS:
        blockers.append("CONTRACT_GAP_HIGH")
    if require_exact_four and set(root_launchers_found) != ALLOWED_ROOT_LAUNCHERS:
        blockers.append("CONTRACT_GAP_HIGH")
    if any(finding.issues for finding in findings if finding.allowed):
        blockers.append("LIVE_FINAL_GUARD_FAILED")
    if direct_strategy_to_exchange_call_found:
        blockers.append("CANDIDATE_DIRECT_LIVE_FORBIDDEN")

    blockers = list(dict.fromkeys(blockers))
    if blockers:
        if unexpected:
            message = "unexpected root launcher files are present"
        elif root_launchers_found and set(root_launchers_found) != ALLOWED_ROOT_LAUNCHERS:
            message = "partial root launcher surface is blocked until exactly four launchers are present"
        elif require_exact_four:
            message = "required root launcher surface is missing"
        else:
            message = "root launcher policy violation blocks live readiness"
        return RootLauncherGuardResult(
            status="BLOCKED",
            message=message,
            root_launchers_found=root_launchers_found,
            unexpected_root_launchers_found=unexpected,
            live_order_path_found=live_order_path_found,
            direct_strategy_to_exchange_call_found=direct_strategy_to_exchange_call_found,
            blockers=blockers,
            findings=findings,
        )

    if not root_launchers_found:
        message = "no root execution launcher surface is present; MVP-1 launcher creation remains blocked for live trading"
    else:
        message = "root launcher surface contains exactly the four allowed launchers"
    return RootLauncherGuardResult(
        status="PASS",
        message=message,
        root_launchers_found=root_launchers_found,
        unexpected_root_launchers_found=[],
        live_order_path_found=live_order_path_found,
        direct_strategy_to_exchange_call_found=direct_strategy_to_exchange_call_found,
        blockers=[],
        findings=findings,
    )
