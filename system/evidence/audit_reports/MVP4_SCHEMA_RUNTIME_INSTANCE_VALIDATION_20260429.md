# MVP4 Schema Runtime Instance Validation Audit

created_at_utc: 2026-04-29T00:07:59Z
patch_id: MVP4_SCHEMA_RUNTIME_INSTANCE_VALIDATION_20260429_001

Findings:
- Runtime JSON instances were checked by specialized validators, but not by a shared schema-instance validator.
- Several schemas referenced common.defs.schema.json#/$defs/final_decision, but common defs did not expose that definition.
- Schema/runtime mismatch risk existed for required fields, enum drift, array cardinality, and additionalProperties.

Patch:
- Added a dependency-free schema-instance validator for the MVP JSON Schema subset used by runtime artifacts.
- Added runtime_schema_instance_validator over generated launcher/startup/heartbeat/summary/dashboard/paper portfolio instances and current PAPER runtime artifacts.
- Added negative tests for extra properties and dashboard stability metric count mismatch.
- Added final_decision to common defs to resolve existing schema references.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
