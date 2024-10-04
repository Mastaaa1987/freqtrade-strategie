import math, os, json, sys, time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Dict, Optional, Union, Tuple

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    PairLocks,
    informative,  # @informative decorator
    # Hyperopt Parameters
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    RealParameter,
    # timeframe helpers
    timeframe_to_minutes,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    # Strategy helper functions
    merge_informative_pair,
    stoploss_from_absolute,
    stoploss_from_open,
)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import pandas_ta as pta
from technical import qtpylib

class Scalping(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = '5m'

    # Trading Parameter
    # minimal_roi = {
    #     "60": 0.01,
    #     "30": 0.02,
    #     "0": 0.04
    # }
    stoploss = -0.05
    trailing_stop = False
    process_only_new_candles = True
    use_exit_signal = True
    use_custom_stoploss=False
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    startup_candle_count = 200

    # Plot Konfiguration
    @property
    def plot_config(self):
        return {
            "main_plot": {},
            "subplots": {
                "stoch": {
                    "slowd": {
                        "color": "#eeff00",
                        "type": "line"
                    },
                    "slowk": {
                        "color": "#ff0000",
                        "type": "line"
                    }
                },
                "rsi": {
                    "rsi": {
                        "color": "#00ff04",
                        "type": "line"
                    },
                    "rsi_mid": {
                        "color": "#ffffff",
                        "type": "line"
                    }
                },
                "macd": {
                    "macd": {
                        "color": "#00fbff",
                        "type": "line"
                    },
                    "macdsignal": {
                        "color": "#ff0000",
                        "type": "line"
                    }
                },
                "cond": {
                    "awin": {
                        "color": "white"
                    },
                    "tag": {
                        "color": "#de27f8"
                    },
                    "change": {
                        "color": "#14896f"
                    },
                    "wait": {
                        "color": "#7fd9da"
                    },
                    "count": {
                        "color": "#4fa25f"
                    },
                    "c": {
                        "color": "#c84269"
                    },
                    "sl1": {
                        "color": "#de342b"
                    },
                    "sl2": {
                        "color": "#2bbb7d"
                    }
                }
            }
        }

    def calc(self, dataframe: DataFrame, pair):
        if(self.timeframe == '1h'):
            df = dataframe.copy()
        else:
            df = self.dp.get_pair_dataframe(pair=pair, timeframe='1h')
            if(int(df.loc[len(df)-1]['date'].strftime("%M")) != 55):
                data = {'date': dataframe.loc[len(dataframe)-1]['date'], 'open': df.loc[len(df)-1]['close'], 'high': 0, 'low': 0, 'close': dataframe.loc[len(dataframe)-1]['close'], 'volume': 0}
                df = df._append(data, ignore_index = True)
        df["change"] = (100 / df['open'] * df['close'] - 100)

        df['vol_ma'] = df['volume'].rolling(window=30).mean()
        df['vc'] = 0
        df.loc[((df['open'] < df['close']) & (df['volume'] > df['vol_ma'])), 'vc'] = 1

        df["rsi"] = ta.RSI(df)
        df["rsi_ma"] = ta.SMA(df['rsi'], timeperiod=14)
        df["rsi_mid"] = 50
        df['rc'] = 0
        df.loc[
            (
                ((df['rsi'].shift(1) < 50) & (df['rsi'] > 50)) |
                ((df['rsi'].shift(2) < 50) & (df['rsi'].shift(1) > 50)) |
                ((df['rsi'].shift(3) < 50) & (df['rsi'].shift(2) > 50))
            ), 'rc'] = 1

        stoch = ta.STOCH(df)
        df["slowd"] = stoch["slowd"]
        df["slowk"] = stoch["slowk"]
        #df = self.calc_stoch(df, metadata['pair'])

        df["ema50"] = ta.EMA(df, timeperiod=50)
        df["ema200"] = ta.EMA(df, timeperiod=200)

        macd = ta.MACD(df)
        df["macd"] = macd["macd"]
        df["macdsignal"] = macd["macdsignal"]
        df["mc"] = 0
        df.loc[(
                ((df['macd'].shift(1) < df['macdsignal'].shift(1)) & (df['macd'] > df['macdsignal'])) |
                ((df['macd'].shift(2) < df['macdsignal'].shift(2)) & (df['macd'].shift(1) > df['macdsignal'].shift(1))) |
                ((df['macd'].shift(3) < df['macdsignal'].shift(3)) & (df['macd'].shift(2) > df['macdsignal'].shift(2)))
                ), 'mc'] = 1
        v = {'enter': 0, 'exit': 0, 'trade': 0, 'win': 0, 'awin': 0, 'TRADE': [], 'ENTER': [], 'COUNT': [], 'EXIT': [], 'WAIT': [], 'AWIN': [], 'C': [], 'stoch': 0, 'STOCH': [], 'SL1': [], 'SL2': [], 'sl1': 0, 'sl2': 0, 'count': 0, 'c': 0, 'sc': 0, 'wait': 0, 'TAGG': [], 'tagg': ''}
        if(self.timeframe != '1h'):
            if(len(df) == 999): z = 1
            else: z = 0
        else: z = 0
        for i in range(z, len(df)):
            v['enter'], v['exit'] = 0, 0
            if(df.loc[i]['slowd'] > 80) and (df.loc[i]['slowk'] > 80): v['stoch'] = 1
            elif(df.loc[i]['slowd'] < 20) and (df.loc[i]['slowk'] < 20): v['stoch'] = -1
            if(v['trade'] == 0):
                if(df.loc[i]['rc'] == 1) and (df.loc[i]['mc'] == 1) and (v['stoch'] == -1) and (df.loc[i]['close'] > df.loc[i]['open']):
                    if(i > 0):
                        if(df.loc[i]['close'] > df.loc[i]['ema200']) and (df.loc[i]['ema50'] > df.loc[i]['ema200']) and (df.loc[i]['ema200'] > df.loc[i-1]['ema200']):
                            op = df.loc[i]['open']
                            op2 = df.loc[i]['open']
                            for x in range(1, i):
                                if(df.loc[i-x]['open'] < df.loc[i-x]['close']): op2 = df.loc[i-x]['open']
                                else: break
                            v['sl1'] = (df.loc[i]['close'] - op)
                            v['sl2'] = (df.loc[i]['close'] - op2)
                            v['c'] = df.loc[i]['close']

                            v['enter'], v['trade'], v['count'], v['win'], v['tagg'] = 1, 1, 0, 0, ''
            elif(v['trade'] == 1):
                exit = 0
                v['count'] = (v['count'] + 1)
                if(v['wait'] == 1):
                    if(df.loc[i]['close'] < df.loc[i]['open']):
                        exit = 1
                        v['tagg'] = 'exit: wait=1'
                elif(df.loc[i]['close'] > v['c'] + v['sl2'] * 1.5) or (df.loc[i]['close'] < v['c'] - v['sl2']):
                    exit = 1
                    if(df.loc[i]['close'] > v['c'] + v['sl2'] * 1.5):
                        v['tagg'] = 'exit: close>sl2'
                    elif(df.loc[i]['close'] < v['c'] - v['sl2']):
                        v['tagg'] = 'exit: close<sl2'
                    if(v['win'] < 0) and (v['stoch'] == -1):
                        v['stoch'] = 0
                        v['tagg'] = 'exit: close<sl2'
                elif(v['count'] > 2) and (v['count'] < 7):
                    if(df.loc[i]['close'] > v['c'] + v['sl1'] * 1.5):
                        if(v['wait'] == 0):
                            exit = 1
                            v['tagg'] = 'exit: close>sl1'
                    elif(df.loc[i]['close'] > v['c']):
                        win = (100 / v['c'] * df.loc[i]['close'] - 100)
                        if(win > 1):
                            t = True
                            for x in range(1, v['count']):
                                if(df.loc[i-x]['close'] < df.loc[i-x]['open']):
                                    t = False
                                    break
                            if(t):
                                v['wait'] = 1
                                v['tagg'] = 'wait=1'
                            if(v['wait'] == 0):
                                exit = 1
                                v['tagg'] = 'exit: win>1'
                elif(v['count'] >= 7):
                    win = (100 / v['c'] * df.loc[i]['close'] - 100)
                    if(win > 2):
                        exit = 1
                        v['tagg'] = 'exit: win>2,count>=7'
                elif(v['count'] > 10) and (df.loc[i]['close'] > v['c']):
                    win = (100 / v['c'] * df.loc[i]['close'] - 100)
                    if(win > 0):
                        exit = 1
                        v['tagg'] = 'exit: win>0'
                if(exit == 1):
                    v['win'] = (100 / v['c'] * df.loc[i]['close'] - 100)
                    v['awin'] = (v['awin'] + v['win'] - 0.2)
                    v['exit'], v['trade'], v['sl1'], v['sl2'], v['c'], v['wait'], v['count'] = 1, 0, 0, 0, 0, 0, 0
            v['TRADE'].append(v['trade']), v['COUNT'].append(v['count']), v['WAIT'].append(v['wait']), v['C'].append(v['c']), v['SL1'].append(v['sl1']), v['SL2'].append(v['sl2']), v['ENTER'].append(v['enter']), v['EXIT'].append(v['exit']), v['AWIN'].append(v['awin']), v['STOCH'].append(v['stoch']), v['TAGG'].append(v['tagg'])
        df['trade'], df['count'], df['wait'], df['enter'], df['exit'], df['awin'], df['sc'], df['tag'], df['sl1'], df['sl2'], df['c'] = v['TRADE'], v['COUNT'], v['WAIT'], v['ENTER'], v['EXIT'], v['AWIN'], v['STOCH'], v['TAGG'], v['SL1'], v['SL2'], v['C']
        if(self.timeframe != '1h'):
            dataframe = merge_informative_pair(dataframe, df, self.timeframe, '1h', ffill=True)

        # if(v['awin'] > 20):
        print(pair, v['awin'])
        if(self.timeframe != '1h'):
            return dataframe
        else:
            return df

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        #informative_pairs = [(pair, '1d') for pair in pairs]
        if(self.timeframe == '1h'):
            informative_pairs = [(pair, '1h') for pair in pairs]
        else:
            informative_pairs = [(pair, self.timeframe) for pair in pairs]
            informative_pairs += [(pair, '1h') for pair in pairs]
        return informative_pairs

    # Indikatoren berechnen
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        if not self.dp:
            return dataframe
        # Some Stuff ...
        pairs = self.dp.current_whitelist()
        p1 = pairs[len(pairs)-1]
        p0 = pairs[0]
        if(metadata["pair"] == p0):
            rp = os.path.normpath(os.path.dirname(os.path.abspath(__file__))+'/../')
            file = os.path.join(rp, '.ts')
            if os.path.exists(file+".json"):
                os.remove(file+".json")
            t = int(time.time())
            data = {"value": t}
            with open(file+".json", "w") as k:
                json.dump(data, k, indent=4)

        # Strategy Position ...
        dataframe["enter"] = 0
        dataframe["exit"] = 0
        if(self.timeframe == '1h'):
            dataframe["enter_1h"] = 0
            dataframe["exit_1h"] = 0

        dataframe = self.calc(dataframe, metadata['pair'])

        # Other Stuff ...
        if(metadata["pair"] == p1):
            rp = os.path.normpath(os.path.dirname(os.path.abspath(__file__))+'/../')
            file = os.path.join(rp, '.ts')
            if os.path.exists(file+".json"):
                with open(file+".json") as k:
                    r = json.load(k)
                value = r.get('value')
                t = int(time.time())
                print('Loading took %s seconds ...' % str(t-value))

        return dataframe

    # Kaufbedingung (Long Entry)
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['enter'] == 1) |
                (dataframe['enter_1h'] == 1)
            ),
            'enter_long'] = 1
        return dataframe

    # Verkaufsbedingung (Exit)
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['exit'] == 1) |
                (dataframe['exit_1h'] == 1)
            ),
            'exit_long'] = 1
        return dataframe

    # def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
    #                     current_rate: float, current_profit: float, after_fill: bool,
    #                     **kwargs) -> Optional[float]:
    #
    #     dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
    #     last_candle = dataframe.iloc[-1].squeeze()
    #
    #     # Use parabolic sar as absolute stoploss price
    #     sp1 = last_candle['sl1']
    #     sp2 = last_candle['sl2']
    #     c = last_candle['c']
    #     print(sp1, current_rate, c)
    #
    #     # Convert absolute price to percentage relative to current_rate
    #     # if stoploss_price < current_rate:
    #     #     return stoploss_from_absolute(stoploss_price, current_rate, is_short=trade.is_short)
    #
    #     # return maximum stoploss value, keeping current stoploss price unchanged
    #     return None
