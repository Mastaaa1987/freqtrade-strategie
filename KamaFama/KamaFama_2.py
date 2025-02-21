# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame, Series

# --------------------------------
import talib.abstract as ta
import pandas_ta as pta
import pandas as pd  # noqa
import datetime
from datetime import datetime, timedelta
from freqtrade.persistence import Trade
from freqtrade.strategy import (
    DecimalParameter,
    IntParameter,
)

pd.options.mode.chained_assignment = None  # default='warn'

import logging

logger = logging.getLogger(__name__)

# ------- Strategie by Mastaaa1987
# ------- Updated and Hyperoped by Alfirin

def williams_r(dataframe: DataFrame, period: int = 14) -> Series:
    """Williams %R, or just %R, is a technical analysis oscillator showing the current closing price in relation to the high and low
    of the past N days (for a given N). It was developed by a publisher and promoter of trading materials, Larry Williams.
    Its purpose is to tell whether a stock or commodity market is trading near the high or the low, or somewhere in between,
    of its recent trading range.
    The oscillator is on a negative scale, from −100 (lowest) up to 0 (highest).
    """

    highest_high = dataframe["high"].rolling(center=False, window=period).max()
    lowest_low = dataframe["low"].rolling(center=False, window=period).min()

    WR = Series(
        (highest_high - dataframe["close"]) / (highest_high - lowest_low),
        name=f"{period} Williams %R",
    )

    return WR * -100


class KamaFama_2(IStrategy):
    INTERFACE_VERSION = 2

    @property
    def protections(self):
        return [
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 60,
                "trade_limit": 1,
                "stop_duration_candles": 60,
                "required_profit": -0.05,
            },
            {"method": "CooldownPeriod", "stop_duration_candles": 5},
        ]

    minimal_roi = {"0": 1}
    cc = {}

    # Stoploss:
    stoploss = -0.1

    # Sell Params
    sell_fastx = IntParameter(50, 100, default=84, space="sell", optimize=True)

    mama_percent_buy = DecimalParameter(
        0.8, 1, default=0.981, decimals=3, space="buy", optimize=True
    )
    r_14_buy = DecimalParameter(
        -100, -30, default=-61.3, decimals=1, space="buy", optimize=True
    )
    mama_diff_buy = DecimalParameter(
        -0.1, 0, default=-0.025, decimals=3, space="buy", optimize=True
    )
    cti_buy = DecimalParameter(
        -1, -0.5, default=-0.715, decimals=3, space="buy", optimize=True
    )
    close_48_buy = DecimalParameter(
        1, 1.2, default=1.05, decimals=2, space="buy", optimize=True
    )
    close_288_buy = DecimalParameter(
        1, 1.25, default=1.125, decimals=3, space="buy", optimize=True
    )
    rsi_84_buy = IntParameter(50, 100, default=60, space="buy", optimize=True)
    rsi_112_buy = IntParameter(50, 100, default=60, space="buy", optimize=True)

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = True

    use_custom_stoploss = True

    order_types = {
        "entry": "market",
        "exit": "market",
        "emergency_exit": "market",
        "force_entry": "market",
        "force_exit": "market",
        "stoploss": "market",
        "stoploss_on_exchange": False,
        "stoploss_on_exchange_interval": 60,
        "stoploss_on_exchange_market_ratio": 0.99,
    }

    ## Optional order time in force.
    order_time_in_force = {"entry": "gtc", "exit": "gtc"}

    # Optimal timeframe for the strategy
    timeframe = "5m"

    process_only_new_candles = True
    startup_candle_count = 999

    plot_config = {
        "main_plot": {
            "mama": {"color": "#d0da3e"},
            "fama": {"color": "#da3eb8"},
            "kama": {"color": "#3edad8"},
        },
        "subplots": {
            "fastk": {"fastk": {"color": "#da3e3e"}},
            "cond": {"change": {"color": "#da3e3e"}},
        },
    }

    def custom_stoploss(
        self,
        pair: str,
        trade: Trade,
        current_time: datetime,
        current_rate: float,
        current_profit: float,
        **kwargs,
    ) -> float:
        if current_profit >= 0.05:
            return -0.002

        return self.stoploss

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # PCT CHANGE
        dataframe["change"] = 100 / dataframe["open"] * dataframe["close"] - 100

        # MAMA, FAMA, KAMA
        dataframe["hl2"] = (dataframe["high"] + dataframe["low"]) / 2
        dataframe["mama"], dataframe["fama"] = ta.MAMA(dataframe["hl2"], 0.25, 0.025)
        dataframe["mama_diff"] = (dataframe["mama"] - dataframe["fama"]) / dataframe[
            "hl2"
        ]
        dataframe["kama"] = ta.KAMA(dataframe["close"], 84)

        # CTI
        dataframe["cti"] = pta.cti(dataframe["close"], length=20)

        # profit sell indicators
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe["fastk"] = stoch_fast["fastk"]

        # RSI
        dataframe["rsi_84"] = ta.RSI(dataframe, timeperiod=84)
        dataframe["rsi_112"] = ta.RSI(dataframe, timeperiod=112)

        # Williams %R
        dataframe["r_14"] = williams_r(dataframe, period=14)

        for days in [2, 3, 4]:
            # Convert days to candles (assuming 5m timeframe)
            lookback_periods = (
                days * 24 * 12
            )  # days * hours * 12 5-minute candles per hour

            # Get the high price for the specific period only
            period_high = (
                dataframe["high"].rolling(window=lookback_periods, min_periods=1).max()
            )
            prev_period_high = (
                dataframe["high"]
                .rolling(window=lookback_periods - (24 * 12), min_periods=1)
                .max()
            )
            dataframe[f"high_{days}d"] = period_high.where(
                period_high != prev_period_high, dataframe["high"]
            )

            # Get the low price for the specific period only
            period_low = (
                dataframe["low"].rolling(window=lookback_periods, min_periods=1).min()
            )
            prev_period_low = (
                dataframe["low"]
                .rolling(window=lookback_periods - (24 * 12), min_periods=1)
                .min()
            )
            dataframe[f"low_{days}d"] = period_low.where(
                period_low != prev_period_low, dataframe["low"]
            )

            # Calculate the price change from highest point (as percentage) for this specific period
            dataframe[f"price_change_{days}d"] = (
                (dataframe["close"] - dataframe[f"high_{days}d"])
                / dataframe[f"high_{days}d"]
                * 100
            ).fillna(0)

            # Calculate price volatility (high-low range as percentage) for this specific period
            dataframe[f"volatility_{days}d"] = (
                (dataframe[f"high_{days}d"] - dataframe[f"low_{days}d"])
                / dataframe[f"low_{days}d"]
                * 100
            ).fillna(0)

            # Optional: Add a smoothing factor to reduce noise
            dataframe[f"volatility_{days}d"] = (
                dataframe[f"volatility_{days}d"].rolling(window=6).mean()
            )

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, "enter_tag"] = ""

        # Original buy conditions
        buy = (
            (dataframe["kama"] > dataframe["fama"])
            & (dataframe["fama"] > dataframe["mama"] * self.mama_percent_buy.value)
            & (dataframe["r_14"] < self.r_14_buy.value)
            & (dataframe["mama_diff"] < self.mama_diff_buy.value)
            & (dataframe["cti"] < self.cti_buy.value)
            & (
                dataframe["close"].rolling(48).max()
                >= dataframe["close"] * self.close_48_buy.value
            )
            & (
                dataframe["close"].rolling(288).max()
                >= dataframe["close"] * self.close_288_buy.value
            )
            & (dataframe["rsi_84"] < self.rsi_84_buy.value)
            & (dataframe["rsi_112"] < self.rsi_112_buy.value)
        )

        conditions.append(buy)
        dataframe.loc[buy, "enter_tag"] += "buy"

        if conditions:
            dataframe.loc[reduce(lambda x, y: x | y, conditions), "enter_long"] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, "exit_long"] = 0

        return dataframe

    def custom_exit(
        self,
        pair: str,
        trade: "Trade",
        current_time: "datetime",
        current_rate: float,
        current_profit: float,
        **kwargs,
    ):
        dataframe, _ = self.dp.get_analyzed_dataframe(
            pair=pair, timeframe=self.timeframe
        )
        current_candle = dataframe.iloc[-1].squeeze()

        # min_profit = trade.calc_profit_ratio(trade.min_rate)

        if self.config["runmode"].value in ("live", "dry_run"):
            state = self.cc
            pc = state.get(
                trade.id,
                {
                    "date": current_candle["date"],
                    "open": current_candle["close"],
                    "high": current_candle["close"],
                    "low": current_candle["close"],
                    "close": current_rate,
                    "volume": 0,
                },
            )
            if current_candle["date"] != pc["date"]:
                pc["date"] = current_candle["date"]
                pc["high"] = current_candle["close"]
                pc["low"] = current_candle["close"]
                pc["open"] = current_candle["close"]
                pc["close"] = current_rate
            if current_rate > pc["high"]:
                pc["high"] = current_rate
            if current_rate < pc["low"]:
                pc["low"] = current_rate
            if current_rate != pc["close"]:
                pc["close"] = current_rate

            state[trade.id] = pc

        if current_profit > 0:
            # if min_profit <= -0.015:
            if self.config["runmode"].value in ("live", "dry_run"):
                if current_time > pc["date"] + timedelta(minutes=9) + timedelta(
                    seconds=55
                ):
                    df = dataframe.copy()
                    df = df._append(pc, ignore_index=True)
                    stoch_fast = ta.STOCHF(df, 5, 3, 0, 3, 0)
                    df["fastk"] = stoch_fast["fastk"]
                    cc = df.iloc[-1].squeeze()
                    if cc["fastk"] > self.sell_fastx.value:
                        return "fastk_profit_sell_2"
            else:
                if current_candle["fastk"] > self.sell_fastx.value:
                    return "fastk_profit_sell"

        return None
