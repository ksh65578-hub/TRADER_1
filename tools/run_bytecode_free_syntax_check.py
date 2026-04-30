from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.validation.bytecode_free_syntax import build_bytecode_free_syntax_report
from tools.emit_root_launcher_operator_visibility_patch_evidence import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a bytecode-free syntax check without writing __pycache__ files.")
    parser.add_argument("--root", default=str(ROOT), help="Repository root to scan.")
    parser.add_argument("--paths", nargs="*", default=["trader1", "tools", "tests"], help="Relative paths to scan.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    report = build_bytecode_free_syntax_report(root=Path(args.root), scan_paths=args.paths)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        write_json(Path(args.output), report)
    print(text)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
