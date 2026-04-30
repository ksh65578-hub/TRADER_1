# MVP4 Upbit Public REST Read-only Transform Audit

created_at_utc: 2026-04-30T11:39:52Z
patch_id: MVP4_UPBIT_PUBLIC_REST_READ_ONLY_TRANSFORM_20260430_001

Findings:
- Hidden issue: public collector could only use internal fixtures, so actual Upbit public candle payload shape was not contract-tested.
- Hidden issue: public data validation did not explicitly reject authorization header markers or private/order endpoint markers.
- Hidden issue: duplicate candle timestamps were not blocked at public candle validation time.

Patch:
- Added Upbit public REST read-only candle payload transform for api.upbit.com/v1/candles/minutes/1 shaped data.
- Added fail-closed validation for endpoint identity, authorization header use, private endpoint markers, order endpoint markers, and duplicate timestamps.
- Added tests for safe public REST-shaped payloads, authorization header blocking, and duplicate timestamp reconciliation.
- Re-ran bounded UPBIT/KRW_SPOT/PAPER runtime from PUBLIC_REST_READ_ONLY-shaped inputs.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
