# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from typing import Dict, List
from functools import reduce
from pandas import DataFrame, Series, DatetimeIndex, merge
# --------------------------------
import talib.abstract as ta
import pandas_ta as pta
import numpy as np
import pandas as pd  # noqa
import warnings, datetime
import freqtrade.vendor.qtpylib.indicators as qtpylib
from technical.util import resample_to_interval, resampled_merge
from datetime import datetime, timedelta
from freqtrade.persistence import Trade, Order
from freqtrade.strategy import stoploss_from_open, DecimalParameter, IntParameter, CategoricalParameter
import technical.indicators as ftt
from functools import reduce

pd.options.mode.chained_assignment = None  # default='warn'

# @Rallipanos # changes by Mastaaa1987

# Buy hyperspace params:
buy_params = {
        "base_nb_candles_buy": 12,
    }

# Sell hyperspace params:
sell_params = {
        "base_nb_candles_sell": 22,
        "high_offset": 1.008,
        "high_offset_2": 1.016,
    }

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


class KamaFama(IStrategy):
    INTERFACE_VERSION = 2
    """
    # ROI table:
    minimal_roi = {
        "0": 0.08,
        "20": 0.04,
        "40": 0.032,
        "87": 0.016,
        "201": 0,
        "202": -1
    }
    """
    @property
    def protections(self):
        return [
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 60,
                "trade_limit": 1,
                "stop_duration_candles": 60,
                "required_profit": -0.05
            },
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": 5
            }
        ]

    minimal_roi = {
        "0": 1
    }

    # Stoploss:
    stoploss = -0.25

    # Buy Params
    base_nb_candles_buy = IntParameter(5, 80, default=buy_params['base_nb_candles_buy'], space='buy', optimize=True)
    #low_offset = DecimalParameter(0.9, 0.99, default=buy_params['low_offset'], space='buy', optimize=True)
    # Sell Params
    base_nb_candles_sell = IntParameter(5, 80, default=sell_params['base_nb_candles_sell'], space='sell', optimize=True)
    high_offset = DecimalParameter(0.95, 1.1, default=sell_params['high_offset'], space='sell', optimize=True)
    high_offset_2 = DecimalParameter(0.99, 1.5, default=sell_params['high_offset_2'], space='sell', optimize=True)

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = True

    use_custom_stoploss = True

    order_types = {
        'entry': 'limit',
        'exit': 'limit',
        'emergency_exit': 'market',
        'force_entry': 'market',
        'force_exit': "market",
        'stoploss': 'market',
        'stoploss_on_exchange': False,
        'stoploss_on_exchange_interval': 60,
        'stoploss_on_exchange_market_ratio': 0.99
    }

    ## Optional order time in force.
    order_time_in_force = {
        'entry': 'gtc',
        'exit': 'gtc'
    }

    # Optimal timeframe for the strategy
    timeframe = '5m'

    process_only_new_candles = True
    startup_candle_count = 400

    plot_config = {
        'main_plot': {
            'ma_buy': {'color': '#27d81b'},
            'ma_sell': {'color': '#d0da3e'},
            'hma_50': {'color': '#3edad8'}
        },
        "subplots": {
            "FKMAMA": {
                "mama": {'color': '#d0da3e'},
                "fama": {'color': '#da3eb8'},
                "kama": {'color': '#3edad8'}
            },
            "cond": {
                "change": {'color': '#da3e3e'}
            }
        }
    }

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:

        if current_profit >= 0.05:
            return -0.002

        return None

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # PCT CHANGE
        dataframe['change'] = 100 / dataframe['open'] * dataframe['close'] - 100

        # Calculate all ma_buy values
        for val in self.base_nb_candles_buy.range:
            dataframe['ma_buy'] = ta.EMA(dataframe, timeperiod=val)

        # Calculate all ma_sell values
        for val in self.base_nb_candles_sell.range:
            dataframe['ma_sell'] = ta.EMA(dataframe, timeperiod=val)

        # HMA
        dataframe['hma_50'] = qtpylib.hull_moving_average(dataframe['close'], window=50)

        # MAMA, FAMA, KAMA
        dataframe['hl2'] = (dataframe['high'] + dataframe['low']) / 2
        dataframe['mama'], dataframe['fama'] = ta.MAMA(dataframe['hl2'], 0.25, 0.025)
        dataframe['mama_diff'] = ( ( dataframe['mama'] - dataframe['fama'] ) / dataframe['hl2'] )
        dataframe['kama'] = ta.KAMA(dataframe['close'], 84)

        # CTI
        dataframe['cti'] = pta.cti(dataframe["close"], length=20)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_fast'] = ta.RSI(dataframe, timeperiod=4)
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=20)
        dataframe['rsi_84'] = ta.RSI(dataframe, timeperiod=84)
        dataframe['rsi_112'] = ta.RSI(dataframe, timeperiod=112)

        # Williams %R
        dataframe['r_14'] = williams_r(dataframe, period=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, 'enter_tag'] = ''

        buy = (
                (dataframe['kama'] > dataframe['fama']) &
                (dataframe['fama'] > dataframe['mama'] * 0.981) &
                (dataframe['r_14'] < -61.3) &
                (dataframe['mama_diff'] < -0.025) &
                (dataframe['cti'] < -0.715) &
                (dataframe['close'].rolling(48).max() >= dataframe['close'] * 1.05) &
                (dataframe['close'].rolling(288).max() >= dataframe['close'] * 1.125) &
                (dataframe['rsi_84'] < 60) &
                (dataframe['rsi_112'] < 60)
        )
        conditions.append(buy)
        dataframe.loc[buy, 'enter_tag'] += 'buy'

        if conditions:
            dataframe.loc[reduce(lambda x, y: x | y, conditions), 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, 'exit_tag'] = ''

        sell = (
            (
                (dataframe['close'] > dataframe['hma_50']) &
                (dataframe['close'] > (dataframe['ma_sell'] * self.high_offset_2.value)) &
                (dataframe['rsi'] > 50) &
                (dataframe['volume'] > 0) &
                (dataframe['rsi_fast'] > dataframe['rsi_slow'])
            ) | (
                (dataframe['close'] < dataframe['hma_50']) &
                (dataframe['close'] > (dataframe['ma_sell'] * self.high_offset.value)) &
                (dataframe['volume'] > 0) &
                (dataframe['rsi_fast'] > dataframe['rsi_slow'])
            )
        )
        conditions.append(sell)
        dataframe.loc[sell, 'exit_tag'] += 'sell'

        if conditions:
            dataframe.loc[reduce(lambda x, y: x | y, conditions), 'exit_long'] = 1

        return dataframe

