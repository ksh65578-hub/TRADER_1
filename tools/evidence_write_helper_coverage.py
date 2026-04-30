from __future__ import annotations

import ast
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json


SHARED_WRITER_MODULE = "tools.emit_root_launcher_operator_visibility_patch_evidence"
WRITER_NAMES = {"write_json", "write_text"}
DIRECT_WRITE_METHODS = {"write_text", "write_bytes"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _module_name_for_path(path: Path, root: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix().replace("/", ".")


def _imports_shared_writer(tree: ast.Module) -> bool:
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == SHARED_WRITER_MODULE:
            if any(alias.name in WRITER_NAMES for alias in node.names):
                return True
    return False


def _imported_tool_aliases(tree: ast.Module) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.Import):
            continue
        for alias in node.names:
            if not alias.name.startswith("tools."):
                continue
            aliases[alias.asname or alias.name.rsplit(".", 1)[-1]] = alias.name
    return aliases


def _direct_write_call_lines(tree: ast.Module, safe_writer_aliases: set[str] | None = None) -> list[int]:
    safe_writer_aliases = safe_writer_aliases or set()
    lines: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr in DIRECT_WRITE_METHODS:
            if isinstance(node.func.value, ast.Name) and node.func.value.id in safe_writer_aliases:
                continue
            lines.append(getattr(node, "lineno", 0))
    return sorted(line for line in lines if line)


def _local_writer_classification(tree: ast.Module, source: str) -> str | None:
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    has_writer = any(name in functions for name in WRITER_NAMES)
    if not has_writer:
        return None
    atomic_helper = functions.get("_atomic_write_text")
    if atomic_helper is not None:
        helper_source = ast.get_source_segment(source, atomic_helper) or ""
        if "os.replace" in helper_source and "os.fsync" in helper_source and ".tmp" in helper_source:
            return "LOCAL_ATOMIC"
    return "LOCAL_DIRECT"


def scan_evidence_write_helpers(root: Path = ROOT) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    parsed_files: list[dict[str, Any]] = []
    provider_modules: set[str] = set()
    for path in sorted((root / "tools").glob("*.py")):
        source = path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            rows.append(
                {
                    "path": _rel(path, root),
                    "classification": "PARSE_FAIL",
                    "reason": str(exc),
                }
            )
            continue
        module_name = _module_name_for_path(path, root)
        local_classification = _local_writer_classification(tree, source)
        imports_shared = _imports_shared_writer(tree)
        if imports_shared or local_classification == "LOCAL_ATOMIC":
            provider_modules.add(module_name)
        parsed_files.append(
            {
                "path": path,
                "module_name": module_name,
                "source": source,
                "tree": tree,
                "local_classification": local_classification,
                "imports_shared_writer": imports_shared,
                "imported_aliases": _imported_tool_aliases(tree),
            }
        )
    changed = True
    while changed:
        changed = False
        for item in parsed_files:
            if item["module_name"] in provider_modules:
                continue
            if any(module in provider_modules for module in item["imported_aliases"].values()):
                provider_modules.add(item["module_name"])
                changed = True
    for item in parsed_files:
        path = item["path"]
        tree = item["tree"]
        source = item["source"]
        safe_writer_aliases = {
            alias
            for alias, module in item["imported_aliases"].items()
            if module in provider_modules
        }
        local_classification = _local_writer_classification(tree, source)
        imports_shared = _imports_shared_writer(tree) or bool(safe_writer_aliases)
        direct_write_lines = _direct_write_call_lines(tree, safe_writer_aliases)
        if direct_write_lines and local_classification != "LOCAL_ATOMIC":
            local_classification = "LOCAL_DIRECT"
        if local_classification is None and not imports_shared:
            continue
        classification = local_classification or "SHARED_IMPORT"
        rows.append(
            {
                "path": _rel(path, root),
                "classification": classification,
                "imports_shared_writer": imports_shared,
                "direct_write_line_numbers": direct_write_lines,
            }
        )
    return {
        "scanned_tool_count": len(list((root / "tools").glob("*.py"))),
        "writer_file_count": len(rows),
        "rows": rows,
    }


def build_evidence_write_helper_audit(*, root: Path = ROOT, generated_at_utc: str | None = None) -> dict[str, Any]:
    generated_at_utc = generated_at_utc or utc_now()
    scan = scan_evidence_write_helpers(root)
    local_direct = [row["path"] for row in scan["rows"] if row.get("classification") == "LOCAL_DIRECT"]
    shared = [row["path"] for row in scan["rows"] if row.get("classification") == "SHARED_IMPORT"]
    local_atomic = [row["path"] for row in scan["rows"] if row.get("classification") == "LOCAL_ATOMIC"]
    parse_fail = [row["path"] for row in scan["rows"] if row.get("classification") == "PARSE_FAIL"]
    covered = len(shared) + len(local_atomic)
    writer_count = scan["writer_file_count"]
    coverage_pct = round((covered / writer_count) * 100, 2) if writer_count else 100.0
    has_blockers = bool(local_direct or parse_fail)
    audit = {
        "schema_id": "trader1.evidence_write_helper_coverage_audit.v1",
        "generated_at_utc": generated_at_utc,
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": sha256_file(root / "TRADER_1.md"),
            "agents_sha256": sha256_file(root / "AGENTS.md"),
        },
        "status": "BLOCKED" if has_blockers else "PASS",
        "coverage_pct": coverage_pct,
        "scanned_tool_count": scan["scanned_tool_count"],
        "writer_file_count": writer_count,
        "covered_writer_count": covered,
        "shared_atomic_writer_count": len(shared),
        "local_atomic_writer_count": len(local_atomic),
        "legacy_local_direct_writer_count": len(local_direct),
        "parse_fail_count": len(parse_fail),
        "shared_atomic_writer_paths": shared,
        "local_atomic_writer_paths": local_atomic,
        "legacy_local_direct_writer_paths": local_direct,
        "parse_fail_paths": parse_fail,
        "blockers": []
        if not has_blockers
        else [
            {
                "code": "CONTRACT_GAP_HIGH",
                "severity": "HIGH",
                "message": "Legacy evidence writer helpers still use direct file writes; do not treat evidence helper coverage as complete.",
                "source_requirement_id": "REQ-MVP4-EVIDENCE-WRITE-HELPER-COVERAGE-RECHECK",
            }
        ],
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
        "next_action": "Continue enforcing shared atomic writer coverage."
        if not has_blockers
        else "Convert remaining LOCAL_DIRECT helper scripts to the shared atomic writer or preserve them as legacy blocked evidence.",
        "audit_hash": "",
    }
    audit["audit_hash"] = sha256_json({key: value for key, value in audit.items() if key != "audit_hash"})
    return audit


def write_evidence_write_helper_audit(path: Path, *, root: Path = ROOT) -> dict[str, Any]:
    audit = build_evidence_write_helper_audit(root=root)
    write_json(path, audit)
    return audit


def main() -> int:
    audit = write_evidence_write_helper_audit(
        ROOT / "system" / "evidence" / "audit_reports" / "EVIDENCE_WRITE_HELPER_COVERAGE_AUDIT.json",
        root=ROOT,
    )
    print(json.dumps(audit, indent=2))
    return 0 if audit["status"] in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
