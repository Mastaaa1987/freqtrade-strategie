# Allgemein Information ::

Die Strategie die ich hier verfolge liegt ihren Uhrsprung in der "Triple Threat Trading Strategy" welche eigentlich im 5 min Frame genutzt wird.

Um die Signalstärke zu verbessern nutzt meine Strategie die Indikatoren im 1 Stunden Candle.

Die Indikatoren die für den Einstieg genutzt werden sind RSI, Stochastik & MACD, alle mit den Vorgegebenen Einstellungen:

- RSI:: Length: 14

- Stochastik:: %K-Period: 14, %K-Smoothing: 3, %D-Smoothing: 3

- MACD:: Fast-Length: 12, Slow-Length: 26, Signal-Length: 9

## Einstieg in den Trade:

![Indikatoren1](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main/res/freqtrade_indikatoren.jpg)

- 1: Der Stochastik %K,%D befinden sich unter Oversold Line (20)
- 2: Der RSI kreuzt die 50er line von unten nach oben.
- 3: Der MACD kreuzt die Signal Line von unten nach oben.
- 4: Der Stochastik %K,%D liegt noch in dem Bereich über 20 und unter 80.
- 5: Sind alle Bedingungen erfüllt, beginnt hier ein neuer Trade.

- Den ersten Stoploss setzt die Strategie hierbei an der Kerzen länge.
- Der zweite Stoploss liegt beim Swing Low der letzten Kerzen. (Alle Grünen Kerzen zusammen, bis zur ersten Roten ...)
- Der Take Profit setzt sich hierbei beim zweiten Stoploss * 1.5 (Was eine Ratio von 1 zu 1,5 entspricht ...)

## Zuvor müssen erst 3 Faktoren zutreffen damit ein Trade auch wirklich beginnt.

![Indikatoren2](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main/res/freqtrade_indikatoren2.jpg)

- 1: Die EMA 50 Liegt über EMA 200 Linie.
- 2: Die EMA 200 Line bewegt sich aufwärts.
- 3: Die Kerze schließt über EMA 200.

## Strategie Information die ausgegeben werden.

Da meine Strategie jede Kerze jedes Pairs analysiert, gibt es eine Menge Faktoren die man sich in der UI bei dem Plot aller jeweiligen Pairs anzeigen lassen kann.

Viele habe ich von Haus aus in der Strategie mit intigriert. Diese kann man ganz easy oben rechts über [Einstellungs] Knopf und dann [from strategy] laden...

Hier eine Übersicht aller Infos und deren Bedeutung:

- awin (all wins) :: Die Summe in Prozent aller Trades des Pairs.
- aw, wc (all win, win count) :: Die Summe in Prozent aller gewonnen Trades, und die Anzahl.
- al, lc (all loose, loose count) :: Die Summer in Prozent aller verlohrenen Trades, und die Anzahl.
- tag :: Ausstiegsgrund des letzten Trades.
- c (close) :: Einstiegskurs des letzten Trades.
- sc, rc, mc (stoch condition, rsi condition, macd condition) :: Indikatoren Conditionen für den Trade einstieg.
    - (sc -1: Stochastik oversold, 1: Stochastik overbought; rc 1: rsi cross 50 line; mc 1: macd cross signal line ...
    - Soll heißen sc, rc, mc is gleich -1, 1, 1 = Kaufbefehl.)
- count :: Anzahl der vergangenden Kerzen im Trade.
- sl1 (stoploss1) :: errechneter stoploss Price. (Candle: close - open)
- sl2 (stoploss2) :: errechneter stoploss Price 2. (Swing Low: Alle grünen Kerzen betrachtet: 1. Kerze close - letzte Kerze open)
- wait :: Warte befehl für die Strategie wenn Take Profit erreicht wurde aber alle Kerzen grün sind seit trade beginn, bis zur ersten roten Kerze als Ausstieg... (Darauf geh ich gleich näher ein)


## Ausstieg aus dem Trade ...

So jetzt kommen wir zum Tückischen Teil des Trades. 

### Der Ablauf ist wie folgt:
- if trade:
   - if wait und close < open: exit
   - elif profit > stoploss2 * 1.5 oder profit < stoploss2: exit
   - elif count > 2 & < 7 und profit > stoploss1 * 1.5: exit
   - elif count > 2 & < 7 und close > trade.entry und win > 1%:
       - if all candles close > open: wait 1
       - else: exit
   - elif count >= 7 und win > 0: exit
