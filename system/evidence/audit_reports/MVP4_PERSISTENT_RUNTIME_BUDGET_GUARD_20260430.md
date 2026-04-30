# MVP4 Persistent Runtime Budget Guard Audit

created_at_utc: 2026-04-30T07:06:14Z
patch_id: MVP4_PERSISTENT_RUNTIME_BUDGET_GUARD_20260430_001

Finding:
- The persistent SHADOW runtime builder blocked heartbeat intervals above max runtime, but validator and dashboard projection did not independently re-check that cross-field budget relation.
- A tampered report with a valid hash could keep estimated runtime above its own max runtime budget and still look like a normal stub in some paths.

Patch:
- Validator now blocks heartbeat interval above max runtime budget.
- Validator now blocks estimated runtime above max runtime budget.
- Dashboard projection shows that drift as BLOCKED/ERROR with RESOURCE_LIMIT_BLOCK.
- Negative tests cover both report validation and dashboard projection.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
