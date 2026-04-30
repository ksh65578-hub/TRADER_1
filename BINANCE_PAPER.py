from trader1.runtime.boot.safe_launcher import launcher_main


LAUNCHER_NAME = "BINANCE_PAPER"
MARKET_TYPE = "SPOT"
MARKET_TYPE_OPTIONS = ("SPOT", "FUTURES_USDT_M")
FUTURES_USDT_M_STATUS = "BLOCKED_NOT_IMPLEMENTED"
MODE = "PAPER"


if __name__ == "__main__":
    raise SystemExit(launcher_main(LAUNCHER_NAME))
