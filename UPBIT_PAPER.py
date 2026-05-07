from trader1.runtime.paper.upbit_paper_long_runner import root_upbit_paper_long_runner_main


LAUNCHER_NAME = "UPBIT_PAPER"
MARKET_TYPE = "KRW_SPOT"
MODE = "PAPER"


if __name__ == "__main__":
    raise SystemExit(root_upbit_paper_long_runner_main())
