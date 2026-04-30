from trader1.runtime.boot.safe_launcher import launcher_main


LAUNCHER_NAME = "UPBIT_PAPER"
MARKET_TYPE = "KRW_SPOT"
MODE = "PAPER"


if __name__ == "__main__":
    raise SystemExit(launcher_main(LAUNCHER_NAME))

