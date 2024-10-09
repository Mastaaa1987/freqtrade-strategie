## Allgemein Information ::

Die Strategie die ich hier verfolge liegt ihren Uhrsprung in der "Triple Threat Trading Strategy" welche eigentlich im 5 min Frame genutzt wird.

Um die Signalstärke zu verbessern nutzt meine Strategie die Indikatoren im 1 Stunden Candle.

Die Indikatoren die für den Einstieg genutzt werden sind RSI, Stochastik & MACD, alle mit den Vorgegebenen Einstellungen:

- RSI:: Length: 14

- Stochastik:: %K-Period: 14, %K-Smoothing: 3, %D-Smoothing: 3

- MACD:: Fast-Length: 12, Slow-Length: 26, Signal-Length: 9

### Beispiel:

![Beispiel](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main/res/freqtrade_indikatoren.jpg)

1: Der Stochastik %K,%D befinden sich unter Oversold Line (20)

2: Der RSI kreuzt die 50er line von unten nach oben.

3: Der MACD kreuzt die Signal Line von unten nach oben.

4: Der Stochastik %K,%D liegt noch in dem Bereich über 20 und unter 80.

5: Sind alle Bedingungen erfüllt, beginnt hier ein neuer Trade.

- Den ersten Stoploss setzt die Strategie hierbei an der Kerzen länge.

- Der zweite Stoploss liegt beim Swing Low der letzten Kerzen. (Alle Grünen Kerzen zusammen, bis zur ersten Roten ...)

- Der Take Profit setzt sich hierbei beim zweiten Stoploss * 1.5 (Was eine Ratio von 1 zu 1,5 entspricht ...)

### Weitere Details folgen ...
