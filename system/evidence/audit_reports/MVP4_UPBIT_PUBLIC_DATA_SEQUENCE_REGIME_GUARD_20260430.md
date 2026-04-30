# MVP4 Upbit Public Data Sequence Regime Guard Audit

created_at_utc: 2026-04-30T11:46:36Z
patch_id: MVP4_UPBIT_PUBLIC_DATA_SEQUENCE_REGIME_GUARD_20260430_001

Findings:
- Hidden issue: public REST-shaped candles could pass even when canonicalized timestamps were not strictly increasing.
- Hidden issue: runtime tests did not explicitly prove downtrend/risk-off data no-trades without writing fill ledger events.

Patch:
- Public candle validation now requires strictly increasing timestamps and blocks out-of-order samples.
- Added tests for out-of-order timestamp reconciliation.
- Added risk-off/downtrend PAPER runtime no-trade test.
- Re-ran bounded PAPER loop with public REST-shaped input followed by downtrend fixture input.

Live state: live_order_ready=false, live_order_allowed=false, can_live_trade=false, scale_up_allowed=false.
