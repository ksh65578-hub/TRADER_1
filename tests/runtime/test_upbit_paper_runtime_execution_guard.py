from decimal import Decimal

from trader1.runtime.paper.upbit_paper_runtime import (
    _simulate_paper_broker_execution,
)


def test_buy_partial_fill_below_min_notional_is_rejected_without_live_flags():
    execution = _simulate_paper_broker_execution(
        cycle_id="paper-min-fill-reject",
        symbol="KRW-TEST",
        side="BUY",
        requested_notional=Decimal("5000"),
        requested_quantity=Decimal("5"),
        mark_price=Decimal("1000"),
        features={
            "last_price": "1000",
            "spread_bps": "1",
            "volatility_pct": "0.10",
            "total_quote_volume": "50000000",
            "volume_expansion_ratio": "1.00",
            "liquidity_status": "PASS",
        },
        fee_rate=Decimal("0.0005"),
    )

    assert execution["order_lifecycle_state"] == "REJECTED"
    assert execution["reject_reason"] == "PAPER_MIN_FILL_NOTIONAL_REJECT"
    assert execution["filled_notional"] == "0"
    assert execution["filled_quantity"] == "0"
    assert execution["fill_ratio"] == "0"
    assert execution["reservation_released"] is True
    assert execution["live_order_ready"] is False
    assert execution["live_order_allowed"] is False
    assert execution["can_live_trade"] is False
    assert execution["scale_up_allowed"] is False
    assert execution["order_adapter_called"] is False
    assert execution["private_endpoint_called"] is False
    assert execution["credential_load_attempted"] is False


def test_sell_risk_reducing_fill_below_min_notional_remains_allowed():
    execution = _simulate_paper_broker_execution(
        cycle_id="paper-small-exit-allowed",
        symbol="KRW-TEST",
        side="SELL",
        requested_notional=Decimal("4000"),
        requested_quantity=Decimal("4"),
        mark_price=Decimal("1000"),
        features={
            "last_price": "1000",
            "spread_bps": "1",
            "volatility_pct": "0.10",
            "total_quote_volume": "50000000",
            "volume_expansion_ratio": "1.00",
            "liquidity_status": "PASS",
        },
        fee_rate=Decimal("0.0005"),
    )

    assert execution["order_lifecycle_state"] in {"FILLED", "PARTIALLY_FILLED"}
    assert Decimal(execution["filled_notional"]) > Decimal("0")
    assert execution["reject_reason"] is None
    assert execution["live_order_allowed"] is False
    assert execution["order_adapter_called"] is False
    assert execution["private_endpoint_called"] is False
    assert execution["credential_load_attempted"] is False
