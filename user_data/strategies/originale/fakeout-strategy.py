
from pandas import DataFrame
from functools import reduce
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter

import talib.abstract as ta
from scipy.signal import argrelextrema
import numpy as np

class FakeoutStrategy(IStrategy):

    timeframe = "5m"
    can_short = False

    buy_peak_order = IntParameter(80, 180, default=120, space="buy")

    sell_peak_order = IntParameter(80, 180, default=120, space="sell")


    # ROI table:
    minimal_roi = {
        "0": 0.242,
        "13": 0.044,
        "51": 0.02,
        "170": 0
    }

    # Stoploss:
    stoploss = -0.12

    # Trailing stop:
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.05
    trailing_only_offset_is_reached = False

    count_under_level = 0
    count_over_level = 0

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        for val in self.sell_peak_order.range:
            trunc_high = dataframe['high'][:-val].values
            ilocs_max = argrelextrema(trunc_high, np.greater_equal, order=val, mode='wrap')[0]
            dataframe.loc[
                dataframe.iloc[ilocs_max].index,
                f'upper_peak_{val}'
                ] = dataframe['high']
            dataframe[f'upper_peak_{val}'].ffill()
            dataframe[f'count_upper_peak_{val}'] = dataframe.apply( lambda x: self._count_over_level(x['high'], x[f'upper_peak_{val}']), axis=1 )

        for val in self.buy_peak_order.range:
            trunc_low = dataframe['low'][:-val].values
            ilocs_min = argrelextrema(trunc_low, np.less_equal, order=val, mode='wrap')[0]
            dataframe.loc[
                dataframe.iloc[ilocs_min].index,
                f'lower_peak_{val}'
                ] = dataframe['low']
            dataframe[f'lower_peak_{val}'].ffill()
            dataframe[f'count_lower_peak_{val}'] = dataframe.apply( lambda x: self._count_under_level(x['low'], x[f'lower_peak_{val}']), axis=1 )

        return dataframe

    def _count_under_level(self, low, level):
        if low < level:
            self.count_under_level = self.count_under_level + 1
        else:
            self.count_under_level = 0
        return self.count_under_level

    def _count_over_level(self, high, level):
        if high > level:
            self.count_over_level = self.count_over_level + 1
        else:
            self.count_over_level = 0
        return self.count_over_level

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        conditions_long = []
        conditions_short = []

        conditions_long.append(
                dataframe['low'] <= dataframe[f'lower_peak_{self.buy_peak_order.value}'].shift(1)
            )
        conditions_long.append(
                dataframe[f'count_lower_peak_{self.buy_peak_order.value}'].shift(1) == 0
            )

        # conditions_short.append(
        #         dataframe['high'] >= dataframe[f'upper_peak_{self.sell_peak_order.value}'].shift(1)
        #     )
        # conditions_short.append(
        #         dataframe[f'count_upper_peak_{self.sell_peak_order.value}'].shift(1) == 0
        #     )

        dataframe.loc[
            (
                reduce(lambda x, y: x & y, conditions_long)
            ),
            'enter_long'] = 1

        # dataframe.loc[
        #     (
        #         reduce(lambda x, y: x & y, conditions_short)
        #     ),
        #     'enter_short'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        return super().populate_exit_trend(dataframe, metadata)
