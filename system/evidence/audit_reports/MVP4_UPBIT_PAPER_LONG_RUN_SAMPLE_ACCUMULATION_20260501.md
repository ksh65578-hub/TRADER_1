# MVP4 Upbit PAPER Long-Run Sample Accumulation Audit

created_at_utc: 2026-04-30T23:45:21Z
patch_id: MVP4_UPBIT_PAPER_LONG_RUN_SAMPLE_ACCUMULATION_20260501_001

Finding:
- Aggregated PAPER/SHADOW evidence carried evidence_span_hours but did not expose the span provenance or the paired supporting-window count as first-class, hash-covered fields.
- Operation-report accumulation defaulted missing span to 0, which was fail-closed, but operator and validator evidence did not clearly distinguish explicit span input from missing span provenance.

Patch:
- Added evidence_span_source and evidence_span_source_status to the paper/shadow evidence schema and report builder.
- Added supporting_source_window_count and validator drift checks.
- Marked operation-report aggregation without explicit evidence_span_hours as NOT_PROVIDED/MISSING.
- Added regression coverage and refreshed fixtures.

Safety:
- live_order_ready=false
- live_order_allowed=false
- can_live_trade=false
- scale_up_allowed=false
- no credentialed exchange/account/API calls
- no live order path enabled
