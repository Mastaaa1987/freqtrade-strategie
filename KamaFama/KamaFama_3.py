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

def williams_r(dataframe: DataFrame, period: int = 14) -> Series:
    highest_high = dataframe["high"].rolling(center=False, window=period).max()
    lowest_low = dataframe["low"].rolling(center=False, window=period).min()

    WR = Series(
        (highest_high - dataframe["close"]) / (highest_high - lowest_low),
        name=f"{period} Williams %R",
        )

    return WR * -100

# ------- Strategie by Mastaaa1987

class KamaFama_3(IStrategy):
    INTERFACE_VERSION = 2

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

    buy_params = {
        "buy_cti": -0.56,
        "buy_mama_diff": 0.01,
        "buy_r_14": -80.201,
        "buy_rsi_112": 99,
        "buy_rsi_84": 90,
    }
    sell_params = {
        "sell_fastx": 84,  # value loaded from strategy
    }

    minimal_roi = {
        "0": 1
    }
    # minimal_roi = {
    #     "0": 0.1,
    #     "60": 0.05,
    #     "120": 0.03,
    #     "180": 0.01
    # }
    cc = {}

    # Stoploss:
    stoploss = -0.25

    # Buy Params
    buy_r_14 = DecimalParameter(-100, 0, default=buy_params['buy_r_14'], space='buy', optimize=True)
    buy_mama_diff = DecimalParameter(0.01, 0.1, default=buy_params['buy_mama_diff'], decimals=2, space='buy', optimize=True)
    buy_cti = DecimalParameter(-1, 1, default=buy_params['buy_cti'], decimals=2, space='buy', optimize=True)
    buy_rsi_84 = IntParameter(0, 100, default=buy_params['buy_rsi_84'], space='buy', optimize=True)
    buy_rsi_112 = IntParameter(0, 100, default=buy_params['buy_rsi_112'], space='buy', optimize=True)

    # Sell Params
    sell_fastx = IntParameter(50, 100, default=sell_params['sell_fastx'], space='sell', optimize=True)

    # Trailing stop:
    trailing_stop = False
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = True

    use_custom_stoploss = True

    order_types = {
        'entry': 'market',
        'exit': 'market',
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
    startup_candle_count = 50

    plot_config = {
        'main_plot': {
            "mama": {'color': '#d0da3e'},
            "fama": {'color': '#da3eb8'},
            "kama": {'color': '#3edad8'}
        },
        "subplots": {
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

        # MAMA, FAMA, KAMA
        dataframe['hl2'] = (dataframe['high'] + dataframe['low']) / 2
        dataframe['mama'], dataframe['fama'] = ta.MAMA(dataframe['hl2'], 0.25, 0.025)
        dataframe['mama_diff'] = ( ( dataframe['mama'] - dataframe['fama'] ) / dataframe['hl2'] )
        dataframe['kama'] = ta.KAMA(dataframe['close'], 84)

        # CTI
        dataframe['cti'] = pta.cti(dataframe["close"], length=20)

        # profit sell indicators
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastk'] = stoch_fast['fastk']

        # RSI
        dataframe['rsi_84'] = ta.RSI(dataframe, timeperiod=84)
        dataframe['rsi_112'] = ta.RSI(dataframe, timeperiod=112)

        # Williams %R
        dataframe['r_14'] = williams_r(dataframe, period=14)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, 'enter_tag'] = ''

        buy = (
                (dataframe['mama'] > dataframe['kama']) &
                (dataframe['kama'] > dataframe['fama']) &
                (dataframe['r_14'] > self.buy_r_14.value) &
                (dataframe['mama_diff'] > self.buy_mama_diff.value) &
                (dataframe['cti'] > self.buy_cti.value) &
                (dataframe['rsi_84'] < self.buy_rsi_84.value) &
                (dataframe['rsi_112'] < self.buy_rsi_112.value)
        )
        conditions.append(buy)
        dataframe.loc[buy, 'enter_tag'] += 'buy'

        if conditions:
            dataframe.loc[reduce(lambda x, y: x | y, conditions), 'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        dataframe.loc[:, 'exit_long'] = 0

        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        current_candle = dataframe.iloc[-1].squeeze()

        min_profit = trade.calc_profit_ratio(trade.min_rate)

        if self.config['runmode'].value in ('live', 'dry_run'):
            state = self.cc
            pc = state.get(trade.id, {'date': current_candle['date'], 'open': current_candle['close'], 'high': current_candle['close'], 'low': current_candle['close'], 'close': current_rate, 'volume': 0})
            if current_candle['date'] != pc['date']:
                pc['date'] = current_candle['date']
                pc['high'] = current_candle['close']
                pc['low'] = current_candle['close']
                pc['open'] = current_candle['close']
                pc['close'] = current_rate
            if current_rate > pc['high']:
                pc['high'] = current_rate
            if current_rate < pc['low']:
                pc['low'] = current_rate
            if current_rate != pc['close']:
                pc['close'] = current_rate

            state[trade.id] = pc

        if current_profit > 0:
            # if min_profit <= -0.015:
            if self.config['runmode'].value in ('live', 'dry_run'):
                if current_time > pc['date'] + timedelta(minutes=9) + timedelta(seconds=55):
                    df = dataframe.copy()
                    df = df._append(pc, ignore_index = True)
                    stoch_fast = ta.STOCHF(df, 5, 3, 0, 3, 0)
                    df['fastk'] = stoch_fast['fastk']
                    cc = df.iloc[-1].squeeze()
                    if cc["fastk"] > self.sell_fastx.value:
                        return "fastk_profit_sell_2"
            else:
                if current_candle["fastk"] > self.sell_fastx.value:
                    return "fastk_profit_sell"

        return None
