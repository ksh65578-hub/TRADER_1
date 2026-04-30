from __future__ import annotations

import argparse
import ast
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.emit_root_launcher_operator_visibility_patch_evidence import sha256_file, write_json


HIGH_RISK_KEYWORDS = {
    "live",
    "order",
    "optimizer",
    "convergence",
    "risk",
    "scale",
    "ledger",
    "reconciliation",
    "emergency",
    "safety",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _string_literals(node: ast.AST) -> set[str]:
    return {item.value for item in ast.walk(node) if isinstance(item, ast.Constant) and isinstance(item.value, str)}


def _call_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for item in ast.walk(node):
        if not isinstance(item, ast.Call):
            continue
        func = item.func
        if isinstance(func, ast.Name):
            names.append(func.id)
        elif isinstance(func, ast.Attribute):
            names.append(func.attr)
    return names


def _registry_validator_ids(registry: dict[str, Any]) -> list[str]:
    validator_ids: set[str] = set()
    for validators in registry.get("validators", {}).values():
        if isinstance(validators, list):
            validator_ids.update(item for item in validators if isinstance(item, str))
    return sorted(validator_ids)


def _depth_class(
    line_count: int,
    fail_or_blocked_calls: int,
    branch_count: int,
    validate_or_evaluate_calls: int,
    fixture_ref_count: int,
    test_ref_count: int,
    literals: set[str],
) -> str:
    if line_count <= 8 and fail_or_blocked_calls == 0:
        return "DEPTH_1_SCHEMA_OR_WRAPPER_ONLY"
    if fail_or_blocked_calls == 0 and branch_count == 0:
        return "DEPTH_0_DECLARED_ONLY"
    if fail_or_blocked_calls >= 1 and branch_count >= 1:
        if fixture_ref_count or {"FAIL", "BLOCKED"} <= literals:
            return "DEPTH_3_NEGATIVE_FIXTURE_OR_STATUS_TESTED"
        if test_ref_count or validate_or_evaluate_calls >= 1:
            return "DEPTH_2_VALIDATOR_LOGIC_WITH_TEST_REFERENCE"
        return "DEPTH_2_VALIDATOR_LOGIC"
    return "DEPTH_1_SHALLOW_LOGIC"


def build_validator_depth_audit() -> dict[str, Any]:
    state_path = ROOT / "contracts" / "generated" / "current_implementation_state.json"
    registry_path = ROOT / "contracts" / "registry.yaml"
    validator_module_path = ROOT / "trader1" / "validation" / "mvp0_validators.py"
    state = load_json(state_path)
    registry = load_json(registry_path)
    implemented_ids = sorted(set(state.get("implemented_validator_ids", [])))
    registered_ids = _registry_validator_ids(registry)

    source = validator_module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}

    test_texts = [(path, path.read_text(encoding="utf-8")) for path in sorted((ROOT / "tests").rglob("*.py"))]
    fixture_texts = [
        (path, path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "tests" / "validators" / "fixtures").glob("*.json"))
    ]

    validator_reports: list[dict[str, Any]] = []
    blocking_gaps: list[dict[str, Any]] = []
    warning_gaps: list[dict[str, Any]] = []

    for validator_id in implemented_ids:
        node = functions.get(validator_id)
        risk_tags = sorted(keyword for keyword in HIGH_RISK_KEYWORDS if keyword in validator_id)
        if node is None:
            gap = {
                "validator_id": validator_id,
                "severity": "HIGH",
                "gap_type": "IMPLEMENTED_VALIDATOR_FUNCTION_MISSING",
                "risk_tags": risk_tags,
            }
            blocking_gaps.append(gap)
            validator_reports.append({"validator_id": validator_id, "depth_class": "NO_FUNCTION", "risk_tags": risk_tags})
            continue

        calls = _call_names(node)
        literals = _string_literals(node)
        fail_or_blocked_calls = calls.count("fail_result") + calls.count("blocked_result")
        branch_count = sum(isinstance(item, (ast.If, ast.For, ast.While, ast.Try, ast.BoolOp, ast.Assert)) for item in ast.walk(node))
        validate_or_evaluate_calls = sum(
            name.startswith("validate_") or name.startswith("evaluate_") or name.endswith("_errors")
            for name in calls
        )
        fixture_refs = [
            rel(path)
            for path, text in fixture_texts
            if validator_id in text or validator_id.replace("_validator", "") in path.stem
        ]
        test_refs = [rel(path) for path, text in test_texts if validator_id in text]
        line_count = int(getattr(node, "end_lineno", node.lineno) - node.lineno + 1)
        depth_class = _depth_class(
            line_count=line_count,
            fail_or_blocked_calls=fail_or_blocked_calls,
            branch_count=branch_count,
            validate_or_evaluate_calls=validate_or_evaluate_calls,
            fixture_ref_count=len(fixture_refs),
            test_ref_count=len(test_refs),
            literals=literals,
        )
        report = {
            "validator_id": validator_id,
            "depth_class": depth_class,
            "line_count": line_count,
            "branch_count": branch_count,
            "fail_or_blocked_calls": fail_or_blocked_calls,
            "validate_or_evaluate_calls": validate_or_evaluate_calls,
            "test_ref_count": len(test_refs),
            "fixture_ref_count": len(fixture_refs),
            "risk_tags": risk_tags,
            "function_location": f"{rel(validator_module_path)}:{node.lineno}",
            "test_refs": test_refs[:8],
            "fixture_refs": fixture_refs[:8],
        }
        validator_reports.append(report)
        if risk_tags and depth_class in {"DEPTH_0_DECLARED_ONLY", "DEPTH_1_SCHEMA_OR_WRAPPER_ONLY", "DEPTH_1_SHALLOW_LOGIC"}:
            blocking_gaps.append(
                {
                    "validator_id": validator_id,
                    "severity": "HIGH",
                    "gap_type": "HIGH_RISK_VALIDATOR_TOO_SHALLOW",
                    "depth_class": depth_class,
                    "risk_tags": risk_tags,
                }
            )
        elif depth_class in {"DEPTH_0_DECLARED_ONLY", "DEPTH_1_SCHEMA_OR_WRAPPER_ONLY", "DEPTH_1_SHALLOW_LOGIC"}:
            warning_gaps.append(
                {
                    "validator_id": validator_id,
                    "severity": "MEDIUM",
                    "gap_type": "VALIDATOR_DEPTH_REVIEW_RECOMMENDED",
                    "depth_class": depth_class,
                    "risk_tags": risk_tags,
                }
            )

    registered_but_unimplemented = sorted(set(registered_ids) - set(implemented_ids))
    implemented_but_unregistered = sorted(set(implemented_ids) - set(registered_ids))
    if implemented_but_unregistered:
        warning_gaps.append(
            {
                "severity": "MEDIUM",
                "gap_type": "IMPLEMENTED_VALIDATORS_NOT_IN_REGISTRY_GROUPS",
                "validator_ids": implemented_but_unregistered,
            }
        )

    depth_counts: dict[str, int] = {}
    for report in validator_reports:
        depth_counts[report["depth_class"]] = depth_counts.get(report["depth_class"], 0) + 1

    status = "PASS" if not blocking_gaps else "BLOCKED"
    return {
        "schema_id": "trader1.validator_depth_audit.v1",
        "generated_at_utc": utc_now(),
        "project_id": "TRADER_1",
        "authority": {
            "trader1_sha256": sha256_file(ROOT / "TRADER_1.md"),
            "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
        },
        "audit_status": status,
        "implemented_validator_count": len(implemented_ids),
        "registered_validator_count": len(registered_ids),
        "validator_reports": validator_reports,
        "depth_counts": depth_counts,
        "blocking_gap_count": len(blocking_gaps),
        "warning_gap_count": len(warning_gaps),
        "blocking_gaps": blocking_gaps,
        "warning_gaps": warning_gaps,
        "registered_but_unimplemented_validator_ids": registered_but_unimplemented,
        "implemented_but_unregistered_validator_ids": implemented_but_unregistered,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    audit = build_validator_depth_audit()
    if args.output is not None:
        write_json(args.output, audit)
    print(json.dumps(audit, indent=2))
    return 0 if audit["audit_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
