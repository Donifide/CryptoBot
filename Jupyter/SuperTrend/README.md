# CryptoBot - SuperTrend Algorithm

---

## Welcome to the CryptoBot-SuperTrend Readme! :robot:

The purpose of this repository is to document the development of our very first trading bot. The bot will be broken out into 3 broad classes:

1. Data Class
2. Trade Strategy Class
3. Execution Class

### SuperTrend - Data :computer:

This class will consist of a CCXT connection into Binance.US WebSocket interface that will feed live cryptocurrency data in the form of candle sticks; Open, High, Low, Close (OHLC).

We also apply rolling averages, upper/lower Bollinger bands, and binary variables that evaluates uptrend/downtrend intervals. 

### Trade Strategy :chart_with_upwards_trend:

Like many things in life, sometimes one needs a little variety. There is no shortage of trade strategies to apply to our bot. With this in mind, the strategy class will be designed to be modular.
That is, it is to be developed with "plug-and-play" design in order to develop different trading strategies over time. As long as the strategy sends a buy/sell signal for the execution, it will function properly.

### Execution :moneybag:

Once the trade signal is sent, the execution class with send the order to Binance.US via ccxt.exchange. For this execution to work, the user will need to verify their identity at CryBot startup.

Once properly authenticated, and trading strategy chosen, let the gains begin! :tada::rocket::full_moon:
