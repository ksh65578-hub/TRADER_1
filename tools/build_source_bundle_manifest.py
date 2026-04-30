from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader1.security.source_bundle import write_source_bundle_manifest


def main() -> int:
    manifest = write_source_bundle_manifest()
    print(
        json.dumps(
            {
                "status": "PASS" if not manifest["contains_secret"] and manifest["forbidden_count"] == 0 else "FAIL",
                "included_count": len(manifest["included_files"]),
                "excluded_count": len(manifest["excluded_files"]),
                "forbidden_count": manifest["forbidden_count"],
                "contains_secret": manifest["contains_secret"],
                "live_order_allowed": False,
            },
            indent=2,
        )
    )
    return 0 if not manifest["contains_secret"] and manifest["forbidden_count"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
