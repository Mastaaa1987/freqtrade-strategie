from datetime import datetime, timedelta
import talib.abstract as ta
import pandas_ta as pta
from freqtrade.persistence import Trade
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from freqtrade.strategy import DecimalParameter, IntParameter
from functools import reduce
import warnings

warnings.simplefilter(action="ignore", category=RuntimeWarning)
TMP_HOLD = []
TMP_HOLD1 = []


class E0V1E_test(IStrategy):
    minimal_roi = {
        "0": 1
    }
    timeframe = '5m'
    process_only_new_candles = True
    startup_candle_count = 240
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
    slippage_protection = {
        'retries': 3,
        'max_slippage': -0.02
    }
    cc = {}
    # current_candle = {}

    stoploss = -0.25
    trailing_stop = False
    trailing_stop_positive = 0.002
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = True

    use_custom_stoploss = True

    is_optimize_32 = True
    buy_rsi_fast_32 = IntParameter(20, 70, default=40, space='buy', optimize=is_optimize_32)
    buy_rsi_32 = IntParameter(15, 50, default=42, space='buy', optimize=is_optimize_32)
    buy_sma15_32 = DecimalParameter(0.900, 1, default=0.973, decimals=3, space='buy', optimize=is_optimize_32)
    buy_cti_32 = DecimalParameter(-1, 1, default=0.69, decimals=2, space='buy', optimize=is_optimize_32)

    sell_fastx = IntParameter(50, 100, default=84, space='sell', optimize=True)

    cci_opt = False
    sell_loss_cci = IntParameter(low=0, high=600, default=120, space='sell', optimize=cci_opt)
    sell_loss_cci_profit = DecimalParameter(-0.15, 0, default=-0.05, decimals=2, space='sell', optimize=cci_opt)

    @property
    def protections(self):

        return [
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 60,
                "trade_limit": 1,
                "stop_duration": 60,
                "required_profit": -0.05
            },
            {
                "method": "CooldownPeriod",
                "stop_duration_candles": 5
            }
        ]

    def custom_stoploss(self, pair: str, trade: Trade, current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:

        if current_profit >= 0.05:
            return -0.002

        if str(trade.enter_tag) == "buy_new" and current_profit >= 0.03:
            return -0.003

        return None
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # buy_1 indicators
        buy_sma15_32 = 2 - self.buy_sma15_32.value
        dataframe['sma_15'] = ta.SMA(dataframe, timeperiod=15)
        dataframe['sma_15_a'] = dataframe['sma_15'] * buy_sma15_32
        dataframe['sma_15_b'] = dataframe['sma_15'] * self.buy_sma15_32.value
        dataframe['cti'] = pta.cti(dataframe["close"], length=20)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_fast'] = ta.RSI(dataframe, timeperiod=4)
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=20)

        # profit sell indicators
        stoch_fast = ta.STOCHF(dataframe, 5, 3, 0, 3, 0)
        dataframe['fastk'] = stoch_fast['fastk']

        dataframe['cci'] = ta.CCI(dataframe, timeperiod=20)

        dataframe['ma120'] = ta.MA(dataframe, timeperiod=120)
        dataframe['ma240'] = ta.MA(dataframe, timeperiod=240)

        # my add
        dataframe['change'] = (100 / dataframe['open'] * dataframe['close'] - 100)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        conditions = []
        dataframe.loc[:, 'enter_tag'] = ''
        buy_1 = (
                (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &
                (dataframe['rsi_fast'] < self.buy_rsi_fast_32.value) &
                (dataframe['rsi'] > self.buy_rsi_32.value) &
                (dataframe['close'] < dataframe['sma_15'] * self.buy_sma15_32.value) &
                (dataframe['cti'] < self.buy_cti_32.value)
        )

        # buy_new = (
        #         (dataframe['rsi_slow'] < dataframe['rsi_slow'].shift(1)) &
        #         (dataframe['rsi_fast'] < 34) &
        #         (dataframe['rsi'] > 28) &
        #         (dataframe['close'] < dataframe['sma_15'] * 0.96) &
        #         (dataframe['cti'] < self.buy_cti_32.value)
        # )


        conditions.append(buy_1)
        dataframe.loc[buy_1, 'enter_tag'] += 'buy_1'

        # conditions.append(buy_new)
        # dataframe.loc[buy_new, 'enter_tag'] += 'buy_new'

        if conditions:
            dataframe.loc[
                reduce(lambda x, y: x | y, conditions),
                'enter_long'] = 1
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

        if trade.id not in TMP_HOLD:
            if len(dataframe.loc[dataframe['date'] < trade.open_date_utc]) > 0:
                open_candle = dataframe.loc[dataframe['date'] < trade.open_date_utc].iloc[-1].squeeze()
                if open_candle['close'] > open_candle["ma120"] and open_candle['close'] > open_candle["ma240"]:
                    TMP_HOLD.append(trade.id)
            elif current_candle['close'] > current_candle["ma120"] and current_candle['close'] > current_candle["ma240"]:
                TMP_HOLD.append(trade.id)

        if trade.id not in TMP_HOLD1:
            if (trade.open_rate - current_candle["ma120"]) / trade.open_rate >= 0.1:
                TMP_HOLD1.append(trade.id)

        if current_profit > 0:
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
            else:
                if current_candle["fastk"] > self.sell_fastx.value:
                    return "fastk_profit_sell"

        if min_profit <= -0.1:
            if current_profit > self.sell_loss_cci_profit.value:
                if current_candle["cci"] > self.sell_loss_cci.value:
                    return "cci_loss_sell"

        if trade.id in TMP_HOLD1 and current_candle["close"] < current_candle["ma120"]:
            TMP_HOLD1.remove(trade.id)
            return "ma120_sell_fast"

        if trade.id in TMP_HOLD and current_candle["close"] < current_candle["ma120"] and current_candle["close"] < current_candle["ma240"]:
            if min_profit <= -0.1:
                TMP_HOLD.remove(trade.id)
                return "ma120_sell"

        return None

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[:, ['exit_long', 'exit_tag']] = (0, 'long_out')
        return dataframe
