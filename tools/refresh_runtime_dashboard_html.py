from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.dashboard.read_only_dashboard import render_dashboard_html, validate_dashboard_visual_layout_contract
from tools.emit_root_launcher_operator_visibility_patch_evidence import write_text


def main() -> int:
    refreshed: list[str] = []
    failures: list[dict[str, str]] = []
    for shell_path in sorted((ROOT / "system" / "runtime").glob("**/dashboard_shell.json")):
        shell = json.loads(shell_path.read_text(encoding="utf-8"))
        html = render_dashboard_html(shell)
        result = validate_dashboard_visual_layout_contract(html)
        if result.status != "PASS":
            failures.append({"path": shell_path.relative_to(ROOT).as_posix(), "message": result.message})
            continue
        html_path = shell_path.parent / "dashboard" / "index.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(html_path, html)
        refreshed.append(html_path.relative_to(ROOT).as_posix())
    report = {
        "status": "PASS" if not failures else "FAIL",
        "refreshed_dashboard_count": len(refreshed),
        "refreshed_dashboard_paths": refreshed,
        "failures": failures,
        "live_order_ready": False,
        "live_order_allowed": False,
        "can_live_trade": False,
        "scale_up_allowed": False,
    }
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
