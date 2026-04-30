# MVP4 Source Package Hygiene Cache Directory Guard

created_at_utc: 2026-04-30T15:24:21Z
patch_id: MVP4_SOURCE_PACKAGE_HYGIENE_CACHE_DIR_GUARD_20260501_001

Finding:
- The shipped package hygiene check caught .pyc files, but nested cache directories needed explicit negative coverage for non-.pyc marker files such as CACHEDIR.TAG.

Patch:
- Added nested cache directory deny patterns for source and shipped package classification.
- Added negative tests for nested __pycache__, .pytest_cache, .mypy_cache, and .ruff_cache paths.
- Regenerated source_bundle_manifest with live flags false.

Audit:
- current_pycache_dir_count: 0
- current_pyc_file_count: 0
- shipped_forbidden_count: 0
- contains_secret: False

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
