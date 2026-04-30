from trader1.runtime.boot.safe_launcher import launcher_main


LAUNCHER_NAME = "BINANCE_PAPER"
MARKET_TYPE = "SPOT"
MODE = "PAPER"


if __name__ == "__main__":
    raise SystemExit(launcher_main(LAUNCHER_NAME))

