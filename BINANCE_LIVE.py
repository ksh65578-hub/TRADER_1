from trader1.runtime.boot.safe_launcher import launcher_main


LAUNCHER_NAME = "BINANCE_LIVE"
MARKET_TYPE = "SPOT"
MODE = "LIVE"


if __name__ == "__main__":
    raise SystemExit(launcher_main(LAUNCHER_NAME))

