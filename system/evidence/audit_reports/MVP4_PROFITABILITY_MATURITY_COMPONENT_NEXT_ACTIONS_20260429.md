# MVP4 Profitability Maturity Component Next Actions

created_at_utc: 2026-04-29T08:07:04Z
patch_id: MVP4_PROFITABILITY_MATURITY_COMPONENT_NEXT_ACTIONS_20260429_001

Hidden defect:
- Strategy Evidence Maturity showed component status and messages, but each component did not have a schema-required next evidence action.
- A user could see a gap but not know which safe evidence artifact to collect next.

Patch:
- Added next_required_evidence to every profitability maturity component.
- Rendered the next action in the dashboard component card.
- Added schema and validator checks so missing next evidence fails closed.
- Added a negative dashboard test for empty next_required_evidence.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
