from trader1.runtime.boot.safe_launcher import root_stop_launcher_main

LAUNCHER_NAME = "STOP_TRADER_1"
MARKET_TYPE = "ALL"
MODE = "CONTROL"

if __name__ == "__main__":
    raise SystemExit(root_stop_launcher_main(LAUNCHER_NAME))
