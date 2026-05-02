from trader1.runtime.boot.safe_launcher import root_operator_launcher_main


LAUNCHER_NAME = "BINANCE_LIVE"
MARKET_TYPE = "SPOT"
MARKET_TYPE_OPTIONS = ("SPOT", "FUTURES_USDT_M")
FUTURES_USDT_M_STATUS = "BLOCKED_NOT_IMPLEMENTED"
MODE = "LIVE"


if __name__ == "__main__":
    raise SystemExit(root_operator_launcher_main(LAUNCHER_NAME))
