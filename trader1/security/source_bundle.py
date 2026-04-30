from __future__ import annotations

import fnmatch
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DENYLIST_PATH = ROOT / "contracts" / "security" / "source_bundle_denylist.json"
MANIFEST_PATH = ROOT / "contracts" / "security" / "source_bundle_manifest.json"


CREDENTIAL_PATTERNS = [
    re.compile(r"(?i)\b(api[_-]?key|secret|token|access[_-]?key|private[_-]?key)\b\s*[:=]\s*[\"']?[A-Za-z0-9_/\-+=]{24,}"),
    re.compile(r"(?i)\b[A-Z0-9_]*(API|ACCESS|SECRET|PRIVATE|TOKEN)[A-Z0-9_]*(KEY|TOKEN|SECRET)\b\s*[:=]\s*[\"']?[A-Za-z0-9_/\-+=]{24,}"),
    re.compile(r"(?i)\bauthorization\b\s*[:=]\s*[\"']?Bearer\s+[A-Za-z0-9._~+/\-]{20,}=*"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
]


@dataclass(frozen=True)
class BundlePathDecision:
    path: str
    include: bool
    reason: str


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def source_bundle_file_fingerprint(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        payload = path.read_bytes()
    else:
        payload = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return {"sha256": hashlib.sha256(payload).hexdigest().upper(), "size_bytes": len(payload)}


def load_denylist() -> dict[str, Any]:
    return json.loads(DENYLIST_PATH.read_text(encoding="utf-8"))


def normalize_path(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def is_under_allowed_root(relative_path: str, allow_roots: list[str]) -> bool:
    return any(relative_path == root.rstrip("/") or relative_path.startswith(root.rstrip("/") + "/") for root in allow_roots)


def matches_pattern(relative_path: str, pattern: str) -> bool:
    normalized = relative_path.replace("\\", "/")
    if pattern.endswith("/"):
        prefix = pattern.rstrip("/")
        return normalized == prefix or normalized.startswith(prefix + "/")
    return fnmatch.fnmatch(normalized, pattern)


def classify_path(relative_path: str, denylist: dict[str, Any]) -> BundlePathDecision:
    allow_roots = denylist.get("allow_roots", [])
    deny_paths = denylist.get("deny_paths", [])
    for pattern in deny_paths:
        if matches_pattern(relative_path, pattern):
            return BundlePathDecision(relative_path, False, f"denied:{pattern}")
    if not is_under_allowed_root(relative_path, allow_roots):
        return BundlePathDecision(relative_path, False, "not_in_allow_roots")
    return BundlePathDecision(relative_path, True, "included")


def shipped_forbidden_patterns(denylist: dict[str, Any]) -> list[str]:
    return denylist.get(
        "shipped_forbidden_paths",
        [
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            ".env",
            ".env.*",
            "*.pem",
            "*.key",
            "*token_dump*",
            "*credential_dump*",
        ],
    )


def classify_shipped_forbidden_path(relative_path: str, denylist: dict[str, Any]) -> str | None:
    for pattern in shipped_forbidden_patterns(denylist):
        if matches_pattern(relative_path, pattern):
            return f"shipped_forbidden:{pattern}"
    return None


def iter_repo_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = normalize_path(path, root)
        if relative.startswith(".git/"):
            continue
        files.append(path)
    return sorted(files)


def detect_credential_material(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    findings = []
    for pattern in CREDENTIAL_PATTERNS:
        if pattern.search(text):
            findings.append(pattern.pattern)
    return findings


def build_source_bundle_manifest(root: Path = ROOT, denylist: dict[str, Any] | None = None) -> dict[str, Any]:
    denylist = denylist or load_denylist()
    included = []
    excluded = []
    shipped_forbidden_files = []
    secret_findings = []
    for path in iter_repo_files(root):
        relative = normalize_path(path, root)
        shipped_forbidden_reason = classify_shipped_forbidden_path(relative, denylist)
        if shipped_forbidden_reason is not None:
            shipped_forbidden_files.append({"path": relative, "reason": shipped_forbidden_reason})
        decision = classify_path(relative, denylist)
        if decision.include:
            findings = detect_credential_material(path)
            if findings:
                secret_findings.append({"path": relative, "patterns": findings})
            included.append({"path": relative, **source_bundle_file_fingerprint(path)})
        else:
            excluded.append({"path": relative, "reason": decision.reason})
    return {
        "schema_id": "trader1.source_bundle_manifest.v1",
        "denylist_path": "contracts/security/source_bundle_denylist.json",
        "candidate_bundle_type": "SOURCE_BUNDLE_CANDIDATE",
        "included_files": included,
        "excluded_files": excluded,
        "forbidden_count": len(shipped_forbidden_files),
        "shipped_forbidden_files": shipped_forbidden_files,
        "shipped_forbidden_count": len(shipped_forbidden_files),
        "secret_findings": secret_findings,
        "contains_secret": bool(secret_findings),
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
    }


def write_source_bundle_manifest() -> dict[str, Any]:
    manifest = build_source_bundle_manifest()
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def load_source_bundle_manifest() -> dict[str, Any]:
    if not MANIFEST_PATH.exists():
        return write_source_bundle_manifest()
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
