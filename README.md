# CryptoBot - SuperTrend Algorithm

---

## Welcome to the CryptoBot-SuperTrend Readme! :robot:

The purpose of this repository is to document the development of our very first trading bot. The bot will be broken out into 3 broad classes:

1. Data Class
2. Trade Strategy Class
3. Execution Class

### What's Needed?

Although our team is working very hard to get the fully user-friendly app deployed, there will still be plenty of time to test the bot on your own as we work through our goals and plans for the future. Feel free to fork, star, and/or watch for any of our updates here on GitHub. Here's what you'll currently need in order to execute the bot locally on your machine. (An introductory Python crash course probably wouldn't hurt.) If you do run, we seek your inputs, suggestions, and ideas that you can prove have a place in our code. Whether it's to help the bot run more efficiently or how we can better scale, your thoughts are welcome! This product is far from perfect, but with your support and growing interest we feel even more encouraged to get this out and running as smoothly as we can. Don't hesitate to contact us if there's anything we can do to help: contact@dascient.com

1. Latest Python (3.9.7)
2. Jupyter Notebook - Anaconda (mini-conda will certainly suffice)
3. Binance.US crypto brokerage account. (API_KEY, API_SECRET) 
4. Lastly, you'll need this repository. 

### SuperTrend - Data :computer:

This class will consist of a CCXT connection into Binance.US WebSocket interface that will feed live cryptocurrency data in the form of candle sticks; Open, High, Low, Close (OHLC).

We also apply rolling averages, upper/lower Bollinger bands, and binary variables that evaluates uptrend/downtrend intervals. 

### Trade Strategy :chart_with_upwards_trend:

Like many things in life, sometimes one needs a little variety. There is no shortage of trade strategies to apply to our bot. With this in mind, the strategy class will be designed to be modular.
That is, it is to be developed with "plug-and-play" design in order to develop different trading strategies over time. As long as the strategy sends a buy/sell signal for the execution, it will function properly.

### Execution :moneybag:

Once the trade signal is sent, the execution class with send the order to Binance.US via ccxt.exchange. For this execution to work, the user will need to verify their identity at CryBot startup.

Relax, have fun, and don't forget to drink plenty of water! :tada::rocket::full_moon:
