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
   - if wait & close < open: exit
   - elif profit > stoploss2 * 1.5 or profit < stoploss2: exit
   - elif count > 2 & < 7 & profit > stoploss1 * 1.5: exit
   - elif count > 2 & < 7 & close > trade.entry & win > 1%:
       - if all candles close > open: wait 1
       - else: exit
   - elif count >= 7 & win > 0: exit

## Meine Erfahrungswerte:

Ich habe die Erfahrung gemacht, das es sehr viel profitabler ist die 2-3 Prozent in einem Trade mit zu nehmen und dem entsprechend aus zu steigen, als noch länger zu warten!

Natürlich gehen einem das eine oder andere mal höhere preissprünge dabei vor der Nase verlohren weil die Strategie zu früh aussteigt.

Aber Schlussendlich ist es so das am häufigsten der Fall eintritt: Win Candle +0,5% -> Win Candle +1% -> Loose Candle -2% -> Loose -0,5% ... -> Bis insgesamt Loose -5% und somit der Stoploss (ganz oben in der Strategie angegeben mit: -0.05) eintritt. 

Über einen längeren zeitraum betrachtet ist jeder Trade der Profit abwirft (egal wie klein er auch sein mag...) weitaus besser als Trade der Verlust mit sich bringt. 

Klein Fieh macht auch riesen Mist, wie man unschwer an den Backtest Profiten 01.02.2023 - 01.12.2023 & 01.01.2024 - 08.10.2024 erkennen kann.

Die Sagenhafte 2663% und 2328% Profite erziehlen. Was in USDT bedeutet: Angefangen mit 100 USDT, Beendet mit 2763 USDT & 2428 USDT !

## Background Infos:

Mach einer Mag sich fragen ob solche Profite die die Backtests erziehlen überhaupt realistisch sind? Und wenn ja wie diese zu stande kommen?

Nehmen wir an die Trades werfen ca. 3% Profit ab. Und wir gewinnen jeden Trade. Wir gewinnen jeden Tag 1 Trade, daraus würde sich ein Profit von (ca.) 100% ergeben. Ergo (angefangen mit 100): 200.

Testet der Bot nun weiter weil der Zeitraum noch nicht zu ende ist, ergibt sich folglich das die selben 3% jetzt Trades mit 6% ergeben weil die eingesetzte USDT Menge ja Doppelt so hoch ist wie am anfang.

Nun bedeutet das folglich das nur noch die hälfte an win Trades nötig sind um wieder diese 100% (100 USDT) zu erreichen. Rechnet man nun einfach weiter kommt irgentwann immer der Punkt wo die Profite astronomische

Ausmaße annehmen weil wenn wir das 10 fache von 100 USDT investieren und wieder unsere 3% ereichen, der Trade 30% ergibt wenn wir von unseren 100 USDT als maßstab aus sehen ... 3% von 1000 USDT = 30 USDT,

was wiederum 30% von 100 USDT sind. Eigentlich doch richtig einleuchtend oder? Ihr müsst also ganz einfach im Hinterkopf behalten das freqtrade bei den bilanzen einen Backtests von dem Startkapital 

(sprich 100 USDT) die Prozente ableitet ... Um das nochmal zu veranschaulichen: Angefangen mit 100 USDT, sind wir bei 1000 USDT und verliehren einen trade mit -1.5% was wiederum bei 1000 USDT = 15 USDT sind.

Also wird der trade mit -15% angezeigt, was wiederum richtig ist weil -15 USDT von anfangs 100 USDT halt -15% sind. Wenn ihr sehen wollt bei wieviel Prozent der Trade wirklich abschließt,

müsst ihr den "Avg Profit %" betrachten. Dort wird euch angezeigt wieviel Profit ihr bei diesem Pair erwarten könnt (In diesem Zenario immernoch 3%) ;-)

So das wars auch erstmal von mir ...

Immer schön Cremig bleiben :D

