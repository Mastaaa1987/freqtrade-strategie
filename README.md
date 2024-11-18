For the English translation, you have to scroll down ...

## Allgemein Information ::

Die Strategie die ich hier verfolge liegt ihren Uhrsprung in der "Triple Threat Trading Strategy" welche eigentlich im 5 min Frame genutzt wird.

Um die Signalstärke zu verbessern nutzt meine Strategie die Indikatoren im 1 Stunden Candle.

Die Indikatoren die für den Einstieg genutzt werden sind RSI, Stochastik & MACD, alle mit den Vorgegebenen Einstellungen:

- RSI:: Length: 14

- Stochastik:: %K-Period: 14, %K-Smoothing: 3, %D-Smoothing: 3

- MACD:: Fast-Length: 12, Slow-Length: 26, Signal-Length: 9

## Einstieg in den Trade:

![Indikatoren1](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main_bakk/res/freqtrade_indikatoren.jpg)

- 1: Der Stochastik %K,%D befinden sich unter Oversold Line (20)
- 2: Der RSI kreuzt die 50er line von unten nach oben.
- 3: Der MACD kreuzt die Signal Line von unten nach oben.
- 4: Der Stochastik %K,%D liegt noch in dem Bereich über 20 und unter 80.
- 5: Sind alle Bedingungen erfüllt, beginnt hier ein neuer Trade.

- Den ersten Stoploss setzt die Strategie hierbei an der Kerzen länge.
- Der zweite Stoploss liegt beim Swing Low der letzten Kerzen. (Alle Grünen Kerzen zusammen, bis zur ersten Roten ...)
- Der Take Profit setzt sich hierbei beim zweiten Stoploss * 1.5 (Was eine Ratio von 1 zu 1,5 entspricht ...)

## Zuvor müssen erst 3 Faktoren zutreffen damit ein Trade auch wirklich beginnt.

![Indikatoren2](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main_bakk/res/freqtrade_indikatoren2.jpg)

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

Manch einer Mag sich fragen ob solche Profite die die Backtests erziehlen überhaupt realistisch sind? Und wenn ja wie diese zu stande kommen?

Nehmen wir an die Trades werfen ca. 3% Profit ab. Und wir gewinnen jeden Trade. Wir gewinnen jeden Tag 1 Trade, daraus würde sich ein Profit von (ca.) 100% in 30 Tagen ergeben. Ergo (angefangen mit 100): 200.

Testet der Bot nun weiter weil der Zeitraum noch nicht zu ende ist, ergibt sich folglich das die selben 3% jetzt Trades mit 6% ergeben weil die eingesetzte USDT Menge ja Doppelt so hoch ist wie am anfang.

Nun bedeutet das folglich das nur noch die hälfte an win Trades nötig sind um wieder diese 100% (100 USDT) zu erreichen. Rechnet man nun einfach weiter kommt irgentwann immer der Punkt wo die Profite astronomische

Ausmaße annehmen weil wenn wir das 10 fache von 100 USDT investieren und wieder unsere 3% ereichen, der Trade 30% ergibt wenn wir von unseren 100 USDT als maßstab aus sehen ... 3% von 1000 USDT = 30 USDT,

was wiederum 30% von 100 USDT sind. Eigentlich doch richtig einleuchtend oder? Ihr müsst also ganz einfach im Hinterkopf behalten das freqtrade bei den bilanzen einen Backtests von dem Startkapital 

(sprich 100 USDT) die Prozente ableitet ... Um das nochmal zu veranschaulichen: Angefangen mit 100 USDT, sind wir bei 1000 USDT und verliehren einen trade mit -1.5% was wiederum bei 1000 USDT = 15 USDT sind.

Also wird der trade mit -15% angezeigt, was wiederum richtig ist weil -15 USDT von anfangs 100 USDT halt -15% sind. Wenn ihr sehen wollt bei wieviel Prozent der Trade wirklich abschließt,

müsst ihr den "Avg Profit %" betrachten. Dort wird euch angezeigt wieviel Profit ihr bei diesem Pair erwarten könnt (In diesem Zenario immernoch 3%) ;-)

So das wars auch erstmal von mir ...

Immer schön Cremig bleiben :D


# English Readme ...

## General Information ::

The strategy I am following here has its origins in the "Triple Threat Trading Strategy" which is actually used in the 5 minute frame.

To improve the signal strength, my strategy uses the indicators in the 1 hour candle.

The indicators used for entry are RSI, Stochastic & MACD, all with the default settings:

- RSI:: Length: 14

- Stochastik:: %K-Period: 14, %K-Smoothing: 3, %D-Smoothing: 3

- MACD:: Fast-Length: 12, Slow-Length: 26, Signal-Length: 9

## Entry into the trade:

![Indikatoren1](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main_bakk/res/freqtrade_indikatoren.jpg)

- 1: The stochastic %K,%D are below the oversold line (20)
- 2: The RSI crosses the 50 line from bottom to top.
- 3: The MACD crosses the signal line from bottom to top.
- 4: The stochastic %K,%D is still in the area above 20 and below 80.
- 5: If all conditions are met, a new trade begins here.

- The strategy sets the first stop loss based on the length of the candle.
- The second stop loss is at the swing low of the last candle. (All green candles together, up to the first red one ...)
- The take profit is set at the second stop loss * 1.5 (which corresponds to a ratio of 1 to 1.5 ...)

## Three factors must be met before a trade can actually begin.

![Indikatoren2](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main_bakk/res/freqtrade_indikatoren2.jpg)

- 1: The EMA 50 is above the EMA 200 line.
- 2: The EMA 200 line is moving up.
- 3: The candle closes above the EMA 200.

## Strategy information that is issued.

Since my strategy analyzes every candle of every pair, there are a lot of factors that can be displayed in the UI when plotting all the respective pairs.

I have integrated many of them into the strategy by default. You can easily load these using the [Settings] button at the top right and then [from strategy]...

Here is an overview of all the information and what it means:

- awin (all wins) :: The sum in percent of all trades in the pair.

- aw, wc (all win, win count) :: The sum in percent of all won trades, and the number.

- al, lc (all loose, loose count) :: The totals in percent of all lost trades, and the number.

- tag :: Reason for exiting the last trade.

- c (close) :: Entry price of the last trade.

- sc, rc, mc (stoch condition, rsi condition, macd condition) :: Indicator conditions for entering the trade.
- (sc -1: stochastic oversold, 1: stochastic overbought; rc 1: rsi cross 50 line; mc 1: macd cross signal line ...
- This means sc, rc, mc is equal to -1, 1, 1 = buy order.)
- count :: number of past candles in the trade.
- sl1 (stoploss1) :: calculated stoploss price. (Candle: close - open)
- sl2 (stoploss2) :: calculated stoploss price 2. (Swing Low: All green candles considered: 1st candle close - last candle open)
- wait :: Wait command for the strategy when take profit has been reached but all candles have been green since the start of the trade, until the first red candle as an exit... (I'll go into this in more detail in a moment)

## Exit from the trade ...

So now we come to the tricky part of the trade.

### The process is as follows:

- if trade:
   - if wait & close < open: exit
   - elif profit > stoploss2 * 1.5 or profit < stoploss2: exit
   - elif count > 2 & < 7 & profit > stoploss1 * 1.5: exit
   - elif count > 2 & < 7 & close > trade.entry & win > 1%:
       - if all candles close > open: wait 1
       - else: exit
   - elif count >= 7 & win > 0: exit

## My experience:

I have found that it is much more profitable to take the 2-3 percent in a trade and exit accordingly than to wait any longer!

Of course, you sometimes miss out on larger price jumps because the strategy exits too early.

But ultimately, the most common case is: Win Candle +0.5% -> Win Candle +1% -> Loose Candle -2% -> Loose -0.5% ... -> Up to a total of Loose -5% and thus the stop loss (stated at the top of the strategy with: -0.05) occurs.

Over a longer period of time, any trade that makes a profit (no matter how small it may be...) is far better than a trade that results in a loss.

Small things also make a big difference, as can easily be seen from the backtest profits 01.02.2023 - 01.12.2023 & 01.01.2024 - 08.10.2024.

They achieved incredible 2663% and 2328% profits. What that means in USDT: Started with 100 USDT, ended with 2763 USDT & 2428 USDT!

## Background Infos:

Some people may ask themselves whether the profits achieved by the backtests are realistic at all? And if so, how do they come about?

Let's assume that the trades yield around 3% profit. And we win every trade. We win 1 trade every day, which would result in a profit of (around) 100% in 30 days. Ergo (starting with 100): 200.

If the bot continues testing because the period is not yet over, the result is that the same 3% now results in trades with 6% because the amount of USDT used is twice as high as at the beginning.

This means that only half as many winning trades are needed to reach this 100% (100 USDT) again. If you just keep calculating, there will always come a point where the profits reach astronomical proportions

because if we invest 10 times 100 USDT and reach our 3% again, the trade will be 30% if we use our 100 USDT as a benchmark... 3% of 1000 USDT = 30 USDT, which in turn is 30% of 100 USDT. Actually, it makes 

sense, right? You just have to keep in mind that freqtrade derives the percentages from the starting capital (i.e. 100 USDT) in the balance sheet... To illustrate this again: starting with 100 USDT, we are at 

1000 USDT and we lose a trade with -1.5%, which in turn is 1000 USDT = 15 USDT. So the trade is shown as -15%, which is correct because -15 USDT out of an initial 100 USDT is -15%. If you want to see what 

percentage the trade actually ends at, you have to look at the "Avg Profit %". This shows you how much profit you can expect from this pair (in this scenario still 3%) ;-)

So that's all from me for now...

Always stay creamy :D
