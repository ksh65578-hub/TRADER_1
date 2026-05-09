from trader1.runtime.boot.safe_launcher import root_stop_launcher_main

LAUNCHER_NAME = "STOP_BINANCE_PAPER"
MARKET_TYPE = "SPOT"
MARKET_TYPE_OPTIONS = ("SPOT", "FUTURES_USDT_M")
FUTURES_USDT_M_STATUS = "BLOCKED_NOT_IMPLEMENTED"
MODE = "PAPER"

if __name__ == "__main__":
    raise SystemExit(root_stop_launcher_main(LAUNCHER_NAME))
