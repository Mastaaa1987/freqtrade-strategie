# freqtrade-strategie

## Technische Informationen

### KamaFama Strategie

Momentan gibt's noch nicht viel zu sagen außer wenn ihr auch gemerkt habt das die E0V1E mehr verspricht als sie hält, dann solltet ihr euch mal meine neuste Strategie an schauen. Sie verspricht zwar nicht all zu hohe win ratio (ca. 66%) aber dafür schreibt sie über das ganze Jahr eine nette Profit Ratio auch wenn man 250 Pairs laufen hat.

Ich werde bei Zeiten ein paar dry_run Test's Ergebnisse posten.

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
* Day ----- (count) ---- USDT --------- USD ------- Profit %
* 2024-11-28 (6) __ 17.443 USDT ___ 17.44 USD ___ 1.87%
* 2024-11-27 (9) __ 41.786 USDT ___ 41.79 USD ___ 4.69%
* 2024-11-26 (10) _ -46.811 USDT _ -46.81 USD __ -4.99%
* 2024-11-25 (14) _ 61.347 USDT ___ 61.35 USD ___ 6.99%
* 2024-11-24 (12) _ -139.507 USDT _ -139.51 USD -13.72%
* 2024-11-23 (6) __ 23.405 USDT ___ 23.40 USD ___ 2.36%

Test 5 secondes : 
* Day ----- (count) ---- USDT --------- USD ------ Profit %
* 2024-11-28 (6) __ 46.758 USDT __ 46.80 USD ___ 4.35%
* 2024-11-27 (9) __ 43.052 USDT __ 43.10 USD ___ 4.17%
* 2024-11-26 (10) _ -21.676 USDT _ -21.70 USD _ -2.06%
* 2024-11-25 (14) _ 78.415 USDT __ 78.49 USD ___ 8.04%
* 2024-11-24 (13) _ -81.663 USDT _ -81.74 USD _ -7.72%
* 2024-11-23 (12) _ 68.532 USDT __ 68.60 USD ___ 6.93%

### Heute noch nachträglich herein gekommen ...

For me with your conf : 
* Day ----- (count) ---- USDT --------- USD ------ Profit %
* 2024-12-03 (10) _ 106.765 USDT _ 106.77 USD __ 12.00%
* 2024-12-02 (6) __ -31.298 USDT _ -31.30 USD __ -3.40%
* 2024-12-01 (2) __ -48.092 USDT _ -48.09 USD __ -4.96%
* 2024-11-30 (10) __ 66.297 USDT __ 66.30 USD ___ 7.35%
* 2024-11-29 (8) ___ -48.39 USDT _ -48.39 USD __ -5.09%
* 2024-11-28 (6) ___ 17.443 USDT __ 17.44 USD ___ 1.87%
* 2024-11-27 (9) ___ 41.786 USDT __ 41.79 USD ___ 4.69%

And 5 seconds test : 
* Day ----- (count) ---- USDT --------- USD ------ Profit %
* 2024-12-03 (11) _ 101.925 USDT _ 101.86 USD ___ 8.96%
* 2024-12-02 (5) ___ 25.712 USDT __ 25.70 USD ___ 2.31%
* 2024-12-01 (3) __ -55.023 USDT _ -54.99 USD __ -4.72%
* 2024-11-30 (11) __ 13.604 USDT __ 13.60 USD ___ 1.18%
* 2024-11-29 (5) ___ 31.872 USDT __ 31.85 USD ___ 2.84%
* 2024-11-28 (6) ___ 46.758 USDT __ 46.73 USD ___ 4.35%
* 2024-11-27 (9) ___ 43.052 USDT __ 43.03 USD ___ 4.18%

Wie man unschwer erkennen kann erzeugt die slippage funktion von mir an jedem Tag mehr Profite und teilweise sogar mehr Signale, das hängt damit zusammen das wenn der exit order 5 sec vor candle ende gegeben wird, der bot noch genug Zeit hat in einen anderen coin zu investieren der zufälligerweise noch einen buy befehl ist.

(Dies wäre nicht mehr der Fall wenn der candle geschlossen worden wäre & dann erst den exit order gegeben hätten ... Weil wir dann von der Zeit her 5 min in der Zukunft wären, dem kommen wir ja mit unserer 5 sek funktion zuvor ;-)

### Mir ist zudem aufgefallen wenn ich die E0V1E Strategie mit max_open_trades 1 anstatt 2 laufen lasse (stake_amount immernoch auf unlimited!) Dann erhöhe ich damit die profit ratio um ca. das 10x (man siehe den letzten backtest der unglaublich 100.000% profit in einem Jahr abwirft, hingegen max_open_trades 2 es nur auf ca. 8000% im selben zeitraum schafft ...)

# Backtest Results Information

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
