from trader1.runtime.boot.safe_launcher import root_stop_launcher_main

LAUNCHER_NAME = "STOP_UPBIT_LIVE"
MARKET_TYPE = "KRW_SPOT"
MODE = "LIVE"

if __name__ == "__main__":
    raise SystemExit(root_stop_launcher_main(LAUNCHER_NAME))
