from datetime import datetime, timedelta
import talib.abstract as ta
import pandas_ta as pta
from freqtrade.persistence import Trade, Order
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from freqtrade.strategy import DecimalParameter, IntParameter
from functools import reduce
import warnings

import freqtrade.vendor.qtpylib.indicators as qtpylib
import pandas as pd  # noqa
pd.options.mode.chained_assignment = None  # default='warn'
import technical.indicators as ftt
from freqtrade.strategy import merge_informative_pair
import numpy as np
from freqtrade.strategy import stoploss_from_open

warnings.simplefilter(action="ignore", category=RuntimeWarning)
TMP_HOLD = []
TMP_HOLD1 = []


class EV(IStrategy):
    minimal_roi = {
        "0": 1
    }
    timeframe = '5m'
    process_only_new_candles = True
    startup_candle_count = 240
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
    unfilledtimeout = {
        "entry": 60 * 25,
        "exit": 60 * 25
    }
    # buy_params = {
    #     "buy_trend_above_senkou_level": 1,
    #     "buy_trend_bullish_level": 6,
    #     "buy_fan_magnitude_shift_value": 3,
    #     "buy_min_fan_magnitude_gain": 1.009
    #     # "buy_min_fan_magnitude_gain": 1.002 # NOTE: Good value (Win% ~70%), alot of trades
    #     # "buy_min_fan_magnitude_gain": 1.008 # NOTE: Very save value (Win% ~90%), only the biggest moves 1.008,
    # }
    # sell_params = {
    #     "sell_trend_indicator": "trend_close_2h",
    # }
    # Stoploss:
    stoploss = -0.05

    trailing_stop = True
    trailing_stop_positive = 0.001
    trailing_stop_positive_offset = 0.037
    trailing_only_offset_is_reached = True

    is_optimize_32 = True
    buy_rsi_fast_32 = IntParameter(20, 70, default=40, space='buy', optimize=is_optimize_32)
    buy_rsi_32 = IntParameter(15, 50, default=42, space='buy', optimize=is_optimize_32)
    buy_sma15_32 = DecimalParameter(0.900, 1, default=0.973, decimals=3, space='buy', optimize=is_optimize_32)
    buy_cti_32 = DecimalParameter(-1, 1, default=0.69, decimals=2, space='buy', optimize=is_optimize_32)

    sell_fastx = IntParameter(50, 100, default=84, space='sell', optimize=True)

    cci_opt = True
    sell_win_cci = IntParameter(low=0, high=600, default=120, space='sell', optimize=cci_opt)
    sell_loss_cci = IntParameter(low=0, high=600, default=80, space='sell', optimize=cci_opt)
    sell_loss_profit = DecimalParameter(-1, 1, default=-0.01, decimals=2, space='sell', optimize=cci_opt)
    sell_win_profit = DecimalParameter(-1, 1, default=0.01, decimals=2, space='sell', optimize=cci_opt)

    @property
    def protections(self):

        return [
        {
            "method": "CooldownPeriod",
            "stop_duration_candles": 12
        }
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # df = dataframe.copy()
        #
        # heikinashi = qtpylib.heikinashi(df)
        # df['open'] = heikinashi['open']
        # #dataframe['close'] = heikinashi['close']
        # df['high'] = heikinashi['high']
        # df['low'] = heikinashi['low']
        #
        # dataframe['ha_open'] = heikinashi['open']
        # dataframe['ha_high'] = heikinashi['high']
        # dataframe['ha_low'] = heikinashi['low']

        # dataframe['trend_close_5m'] = dataframe['close']
        # dataframe['trend_close_15m'] = ta.EMA(dataframe['close'], timeperiod=3)
        # dataframe['trend_close_30m'] = ta.EMA(dataframe['close'], timeperiod=6)
        # dataframe['trend_close_1h'] = ta.EMA(dataframe['close'], timeperiod=12)
        # dataframe['trend_close_2h'] = ta.EMA(dataframe['close'], timeperiod=24)
        # dataframe['trend_close_4h'] = ta.EMA(dataframe['close'], timeperiod=48)
        # dataframe['trend_close_6h'] = ta.EMA(dataframe['close'], timeperiod=72)
        # dataframe['trend_close_8h'] = ta.EMA(dataframe['close'], timeperiod=96)
        #
        # dataframe['trend_open_5m'] = dataframe['ha_open']
        # dataframe['trend_open_15m'] = ta.EMA(dataframe['ha_open'], timeperiod=3)
        # dataframe['trend_open_30m'] = ta.EMA(dataframe['ha_open'], timeperiod=6)
        # dataframe['trend_open_1h'] = ta.EMA(dataframe['ha_open'], timeperiod=12)
        # dataframe['trend_open_2h'] = ta.EMA(dataframe['ha_open'], timeperiod=24)
        # dataframe['trend_open_4h'] = ta.EMA(dataframe['ha_open'], timeperiod=48)
        # dataframe['trend_open_6h'] = ta.EMA(dataframe['ha_open'], timeperiod=72)
        # dataframe['trend_open_8h'] = ta.EMA(dataframe['ha_open'], timeperiod=96)

        # dataframe['fan_magnitude'] = (dataframe['trend_close_1h'] / dataframe['trend_close_8h'])
        # dataframe['fan_magnitude_gain'] = dataframe['fan_magnitude'] / dataframe['fan_magnitude'].shift(1)
        #
        # ichimoku = ftt.ichimoku(df, conversion_line_period=20, base_line_periods=60, laggin_span=120, displacement=30)
        # dataframe['senkou_a'] = ichimoku['senkou_span_a']
        # dataframe['senkou_b'] = ichimoku['senkou_span_b']

        # buy_1 indicators
        dataframe['sma_15'] = ta.SMA(dataframe, timeperiod=15)
        dataframe['cti'] = pta.cti(dataframe["close"], length=20)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_fast'] = ta.RSI(dataframe, timeperiod=4)
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=20)

        # profit sell indicators
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastk'] = stoch_fast['fastk']
        dataframe['fastd'] = stoch_fast['fastd']

        # fastk_period=5, slowk_period=3, slowk_matype=0, slowd_period=3, slowd_matype=0
        stoch_slow = ta.STOCH(dataframe, fastk_period=5, slowk_period=3, slowd_period=3)
        dataframe['slowk'] = stoch_slow['slowk']
        dataframe['slowd'] = stoch_slow['slowd']

        dataframe['change'] = 100 / dataframe['open'] * dataframe['close'] - 100

        dataframe['ma120'] = ta.MA(dataframe, timeperiod=120)
        dataframe['ma240'] = ta.MA(dataframe, timeperiod=240)

        dataframe['cci'] = ta.CCI(dataframe, timeperiod=20)
        # dataframe["cci_mid"] = 0
        #
        # dataframe["rsi_ma"] = ta.SMA(dataframe['rsi'], timeperiod=14)
        # dataframe["rsi_mid"] = 50
        # dataframe['rc'] = 0
        # dataframe.loc[
        #     (
        #         ((dataframe['rsi'].shift(1) < 50) & (dataframe['rsi'] > 50)) |
        #         ((dataframe['rsi'].shift(2) < 50) & (dataframe['rsi'].shift(1) > 50)) |
        #         ((dataframe['rsi'].shift(3) < 50) & (dataframe['rsi'].shift(2) > 50))
        #     ), 'rc'] = 1
        #
        # stoch = ta.STOCH(dataframe)
        # dataframe["slowd"] = stoch["slowd"]
        # dataframe["slowk"] = stoch["slowk"]
        # dataframe.loc[:, 'sc'] = np.nan
        # dataframe.loc[0, 'sc'] = 0
        # dataframe.loc[((dataframe['slowd'] > 80) & (dataframe['slowk'] > 80)), 'sc'] = 1
        # dataframe.loc[((dataframe['slowd'] < 20) & (dataframe['slowk'] < 20)), 'sc'] = -1
        # dataframe['sc'] = dataframe['sc'].ffill()
        #
        # dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        # dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        # dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        #
        # macd = ta.MACD(dataframe)
        # dataframe["macd"] = macd["macd"]
        # dataframe["macdsignal"] = macd["macdsignal"]
        # dataframe["macdhist"] = macd["macdhist"]
        # dataframe["mc"] = 0
        # dataframe["hc"] = 0
        # dataframe.loc[(
        #         ((dataframe['macd'].shift(1) < dataframe['macdsignal'].shift(1)) & (dataframe['macd'] > dataframe['macdsignal'])) |
        #         ((dataframe['macd'].shift(2) < dataframe['macdsignal'].shift(2)) & (dataframe['macd'].shift(1) > dataframe['macdsignal'].shift(1))) |
        #         ((dataframe['macd'].shift(3) < dataframe['macdsignal'].shift(3)) & (dataframe['macd'].shift(2) > dataframe['macdsignal'].shift(2)))
        #         ), 'mc'] = 1
        # dataframe.loc[(
        #         ((dataframe['macdhist'].shift(1) < 0) & (dataframe['macdhist'] > 0)) |
        #         ((dataframe['macdhist'].shift(2) < 0) & (dataframe['macdhist'].shift(1) > 0)) |
        #         ((dataframe['macdhist'].shift(3) < 0) & (dataframe['macdhist'].shift(2) > 0))
        #         ), 'hc'] = 1

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions1 = []
        conditions2 = []
        conditions3 = []
        dataframe.loc[:, 'enter_tag'] = ''

        # buy_3 = (
        #         (dataframe['sc'] == -1) &
        #         (dataframe['mc'] == 1) &
        #         (dataframe['rc'] == 1) &
        #         (dataframe['fastk'] < 90) &
        #         (dataframe['close'] > dataframe['open']) &
        #         (dataframe['close'] > dataframe['ema200']) &
        #         (dataframe['ema50'] > dataframe['ema200']) &
        #         (dataframe['ema200'] > dataframe['ema200'].shift(1))
        # )
        # conditions3.append(buy_3)
        # dataframe.loc[buy_3, 'enter_tag'] += 'scalp_'
        # dataframe['tag'] = 0
        # dataframe.loc[buy_3, 'tag'] = 1
        # if conditions3:
        #     dataframe.loc[
        #         reduce(lambda x, y: x | y, conditions3),
        #         'enter_long'] = 1

        buy_1 = (
                (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &
                (dataframe['rsi_fast'] < self.buy_rsi_fast_32.value) &
                (dataframe['rsi'] > self.buy_rsi_32.value) &
                (dataframe['close'] < dataframe['sma_15'] * self.buy_sma15_32.value) &
                (dataframe['cti'] < self.buy_cti_32.value)
        )

        conditions1.append(buy_1)
        dataframe.loc[buy_1, 'enter_tag'] += 'ev_1'

        # buy_new = (
        #         (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &
        #         (dataframe['rsi_fast'] < 34) &
        #         (dataframe['rsi'] > 28) &
        #         (dataframe['close'] < dataframe['sma_15'] * 0.96) &
        #         (dataframe['cti'] < self.buy_cti_32.value) &
        #         (
        #                 (dataframe['ma120'] * 1.001 < dataframe['low']) |
        #                 (dataframe['ma120'] > dataframe['high'])
        #         ) &
        #         (
        #                 (dataframe['ma240'] * 1.001 < dataframe['low']) |
        #                 (dataframe['ma240'] > dataframe['high'])
        #         )
        # )
        #
        # conditions1.append(buy_new)
        # dataframe.loc[buy_new, 'enter_tag'] += 'ev_new'

        if conditions1:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions1),
                'enter_long'] = 1

        # if self.buy_params['buy_trend_above_senkou_level'] >= 1:
        #     conditions2.append(dataframe['trend_close_5m'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_5m'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 2:
        #     conditions2.append(dataframe['trend_close_15m'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_15m'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 3:
        #     conditions2.append(dataframe['trend_close_30m'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_30m'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 4:
        #     conditions2.append(dataframe['trend_close_1h'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_1h'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 5:
        #     conditions2.append(dataframe['trend_close_2h'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_2h'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 6:
        #     conditions2.append(dataframe['trend_close_4h'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_4h'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 7:
        #     conditions2.append(dataframe['trend_close_6h'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_6h'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_above_senkou_level'] >= 8:
        #     conditions2.append(dataframe['trend_close_8h'] > dataframe['senkou_a'])
        #     conditions2.append(dataframe['trend_close_8h'] > dataframe['senkou_b'])
        # if self.buy_params['buy_trend_bullish_level'] >= 1:
        #     conditions2.append(dataframe['trend_close_5m'] > dataframe['trend_open_5m'])
        # if self.buy_params['buy_trend_bullish_level'] >= 2:
        #     conditions2.append(dataframe['trend_close_15m'] > dataframe['trend_open_15m'])
        # if self.buy_params['buy_trend_bullish_level'] >= 3:
        #     conditions2.append(dataframe['trend_close_30m'] > dataframe['trend_open_30m'])
        # if self.buy_params['buy_trend_bullish_level'] >= 4:
        #     conditions2.append(dataframe['trend_close_1h'] > dataframe['trend_open_1h'])
        # if self.buy_params['buy_trend_bullish_level'] >= 5:
        #     conditions2.append(dataframe['trend_close_2h'] > dataframe['trend_open_2h'])
        # if self.buy_params['buy_trend_bullish_level'] >= 6:
        #     conditions2.append(dataframe['trend_close_4h'] > dataframe['trend_open_4h'])
        # if self.buy_params['buy_trend_bullish_level'] >= 7:
        #     conditions2.append(dataframe['trend_close_6h'] > dataframe['trend_open_6h'])
        # if self.buy_params['buy_trend_bullish_level'] >= 8:
        #     conditions2.append(dataframe['trend_close_8h'] > dataframe['trend_open_8h'])
        #
        # conditions2.append(dataframe['fan_magnitude_gain'] >= self.buy_params['buy_min_fan_magnitude_gain'])
        # conditions2.append(dataframe['fan_magnitude_gain'] > dataframe['fan_magnitude_gain'].shift(1))
        # conditions2.append(dataframe['fan_magnitude'] > 1)
        #
        # for x in range(self.buy_params['buy_fan_magnitude_shift_value']):
        #     conditions2.append(dataframe['fan_magnitude'].shift(x+1) < dataframe['fan_magnitude'])
        #
        # if conditions2:
        #     dataframe.loc[
        #         reduce(lambda x, y: x & y, conditions2),
        #         'enter_long'] = 1
        #     dataframe.loc[
        #         reduce(lambda x, y: x & y, conditions2),
        #         'enter_tag'] += '[ichi]'
        return dataframe

    def custom_exit(self, pair: str, trade: 'Trade', current_time: 'datetime', current_rate: float,
                    current_profit: float, **kwargs):
        dataframe, _ = self.dp.get_analyzed_dataframe(pair=pair, timeframe=self.timeframe)
        current_candle = dataframe.iloc[-1].squeeze()
        last_candle = dataframe.iloc[-2].squeeze()

        if 'ev' in trade.enter_tag:
            min_profit = trade.calc_profit_ratio(trade.min_rate)

            if trade.id not in TMP_HOLD:
                if len(dataframe.loc[dataframe['date'] < trade.open_date_utc]) > 0:
                    open_candle = dataframe.loc[dataframe['date'] < trade.open_date_utc].iloc[-1].squeeze()
                    if open_candle['close'] > open_candle["ma120"] or open_candle['close'] > open_candle["ma240"]:
                        TMP_HOLD.append(trade.id)
                elif current_candle['close'] > current_candle["ma120"] or current_candle['close'] > current_candle["ma240"]:
                    TMP_HOLD.append(trade.id)
            # else:
            #     if trade.id not in TMP_HOLD1:
            #         TMP_HOLD1.append(trade.id)

            if current_profit > self.sell_win_profit.value:
                #if current_candle["slowk"] > self.sell_fastx.value:
                if current_candle["fastk"] > self.sell_fastx.value:
                    return "fastk_profit_sell"

            if current_candle["cci"] > self.sell_win_cci.value:
                if current_candle["high"] >= trade.open_rate:
                    return "cci_high_sell"

            if min_profit <= self.sell_loss_profit.value:
                if current_profit > self.sell_loss_profit.value:
                    if current_candle["cci"] > self.sell_loss_cci.value:
                        return "cci_loss_sell"

            if trade.id in TMP_HOLD and current_candle["close"] < current_candle["ma120"] and current_candle["close"] < current_candle["ma240"]:
                if current_time - timedelta(minutes=12) > trade.open_date_utc:
                    TMP_HOLD.remove(trade.id)
                    return "ma120_sell"

            # if trade.id in TMP_HOLD1:
            #     if current_candle["high"] > current_candle["ma120"] or current_candle["high"] > current_candle["ma240"]:
            #         if self.stoploss <= min_profit <= self.sell_loss_profit.value:
            #             TMP_HOLD1.remove(trade.id)
            #             return "cross_120_or_240_sell"
        # elif 'ichi' in trade.enter_tag:
        #     if last_candle['trend_close_5m'] >= last_candle[self.sell_params['sell_trend_indicator']] and current_candle['trend_close_5m'] < current_candle[self.sell_params['sell_trend_indicator']]:
        #         return "long_out"

        if current_time - timedelta(minutes=120) > trade.open_date_utc and current_profit and current_profit > 0.017:
            return "roi"
        elif current_time - timedelta(minutes=180) > trade.open_date_utc and current_profit and current_profit > 0:
            return "roi"
        # elif current_time - timedelta(minutes=180) > trade.open_date_utc and current_profit and current_profit > -0.017:
        #     return "roi"

        return None

    def check_entry_timeout(self, pair: str, trade: Trade, order: Order,
                            current_time: datetime, **kwargs) -> bool:
        ob = self.dp.orderbook(pair, 1)
        current_price = ob["bids"][0][0]
        print(current_price, order.price)
        # Cancel buy order if price is more than 2% above the order.
        if current_price > order.price * 1.02:
            return True
        return False


    def check_exit_timeout(self, pair: str, trade: Trade, order: Order,
                           current_time: datetime, **kwargs) -> bool:
        ob = self.dp.orderbook(pair, 1)
        current_price = ob["asks"][0][0]
        print(current_price, order.price)
        # Cancel sell order if price is more than 2% below the order.
        if current_price < order.price * 0.98:
            return True
        return False

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, ['exit_long', 'exit_tag']] = (0, 'long_out')
        return dataframe
