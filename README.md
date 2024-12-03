# freqtrade-strategie

## Technische Informationen

### E0V1E Strategie

Was hab ich genau an der Ursprünglichen strategie von ssssi geändert?

1. In der custom_exit function ermittel ich den open_candle um den trade ggf. in TMP_HOLD auf zu nehmen. Mit open_candle ist der candle gemeint er zum Zeitpunkt des Kaufbefehles aktuell war.

Das ist insofern nützlich wenn man den Bot restartet oder die config reloaded wird TMP_HOLD resettet & um fehlsignale zu vermeiden wird halt der open_candle überprüft und nicht der current_candle (welcher sowieso nur der last_candle, der geschlossen ist ... )

2. Habe ich auch in der custom_exit function die ermittelung des "wirklichen" current_candle integriert. Damit ist der candle gemeint der momentan noch nicht geschlossen ist. 

Den zusätzlichen candle nutzen wir nun um nun den slippage zu vermeiden, der alle 5 min durch die neuberechnung aller Coins entsteht. Indem 5 sek bevor die neuen candle data rein kommen (und somit freqtrade alles von neuem berechnet) fastk zu ermitteln und ggf. den market exit kurz vor candle close zu befehlen.

Denn je nach Coin menge die ihr gleichzeitig beobachtet kann die Berechnung alle 5 min bis zu 30 sek in anspruch nehmen. (je nach system bestimmt auch länger ...)

Der slippage wird dadurch von +30 nach candle close auf -5 sek vor next candle close reduziert. Was gerade bei den market orders um einiges genauer ist. Bzw. die exit rate viel näher an der erwarteten exit rate ist ... ;-)

### Hier mal ein paar tage mit 5 sec funktion & original E0V1E strategie mit den selben configs im direkt vergleich:

Regular :

Day (count)      USDT           USD          Profit %

---------------  -------------  -----------  ----------

2024-11-29 (2)   39.026 USDT    39.03 USD    4.10%

2024-11-28 (6)   17.443 USDT    17.44 USD    1.87%

2024-11-27 (9)   41.786 USDT    41.79 USD    4.69%

2024-11-26 (10)  -46.811 USDT   -46.81 USD   -4.99%

2024-11-25 (14)  61.347 USDT    61.35 USD    6.99%

2024-11-24 (12)  -139.507 USDT  -139.51 USD  -13.72%

2024-11-23 (6)   23.405 USDT    23.40 USD    2.36%

Test 5 secondes : 

Day (count)      USDT          USD         Profit %

---------------  ------------  ----------  ----------

2024-11-29 (1)   3.169 USDT    3.17 USD    0.28%

2024-11-28 (6)   46.758 USDT   46.80 USD   4.35%

2024-11-27 (9)   43.052 USDT   43.10 USD   4.17%

2024-11-26 (10)  -21.676 USDT  -21.70 USD  -2.06%

2024-11-25 (14)  78.415 USDT   78.49 USD   8.04%

2024-11-24 (13)  -81.663 USDT  -81.74 USD  -7.72%

2024-11-23 (12)  68.532 USDT   68.60 USD   6.93%

### Mir ist zudem aufgefallen wenn ich die E0V1E Strategie mit max_open_trades 1 anstatt 2 laufen lasse (stake_amount immernoch auf unlimited!) Dann erhöhe ich damit die profit ratio um ca. das 10x (man siehe den letzten backtest der unglaublich 100.000% profit in einem Jahr abwirft, hingegen max_open_trades 2 es nur auf ca. 8000% im selben zeitraum schafft ...)

## Backtest Results Information

### Die Backest's mit den Strategien: FakeoutStrategy & ElliotV8_original_ichiv3 sind komplett Falsch und sollten niemals im Live Trade Mode angewand werden!

ElliotV8_original_ichiv3 ersetzt Open/High/Low mit heikinashi werten was im Backtest zu komplett falschen berechnungswerten im Profit führt ...

FakeoutStrategy schaut in die Zukunft was im Live Mode niemals funktionieren wird :-D

### Die E0V1E von ssssi (ssssi/freqtrade_strs) ist mit Abstand die beste Strategie, nachfolgend von NASOSv5_mod3 die zwar nicht halb so viele signale erzeugt, aber trotzdem beide eine Win Ratio von ~90% aufweisen. Die E0V1E Strategie nutze ich momentan im Live Mode, sie funktioniert sehr gut wie man unschwer an dem png erkennen kann. Die im Real Live erzeugten Signale sind "echte" Trades mit meinem Invest (ca. 300 USDT) ...

### Die NASOSv5_mod3 Signale lassen sich im prinzip gut mit denen von E0V1E ergänzen da das ewo_1 signal zu den buy_1 signalen viele zusätzliche erzeugt ! Ich bleibe aber Safe und nutze nur buy_1 von E0V1E, welche am 14-15.11.2024 an zwei Tagen 20% gewinne erzeugt hat ;-)

![LiveTrade Result](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main/user_data/E0V1E_LiveRun_and_backtest_results-2024-11-14_2024-11-16.png)

### Background Infos:

Der PROS/USDT & VITE/USDT Trade auf der RealLive Seite sind falsche Trades gewesen weil ich dummy mal wieder im Prozess rum werckeln musste was zu abweichungen und verlusten geführt hat ... Die dafür gezeigten Trades auf der Backtest Seite, sind falsch ausgewählt da die Timeline nicht stimmt ... Hab sie nur zum fill in eigefügt, aber wie gesagt falsch ...

Zudem sind alle force_exit Sell's auch auf meinem Mist gewachsen weil ich vor Candle Close die trades beendet habe und deshalb immer bisschen weniger rein geholt habe als möglich gewesen wäre, da zu früh ausgestiegen ...

Der force_exit auf der Backtest Seite resultiert aus dem Backtest ende bzw. data end ...

Alle trades die der bot in real live abgeschlossen hat sind zu 90% der Fälle sogar besser als der auf der Backtest Seite gezeigten Trades ! Mal schaun ob das so bleibt ;-)

Die Daten aus dem Bild sind von 2 Tagen und haben insgesamt 20% Profit in diesen erzeugt ....!

![LiveTrade Result 2](https://raw.githubusercontent.com/Mastaaa1987/freqtrade-strategie/refs/heads/main/user_data/E0V1E_LiveRun_and_backtest_results-2024-11-16_2024-11-22.png)

Hier nun die nächsten tage im Live Trade ...

Diesmal keine lust gehabt alles ggn über zu stellen, das mega viel arbeit, deshalb nur die hälfte geschafft :-D
