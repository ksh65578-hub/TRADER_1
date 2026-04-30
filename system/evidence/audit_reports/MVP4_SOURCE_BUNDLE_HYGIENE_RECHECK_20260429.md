# MVP4 Source Bundle Hygiene Recheck

created_at_utc: 2026-04-29T08:46:41Z
patch_id: MVP4_SOURCE_BUNDLE_HYGIENE_RECHECK_20260429_001

Findings:
- The source bundle candidate previously included contracts/security/source_bundle_manifest.json, making the manifest self-referential and immediately stale after write.
- The candidate also included contracts/generated/ read-cache/state artifacts, which are generated navigation/runtime state rather than source authority.

Patch:
- Denied contracts/generated/.
- Denied contracts/security/source_bundle_manifest.json.
- Added negative tests proving generated state and the manifest itself are excluded.

Audit:
- included_count: 530
- excluded_count: 968
- forbidden_generated_count: 0
- self_referential_manifest_included: False
- contains_secret: False

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no exchange credential use
- no live order path enabled
