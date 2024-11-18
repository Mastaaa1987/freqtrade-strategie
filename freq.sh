#!/bin/bash

if [ "$1" == "" ]; then
	echo "source .venv/bin/activate";
	echo "freqtrade download-data -c user_data/configs/backtesting_config.json -t 1h --timerange=20240101-";
	echo "freqtrade backtesting -c user_data/configs/backtesting_config.json -s ScalpingB --timerange=20240109-";
	echo "freqtrade plot-profit -c user_data/configs/backtesting_config.json -s ScalpingB --timerange=20240109-";
	echo "freqtrade plot-dataframe -c user_data/configs/backtesting_config.json -s ScalpingB --timerange=20240109- -p DATA/USDT"
	echo "freqtrade trade -c user_data/configs/trade_config.json -s Scalping";
fi;
